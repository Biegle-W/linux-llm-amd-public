"""Preload AMD SMI before torch; retain multiprocessing's normal main guard."""
import amdsmi
import hashlib
import os
from pathlib import Path

if os.environ.get('VLLM_LOCAL_RDNA_PREFILL') == '1':
    source = Path(__file__).resolve().parent/'.venv-rocm/lib/python3.12/site-packages/vllm/v1/attention/ops/triton_unified_attention.py'
    if hashlib.sha256(source.read_bytes()).hexdigest() != 'b2c2a9edeb0e2f9d4b339e1db5d976bdf420adbc0453cec69bc83d9e411be58e':
        raise RuntimeError('Validated Radeon prefill patch missing or changed; apply vllm/apply-rdna-prefill.py to the pinned wheel before launching.')
if __name__ == '__main__':
    from vllm.entrypoints.cli.main import main
    main()
