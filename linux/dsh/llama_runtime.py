"""Select the explicitly activated llama runtime before backend handover."""
import json
import os
import re
from pathlib import Path
import subprocess
import time
from hardware_guard import require_current_cuda_pair

ROOT = Path(__file__).resolve().parent
AMD = Path('/sys/bus/pci/devices/0000:03:00.0')



def select_vulkan_devices(binary, env, mixed=False):
    env = dict(env)
    env.pop('GGML_VK_VISIBLE_DEVICES', None)
    inventory = subprocess.run([str(binary), '--list-devices'], env=env,
                               capture_output=True, text=True, timeout=30, check=True)
    names = ['AMD Radeon RX 7900 XTX']
    if mixed:
        names.append('NVIDIA GeForce RTX 4070')
    indices = []
    for name in names:
        matches = re.findall(r'^\s*Vulkan(\d+): ' + re.escape(name) + r'(?:\s|\()',
                             inventory.stdout + inventory.stderr, re.MULTILINE)
        if len(matches) != 1:
            raise RuntimeError('Cannot uniquely identify ' + name + '; no backend has been stopped.')
        indices.append(matches[0])
    env['GGML_VK_VISIBLE_DEVICES'] = ','.join(indices)
    filtered = subprocess.run([str(binary), '--list-devices'], env=env,
                              capture_output=True, text=True, timeout=30, check=True)
    for index, name in enumerate(names):
        if f'Vulkan{index}: {name}' not in filtered.stdout + filtered.stderr:
            raise RuntimeError('Filtered Vulkan device identity changed; no backend has been stopped.')
    return env


def launch_spec():
    config = ROOT / 'llama-runtime.json'
    mode = json.loads(config.read_text())['backend'] if config.exists() else 'cuda'
    if mode == 'cuda':
        require_current_cuda_pair()
        return ROOT.parent / 'llama.cpp/llama-server', ROOT / 'models.ini', dict(os.environ), None
    if mode not in ('vulkan-amd', 'hip-amd'):
        raise RuntimeError('Unknown llama runtime selection; no backend has been stopped.')
    hip = mode == 'hip-amd'
    binary = ROOT.parent / ('llama.cpp/build-hip/bin/llama-server' if hip else 'llama.cpp/build-vulkan/bin/llama-server')
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
    if (not binary.is_file() or (AMD / 'vendor').read_text().strip() != '0x1002'
            or (AMD / 'driver').resolve().name != 'amdgpu'
            or int((AMD / 'mem_info_vram_total').read_text()) < 23 * 1024**3):
        raise RuntimeError('Selected 24 GB AMD runtime is unavailable; no backend has been stopped.')
    if hip:
        inventory = subprocess.run([str(binary), '--list-devices'], env=env,
                                   capture_output=True, text=True, timeout=30, check=True)
        if 'ROCm0: AMD Radeon RX 7900 XTX' not in inventory.stdout + inventory.stderr:
            raise RuntimeError('ROCm0 is not the validated 7900 XTX; no backend has been stopped.')
    else:
        env = select_vulkan_devices(binary, env)
    settings = json.loads(config.read_text())
    presets = ROOT / ('models-hip.ini' if hip else 'models-amd.ini')
    if not settings.get('models') or not presets.is_file():
        raise RuntimeError('No validated AMD model preset is activated.')
    return binary, presets, env, set(settings['models'])


def require_amd_headroom():
    total = int((AMD / 'mem_info_vram_total').read_text())
    mode = json.loads((ROOT / 'llama-runtime.json').read_text())['backend']
    required = (22.75 if mode == 'hip-amd' else 22.0) * 1024**3
    # Device enumeration/previous workers may release allocations asynchronously.
    for _ in range(50):
        used = int((AMD / 'mem_info_vram_used').read_text())
        if total - used >= required:
            return
        time.sleep(0.2)
    if total - used < required:
        raise RuntimeError('Insufficient free AMD VRAM for the validated llama.cpp profiles. Close GPU-heavy applications and retry; no unrelated application was stopped.')
