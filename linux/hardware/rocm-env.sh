# Private ROCm 7.2.3 SDK, matched to the selected nightly PyTorch.
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export ROCM_PATH="$ROOT/llm-tools/rocm-sdk/opt/rocm-7.2.3"
export ROCM_HOME="$ROCM_PATH"
export HIP_PATH="$ROCM_PATH"
export LD_LIBRARY_PATH="$ROCM_PATH/lib:$ROCM_PATH/lib64:$ROOT/llm-tools/rocm-sdk/host-libs/usr/lib/x86_64-linux-gnu"
export LD_LIBRARY_PATH="$ROOT/llm-tools/rocm-sdk/mpi4/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH:$ROOT/llm-tools/rocm-sdk/host-libs/usr/lib/x86_64-linux-gnu/pmix2/lib"
export PATH="$ROCM_PATH/bin:$ROCM_PATH/llvm/bin:$ROOT/llm-tools/cuda-build/bin:$PATH"
export HIP_VISIBLE_DEVICES=0
export ROCR_VISIBLE_DEVICES=0
unset CUDA_VISIBLE_DEVICES CUDA_HOME CUDAHOSTCXX
export PYTORCH_ROCM_ARCH=gfx1100
export AMDGPU_TARGET=gfx1100
export MAX_JOBS=3
export HF_HOME=/opt/local-llm/models/huggingface
export XDG_CACHE_HOME="$ROOT/llm-tools/runtime-cache/rocm"
export VLLM_ROCM_USE_AITER=0
export TOKENIZERS_PARALLELISM=false
