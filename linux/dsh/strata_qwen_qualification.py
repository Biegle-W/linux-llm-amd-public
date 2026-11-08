"""Admit an additional Strata Qwen package only after its own hardware qualification."""
from pathlib import Path
import json

from qualified_native_runtime import backing_digest, config_fingerprint, digest

ROOT = Path(__file__).resolve().parents[1]
_VERIFIED_BACKING_CONTENT = set()


def require_package(cfg, *, root=None):
    root = Path(root) if root is not None else ROOT
    registry = root / 'dsh/qualified-strata-qwen-profiles.json'
    if not registry.is_file():
        raise RuntimeError('Additional Strata Qwen profile has no qualification registry.')
    data = json.loads(registry.read_text())
    record = data.get('profiles', {}).get(cfg.get('model_name'))
    if (data.get('schema_version') != 1 or not record or record.get('status') != 'passed'
            or record.get('family') != 'strata-qwen'):
        raise RuntimeError('Additional Strata Qwen profile requires local qualification.')
    if config_fingerprint(cfg) != record.get('config_sha256'):
        raise RuntimeError('Qualified Strata Qwen profile changed.')
    binary, control = Path(record['binary']), Path(record['control'])
    if (Path(cfg['exe']) != binary or Path(cfg['cwd']) != control
            or not binary.is_file() or digest(binary) != record['binary_sha256']):
        raise RuntimeError('Qualified Strata Qwen package identity changed.')
    files = record.get('control_sha256', {})
    if 'serve/server.py' not in files:
        raise RuntimeError('Qualified Strata Control source must be sealed.')
    actual = {str(p.relative_to(control)) for p in control.rglob('*.py')
              if '__pycache__' not in p.parts}
    if actual != set(files):
        raise RuntimeError('Qualified Strata Control source set changed.')
    for relative, expected in files.items():
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts or digest(control / path) != expected:
            raise RuntimeError('Qualified Strata Control source changed.')
    identities = record.get('backing_identity', {})
    from strata_runtime import required_weight_assets
    required = {str(p) for p in required_weight_assets(cfg)}
    required.update(record.get('gguf_files', []))
    if not record.get('gguf_files') or not required.issubset(identities):
        raise RuntimeError('Qualified Strata Qwen input identities are incomplete.')
    for name, identity in identities.items():
        path = Path(name)
        stat = path.stat()
        actual = {'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns,
                  'inode': stat.st_ino, 'device': stat.st_dev}
        if actual != {k: identity[k] for k in actual}:
            # exFAT can assign another inode, and engine reinstalls (daily updater) can rewrite
            # mtime, without changing file content: those fall back to the sealed sha256.
            if any(actual[k] != identity[k] for k in ('bytes', 'device')):
                raise RuntimeError('Qualified Strata Qwen backing identity changed.')
            key = (name, *actual.values(), identity['sha256'])
            if key not in _VERIFIED_BACKING_CONTENT:
                if backing_digest(path) != identity['sha256']:
                    raise RuntimeError('Qualified Strata Qwen backing content changed.')
                _VERIFIED_BACKING_CONTENT.add(key)
    return record
