"""Require the owner-selected installed kernel before AMD inference admission."""
from pathlib import Path
import platform

REQUIRED_RELEASE = '7.0.14-42-vmpt1'
REQUIRED_AMDGPU_SRCVERSION = '140B8E9A04991D891F18CD3'


def require_inference_kernel():
    release = platform.release()
    if release != REQUIRED_RELEASE:
        raise RuntimeError(f'AMD inference requires kernel {REQUIRED_RELEASE}; running {release}. '
                           'Boot the installed inference kernel before starting a model.')
    try:
        loaded = Path('/sys/module/amdgpu/srcversion').read_text().strip()
    except OSError as error:
        raise RuntimeError('Cannot verify the loaded inference AMDGPU module.') from error
    if loaded != REQUIRED_AMDGPU_SRCVERSION:
        raise RuntimeError('Loaded AMDGPU module differs from the installed inference kernel pin.')
