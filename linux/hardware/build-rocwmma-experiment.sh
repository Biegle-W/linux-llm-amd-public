#!/usr/bin/env bash
# Isolated, pinned Qwen head-256 experiment. Does not alter production binaries.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/rocm-env.sh"
EXP="$ROOT/hardware/generated/level1-tests-2026-10-17"
PIN=f12aaa344c971556ec35be054d7aac1d901fd510
WMMA_PIN=48b7db12a9ade97f0b7ab2ff9321ba0cbb4e5b77
PATCH="$ROOT/hardware/patches/rocwmma-prefill-experiment.patch"
mkdir -p "$EXP"
if [[ ! -d "$EXP/llama-rocwmma/.git" ]]; then
 git clone --shared --no-hardlinks "$ROOT/llama.cpp" "$EXP/llama-rocwmma"
fi
[[ "$(git -C "$EXP/llama-rocwmma" rev-parse HEAD)" == "$PIN" ]] || { echo 'Source revision differs from validated experiment' >&2; exit 1; }
if git -C "$EXP/llama-rocwmma" apply --check "$PATCH" 2>/dev/null; then
 git -C "$EXP/llama-rocwmma" apply "$PATCH"
elif ! git -C "$EXP/llama-rocwmma" apply --reverse --check "$PATCH" 2>/dev/null; then
 echo 'Experimental source differs from the recorded patch' >&2; exit 1
fi
if [[ ! -d "$EXP/rocWMMA/.git" ]]; then
 git clone --depth 1 --branch rocm-7.2.3 https://github.com/ROCm/rocWMMA.git "$EXP/rocWMMA"
fi
[[ "$(git -C "$EXP/rocWMMA" rev-parse HEAD)" == "$WMMA_PIN" ]] || { echo 'Unexpected rocWMMA revision' >&2; exit 1; }
python3 - "$EXP" <<'PY'
from pathlib import Path
import sys
r=Path(sys.argv[1])/'rocWMMA/library/include/rocwmma'
t=(r/'internal/rocwmma-version.hpp.in').read_text()
for k,v in [('MAJOR','2'),('MINOR','2'),('PATCH','0')]: t=t.replace('@rocwmma_VERSION_'+k+'@',v)
out=r/'rocwmma-version.hpp'
if not out.exists() or out.read_text()!=t:
    out.write_text(t)
PY
TOOLCHAIN="$ROOT/llm-tools/cuda-build"
export CC="$TOOLCHAIN/bin/x86_64-conda-linux-gnu-cc"
export CXX="$TOOLCHAIN/bin/x86_64-conda-linux-gnu-c++"
export LD_LIBRARY_PATH="$TOOLCHAIN/lib:$LD_LIBRARY_PATH"
HIP_FLAGS="--gcc-install-dir=$TOOLCHAIN/lib/gcc/x86_64-conda-linux-gnu/14.4.0 --sysroot=$TOOLCHAIN/x86_64-conda-linux-gnu/sysroot -I$EXP/rocWMMA/library/include"
cmake -S "$EXP/llama-rocwmma" -B "$EXP/llama-rocwmma/build-test" -G Ninja \
 -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=OFF -DGGML_VULKAN=OFF -DGGML_HIP=ON \
 -DGPU_TARGETS=gfx1100 -DCMAKE_HIP_ARCHITECTURES=gfx1100 \
 -DCMAKE_HIP_COMPILER="$ROCM_PATH/llvm/bin/clang++" -DCMAKE_HIP_FLAGS="$HIP_FLAGS" \
 -DCMAKE_PREFIX_PATH="$ROCM_PATH" -DGGML_HIP_ROCWMMA_FATTN=ON -DGGML_HIP_NO_VMM=ON \
 -DCMAKE_EXE_LINKER_FLAGS="-Wl,-rpath-link,/usr/lib/x86_64-linux-gnu -Wl,--allow-shlib-undefined" \
 -DLLAMA_BUILD_IS_DEV=ON -DLLAMA_BUILD_TESTS=ON -DLLAMA_BUILD_EXAMPLES=ON \
 -DLLAMA_BUILD_SERVER=ON -DLLAMA_OPENSSL=OFF
cmake --build "$EXP/llama-rocwmma/build-test" --target llama-server llama-bench test-backend-ops -j "${BUILD_JOBS:-2}"
# The cross sysroot lacks host GLIBC_2.42 symbols used by libedit; allow dynamic
# dependency resolution at link time, then require resolution on this real host.
ldd -r "$EXP/llama-rocwmma/build-test/bin/llama-server" > "$EXP/rocwmma-link-validation.log" 2>&1
if rg 'undefined symbol|not found' "$EXP/rocwmma-link-validation.log"; then exit 1; fi
