"""Write the two TP2 half-width H3 checkpoints once (fcys core.slice_state_dict, unchanged).

Each rank then loads only its own ~10 GB half; the load hook sees qkv rows 10752 and skips the
per-job CPU split. A manifest records the source file's size/mtime/sha256 and each half's sha256;
the TP2 glue only uses the halves when the manifest still matches the source.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import torch
from safetensors import safe_open
from safetensors.torch import save_file

sys.path.insert(0, os.environ["H3_TP2_CORE"])
import core  # noqa: E402

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


st = SRC.stat()
manifest = {"schema": 1, "source": SRC.name, "source_bytes": st.st_size, "source_mtime_ns": st.st_mtime_ns,
            "source_sha256": sha(SRC), "method": "fcys tp2-comfy core.slice_state_dict (world 2)", "halves": {}}
with safe_open(str(SRC), framework="pt") as f:
    meta = f.metadata() or {}
    keys = list(f.keys())
for rank in (0, 1):
    with safe_open(str(SRC), framework="pt") as f:
        sd = {k: f.get_tensor(k) for k in keys}
    sd = core.slice_state_dict(sd, rank)
    assert tuple(sd["blocks.0.attn.qkv_proj.weight"].shape) == (10752, 5376)
    name = SRC.stem + f".tp2-rank{rank}.safetensors"
    dst = OUT / name
    save_file({k: v.contiguous() for k, v in sd.items()}, str(dst), metadata=meta)
    del sd
    manifest["halves"][str(rank)] = {"file": name, "bytes": dst.stat().st_size, "sha256": sha(dst)}
    print("wrote", dst, dst.stat().st_size, flush=True)
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("manifest ok")
