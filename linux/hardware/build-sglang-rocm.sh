#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/rocm-env.sh"
export CC="$ROOT/llm-tools/cuda-build/bin/x86_64-conda-linux-gnu-cc"
export CXX="$ROOT/llm-tools/cuda-build/bin/x86_64-conda-linux-gnu-c++"
export HIPCC_COMPILE_FLAGS_APPEND="--gcc-install-dir=$ROOT/llm-tools/cuda-build/lib/gcc/x86_64-conda-linux-gnu/14.4.0 --sysroot=$ROOT/llm-tools/cuda-build/x86_64-conda-linux-gnu/sysroot"
cd "$ROOT/sglang/rocm-src/python/sglang/kernels/aot"
"$ROOT/sglang/.venv-rocm/bin/python" -c "import amdsmi,runpy;runpy.run_path('setup_rocm.py',run_name='__main__')" build_ext --inplace
"$ROOT/sglang/.venv-rocm/bin/python" - <<'PY'
import shutil,sys
from pathlib import Path
shutil.copytree('python/sgl_kernel',Path(sys.prefix)/'lib/python3.12/site-packages/sgl_kernel',dirs_exist_ok=True)
PY
