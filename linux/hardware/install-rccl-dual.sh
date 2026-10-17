#!/usr/bin/env bash
# Isolated compatibility library; never replaces system or SDK libraries.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
DEST="$ROOT/llm-tools/rccl-nohostcall"
PIN=23c2beb2e200353fda84afa216c2cea2f7c579e9
BASE=https://github.com/cadamcat/dual-radeon-vllm/releases/download/v0.1.0
mkdir -p "$DEST"
curl -fL "$BASE/librccl-nohostcall-2.27.7-gfx1100.so" -o "$DEST/librccl-nohostcall-2.27.7-gfx1100.so"
printf '%s  %s\n' 0717e4f59d174b89bb6d249ea93e5cfeff75be6f2cadd9260f5a6feabf67dfcb "$DEST/librccl-nohostcall-2.27.7-gfx1100.so" | sha256sum -c -
curl -fL "$BASE/LICENSE.rccl.txt" -o "$DEST/LICENSE.rccl.txt"
curl -fL "https://raw.githubusercontent.com/cadamcat/dual-radeon-vllm/$PIN/LICENSE" -o "$DEST/LICENSE.dual-radeon-vllm"
curl -fL "https://raw.githubusercontent.com/cadamcat/dual-radeon-vllm/$PIN/deploy/rsmi_stub.c" -o "$DEST/rsmi_stub.c"
gcc -shared -fPIC -Wl,-soname,librsmi_stub.so.1 "$DEST/rsmi_stub.c" -o "$DEST/librsmi_stub.so.1"
ln -sfn librccl-nohostcall-2.27.7-gfx1100.so "$DEST/librccl.so.1"
echo 'Installed only in the local runtime directory. Run hardware/test-rccl-dual.py with each ROCm Python before loading models.'
