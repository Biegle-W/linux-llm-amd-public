"""Verify and mount configured model volumes before any backend handover."""
from pathlib import Path
import json
import subprocess

SHARED = Path('/mnt/shared')
MODELS = SHARED / 'GGUF-Models'
UUID = 'CONFIGURE_SHARED_DRIVE_UUID'
STREAM_SHARED = Path('/mnt/shared-nvme')
STREAM_MODELS = STREAM_SHARED / 'LLM-Models'
STREAM_UUID = 'CONFIGURE_SHARED_NVME_UUID'


def mounted_uuid(mount=None):
    mount = SHARED if mount is None else Path(mount)
    result = subprocess.run(
        ['findmnt', '--noheadings', '--raw', '--mountpoint', str(mount), '--output', 'UUID'],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError('Cannot inspect the model drive mount: ' + result.stderr.strip())
    return result.stdout.strip()


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
        result = subprocess.run(
            ['udisksctl', 'mount', '--block-device', str(device), '--no-user-interaction'],
            capture_output=True, text=True, timeout=30,
        )
        if mounted_uuid(mount) != expected_uuid:
            detail = (result.stderr or result.stdout).strip()
            raise RuntimeError(f'Cannot mount {label} at {mount}. {detail} '
                               'Open the configured drive in Files, then retry. '
                               'Do not download replacement weights.')
    if not models.is_dir():
        raise RuntimeError(f'{label} is mounted, but {models} is missing. '
                           'Restore the model directory before starting a backend.')
    print(f'{label} model drive ready: {models}', flush=True)


def ensure_shared_models():
    ensure_model_drive(SHARED, MODELS, UUID, 'Shared SATA')


def ensure_streaming_models():
    ensure_model_drive(STREAM_SHARED, STREAM_MODELS, STREAM_UUID, 'Shared NVMe')


def ensure_strata_models(config=None):
    config = Path(config) if config is not None else Path(__file__).resolve().parent / 'strata-iq3-profile.json'
    cfg = json.loads(config.read_text())
    args = cfg['args']
    pack = Path(args[args.index('--pack') + 1])
    if pack.is_relative_to(STREAM_MODELS):
        ensure_streaming_models()
    elif pack.is_relative_to(MODELS):
        ensure_shared_models()
    else:
        raise RuntimeError('Strata pack is outside the configured model volumes; review its storage configuration before starting.')


if __name__ == '__main__':
    ensure_shared_models()
