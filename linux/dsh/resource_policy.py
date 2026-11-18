"""Owner-selected headroom policy; hardware-free except explicit inventory reads."""
from pathlib import Path

GIB = 1024**3
MIB = 1024**2
NAME = 'owner-headroom-v1'
RAM_RESERVE_BYTES = GIB
VRAM_RESERVE_BYTES = 128 * MIB


def scope_limits(meminfo=None):
    if meminfo is None:
        meminfo = {line.split(':')[0]: int(line.split()[1]) * 1024
                   for line in Path('/proc/meminfo').read_text().splitlines()
                   if line.startswith(('MemTotal:', 'SwapTotal:'))}
    total, swap = meminfo['MemTotal'], meminfo['SwapTotal']
    if type(total) is not int or total <= RAM_RESERVE_BYTES or type(swap) is not int or swap < 0:
        raise RuntimeError('Invalid physical RAM/swap capacity for the owner guard policy')
    return {'memory.high': 'max', 'memory.max': total - RAM_RESERVE_BYTES,
            'memory.swap.max': swap}


def properties(limits=None):
    names = {'memory.high': 'MemoryHigh', 'memory.max': 'MemoryMax', 'memory.swap.max': 'MemorySwapMax'}
    return ['--property=' + names[k] + '=' + ('infinity' if v == 'max' else str(v))
            for k, v in (scope_limits() if limits is None else limits).items()]


def free_ram_blocker(available):
    """The one free-RAM floor for every model load (owner choice, November 18 2026).

    No per-model figure is counted before loading: a load needs the host reserve available and nothing
    more. The worker scope limit above and the running guards bound what happens after that.
    """
    if type(available) not in (int, float) or available < 0:
        raise ValueError('Invalid available-RAM telemetry')
    if available < RAM_RESERVE_BYTES:
        return (f'Loading needs {RAM_RESERVE_BYTES/GIB:g} GiB available RAM (the host reserve); '
                f'found {available/GIB:.2f} GiB. Swap is not capacity.')
    return None


def headroom_failure(available, cards):
    if type(available) is not int or available < 0 or not cards or len(cards) != 2 or any(
            type(c.get('free')) is not int or c['free'] < 0 for c in cards):
        raise ValueError('Invalid RAM/VRAM headroom telemetry')
    if available < RAM_RESERVE_BYTES:
        return 'Host RAM headroom below 1 GiB'
    if min(c['free'] for c in cards) < VRAM_RESERVE_BYTES:
        return 'GPU VRAM headroom below 128 MiB per card'
    return None
