#!/usr/bin/env python3
"""Read H3 file metadata and Python ASTs; never import model or GPU code."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import struct

MAX_SOURCE = 2 * 1024 * 1024
MAX_HEADER = 16 * 1024 * 1024


def inspect_python(path):
    if not path.is_file():
        return {"present": False}
    if path.stat().st_size > MAX_SOURCE:
        raise ValueError("Unexpected source file size: " + path.name)
    data = path.read_bytes()
    tree = ast.parse(data, filename=path.name)
    return {"present": True, "sha256": hashlib.sha256(data).hexdigest(),
            "classes": [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)],
            "imports": sorted({n.module or "" for n in ast.walk(tree)
                               if isinstance(n, ast.ImportFrom)}),
            "int8_tp_reference": b"Int8TensorwiseOps" in data or
                                  b".int8_quant" in data,
            "W4A4_loader_reference": b"convrot_w4a4" in data}


def inspect_asset(path):
    if not path.is_file():
        return {"present": False}
    size = path.stat().st_size
    with path.open("rb") as stream:
        length_bytes = stream.read(8)
        if len(length_bytes) != 8:
            raise ValueError("Truncated safetensors file: " + path.name)
        length = struct.unpack("<Q", length_bytes)[0]
        if not 2 <= length <= min(MAX_HEADER, size - 8):
            raise ValueError("Invalid or excessive safetensors header: " + path.name)
        raw = stream.read(length)
        if len(raw) != length:
            raise ValueError("Truncated safetensors header: " + path.name)
    header = json.loads(raw)
    if not isinstance(header, dict):
        raise ValueError("Safetensors header must be an object: " + path.name)
    tensors = [v for k, v in header.items() if k != "__metadata__"]
    for item in tensors:
        if not isinstance(item, dict):
            raise ValueError("Invalid tensor entry: " + path.name)
        offsets = item.get("data_offsets")
        if (not isinstance(offsets, list) or len(offsets) != 2 or
                any(type(n) is not int for n in offsets)):
            raise ValueError("Invalid tensor offsets: " + path.name)
        start, end = offsets
        if not 0 <= start <= end <= size - 8 - length:
            raise ValueError("Out-of-bounds tensor metadata: " + path.name)
    return {"present": True, "size_bytes": size, "tensor_count": len(tensors),
            "header_sha256": hashlib.sha256(raw).hexdigest(),
            "tensor_payload_read": False, "model_compatible": "not_qualified"}


def inspect(comfy, tp, models, sparse=None, runner=None):
    plugin = comfy / "custom_nodes/ComfyUI-INT8-Fast-ROCM"
    sources = {"plugin/" + name: inspect_python(plugin / name) for name in
               ("__init__.py", "int4_unet_loader.py", "int4_lora.py", "w4a8_int8.py")}
    sources.update({"tp/" + name: inspect_python(tp / name) for name in
                    ("core.py", "tp_boot.py", "tp_linear.py")})
    sources["sparse_attention"] = inspect_python(sparse) if sparse else {"present": False}
    sources["custom_w4a8_runner"] = inspect_python(runner) if runner else {"present": False}
    assets = {"diffusion": inspect_asset(models / "diffusion_models" /
                 "Minimax-h3_Singularity_ref2va_v2_pruned_w4a8.safetensors"),
              "turbo_lora": inspect_asset(models / "loras" /
                 "minimax_h3_turbo_v4_step600_ema_pruned_comfyui.safetensors")}
    missing = [k for k, value in assets.items() if not value["present"]]
    missing += [k for k in ("sparse_attention", "custom_w4a8_runner")
                if not sources[k]["present"]]
    return {"schema": 1, "status": "inventory_only", "sources": sources,
            "assets": assets, "missing": missing,
            "qualification_pending": ["source/license and asset-format review",
                "W4A8 packed-weight sharding, scales, ConvRot and LoRA correctness",
                "sparse-attention integration and finite numerical output",
                "existing memory/ownership/thermal/swap guards",
                "measured transport identity and full media checks"],
            "ready_to_launch": False, "GPU_work_submitted": False,
            "note": "File presence and AST validity do not establish compatibility."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comfy-root", type=Path, required=True)
    parser.add_argument("--tp-root", type=Path, required=True)
    parser.add_argument("--models-root", type=Path, required=True)
    parser.add_argument("--sparse-source", type=Path)
    parser.add_argument("--runner-source", type=Path)
    args = parser.parse_args()
    try:
        result = inspect(args.comfy_root, args.tp_root, args.models_root,
                         args.sparse_source, args.runner_source)
    except (OSError, ValueError, KeyError, TypeError, SyntaxError) as exc:
        parser.exit(2, str(exc) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
