#!/usr/bin/env bash
# Build separately from the working CUDA runtime; does not start inference.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
SDK="$ROOT/llm-tools/vulkan-sdk"
TOOLCHAIN="$ROOT/llm-tools/cuda-build"
export PATH="$TOOLCHAIN/bin:$SDK/usr/bin:$PATH"
export LD_LIBRARY_PATH="$SDK/usr/lib/x86_64-linux-gnu:$TOOLCHAIN/lib:${LD_LIBRARY_PATH:-}"
export CC="$TOOLCHAIN/bin/x86_64-conda-linux-gnu-cc"
export CXX="$TOOLCHAIN/bin/x86_64-conda-linux-gnu-c++"
cmake -S "$ROOT/llama.cpp" -B "$ROOT/llama.cpp/build-vulkan" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=OFF -DGGML_VULKAN=ON \
  -DLLAMA_BUILD_IS_DEV=ON -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF \
  -DLLAMA_BUILD_SERVER=ON -DLLAMA_OPENSSL=OFF \
  -DVulkan_INCLUDE_DIR="$SDK/usr/include" \
  -DVulkan_LIBRARY="$SDK/usr/lib/x86_64-linux-gnu/libvulkan.so" \
  -DVulkan_GLSLC_EXECUTABLE="$SDK/usr/bin/glslc" \
  -DSPIRV-Headers_DIR="$SDK/usr/share/cmake/SPIRV-Headers"
cmake --build "$ROOT/llama.cpp/build-vulkan" --target llama-server -j "${BUILD_JOBS:-2}"
