#!/usr/bin/env bash
# Source this file only in the isolated FreeToken process.
FREETOKEN_WORKSPACE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
FREETOKEN_VENV="$FREETOKEN_WORKSPACE/freetoken/.venv-rocm"
FREETOKEN_SITE="$FREETOKEN_VENV/lib/python3.12/site-packages"
export ROCM_HOME="$FREETOKEN_SITE/_rocm_sdk_devel"
export ROCM_PATH="$ROCM_HOME"
export HIP_PATH="$ROCM_HOME"
export PATH="$FREETOKEN_VENV/bin:$ROCM_HOME/bin:$ROCM_HOME/lib/llvm/bin:$PATH"
export LD_LIBRARY_PATH="$ROCM_HOME/lib:$FREETOKEN_SITE/_rocm_sdk_core/lib:$FREETOKEN_SITE/_rocm_sdk_libraries/lib:$FREETOKEN_SITE/torch/lib"
export HIP_VISIBLE_DEVICES=0,1
export ROCR_VISIBLE_DEVICES=0,1
export PYTORCH_ROCM_ARCH=gfx1100
export FREETOKEN_ROCM_ARCH=gfx1100
export MAX_JOBS=2
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false
export NCCL_P2P_DISABLE=1
export HSA_ENABLE_SDMA=0
export UV_CACHE_DIR="$FREETOKEN_WORKSPACE/freetoken/cache/uv"
export XDG_CACHE_HOME="$FREETOKEN_WORKSPACE/freetoken/cache"
export TVM_FFI_CACHE_DIR="$FREETOKEN_WORKSPACE/freetoken/cache/tvm-ffi"
export TRITON_CACHE_DIR="$FREETOKEN_WORKSPACE/freetoken/cache/triton"
export FREETOKEN_KERNEL_CACHE_DIR="$FREETOKEN_WORKSPACE/freetoken/cache/kernels"
export HF_HOME="$FREETOKEN_WORKSPACE/models/huggingface"
unset CUDA_VISIBLE_DEVICES CUDA_HOME CUDACXX CUDAHOSTCXX
