"""AMDGPU VRAM eviction accounting, separate from requested/unbacked buffers."""


def memory_counter(fields, key):
    value = fields[key]
    parts = value.split() if isinstance(value, str) else []
    if len(parts) not in (1, 2) or not parts[0].isascii() or not parts[0].isdigit():
        raise ValueError('Invalid DRM memory counter')
    units = {'B': 1, 'KiB': 1024, 'MiB': 1024**2}
    unit = parts[1] if len(parts) == 2 else 'B'
    if unit not in units:
        raise ValueError('Invalid DRM memory unit')
    return int(parts[0]) * units[unit]


def vram_accounting(fields):
    """Prefer actual BO placement outside preferred domains; legacy stays strict.

    Linux 7.0 amdgpu_vm_update_stats_locked counts drm-total by preferred
    placement, drm-resident by actual placement, and amd-evicted-vram only
    when actual placement is outside a BO's preferred domains. Total-minus-
    resident also includes unbacked requested buffers, so is not eviction.
    Missing optional eviction counters retain the old conservative rule;
    malformed present counters are errors, never silently treated as zero.
    """
    total = memory_counter(fields, 'drm-total-vram')
    resident = memory_counter(fields, 'drm-resident-vram')
    gap = max(0, total - resident)
    # Resident can exceed preferred-placement total when other buffers reside
    # here. The kernel accounts these categories independently.
    explicit = 'amd-evicted-vram' in fields
    if not explicit and resident > total:
        raise ValueError('Legacy residency counters cannot verify eviction')
    evicted = memory_counter(fields, 'amd-evicted-vram') if explicit else None
    if evicted is not None and evicted > total:
        raise ValueError('Invalid AMD eviction counter')
    return {'spill': evicted if explicit else gap, 'requested': total,
            'resident': resident, 'requested_nonresident': gap,
            'evicted': evicted, 'explicit': explicit}
