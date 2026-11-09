"""Protect desktop GPU headroom; never signal unrelated processes."""
from amd_device import amd_devices
import resource_policy

GIB = 1024**3
STARTUP_FREE_VRAM_GIB = resource_policy.VRAM_RESERVE_BYTES / GIB


def startup_vram_blocker(readings):
    """Check actual loaded headroom, separately from engine reserve targets."""
    if readings is None or len(readings) != 2:
        return 'Both AMD cards must have valid startup VRAM telemetry'
    if min(row['free'] for row in readings) < STARTUP_FREE_VRAM_GIB * GIB:
        free = '/'.join(f"{row['free']/GIB:.3f}" for row in readings)
        return (f'Strata startup needs at least {STARTUP_FREE_VRAM_GIB:g} GiB free '
                f'on each GPU; found {free} GiB')
    return None


def vram_snapshot():
    readings = []
    for device in amd_devices():
        total = int((device / 'mem_info_vram_total').read_text())
        used = int((device / 'mem_info_vram_used').read_text())
        if not 0 <= used <= total:
            raise RuntimeError('Invalid AMD VRAM telemetry')
        readings.append({'device': device.name, 'total': total, 'used': used,
                         'free': total - used})
    return readings


class MemoryGuard:
    """Stateful sample policy, independent of the process termination callback."""
    def __init__(self):
        self.missing = 0

    def check(self, available, swap, spill, readings):
        if readings is None:
            self.missing += 1
            if self.missing >= 3:
                return 'AMD VRAM telemetry unavailable for three samples'
            return None
        if len(readings) != 2:
            return 'Both AMD cards must have valid VRAM telemetry'
        return resource_policy.headroom_failure(available, readings)
