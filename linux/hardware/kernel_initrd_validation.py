"""Validate NVMe/ext4 trial initramfs contents without requiring late GPU drivers."""
from pathlib import PurePosixPath
import re


def install_action(status):
    """Resume by validating existing files; never overwrite a partial-stage backup."""
    if status is None:
        return 'stage'
    if status in ('staging', 'staged-not-booted', 'one-shot-armed'):
        return 'verify-stage'
    raise ValueError('Installation phase requires inspection before continuing: ' + str(status))


def validate_initrd_listing(listing, release, config):
    """Check the actual boot path. Signed installed GPU modules are checked separately."""
    paths = set()
    for line in listing.splitlines():
        if not line.strip():
            continue
        path = PurePosixPath(line.strip().lstrip('/'))
        if '..' in path.parts:
            raise ValueError('Unexpected parent component in initramfs listing')
        paths.add(str(path))
    if 'init' not in paths:
        raise ValueError('Initramfs lacks /init')
    releases = set()
    for path in paths:
        match = re.match(r'(?:usr/)?lib/modules/([^/]+)(?:/|$)', path)
        if match:
            releases.add(match[1])
    if releases != {release}:
        raise ValueError('Initramfs module release mismatch: ' + str(sorted(releases)))
    settings = dict(line.split('=', 1) for line in config.splitlines()
                    if line.startswith('CONFIG_') and '=' in line)

    def has_module(relative):
        return any(prefix + '/kernel/' + relative + suffix in paths
                   for prefix in ('lib/modules/' + release, 'usr/lib/modules/' + release)
                   for suffix in ('', '.gz', '.xz', '.zst'))

    required = [('CONFIG_BLK_DEV_NVME', 'drivers/nvme/host/nvme.ko'),
                ('CONFIG_NVME_CORE', 'drivers/nvme/host/nvme-core.ko'),
                ('CONFIG_EXT4_FS', 'fs/ext4/ext4.ko')]
    for setting, module in required:
        value = settings.get(setting)
        if value not in ('y', 'm'):
            raise ValueError('Required root-storage support unavailable: ' + setting)
        if value == 'm' and not has_module(module):
            raise ValueError('Initramfs lacks boot-required module: ' + module)
    return {'module_release': release, 'init_present': True,
            'NVMe_boot_support_verified': True,
            'ext4_builtin': settings['CONFIG_EXT4_FS'] == 'y',
            'simpledrm_builtin': settings.get('CONFIG_DRM_SIMPLEDRM') == 'y',
            'amdgpu_in_initrd': has_module('drivers/gpu/drm/amd/amdgpu/amdgpu.ko'),
            'amdgpu_policy': 'May load from the separately hash-verified signed root module tree'}
