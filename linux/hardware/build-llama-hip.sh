#!/usr/bin/env bash
# Isolated ROCm build; keep the validated Vulkan binary for fallback.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/rocm-env.sh"
TOOLCHAIN="$ROOT/llm-tools/cuda-build"
export CC="$TOOLCHAIN/bin/x86_64-conda-linux-gnu-cc"
export CXX="$TOOLCHAIN/bin/x86_64-conda-linux-gnu-c++"
export LD_LIBRARY_PATH="$TOOLCHAIN/lib:$LD_LIBRARY_PATH"
HIP_FLAGS="--gcc-install-dir=$TOOLCHAIN/lib/gcc/x86_64-conda-linux-gnu/14.4.0 --sysroot=$TOOLCHAIN/x86_64-conda-linux-gnu/sysroot"
cmake -S "$ROOT/llama.cpp" -B "$ROOT/llama.cpp/build-hip" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=OFF -DGGML_VULKAN=OFF -DGGML_HIP=ON \
  -DGPU_TARGETS=gfx1100 -DCMAKE_HIP_ARCHITECTURES=gfx1100 \
  -DCMAKE_HIP_COMPILER="$ROCM_PATH/llvm/bin/clang++" \
  -DCMAKE_HIP_FLAGS="$HIP_FLAGS" -DCMAKE_PREFIX_PATH="$ROCM_PATH" \
  -DCMAKE_EXE_LINKER_FLAGS="-Wl,-rpath-link,/usr/lib/x86_64-linux-gnu" \
  -DLLAMA_BUILD_IS_DEV=ON -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF \
  -DLLAMA_BUILD_SERVER=ON -DLLAMA_OPENSSL=OFF
cmake --build "$ROOT/llama.cpp/build-hip" --target llama-server -j "${BUILD_JOBS:-2}"
