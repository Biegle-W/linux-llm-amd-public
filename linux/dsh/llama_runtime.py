"""Select the explicitly activated llama runtime before backend handover."""
import json
import os
import re
import shutil
from pathlib import Path
import subprocess
import time
from hardware_guard import require_current_cuda_pair

from amd_device import amd_devices
from moe_memory import validate_profiles

ROOT = Path(__file__).resolve().parent


def require_worker_scope():
    """Verify that the owned AMD worker can be protected from swap before handover."""
    if not shutil.which('systemd-run'):
        raise RuntimeError('AMD llama.cpp requires systemd-run for its worker-only no-swap scope.')
    try:
        subprocess.run(['systemctl', '--user', 'is-active', 'default.target'],
                       check=True, capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError('The user service manager is unavailable; cannot enforce llama.cpp-only no-swap. No backend has been stopped.') from error



def select_vulkan_devices(binary, env, mixed=False):
    env = dict(env)
    env.pop('GGML_VK_VISIBLE_DEVICES', None)
    inventory = subprocess.run([str(binary), '--list-devices'], env=env,
                               capture_output=True, text=True, timeout=30, check=True)
    if mixed:
        raise RuntimeError('Mixed-vendor profiles are retired.')
    names = ['AMD Radeon RX 7900 XTX']
    indices = []
    for name in names:
        matches = re.findall(r'^\s*Vulkan(\d+): ' + re.escape(name) + r'(?:\s|\()',
                             inventory.stdout + inventory.stderr, re.MULTILINE)
        if len(matches) != 2:
            raise RuntimeError('Expected exactly two devices named ' + name + '; no backend has been stopped.')
        indices.extend(matches)
    env['GGML_VK_VISIBLE_DEVICES'] = ','.join(indices)
    filtered = subprocess.run([str(binary), '--list-devices'], env=env,
                              capture_output=True, text=True, timeout=30, check=True)
    for index, name in enumerate(['AMD Radeon RX 7900 XTX'] * 2):
        if f'Vulkan{index}: {name}' not in filtered.stdout + filtered.stderr:
            raise RuntimeError('Filtered Vulkan device identity changed; no backend has been stopped.')
    return env


def runtime_source(model=None):
    """Select a model-qualified source; explicit test overrides take precedence."""
    override = os.environ.get('LLAMA_CPP_DIR')
    if override:
        return Path(override).resolve(), None
    config = ROOT / 'llama-runtime.json'
    settings = json.loads(config.read_text()) if config.exists() else {}
    selected = settings.get('source_overrides', {}).get(model)
    if selected:
        path, commit = selected['path'], selected['source_commit']
        if not Path(path).is_absolute() or not re.fullmatch(r'[0-9a-f]{40}', commit):
            raise RuntimeError('Invalid qualified llama source path/pin; no worker was changed.')
        return Path(path).resolve(), commit
    return (ROOT.parent / 'llama.cpp').resolve(), None


def runtime_identity(mode, model=None):
    source, commit = runtime_source(model)
    # Check even when reusing a parent: a later child may exec this path.
    verify_source_pin(source, commit)
    return mode, str(source), commit


def verify_source_pin(source, commit):
    if commit:
        actual = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'],
                                         text=True, timeout=10).strip()
        if actual != commit:
            raise RuntimeError('Qualified llama source revision changed; no worker was changed.')


def launch_spec(backend=None, model=None):
    config = ROOT / 'llama-runtime.json'
    settings = json.loads(config.read_text()) if config.exists() else {}
    paused = settings.get('paused_models', {})
    if model in paused:
        raise RuntimeError(paused[model])
    mode = backend or (settings['backend'] if config.exists() else 'cuda')
    if mode == 'cuda':
        require_current_cuda_pair()
        return ROOT.parent / 'llama.cpp/llama-server', ROOT / 'models.ini', dict(os.environ), None
    if mode not in ('vulkan-amd', 'hip-amd'):
        raise RuntimeError('Unknown llama runtime selection; no backend has been stopped.')
    require_worker_scope()
    validate_profiles(ROOT)
    hip = mode == 'hip-amd'
    # LLAMA_CPP_DIR permits isolated candidate checks before promotion, like VLLM_ENV_PATH.
    source, commit = runtime_source(model)
    verify_source_pin(source, commit)
    binary = source / ('build-hip/bin/llama-server' if hip else 'build-vulkan/bin/llama-server')
    env = dict(os.environ)
    for name in ('GGML_VK_PREFER_HOST_MEMORY', 'GGML_VK_ALLOW_SYSMEM_FALLBACK',
                 'GGML_VK_DISABLE_HOST_VISIBLE_VIDMEM', 'GGML_VK_VISIBLE_DEVICES'):
        env.pop(name, None)
    env['LD_LIBRARY_PATH'] = ':'.join(str(ROOT.parent / p) for p in
        ('llm-tools/vulkan-sdk/usr/lib/x86_64-linux-gnu', 'llm-tools/cuda-build/lib'))
    if hip:
        # Reuse the isolated SDK environment without importing PyTorch into the router.
        result = subprocess.run(['bash', '-c', 'source "$1"; env -0', 'bash',
                                 str(ROOT.parent / 'hardware/rocm-env.sh')],
                                capture_output=True, check=True, timeout=10)
        env = dict(item.decode().split('=', 1) for item in result.stdout.split(b'\0') if item)
        env['LD_LIBRARY_PATH'] += ':' + str(ROOT.parent / 'llm-tools/cuda-build/lib')
        env.pop('GGML_CUDA_ENABLE_UNIFIED_MEMORY', None)
    devices = amd_devices()
    if (not binary.is_file() or len(devices) != 2):
        raise RuntimeError('Selected 24 GB AMD runtime is unavailable; no backend has been stopped.')
    if hip:
        inventory = subprocess.run([str(binary), '--list-devices'], env=env,
                                   capture_output=True, text=True, timeout=30, check=True)
        if any(f'ROCm{i}: AMD Radeon RX 7900 XTX' not in inventory.stdout + inventory.stderr for i in range(2)):
            raise RuntimeError('Both ROCm devices must be 7900 XTX cards; no backend has been stopped.')
    else:
        env = select_vulkan_devices(binary, env)
    settings = json.loads(config.read_text())
    presets = ROOT / ('models-hip.ini' if hip else 'models-amd.ini')
    if not settings.get('models') or not presets.is_file():
        raise RuntimeError('No validated AMD model preset is activated.')
    return binary, presets, env, set(settings['models']) - set(settings.get('paused_models', {}))


def require_amd_headroom():
    devices = amd_devices()
    required = 18 * 1024**3
    for _ in range(50):
        free = [int((d / 'mem_info_vram_total').read_text()) -
                int((d / 'mem_info_vram_used').read_text()) for d in devices]
        if min(free) >= required:
            return
        time.sleep(0.2)
    raise RuntimeError('Dual-AMD llama.cpp requires 18 GiB free VRAM on each card. '
                       'No unrelated application was stopped.')
