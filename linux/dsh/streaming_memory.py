"""Explicit bounded 32 GB streaming tier; legacy 64 GB requirements stay intact."""
GIB = 1024**3


def is_32gb(cfg):
    tier = cfg.get('host_ram_profile')
    if tier is None:
        return False
    if tier != '32gb-v1':
        raise RuntimeError('Unknown streaming RAM profile; no worker was started.')
    return True


def scope_limits(cfg):
    if not is_32gb(cfg):
        return {'memory.max': 52*GIB, 'memory.swap.max': 'max'}
    limits = cfg.get('worker_memory_limits', {})
    maximum = limits.get('memory.max')
    expected = {'memory.high': maximum - 2*GIB if type(maximum) is int else None,
                'memory.max': maximum, 'memory.swap.max': 'max'}
    if (type(maximum) is not int or type(limits.get('memory.high')) is not int
            or maximum not in (20*GIB, 22*GIB) or limits != expected):
        raise RuntimeError('32 GB streaming requires sealed 18/20 or 20/22 GiB worker RAM limits and phase-aware swap.')
    return dict(limits)


def scope_properties(cfg):
    if not is_32gb(cfg):
        return ['--property=MemoryMax=52G', '--property=MemorySwapMax=infinity']
    names = {'memory.high': 'MemoryHigh', 'memory.max': 'MemoryMax', 'memory.swap.max': 'MemorySwapMax'}
    return ['--property='+names[k]+'='+('infinity' if value == 'max' else str(value))
            for k,value in scope_limits(cfg).items()]


def check_32gb(cfg, total, available, family, *, check_available=True):
    if not is_32gb(cfg):
        return False
    limits = scope_limits(cfg)
    args = cfg['args']
    def arg(flag):
        return args[args.index(flag)+1] if flag in args else None
    if family == 'qwen':
        if (cfg.get('minimum_host_ram_gib') != 29 or arg('--resident-budget-gib') not in ('8', '12')
                or arg('--max-context') != '262144' or arg('--kv-resident') != '32768'):
            raise RuntimeError('32 GB Qwen requires its bounded 8/12 GiB expert tier and retained 256K/32K KV layout.')
    elif family == 'glm':
        env = cfg.get('env', {})
        if env.get('MAYA_GLM_RAM_GB') not in ('8', '12') or env.get('MAYA_GLM_RAM_HEADROOM_GB') != '12':
            raise RuntimeError('32 GB GLM requires an 8/12 GiB RAM tier and unchanged 12 GiB native headroom.')
        if arg('--max-context') != '32768':
            raise RuntimeError('32 GB GLM must retain the qualified 32K context.')
    elif family == 'deepseek':
        if arg('--max-context') != '32768':
            raise RuntimeError('32 GB DeepSeek must retain its qualified 32K context.')
    else:
        raise RuntimeError('Unknown 32 GB streaming family.')
    # A lower-cache tier changes resource demand, never the independent floors.
    # Reserve at least 3 GiB beyond the tighter enforced worker RAM cap.
    if total < 29*GIB:
        raise RuntimeError('32 GB streaming tier requires at least 29 GiB OS-visible physical RAM.')
    required = limits['memory.max'] + 3*GIB
    if check_available and available < required:
        raise RuntimeError(f'32 GB streaming tier needs {required/GIB:g} GiB available RAM before loading; swap is not capacity.')
    return True
