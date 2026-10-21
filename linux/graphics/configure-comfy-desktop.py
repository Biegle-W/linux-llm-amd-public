#!/usr/bin/env python3
"""Register the existing ROCm ComfyUI installation with official Comfy Desktop.

Writes only this installation's app record/settings, never installs packages,
moves weights, or replaces workflow/user state. Run while Desktop is closed.
"""
import json
import os
import shlex
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL_ID = "local-dual-amd-comfyui"


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_name(path.name + ".before-local-import")
        if not backup.exists():
            backup.write_bytes(path.read_bytes())
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


def main():
    runtime = ROOT / "runtime/comfyui"
    assert (runtime / ".venv/bin/python").is_file(), "Existing environment missing"
    assert (runtime / "main.py").is_file(), "Existing ComfyUI missing"
    data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "comfyui-desktop-2"
    config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "comfyui-desktop-2"
    records = load(data / "installations.json", [])
    assert isinstance(records, list), "Unexpected installation schema; refusing overwrite"
    old = next((r for r in records if r.get("id") == INSTALL_ID), {})
    args = ["--cuda-device", "all", "--default-device", "0", "--listen", "127.0.0.1",
            "--port", "8188", "--extra-model-paths-config", str(ROOT / "graphics/extra_model_paths.yaml"),
            "--reserve-vram", "2", "--disable-pinned-memory", "--disable-async-offload",
            "--disable-dynamic-vram", "--cache-none", "--use-pytorch-cross-attention",
            "--disable-partner-nodes"]
    record = {**old, "id": INSTALL_ID, "name": "Local dual-AMD — existing models and workflows",
              "createdAt": old.get("createdAt", datetime.now(timezone.utc).isoformat()),
              "installPath": str(runtime), "sourceId": "git", "status": "installed", "seen": True,
              "repo": "https://github.com/Comfy-Org/ComfyUI", "branch": "HEAD",
              "venvPath": str(runtime / ".venv"), "launchArgs": shlex.join(args),
              "launchMode": "window", "browserPartition": "shared",
              "useSharedModels": False, "modelDirs": [], "useSharedInput": False,
              "inputDir": str(runtime / "input"), "useSharedOutput": False,
              "outputDir": str(ROOT / "graphics/outputs"),
              "envVars": {"ROCR_VISIBLE_DEVICES": "0,1", "OMP_NUM_THREADS": "8",
                          "PYTHONUNBUFFERED": "1"}}
    records = [r for r in records if r.get("id") != INSTALL_ID] + [record]
    settings = load(config / "settings.json", {})
    settings.update({"autoLaunchOnStartup": INSTALL_ID, "autoInstallUpdates": False,
                     "telemetryEnabled": False, "betaFeaturesEnabled": False,
                     "firstUseCompleted": True, "onAppClose": "quit"})
    save(data / "installations.json", records)
    save(config / "settings.json", settings)
    print("Registered existing ComfyUI; models, workflows and Python packages unchanged.")


if __name__ == "__main__":
    main()
