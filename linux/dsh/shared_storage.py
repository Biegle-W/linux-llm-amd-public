"""Verify and mount configured model volumes before any backend handover.

`python3 dsh/shared_storage.py --all` mounts every configured volume at login
(network/local-llm-mounts.service); launchers still verify their own volume.
"""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import sys
import time

SHARED = Path('/mnt/shared')
MODELS = SHARED / 'GGUF-Models'
UUID = 'CONFIGURE_SHARED_DRIVE_UUID'
STREAM_SHARED = Path('/mnt/shared-nvme')
# STREAM_SHARED is retained only to sanitize historical export paths.
STREAM_UUID = 'CONFIGURE_SHARED_NVME_UUID'
# SATA1 holds GGUF files and checkpoints; SATA2 was removed from the configured volumes.
STATIC_MODELS = SHARED / 'vLLM-Models'
# All retained streaming weights/packs migrated to system NVMe by owner November 2.
INTERNAL_STREAM_MODELS = Path(__file__).resolve().parents[1] / 'models' / 'streaming'
STREAM_MODELS = INTERNAL_STREAM_MODELS
# November 3 owner instruction: NEW SSD-streaming models use the new NVMe.
NEW_STREAM_SHARED = Path('/mnt/new-streaming-nvme')
NEW_STREAM_UUID = 'CONFIGURE_NEW_STREAMING_NVME_UUID'
NEW_STREAM_MODELS = NEW_STREAM_SHARED / 'LLM-Models'
NEW_MODEL_DIRS = {'static': STATIC_MODELS, 'streaming': NEW_STREAM_MODELS}
MAX_USE = 0.90
# (label, UUID, mount point, required model directory or None, required)
VOLUMES = (
    ('sharedSATA1', UUID, SHARED, MODELS, True),
)


