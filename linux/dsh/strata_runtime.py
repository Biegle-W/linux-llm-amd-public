"""Admit the bounded dual-HIP Strata profile before any backend handover."""
import json
import os
import shutil
import subprocess
from pathlib import Path
from amd_device import amd_devices
from moe_memory import host_memory
from streaming_memory import check_32gb

ROOT = Path(__file__).resolve().parent.parent
GIB = 1024**3


def kv_backing_gib(cfg):
    """Budget full host backing when the KV context exceeds the resident window.

    Twelve target QSA layers plus the INT8 draft layer; matches the installed
    engine's streaming layout. The pinned host copy covers the full context.
    """
    args = cfg['args']
    def value(flag, default):
        return args[args.index(flag) + 1] if flag in args else default
    context = int(value('--max-context', 32768))
    resident = int(value('--kv-resident', context))
    if not 0 < resident < context:
        return 0.0
    cell = {'int8': 1056, 'q4_0': 576, 'k8v4': 816}.get(value('--kv', 'int8'))
    if cell is None:
        raise RuntimeError('Unsupported KV format in the bounded Strata profile.')
    return context * (12 * cell + 1056) / GIB


def memory_blockers(total, available, minimum=29, budget=8, *, check_available=True, kv_gib=0):
    problems = []
    if total < minimum * GIB:
        problems.append(f'Strata needs {minimum:g} GiB OS-visible RAM for this profile; found {total/GIB:.1f}.')
    required = budget + kv_gib + 6
    if check_available and available < required * GIB:
        problems.append(f'Strata needs {required:.2f} GiB available RAM before loading '
                        f'({budget:g} GiB expert budget, {kv_gib:.2f} GiB host KV and 6 GiB headroom); '
                        f'found {available/GIB:.1f}. '
                        'Swap does not replace physical RAM.')
    return problems


def check_config(cfg, total, available, *, check_available=True):
    if (cfg.get('backend') != 'hip' or cfg.get('gpu') != [0, 1]
            or cfg.get('split_skip_if_fits') or cfg.get('parallel') != 1):
        raise RuntimeError('Strata requires the dual-AMD HIP profile with one session and no single-card fallback.')
    if 'worker_swap_max_bytes' not in cfg or cfg['worker_swap_max_bytes'] is not None:
        raise RuntimeError('Strata uses phase-aware swap without a fixed resident-byte cap.')
    args = cfg['args']
    reserve = int(args[args.index('--vram-reserve-mib') + 1]) if '--vram-reserve-mib' in args else 0
    later = int(args[args.index('--vram-reserve-later-mib') + 1]) if '--vram-reserve-later-mib' in args else reserve
    if min(reserve, later) < 6144:
        raise RuntimeError('Strata must reserve at least 6 GiB on each desktop/inference GPU.')
    if '--resident-cpu-experts' not in args or '--resident-budget-gib' not in args:
        raise RuntimeError('Strata requires bounded CPU expert backing plus GPU expert caching.')
    budget = float(args[args.index('--resident-budget-gib') + 1])
    if not 0 < budget <= 24:
        raise RuntimeError('Unexpected Strata expert RAM budget.')
    check_32gb(cfg, total, available, 'qwen', check_available=check_available)
    problems = memory_blockers(total, available, cfg['minimum_host_ram_gib'], budget,
                               check_available=check_available, kv_gib=kv_backing_gib(cfg))
    if problems:
        raise RuntimeError(' '.join(problems))


def require_strata(before_handover=False,model=None):
    profiles = json.loads((ROOT / 'dsh/strata-profiles.json').read_text())
    enabled = {k:p for k,p in profiles.items() if p.get('enabled', True)}
    if len([p for p in enabled.values() if p.get('family')!='deepseek41'])!=1:
        raise RuntimeError('Exactly one validated Strata Qwen profile must be enabled. No backend has been stopped.')
    selected=model or next(iter(enabled))
    if selected not in enabled:
        raise RuntimeError('Unknown or disabled Strata profile. No backend has been stopped.')
    profile=enabled[selected]
    if profile.get('family')=='deepseek41':
        from strata_ds41_runtime import require_profile
        cfg=json.loads((ROOT/'dsh'/profile['config']).read_text())
        if cfg['model_name']!=selected or profile['context']!=32768:
            raise RuntimeError('Strata DeepSeek catalog and sealed model/context must match.')
        return require_profile(cfg,before_handover=before_handover)
    # STRATA_PROFILE_CONFIG permits an isolated candidate check before promotion,
    # like LLAMA_CPP_DIR/VLLM_ENV_PATH; its own RAM gate and guards still apply.
    cfg = json.loads((ROOT / 'dsh' / (os.environ.get('STRATA_PROFILE_CONFIG') or profile['config'])).read_text())
    # Old managed weights may occupy the available RAM; check it strictly only
    # after handover, while always rejecting insufficient physical capacity first.
    check_config(cfg, *host_memory(), check_available=not before_handover)
    amd_devices()
    if not shutil.which('systemd-run'):
        raise RuntimeError('Strata requires systemd-run for its worker-only no-swap scope.')
    try:
        subprocess.run(['systemctl', '--user', 'is-active', 'default.target'],
                       check=True, capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError('The user service manager is unavailable; cannot enforce Strata-only no-swap.') from error
    if not os.access('/dev/kfd', os.R_OK | os.W_OK):
        raise RuntimeError('Strata requires KFD access. No backend has been stopped.')
    engine = Path(cfg['exe'])
    if engine != ROOT / 'strata/build-hip/strata' or not os.access(engine, os.X_OK):
        raise RuntimeError('The retained Strata HIP executable is unavailable.')
    args = cfg['args']
    paths = {name: Path(args[args.index(name) + 1]) for name in ('--pack', '--native', '--ple-gguf', '--mtp')}
    required = [paths['--native'], paths['--ple-gguf'], paths['--pack']/'dense.bin',
                paths['--pack']/'experts.bin', paths['--mtp']/'dense.bin',
                paths['--mtp']/'experts.bin', paths['--mtp']/'draft_vocab.bin',
                Path(cfg['tokenizer'])/'tokenizer.json']
    if not all(p.is_file() and p.stat().st_size for p in required):
        raise RuntimeError('Retained Strata Q3 assets are missing. Check the Shared drive.')
    return cfg
