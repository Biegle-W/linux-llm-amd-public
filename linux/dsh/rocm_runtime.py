"""Validate the isolated AMD runtime before switching away from another backend."""
from pathlib import Path
import subprocess
import time

from amd_device import amd_devices

ROOT = Path(__file__).resolve().parent.parent


def require_rocm(kind):
    if kind not in ('vllm', 'sglang'):
        raise ValueError('Unconfigured ROCm backend')
    amd_devices()
    try:
        subprocess.run([str(ROOT / kind / 'run-rocm'), '--check'],
                       check=True, timeout=45, capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError('The isolated ' + kind + ' ROCm runtime cannot verify the '
                           '7900 XTX. No backend has been stopped. Run ' +
                           str(ROOT / kind / 'run-rocm') + ' --check for diagnostics.') from error


def require_rocm_headroom(min_free_gib=21.0):
    devices = amd_devices()
    for _ in range(50):
        free = min(int((d / 'mem_info_vram_total').read_text()) - int((d / 'mem_info_vram_used').read_text()) for d in devices)
        if free >= min_free_gib * 1024**3:
            return
        time.sleep(0.2)
    raise RuntimeError(f'Qwen ROCm requires {min_free_gib:g} GiB free AMD VRAM on each card before loading. '
                       'Close GPU-heavy applications and retry. No unrelated application was stopped.')
