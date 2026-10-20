#!/usr/bin/env bash
# Source this only for Maya builds; production SDKs and other forks are unchanged.
MAYA_LLM_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source "$MAYA_LLM_ROOT/hardware/rocm-env.sh"
MAYA_TOOLCHAIN="$MAYA_LLM_ROOT/llm-tools/cuda-build"
export CC="$MAYA_TOOLCHAIN/bin/x86_64-conda-linux-gnu-cc"
export CXX="$MAYA_TOOLCHAIN/bin/x86_64-conda-linux-gnu-c++"
export LD_LIBRARY_PATH="$MAYA_TOOLCHAIN/lib:$LD_LIBRARY_PATH"
export CPATH="$MAYA_LLM_ROOT/maya/rocwmma-7.2.3/library/include${CPATH:+:$CPATH}"
export HIPFLAGS="--gcc-install-dir=$MAYA_TOOLCHAIN/lib/gcc/x86_64-conda-linux-gnu/14.4.0 --sysroot=$MAYA_TOOLCHAIN/x86_64-conda-linux-gnu/sysroot"
export LDFLAGS="-Wl,-rpath-link,$ROCM_PATH/lib:$MAYA_LLM_ROOT/llm-tools/rocm-sdk/host-libs/usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu"
export PIP_CACHE_DIR="$MAYA_LLM_ROOT/llm-tools/runtime-cache/maya-pip"
