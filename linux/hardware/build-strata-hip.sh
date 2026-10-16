#!/usr/bin/env bash
# Build a separate AMD engine. Never replace strata/engine/strata (CUDA).
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/rocm-env.sh"
test -x "$ROCM_PATH/llvm/bin/clang++"
TOOLCHAIN="$ROOT/llm-tools/cuda-build"
export CC="$TOOLCHAIN/bin/x86_64-conda-linux-gnu-cc"
export CXX="$TOOLCHAIN/bin/x86_64-conda-linux-gnu-c++"
export LD_LIBRARY_PATH="$TOOLCHAIN/lib:$LD_LIBRARY_PATH"
HIP_FLAGS="--gcc-install-dir=$TOOLCHAIN/lib/gcc/x86_64-conda-linux-gnu/14.4.0 --sysroot=$TOOLCHAIN/x86_64-conda-linux-gnu/sysroot"
cmake -S "$ROOT/strata" -B "$ROOT/strata/build-hip" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DSTRATA_ENABLE_CUDA=OFF -DSTRATA_ENABLE_HIP=ON \
  -DSTRATA_GGML_DIR="$ROOT/strata/third_party/llama.cpp" \
  -DCMAKE_HIP_ARCHITECTURES=gfx1100 -DSTRATA_PREFILL_MMQ=ON \
  -DCMAKE_HIP_COMPILER="$ROCM_PATH/llvm/bin/clang++" \
  -DCMAKE_HIP_FLAGS="$HIP_FLAGS" -DCMAKE_PREFIX_PATH="$ROCM_PATH" \
  -DCMAKE_EXE_LINKER_FLAGS="-Wl,-rpath-link,/usr/lib/x86_64-linux-gnu"
cmake --build "$ROOT/strata/build-hip" --target strata strata-device -j "${BUILD_JOBS:-2}"
printf '%s\n' 'Built separate HIP engine. Validate on the AMD GPU before activating a profile.'
