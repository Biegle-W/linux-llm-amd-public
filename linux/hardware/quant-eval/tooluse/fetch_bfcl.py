#!/usr/bin/env python3
"""Fetch the pinned BFCL v4 source files the manifest was built from into bfcl-src/ (not kept in the repository).

    python3 fetch_bfcl.py            # downloads each file listed in fast_amd/manifest.json and checks its sha256

Source: github.com/ShishirPatil/gorilla (Apache-2.0), folder berkeley-function-call-leaderboard/bfcl_eval/, at the
commit recorded in the manifest. A file whose hash differs is refused.
"""
import hashlib, json, sys, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
m = json.loads((HERE / 'fast_amd/manifest.json').read_text())
commit = m['source_commit']
out = HERE / 'bfcl-src'
base = f'https://raw.githubusercontent.com/ShishirPatil/gorilla/{commit}/berkeley-function-call-leaderboard/bfcl_eval/'
for rel, want in m['source_sha256'].items():
    if rel == 'COMMIT':
        continue
    data = urllib.request.urlopen(base + rel, timeout=60).read()
    got = hashlib.sha256(data).hexdigest()
    if got != want:
        sys.exit(f'{rel}: sha256 {got} differs from the manifest ({want})')
    p = out / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    print('ok', rel)
(out / 'COMMIT').write_text(commit + '\n')
if hashlib.sha256((out / 'COMMIT').read_bytes()).hexdigest() != m['source_sha256']['COMMIT']:
    sys.exit('COMMIT file differs from the manifest record')
print('all files match commit', commit)
