"""Admit CPU expert storage and monitor only the managed llama.cpp worker tree."""
import json
from pathlib import Path
import threading
import time

ROOT = Path(__file__).resolve().parent
GIB = 1024**3


def host_memory():
    values = {line.split(':')[0]: int(line.split()[1]) * 1024
              for line in Path('/proc/meminfo').read_text().splitlines()}
    return values['MemTotal'], values['MemAvailable']


def memory_reason(profile, total, available, already_loaded=False):
    minimum = profile.get('minimum_host_ram_gib', 28) * GIB
    if total < minimum:
        return f'MoE profile requires at least {minimum/GIB:g} GiB OS-visible RAM; found {total/GIB:.1f} GiB.'
    reserve = 3 * GIB if already_loaded else profile['host_expert_bytes'] + 4 * GIB
    if available < reserve:
        return (f'MoE CPU expert storage requires {reserve/GIB:.1f} GiB available RAM '
                f'({available/GIB:.1f} GiB available). Close memory-heavy applications and retry; '
                'swap is not counted as expert capacity.')
    return None


def profiles():
    path = ROOT / 'moe-offload.json'
    return json.loads(path.read_text())['models'] if path.exists() else {}


def validate_profiles(root=None):
    """Reject catalogued MoE entries that silently lost CPU backing or their cache."""
    import configparser
    root = ROOT if root is None else Path(root)
    catalog = root/'models.json'
    if not catalog.exists():
        return
    models = json.loads(catalog.read_text())
    path = root/'moe-offload.json'
    plans = json.loads(path.read_text())['models'] if path.exists() else {}
    for model in models:
        if not model.get('enabled', True) or not model.get('expert_count', 0):
            continue
        plan = plans.get(model['id'])
        if not plan or not plan.get('cpu_expert_layers') or plan.get('gpu_expert_cache_mib', 0) <= 0:
            raise RuntimeError(f"MoE {model['id']} requires explicit CPU expert backing and a GPU expert cache; no backend was stopped.")
        name = 'models-hip.ini' if plan['backend'] == 'hip-amd' else 'models-amd.ini'
        text = (root/name).read_text()
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.read_string(text[text.index('[*]'):])
        section = cfg[model['id']]
        cache = int(section.get('moe-cache-mib', cfg['*'].get('moe-cache-mib', '0')))
        placement = section.get('override-tensor', '')
        if cache != plan['gpu_expert_cache_mib'] or '=CPU' not in placement:
            raise RuntimeError(f"MoE {model['id']} preset no longer matches its CPU/cache policy; no backend was stopped.")


def admit_model(model, call, port):
    """Unload an idle, managed old model only if needed to admit the next MoE."""
    profile = profiles().get(model)
    if not profile:
        return
    total, available = host_memory()
    # Reject a 64 GB-only candidate without unloading a usable current model.
    if total < profile.get('minimum_host_ram_gib', 28) * GIB:
        raise RuntimeError(memory_reason(profile, total, available))
    data = call(port, '/v1/models')['data']
    loaded = [item['id'] for item in data
              if item.get('status', {}).get('value') == 'loaded']
    same = model in loaded
    reason = memory_reason(profile, total, available, same)
    if not same:
        reason = reason or vram_headroom_reason(profile, 'min_start_vram_gib')
    if reason and not same:
        for previous in loaded:
            if previous != model:
                call(port, '/models/unload', {'model': previous}, timeout=60)
        for _ in range(20):
            total, available = host_memory()
            reason = memory_reason(profile, total, available)
            reason = reason or vram_headroom_reason(profile, 'min_start_vram_gib')
            if not reason:
                break
            time.sleep(.25)
    if reason:
        raise RuntimeError(reason)


def worker_memory(pid):
    """Read swap and dedicated-VRAM residency for this parent and its descendants."""
    parents = {}
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
            parents[int(path.name)] = int(fields[1])
        except (OSError, ValueError, IndexError):
            continue
    owned = {pid}
    while True:
        more = {child for child, parent in parents.items() if parent in owned} - owned
        if not more:
            break
        owned.update(more)
    swap = nonresident = 0
    clients = set()
    for child in owned:
        base = Path('/proc') / str(child)
        try:
            for line in (base/'status').read_text().splitlines():
                if line.startswith('VmSwap:'):
                    swap += int(line.split()[1]) * 1024
            for info in (base/'fdinfo').iterdir():
                fields = dict(line.split(':', 1) for line in info.read_text().splitlines() if ':' in line)
                if fields.get('drm-driver', '').strip() != 'amdgpu':
                    continue
                client = (fields.get('drm-pdev'), fields.get('drm-client-id'))
                if client in clients:
                    continue
                clients.add(client)
                total = int(fields.get('drm-total-vram', '0').split()[0]) * 1024
                resident = int(fields.get('drm-resident-vram', '0').split()[0]) * 1024
                nonresident += max(0, total-resident)
        except (OSError, ValueError, IndexError):
            continue
    return swap, nonresident


def vram_headroom_reason(profile, reserve_key='min_free_vram_gib'):
    """Optional whole-card reserve, including desktop and unrelated GPU users."""
    reserve = profile.get(reserve_key, 0) * GIB
    if not reserve:
        return None
    from amd_device import amd_devices
    try:
        for device in amd_devices():
            free = int((device/'mem_info_vram_total').read_text()) - int((device/'mem_info_vram_used').read_text())
            if free < reserve:
                return f'MoE requires {reserve/GIB:g} GiB free VRAM per card; {device.name} has {free/GIB:.2f} GiB.'
    except (OSError, RuntimeError, ValueError) as error:
        return f'Cannot verify the required per-card VRAM reserve: {error}'
    return None


def watch_worker(proc, active_model, stop):
    """Stop only the owned native parent when CPU residency becomes unsafe."""
    done = threading.Event()

    def monitor():
        low = spill_count = 0
        while not done.wait(1):
            if proc.poll() is not None:
                return
            profile = profiles().get(active_model())
            if not profile:
                low = 0
                continue
            _, available = host_memory()
            swap, spill = worker_memory(proc.pid)
            vram_reason = vram_headroom_reason(profile)
            low = low + 1 if available < 3*GIB or vram_reason else 0
            spill_count = spill_count + 1 if spill > 256*1024**2 else 0
            if low >= 3 or swap > 256*1024**2 or spill_count >= 3:
                print(f'MoE memory guard: available={available/GIB:.2f} GiB, '
                      f'owned swap={swap/1024**2:.0f} MiB, dedicated VRAM spill={spill/1024**2:.0f} MiB. '
                      f'{vram_reason or ""} '
                      'Stopping only this native model worker; DSH and other apps remain.', flush=True)
                stop(proc)
                return
    threading.Thread(target=monitor, daemon=True).start()
    return done
