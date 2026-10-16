#!/usr/bin/env bash
# Build a separate AMD engine. Never replace strata/engine/strata (CUDA).
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
: "${ROCM_PATH:?Set ROCM_PATH to the selected isolated ROCm SDK with gfx1100 support}"
test -x "$ROCM_PATH/llvm/bin/clang++"
TOOLCHAIN="$ROOT/llm-tools/cuda-build"
export PATH="$ROCM_PATH/bin:$TOOLCHAIN/bin:$PATH"
export LD_LIBRARY_PATH="$ROCM_PATH/lib:$TOOLCHAIN/lib:${LD_LIBRARY_PATH:-}"
export CC="$TOOLCHAIN/bin/x86_64-conda-linux-gnu-cc"
export CXX="$TOOLCHAIN/bin/x86_64-conda-linux-gnu-c++"
cmake -S "$ROOT/strata" -B "$ROOT/strata/build-hip" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DSTRATA_ENABLE_CUDA=OFF -DSTRATA_ENABLE_HIP=ON \
  -DCMAKE_HIP_ARCHITECTURES=gfx1100 -DSTRATA_PREFILL_MMQ=ON \
  -DCMAKE_HIP_COMPILER="$ROCM_PATH/llvm/bin/clang++" \
  -DCMAKE_PREFIX_PATH="$ROCM_PATH"
cmake --build "$ROOT/strata/build-hip" --target strata strata-device -j "${BUILD_JOBS:-2}"
printf '%s\n' 'Built separate HIP engine. Validate on the AMD GPU before activating a profile.'
