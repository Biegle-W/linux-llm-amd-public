"""Explicit bounded streaming tiers; legacy admission stays intact."""
GIB = 1024**3
import resource_policy


def is_32gb(cfg):
    tier = cfg.get('host_ram_profile')
    if tier is None:
        return False
    if tier == '64gb-q1-v1':
        return False
    if tier != '32gb-v1':
        raise RuntimeError('Unknown streaming RAM profile; no worker was started.')
    return True


def scope_limits(cfg):
    return resource_policy.scope_limits()


def scope_properties(cfg):
    return resource_policy.properties(scope_limits(cfg))


def check_32gb(cfg, total, available, family, *, check_available=True):
    # Preserve the callers' legacy entrypoint; the new tier is explicit and family-checked.
    if cfg.get('host_ram_profile') == '64gb-q1-v1':
        return check_64gb(cfg, total, available, family, check_available=check_available)
    if not is_32gb(cfg):
        return False
    scope_limits(cfg)
    args = cfg['args']
    def arg(flag):
        return args[args.index(flag)+1] if flag in args else None
    if family == 'qwen':
        if (cfg.get('minimum_host_ram_gib') != 29 or arg('--resident-budget-gib') not in ('8', '12')
                or arg('--max-context') != '262144' or arg('--kv-resident') != '32768'):
            raise RuntimeError('32 GB Qwen requires its bounded 8/12 GiB expert tier and retained 256K/32K KV layout.')
    elif family == 'glm':
        env = cfg.get('env', {})
        if env.get('MAYA_GLM_RAM_GB') not in ('8', '12') or env.get('MAYA_GLM_RAM_HEADROOM_GB') != '1':
            raise RuntimeError('32 GB GLM requires an 8/12 GiB RAM tier and the 1 GiB native headroom.')
        if arg('--max-context') != '32768':
            raise RuntimeError('32 GB GLM must retain the qualified 32K context.')
    elif family == 'deepseek':
        if arg('--max-context') != '32768':
            raise RuntimeError('32 GB DeepSeek must retain its qualified 32K context.')
    else:
        raise RuntimeError('Unknown 32 GB streaming family.')
    # A lower-cache tier changes resource demand, never the independent floors.
    # owner-headroom-v1: Qwen needs its expert budget + 1 GiB; GLM/DeepSeek need 9 GiB available.
    if total < 29*GIB:
        raise RuntimeError('32 GB streaming tier requires at least 29 GiB OS-visible physical RAM.')
    required = float(arg('--resident-budget-gib') or 8) * GIB + GIB if family == 'qwen' else 9*GIB
    if check_available and available < required:
        raise RuntimeError(f'32 GB streaming tier needs {required/GIB:g} GiB available RAM before loading; swap is not capacity.')
    return True


def check_64gb(cfg, total, available, family, *, check_available=True):
    """Bound the new SSD-backed Q1 cache tier; never count swap as capacity."""
    if cfg.get('host_ram_profile') != '64gb-q1-v1':
        return False
    scope_limits(cfg)
    args = cfg.get('args', [])
    def value(flag):
        return args[args.index(flag)+1] if flag in args else None
    env = cfg.get('env', {})
    if (family != 'deepseek' or value('--max-context') != '32768'
            or value('--cpu-threads') not in ('14', '20')
            or env.get('DS4_WARM_CAP_GB') != '28'
            or env.get('DS4_ENGRAM_CACHE_MB') != '1024'):
        raise RuntimeError('64 GB Q1 requires DeepSeek 32K, 14/20 threads and explicit 28 GB expert/1024 MB Engram caches.')
    if total < 60*GIB:
        raise RuntimeError('64 GB Q1 tier requires at least 60 GiB OS-visible physical RAM.')
    required = 29*GIB
    if check_available and available < required:
        raise RuntimeError('64 GB Q1 tier needs 29 GiB available RAM before loading; swap is not capacity.')
    return True
