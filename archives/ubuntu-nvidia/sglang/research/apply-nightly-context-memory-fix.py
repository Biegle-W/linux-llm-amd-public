#!/usr/bin/env python3
"""Opt out of unsupported NVLink multicast probes on the local mixed GPU pair."""
import difflib
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = subprocess.check_output([
    str(ROOT / 'sglang/.venv/bin/python'), '-c',
    'import importlib.metadata; print(importlib.metadata.version("sglang"))',
], text=True).strip()
assert VERSION == '0.5.22.dev20261015+ga12814c158', f'Review this fix for SGLang {VERSION}'
relative = 'srt/distributed/device_communicators/triton_symm_mem_ag.py'
path = ROOT / 'sglang/.venv/lib/python3.12/site-packages/sglang' / relative
old = path.read_text()
flag = 'SGLANG_LOCAL_DISABLE_MULTIMEM_AG'
if flag in old:
    print('Multicast opt-out already installed for SGLang 0.5.22.dev20261015+ga12814c158.')
    raise SystemExit(0)
needle = '        self._state = self._UNINIT if enabled else None'
assert old.count(needle) == 1
assert old.count('import logging\n') == 1
new = old.replace('import logging\n', 'import logging\nimport os\n', 1)
new = new.replace(needle, '''        # No NVLink multicast on RTX 3060/4070. Skip the symmetric allocation
        # and collective probe, using the same NCCL fallback as failed probes.
        enabled = enabled and os.environ.get("SGLANG_LOCAL_DISABLE_MULTIMEM_AG") != "1"
        self._state = self._UNINIT if enabled else None''', 1)
compile(new, str(path), 'exec')
patch = ''.join(difflib.unified_diff(
    old.splitlines(True), new.splitlines(True),
    fromfile='a/' + relative, tofile='b/' + relative))
(Path(__file__).parent / 'no-multimem-0.5.22.dev20261015+ga12814c158.patch').write_text(patch)
path.write_text(new)
report = {'version': VERSION, 'file': relative,
          'before_sha256': hashlib.sha256(old.encode()).hexdigest(),
          'after_sha256': hashlib.sha256(new.encode()).hexdigest(),
          'env': flag, 'scope': 'Opt-in only; retain NCCL all-gather and full CUDA graphs'}
(ROOT / 'dsh/research/upgrade-2026-10-14/sglang-memory-patch.json').write_text(
    json.dumps(report, indent=2) + '\n')
print('SGLang multicast probe opt-out installed; source syntax checked.')
