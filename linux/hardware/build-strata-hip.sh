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
STRATA_SOURCE_DIR="${STRATA_SOURCE_DIR:-$ROOT/strata}"
STRATA_BUILD_DIR="${STRATA_BUILD_DIR:-$STRATA_SOURCE_DIR/build-hip}"
STRATA_GGML_DIR="${STRATA_GGML_DIR:-$ROOT/strata/third_party/llama.cpp}"
cmake -S "$STRATA_SOURCE_DIR" -B "$STRATA_BUILD_DIR" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DSTRATA_ENABLE_CUDA=OFF -DSTRATA_ENABLE_HIP=ON \
  -DSTRATA_GGML_DIR="$STRATA_GGML_DIR" \
  -DCMAKE_HIP_ARCHITECTURES=gfx1100 -DSTRATA_PREFILL_MMQ=ON \
  -DCMAKE_HIP_COMPILER="$ROCM_PATH/llvm/bin/clang++" \
  -DCMAKE_HIP_FLAGS="$HIP_FLAGS" -DCMAKE_PREFIX_PATH="$ROCM_PATH" \
  -DCMAKE_EXE_LINKER_FLAGS="-Wl,-rpath-link,/usr/lib/x86_64-linux-gnu"
cmake --build "$STRATA_BUILD_DIR" --target strata strata-device -j "${BUILD_JOBS:-2}"
python3 - "$STRATA_SOURCE_DIR" "$STRATA_BUILD_DIR" "$STRATA_GGML_DIR" "$ROCM_PATH" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

source, build, ggml = (Path(value).resolve() for value in sys.argv[1:4])
def commit(path):
    return subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
ggml_info = {'source_directory': str(ggml)}
if (ggml/'.git').exists():
    ggml_info['source_commit'] = commit(ggml)
else:
    # setup.py also supports a source archive with no .git directory. Do not
    # accidentally report the enclosing Strata repository's commit as ggml's.
    version = source/'third_party/ggml/VERSION.txt'
    ggml_info['declared_archive_commit'] = version.read_text().split()[0]
    ggml_info['cmake_sha256'] = hashlib.sha256((ggml/'CMakeLists.txt').read_bytes()).hexdigest()
record = {'source_commit': commit(source), 'ggml': ggml_info,
          'built_utc': datetime.now(timezone.utc).isoformat(),
          'backend': 'HIP', 'architecture': 'gfx1100', 'rocm_path': sys.argv[4],
          'binaries': {name: hashlib.sha256((build/name).read_bytes()).hexdigest()
                       for name in ('strata', 'strata-device')}}
(build/'local-build.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(record, indent=2))
PY
printf '%s\n' 'Built separate HIP engine. Validate on the AMD GPU before activating a profile.'
