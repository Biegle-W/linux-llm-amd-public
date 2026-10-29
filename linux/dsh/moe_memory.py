"""Admit explicit CPU-backed or VRAM-only profiles and watch their owned workers."""
import json
from pathlib import Path
import threading
import time
from amd_memory import vram_accounting

ROOT = Path(__file__).resolve().parent
GIB = 1024**3


def vram_worker_limits(profile):
    placement = profile.get('memory_placement', 'cpu_ram_moe')
    if placement not in ('cpu_ram_moe', 'vram_only'):
        raise RuntimeError('Unknown MoE memory placement; no worker was changed.')
    if placement != 'vram_only':
        return None
    limits = profile.get('worker_memory_limits', {})
    expected = {'memory.high': 4*GIB, 'memory.max': 5*GIB, 'memory.swap.max': 'max'}
    if limits != expected or any(type(limits.get(k)) is not int for k in ('memory.high', 'memory.max')):
        raise RuntimeError('VRAM-only worker limits must match the validated 4/5 GiB RAM scope with phase-aware swap.')
    if (profile.get('host_expert_bytes') != 0 or profile.get('cpu_expert_layers') != [] or
            profile.get('gpu_expert_cache_mib') != 0 or
            profile.get('backend') != 'hip-amd' or
            profile.get('minimum_host_ram_gib', 0) < 12 or
            profile.get('minimum_available_ram_gib', 0) < 7 or
            profile.get('min_start_vram_gib', 0) < 21 or
            profile.get('min_free_vram_gib', 0) < 3):
        raise RuntimeError('VRAM-only placement must retain zero CPU experts and physical staging headroom.')
    return dict(limits)


def worker_limits_for_model(model):
    if model is None:
        return None  # An unloaded bootstrap router has no model placement yet.
    return vram_worker_limits(profiles().get(model, {}))


def require_model_capacity(model):
    """Reject a physically incompatible target before replacing a usable worker."""
    profile = profiles().get(model)
    if profile:
        total, available = host_memory()
        if total < profile.get('minimum_host_ram_gib', 28)*GIB:
            raise RuntimeError(memory_reason(profile, total, available))


def host_memory():
    values = {line.split(':')[0]: int(line.split()[1]) * 1024
              for line in Path('/proc/meminfo').read_text().splitlines()}
    return values['MemTotal'], values['MemAvailable']


def memory_reason(profile, total, available, already_loaded=False):
    minimum = profile.get('minimum_host_ram_gib', 28) * GIB
    if total < minimum:
        return f'MoE profile requires at least {minimum/GIB:g} GiB OS-visible RAM; found {total/GIB:.1f} GiB.'
    gpu = vram_worker_limits(profile) is not None
    reserve = (3*GIB if already_loaded else profile['minimum_available_ram_gib']*GIB) if gpu else (
        3*GIB if already_loaded else profile['host_expert_bytes'] + 4*GIB)
    if available < reserve:
        purpose = 'VRAM-only loading/staging' if gpu else 'MoE CPU expert storage'
        return (f'{purpose} requires {reserve/GIB:.1f} GiB available RAM '
                f'({available/GIB:.1f} GiB available). Close memory-heavy applications and retry; '
                'swap is not counted as expert capacity.')
    return None


def profiles():
    path = ROOT / 'moe-offload.json'
    return json.loads(path.read_text())['models'] if path.exists() else {}


