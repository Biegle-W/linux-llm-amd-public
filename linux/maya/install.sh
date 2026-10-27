#!/usr/bin/env bash
# CPU-only preparation. Never starts/calibrates inference or promotes profiles.
set -euo pipefail
MAYA_SETUP_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
MAYA_MODELS_ROOT=${MAYA_MODELS_ROOT:?Set MAYA_MODELS_ROOT to the Maya folder on the shared NVMe}
case "${1:-}" in glm|deepseek) family=$1 ;; *) echo 'Usage: MAYA_MODELS_ROOT=/path/LLM-Models/Maya maya/install.sh {glm|deepseek}; DeepSeek-S is retired.' >&2; exit 2 ;; esac
cd "$MAYA_SETUP_ROOT"
# XS uses the retained S Engram shards5/6. Only verify this sealed pack: stock
# DeepSeek setup would download retired S assets or duplicate shared Engram data.
if [[ $family == deepseek ]]; then
    exec python3 maya/verify-xs-pack.py --root "$MAYA_MODELS_ROOT"
fi
glm_quant=${MAYA_GLM_QUANT:-$(python3 -c 'import json; print(json.load(open("dsh/maya-glm-profile.json"))["installer"]["quant"])')}
case "$glm_quant" in Maya-S-v2-IQ2_XXS) ;; *) echo 'Unsupported GLM quant; Maya-S24 rollback is retired.' >&2; exit 2 ;; esac
readarray -t pins < <(python3 - <<'PY'
import json
p=json.load(open('maya/runtime.json'));print(p['source_commit']);print(p['rocwmma_commit'])
PY
)
for spec in "upstream https://github.com/mw00/project-maya.git ${pins[0]}" "rocwmma-7.2.3 https://github.com/ROCm/rocWMMA.git ${pins[1]}"; do
    read -r folder repo revision <<< "$spec"
    if [[ ! -d "maya/$folder" ]]; then
        git clone --no-checkout "$repo" "maya/$folder"
        git -C "maya/$folder" checkout --detach "$revision"
    fi
    [[ $(git -C "maya/$folder" rev-parse HEAD) == "$revision" ]] || { echo "$folder source pin differs; preserved for review" >&2; exit 1; }
    git -C "maya/$folder" diff --quiet HEAD -- || { echo "$folder has source edits; preserved for review" >&2; exit 1; }
done
source maya/build-env.sh
MAYA_SETUP_PYTHON=${MAYA_SETUP_PYTHON:-"$MAYA_SETUP_ROOT/llm-tools/python/cpython-3.12.14-linux-x86_64-gnu/bin/python3.12"}
[[ -x maya/upstream/.venv/bin/python ]] || "$MAYA_SETUP_PYTHON" -m venv maya/upstream/.venv
maya/upstream/.venv/bin/python -m pip install -r maya/requirements-lock.txt
common=(--backend hip --gpus 0,1 --context 8192 --models-dir "$MAYA_MODELS_ROOT" --vram-reserve-mib 8192 --port 30031 --host 127.0.0.1 --plain --yes --no-start --no-speed-calibration)
# gfx1100 fused IQ2_S down parity failed in the 1.1.24 candidate; retain MMQ.
selected=(--model "$glm_quant" --gguf-dir "$MAYA_MODELS_ROOT/$glm_quant" --draft mtp --no-vision --env MAYA_GLM_RAM_GB=40 --env MAYA_GLM_RAM_HEADROOM_GB=12 --env MAYA_GLM_RESERVE_MB=8192 --env MAYA_GLM_RESERVE_LATER_MB=8192 --env MAYA_GLM_PREFILL_FUSED=0)
cd maya/upstream
exec .venv/bin/python -B -u maya.py "${common[@]}" "${selected[@]}"
