#!/usr/bin/env bash
set -euo pipefail
FREETOKEN_INSTALL_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
FREETOKEN_REPO=$(cd -- "$FREETOKEN_INSTALL_DIR/.." && pwd)
FREETOKEN_REVISION=8f49e0af98ba444dd261af69e82d5a1841778c68
export UV_CACHE_DIR="$FREETOKEN_INSTALL_DIR/cache/uv"
if [[ ! -d "$FREETOKEN_INSTALL_DIR/upstream/.git" ]]; then
    git clone --no-checkout https://github.com/FlashML-org/FreeToken.git "$FREETOKEN_INSTALL_DIR/upstream"
    git -C "$FREETOKEN_INSTALL_DIR/upstream" checkout --detach "$FREETOKEN_REVISION"
fi
if [[ $(git -C "$FREETOKEN_INSTALL_DIR/upstream" rev-parse HEAD) != "$FREETOKEN_REVISION" ]]; then
    echo 'Unexpected FreeToken source revision; review it before replacing the validated build.' >&2
    exit 1
fi
if git -C "$FREETOKEN_INSTALL_DIR/upstream" apply --check "$FREETOKEN_INSTALL_DIR/patches/amd-torchvision-prerelease.patch" 2>/dev/null; then
    git -C "$FREETOKEN_INSTALL_DIR/upstream" apply "$FREETOKEN_INSTALL_DIR/patches/amd-torchvision-prerelease.patch"
else
    git -C "$FREETOKEN_INSTALL_DIR/upstream" apply --reverse --check "$FREETOKEN_INSTALL_DIR/patches/amd-torchvision-prerelease.patch"
fi
if [[ ! -x "$FREETOKEN_INSTALL_DIR/.venv-rocm/bin/python" ]]; then
    uv venv --python 3.12 "$FREETOKEN_INSTALL_DIR/.venv-rocm"
fi
uv pip install --python "$FREETOKEN_INSTALL_DIR/.venv-rocm/bin/python" \
    --index-url https://stable.repo.amd.com/rocm/whl-next/ \
    --extra-index-url https://pypi.org/simple --index-strategy unsafe-best-match \
    --prerelease allow -r "$FREETOKEN_INSTALL_DIR/requirements-rocm.lock"
"$FREETOKEN_INSTALL_DIR/.venv-rocm/bin/rocm-sdk" init
source "$FREETOKEN_INSTALL_DIR/env.sh"
uv pip install --python "$FREETOKEN_VENV/bin/python" --no-build-isolation --no-deps \
    --editable "$FREETOKEN_INSTALL_DIR/upstream"
uv pip check --python "$FREETOKEN_VENV/bin/python"
"$FREETOKEN_INSTALL_DIR/run" --version
echo 'Installed FreeToken ROCm. Model serving still requires its own hardware/quality validation.'