def validate_profiles(root=None):
    """Reject implicit placement changes; GPU-only needs its own bounded plan."""
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
        if not plan:
            raise RuntimeError(f"MoE {model['id']} requires explicit CPU expert backing and a GPU expert cache; no backend was stopped.")
        mode = plan.get('memory_placement', 'cpu_ram_moe')
        if mode not in ('cpu_ram_moe', 'vram_only'):
            raise RuntimeError('Unknown MoE memory placement; no backend was stopped.')
        name = 'models-hip.ini' if plan['backend'] == 'hip-amd' else 'models-amd.ini'
        text = (root/name).read_text()
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.read_string(text[text.index('[*]'):])
        section = cfg[model['id']]
        cache = int(section.get('moe-cache-mib', cfg['*'].get('moe-cache-mib', '0')))
        placement = section.get('override-tensor', '')
        if mode == 'vram_only':
            vram_worker_limits(plan)
            required = {'device':'ROCm0,ROCm1', 'split-mode':'layer', 'tensor-split':'1,1',
                        'n-gpu-layers':'99', 'fit':'off', 'n-cpu-moe':'0', 'load-mode':'dio',
                        'ctx-size':str(model['context']), 'batch-size':str(plan['batch_size']),
                        'ubatch-size':str(plan['ubatch_size']),
                        'spec-type':'draft-mtp' if model.get('mtp') else 'none'}
            if model.get('mtp'):
                required['spec-draft-n-max'] = '3'
            if 'reasoning_budget_tokens' in plan:
                budget = plan['reasoning_budget_tokens']
                if type(budget) is not int or not 0 <= budget <= 128 or model.get('reasoning_budget') != budget:
                    raise RuntimeError('VRAM-only reasoning budget differs from the bounded model plan.')
                required.update({'reasoning-budget':str(budget), 'reasoning':'on' if budget else 'off'})
            effective = lambda key: section.get(key, cfg['*'].get(key, ''))
            if (cache != 0 or 'CPU' in placement or placement != 'token_embd.*=ROCm0' or
                    model.get('memory_category') != 'vram_only' or plan['context'] != model['context'] or
                    any(effective(k) != v for k,v in required.items())):
                raise RuntimeError(f"MoE {model['id']} VRAM-only preset no longer matches its bounded placement plan.")
            continue
        if not plan.get('cpu_expert_layers') or plan.get('gpu_expert_cache_mib', 0) <= 0:
            raise RuntimeError(f"MoE {model['id']} requires explicit CPU expert backing and a GPU expert cache; no backend was stopped.")
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


def worker_memory(pid, *, proc_root=Path('/proc')):
    """Read swap and dedicated-VRAM residency for this parent and its descendants."""
    parents = {}
    for path in proc_root.iterdir():
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
        base = proc_root / str(child)
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
                nonresident += vram_accounting(fields)['spill']
        except OSError:
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
        from strata_memory import MemoryGuard, vram_snapshot
        gpu_guard = MemoryGuard()
        while not done.wait(1):
            if proc.poll() is not None:
                return
            profile = profiles().get(active_model())
            if not profile:
                low = 0
                continue
            try:
                _, available = host_memory()
                swap, spill = worker_memory(proc.pid)
            except Exception as error:
                print('MoE worker memory telemetry unavailable: '+type(error).__name__+'; stopping only the owned worker.', flush=True)
                stop(proc)
                return
            if profile.get('memory_placement') == 'vram_only':
                try:
                    reason = gpu_guard.check(available, swap, spill, vram_snapshot())
                    if spill:
                        reason = 'VRAM-only dedicated-VRAM spill'
                except Exception as error:
                    reason = 'VRAM-only telemetry unavailable: '+type(error).__name__
                if reason:
                    print('VRAM-only memory guard: '+reason+'; stopping only the owned worker.', flush=True)
                    stop(proc)
                    return
                continue
            vram_reason = vram_headroom_reason(profile)
            low = low + 1 if available < 3*GIB or vram_reason else 0
            spill_count = spill_count + 1 if spill > 256*1024**2 else 0
            if low >= 3 or spill_count >= 3:
                print(f'MoE memory guard: available={available/GIB:.2f} GiB, '
                      f'owned swap={swap/1024**2:.0f} MiB, dedicated VRAM spill={spill/1024**2:.0f} MiB. '
                      f'{vram_reason or ""} '
                      'Stopping only this native model worker; DSH and other apps remain.', flush=True)
                stop(proc)
                return
    threading.Thread(target=monitor, daemon=True).start()
    return done
