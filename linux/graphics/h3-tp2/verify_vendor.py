"""Refuse to start the TP2 server if the vendored fcys/INT8 code differs from the qualified copy."""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENDOR = HERE.parents[1] / "runtime/h3-tp2"
bad = []
for line in (HERE / "vendor-sha256.txt").read_text().splitlines():
    digest, rel = line.split(None, 1)
    path = VENDOR / rel.strip()
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        bad.append(rel.strip())
if bad:
    sys.exit("H3 TP2 vendored code changed or missing: " + ", ".join(bad) + " (use COMFY_MODE=staged)")