def mounted_uuid(mount=None):
    mount = SHARED if mount is None else Path(mount)
    result = subprocess.run(
        ['findmnt', '--noheadings', '--raw', '--mountpoint', str(mount), '--output', 'UUID'],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError('Cannot inspect the model drive mount: ' + result.stderr.strip())
    return result.stdout.strip()


def mount_by_uuid(device, mount, expected_uuid):
    """Mount without prompting; return the last udisksctl message.

    Ubuntu's polkit allows unprompted internal-drive mounts only from the active
    local desktop session. SSH sessions are refused, so retry through the
    user's systemd manager, which polkit attributes to that desktop session.
    """
    command = ['udisksctl', 'mount', '--block-device', str(device), '--no-user-interaction']
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if mounted_uuid(mount) == expected_uuid:
        return ''
    result = subprocess.run(['systemd-run', '--user', '--quiet', '--wait', '--pipe', '--collect', *command],
                            capture_output=True, text=True, timeout=60)
    return (result.stderr or result.stdout).strip()


def ensure_model_drive(mount, models, expected_uuid, label):
    """Never create a model directory on an unmounted or incorrectly mounted disk."""
    uuid = mounted_uuid(mount)
    if uuid and uuid != expected_uuid:
        raise RuntimeError(f'{mount} is mounted from a different drive ({uuid}); '
                           f'expected {label} UUID {expected_uuid}. No files were changed.')
    if not uuid:
        device = Path('/dev/disk/by-uuid') / expected_uuid
        if not device.exists():
            raise RuntimeError(f'{label} model drive is unavailable (UUID {expected_uuid}). '
                               'Reconnect it before starting a backend.')
        print(f'{label} model drive is not mounted. Mounting it now...', flush=True)
        detail = mount_by_uuid(device, mount, expected_uuid)
        if mounted_uuid(mount) != expected_uuid:
            raise RuntimeError(f'Cannot mount {label} at {mount}. {detail} '
                               'Log in to the Linux desktop once (unprompted mounts need an active '
                               'local session), or open the drive in Files, then retry. '
                               'Do not download replacement weights.')
    if not models.is_dir():
        raise RuntimeError(f'{label} is mounted, but {models} is missing. '
                           'Restore the model directory before starting a backend.')
    print(f'{label} model drive ready: {models}', flush=True)


def ensure_shared_models():
    ensure_model_drive(SHARED, MODELS, UUID, 'sharedSATA1')


def ensure_streaming_models():
    if not STREAM_MODELS.is_dir():
        raise RuntimeError('System-drive streaming model folder is missing; no external volume is mounted or replacement downloaded.')


def new_model_dir(kind, size_bytes):
    """Return the directory for a new model of `kind` ('static' or 'streaming') and `size_bytes`.

    Refuses at 90% used; verifies the selected volume and never falls back to another disk.
    """
    target = NEW_MODEL_DIRS[kind]
    if kind == 'static':
        ensure_model_drive(SHARED, STATIC_MODELS, UUID, 'sharedSATA1')
    else:
        ensure_model_drive(NEW_STREAM_SHARED, NEW_STREAM_SHARED, NEW_STREAM_UUID, 'new streaming NVMe')
        target.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(target)
    after = (usage.used + size_bytes) / usage.total
    if after >= MAX_USE:
        raise RuntimeError(f'{target} would be {after:.0%} used after adding {size_bytes / 1e9:.1f} GB '
                           f'(limit {MAX_USE:.0%}). Ask the user where to put this model.')
    return target


def ensure_model_paths(paths):
    """Mount exactly the model volumes these files live on; refuse unknown locations."""
    needed = set()
    for path in map(Path, paths):
        if path.is_relative_to(INTERNAL_STREAM_MODELS):
            continue   # system disk: always present
        if path.is_relative_to(NEW_STREAM_MODELS):
            needed.add(('new streaming NVMe', NEW_STREAM_UUID, NEW_STREAM_SHARED, NEW_STREAM_MODELS))
            continue
        if path.is_relative_to(STATIC_MODELS):
            needed.add(('sharedSATA1', UUID, SHARED, STATIC_MODELS))
            continue
        for label, uuid, mount, models, required in VOLUMES:
            if models is not None and path.is_relative_to(models):
                needed.add((label, uuid, mount, models))
                break
        else:
            raise RuntimeError(f'{path} is outside the configured model volumes; '
                               'review its storage configuration before starting.')
    for label, uuid, mount, models in sorted(needed):
        ensure_model_drive(mount, models, uuid, label)


def ensure_llama_models(presets=None):
    """llama.cpp presets may mix sharedSATA1 and system-drive model paths."""
    root = Path(__file__).resolve().parent
    presets = presets or [root/'models-amd.ini', root/'models-hip.ini']
    paths = [line.split('=', 1)[1].strip() for preset in presets if Path(preset).is_file()
             for line in Path(preset).read_text().splitlines() if line.strip().startswith('model =')]
    if not paths:
        raise RuntimeError('No llama.cpp model paths found in the presets.')
    ensure_model_paths(paths)


def ensure_vllm_models(profiles):
    """Verify external model drives, including sanitized reference mount roots."""
    ensure_model_paths([p['model_path'] for p in profiles.values()
                        if str(p.get('model_path', '')).startswith('/mnt/')
                        or (p.get('model_path') and Path(p['model_path']).is_relative_to(SHARED))])


def ensure_sglang_models(config):
    """Verify the configured main checkpoint and speculative draft before handover."""
    paths = [config['model_path']]
    args = config.get('extra_args', [])
    flag = '--speculative-draft-model-path'
    for i, value in enumerate(args):
        if value == flag:
            if i + 1 >= len(args) or args[i + 1].startswith('--'):
                raise RuntimeError('Missing SGLang speculative draft path.')
            paths.append(args[i + 1])
        elif value.startswith(flag + '='):
            paths.append(value.split('=', 1)[1])
    ensure_model_paths(paths)


def ensure_strata_models(config=None):
    config = Path(config) if config is not None else Path(__file__).resolve().parent / 'strata-iq3-profile.json'
    cfg = json.loads(config.read_text())
    args = cfg['args']
    pack = Path(args[args.index('--pack') + 1])
    if pack.is_relative_to(INTERNAL_STREAM_MODELS):
        ensure_streaming_models()
    elif pack.is_relative_to(NEW_STREAM_MODELS):
        ensure_model_drive(NEW_STREAM_SHARED, NEW_STREAM_MODELS, NEW_STREAM_UUID, 'new streaming NVMe')
    elif pack.is_relative_to(MODELS):
        ensure_shared_models()
    else:
        raise RuntimeError('Strata pack is outside the configured model volumes; review its storage configuration before starting.')


def mount_all(wait=120.0, poll=2.0):
    """Mount every configured volume at login; return the required ones that failed.

    Devices can appear late after boot, so wait for each UUID up to `wait` seconds.
    A wrongly mounted or missing required volume is reported, never repaired.
    """
    failed = []
    for label, uuid, mount, models, required in VOLUMES:
        device = Path('/dev/disk/by-uuid') / uuid
        deadline = time.monotonic() + (wait if required else min(wait, 10))
        while not device.exists() and time.monotonic() < deadline:
            time.sleep(poll)
        try:
            if models is not None:
                ensure_model_drive(mount, models, uuid, label)
            elif not device.exists():
                print(f'{label} (UUID {uuid}) is not connected; skipped.', flush=True)
            elif mounted_uuid(mount) != uuid:
                detail = mount_by_uuid(device, mount, uuid)
                print(f'{label} ' + ('mounted: ' + str(mount) if mounted_uuid(mount) == uuid
                                     else f'could not be mounted. {detail}'), flush=True)
        except RuntimeError as error:
            print(error, file=sys.stderr, flush=True)
            if required:
                failed.append(label)
    return failed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all', action='store_true', help='Mount every configured volume (login service)')
    parser.add_argument('--wait', type=float, default=120.0, help='Seconds to wait for late devices')
    parser.add_argument('--place', choices=sorted(NEW_MODEL_DIRS), help='Print where a new model goes')
    parser.add_argument('--size-gb', type=float, help='Size of the new model for --place')
    options = parser.parse_args()
    if options.place:
        if options.size_gb is None:
            parser.error('--place needs --size-gb')
        print(new_model_dir(options.place, int(options.size_gb * 1e9)))
        raise SystemExit(0)
    if options.all:
        raise SystemExit(1 if mount_all(options.wait) else 0)
    ensure_shared_models()
