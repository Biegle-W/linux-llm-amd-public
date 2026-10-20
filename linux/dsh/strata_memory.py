"""Protect desktop GPU headroom; never signal unrelated processes."""
from amd_device import amd_devices

GIB = 1024**3
STARTUP_FREE_VRAM_GIB = 5


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
        self.low_vram = self.low_ram = self.missing = 0

    def check(self, available, swap, spill, readings):
        if readings is None:
            self.missing += 1
            if self.missing >= 3:
                return 'AMD VRAM telemetry unavailable for three samples'
            return None
        self.missing = 0
        if len(readings) != 2:
            return 'Both AMD cards must have valid VRAM telemetry'
        free = min(r['free'] for r in readings)
        self.low_vram = self.low_vram + 1 if free < 3*GIB else 0
        self.low_ram = self.low_ram + 1 if available < 3*GIB else 0
        if free < 1.5*GIB or self.low_vram >= 2:
            return f'Desktop VRAM headroom low: minimum {free/GIB:.2f} GiB free'
        if self.low_ram >= 3 or swap > 256*1024**2 or spill > 256*1024**2:
            return (f'Worker memory unsafe: available={available/GIB:.2f} GiB, '
                    f'owned swap={swap/1024**2:.0f} MiB, VRAM spill={spill/1024**2:.0f} MiB')
        return None
