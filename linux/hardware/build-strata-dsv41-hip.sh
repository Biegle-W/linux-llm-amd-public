#!/usr/bin/env bash
# Separate Strata DeepSeek component; the Qwen and Maya installations are independent.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/rocm-env.sh"
TOOLCHAIN="$ROOT/llm-tools/cuda-build"
export CC="$TOOLCHAIN/bin/x86_64-conda-linux-gnu-cc"
export CXX="$TOOLCHAIN/bin/x86_64-conda-linux-gnu-c++"
export LD_LIBRARY_PATH="$TOOLCHAIN/lib:$LD_LIBRARY_PATH"
export CPATH="$ROOT/maya/rocwmma-7.2.3/library/include${CPATH:+:$CPATH}"
export LDFLAGS="-Wl,-rpath-link,$ROCM_PATH/lib:$ROOT/llm-tools/rocm-sdk/host-libs/usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu"
SOURCE_DIR="${STRATA_DSV41_SOURCE_DIR:-$ROOT/strata-dsv41/upstream}"
BUILD_DIR="${STRATA_DSV41_BUILD_DIR:-$SOURCE_DIR/build-hip}"
GGML_DIR="${STRATA_GGML_DIR:-$ROOT/strata/third_party/llama.cpp}"
HIP_FLAGS="--gcc-install-dir=$TOOLCHAIN/lib/gcc/x86_64-conda-linux-gnu/14.4.0 --sysroot=$TOOLCHAIN/x86_64-conda-linux-gnu/sysroot"
cmake -S "$SOURCE_DIR" -B "$BUILD_DIR" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DSTRATA_ENABLE_HIP=ON -DSTRATA_ENABLE_CUDA=OFF \
  -DCMAKE_HIP_ARCHITECTURES=gfx1100 -DSTRATA_BUILD_TESTS=OFF \
  -DSTRATA_BUILD_DSV41=ON -DSTRATA_NATIVE_EXPERTS=ON -DSTRATA_GGML_DIR="$GGML_DIR" \
  -DCMAKE_HIP_COMPILER="$ROCM_PATH/llvm/bin/clang++" \
  -DCMAKE_HIP_COMPILER_ROCM_ROOT="$ROCM_PATH" \
  -DCMAKE_HIP_FLAGS="$HIP_FLAGS --rocm-path=$ROCM_PATH --rocm-device-lib-path=$ROCM_PATH/amdgcn/bitcode" \
  -DCMAKE_PREFIX_PATH="$ROCM_PATH"
cmake --build "$BUILD_DIR" -j "${BUILD_JOBS:-3}" --target strata-dsv41 ds4_iq_test ds4_slot_test
python3 "$ROOT/hardware/build-strata-dsv41-tests.py" "$SOURCE_DIR" "$BUILD_DIR"
python3 - "$SOURCE_DIR" "$BUILD_DIR" "$GGML_DIR" <<'PY'
import hashlib,json,subprocess,sys
from pathlib import Path
source,build,ggml=map(Path,sys.argv[1:])
record={'source_commit':subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),
        'backend':'HIP','architecture':'gfx1100','runtime':'ROCm7.2.3',
        'ggml':{'source_directory':str(ggml),'declared_archive_commit':(source/'third_party/ggml/VERSION.txt').read_text().split()[0]},
        'binaries':{'strata-dsv41':hashlib.sha256((build/'strata-dsv41').read_bytes()).hexdigest()}}
(build/'local-build.json').write_text(json.dumps(record,indent=2)+'\n')
PY
