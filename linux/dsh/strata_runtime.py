"""Admit the bounded dual-HIP Strata profile before any backend handover."""
import json
import os
import shutil
import subprocess
from pathlib import Path
from amd_device import amd_devices
from moe_memory import host_memory

ROOT = Path(__file__).resolve().parent.parent
GIB = 1024**3


def memory_blockers(total, available, minimum=29, budget=8, *, check_available=True):
    problems = []
    if total < minimum * GIB:
        problems.append(f'Strata needs {minimum:g} GiB OS-visible RAM for this profile; found {total/GIB:.1f}.')
    if check_available and available < (budget + 6) * GIB:
        problems.append(f'Strata needs {budget+6:g} GiB available RAM before loading '
                        f'({budget:g} GiB expert budget plus 6 GiB headroom); found {available/GIB:.1f}. '
                        'Swap does not replace physical RAM.')
    return problems


def check_config(cfg, total, available, *, check_available=True):
    if (cfg.get('backend') != 'hip' or cfg.get('gpu') != [0, 1]
            or cfg.get('split_skip_if_fits') or cfg.get('parallel') != 1):
        raise RuntimeError('Strata requires the dual-AMD HIP profile with one session and no single-card fallback.')
    if cfg.get('worker_swap_max_bytes') != 0:
        raise RuntimeError('Strata must retain its worker-only no-swap policy.')
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
    problems = memory_blockers(total, available, cfg['minimum_host_ram_gib'], budget,
                               check_available=check_available)
    if problems:
        raise RuntimeError(' '.join(problems))


def require_strata(before_handover=False):
    profiles = json.loads((ROOT / 'dsh/strata-profiles.json').read_text())
    enabled = [p for p in profiles.values() if p.get('enabled', True)]
    if len(enabled) != 1:
        raise RuntimeError('Exactly one validated Strata profile must be enabled. No backend has been stopped.')
    cfg = json.loads((ROOT / 'dsh' / enabled[0]['config']).read_text())
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
