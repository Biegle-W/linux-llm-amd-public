"""Restore the Shared model drive before starting an inference backend."""
from pathlib import Path
import subprocess

SHARED = Path('/mnt/shared')
MODELS = SHARED / 'GGUF-Models'
UUID = 'CONFIGURE_SHARED_DRIVE_UUID'


def mounted_uuid():
    result = subprocess.run(
        ['findmnt', '--noheadings', '--raw', '--mountpoint', str(SHARED),
         '--output', 'UUID'], capture_output=True, text=True, timeout=10,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError('Cannot inspect the Shared model drive mount: ' + result.stderr.strip())
    return result.stdout.strip()


def ensure_shared_models():
    uuid = mounted_uuid()
    if uuid and uuid != UUID:
        raise RuntimeError(f'{SHARED} is mounted from a different drive ({uuid}); '
                           f'expected Shared UUID {UUID}. No files were changed.')
    if not uuid:
        device = Path('/dev/disk/by-uuid') / UUID
        if not device.exists():
            raise RuntimeError(f'Shared SATA model drive is unavailable (UUID {UUID}). '
                               'Reconnect it before starting a backend.')
        print('Shared SATA model drive is not mounted. Mounting it now...', flush=True)
        result = subprocess.run(
            ['udisksctl', 'mount', '--block-device', str(device), '--no-user-interaction'],
            capture_output=True, text=True, timeout=30,
        )
        # Check the mount itself, including a concurrent file-manager mount.
        if mounted_uuid() != UUID:
            detail = (result.stderr or result.stdout).strip()
            raise RuntimeError(f'Cannot mount Shared at {SHARED}. {detail} '
                               'Open the Shared drive in Files, then retry. '
                               'If mounted elsewhere, restore this configured path; '
                               'do not download replacement weights.')
    if not MODELS.is_dir():
        raise RuntimeError(f'Shared is mounted, but {MODELS} is missing. '
                           'Restore the model directory before starting a backend.')
    print(f'Shared model drive ready: {MODELS}', flush=True)


if __name__ == '__main__':
    ensure_shared_models()
