#!/usr/bin/env python3
"""Prepare separate Strata DeepSeek metadata from existing Maya S/XS weights.

Requires the pinned Strata source and existing verified Maya weights; never downloads
or copies weights, and never overwrites a pack. Run before any GPU timing work.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'strata-dsv41/generated'
OUT.mkdir(parents=True,exist_ok=True)
SRC = ROOT/'strata-dsv41/upstream'
sys.path.insert(0, str(ROOT/'dsh'))
from shared_storage import ensure_streaming_models, STREAM_MODELS

ensure_streaming_models()
MODELS = STREAM_MODELS/'Maya/DeepSeek-V4.1-Flash-1017-GGUF'
DEST = STREAM_MODELS/'Strata/DeepSeek-V4.1-Flash-1017'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

spec = importlib.util.spec_from_file_location('packer', SRC/'tools/dsv41/pack_gguf.py')
pk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pk)
records = []
for quant in ('Maya-S', 'Maya-XS'):
    model = MODELS/quant
    pack = DEST/quant/'pack'
    assert not pack.exists(), 'Never overwrite an existing prepared pack'
    originals = {str(model/'maya-ds4'/name):sha(model/'maya-ds4'/name)
                 for name in ('ds4.txt','tensors.txt','engram.bin')}
    shards = sorted(model.glob('*.gguf'))
    if quant == 'Maya-XS':
        assert len(shards) == 3
        shards += [next((MODELS/'Maya-S').glob(f'*-{n:05d}-of-*.gguf')) for n in (5,6)]
    else:
        assert len(shards) == 6
    drafter = MODELS/'dspark'/('dspark-xs2.json' if quant == 'Maya-XS' else 'dspark.json')
    assert drafter.is_file() and drafter.with_suffix('.bin').is_file()
    command = [sys.executable,str(SRC/'tools/dsv41/pack_gguf.py'),
               '--model',str(model),'--out',str(pack),'--drafter',str(drafter),
               '--shards',*[os.path.relpath(p,model) for p in shards]]
    subprocess.run(command,check=True)
    # The upstream packer stores shard basenames. Correct only cross-folder
    # Engram references, preserving every tensor type, offset, shape and byte count.
    path = pack/'tensors.txt'
    before = path.read_text()
    after = before
    for i,p in enumerate(shards):
        relative = os.path.relpath(p,model)
        after = after.replace(f'file {i} {p.name}\n',f'file {i} {relative}\n')
    assert [s for s in before.splitlines() if s.startswith('t ')] == [s for s in after.splitlines() if s.startswith('t ')]
    path.write_text(after)
    files = {}
    types = {}
    for line in after.splitlines():
        fields = line.split()
        if fields[0] == 'file':
            p = model/line.split(' ',2)[2]
            assert p.is_file()
            files[int(fields[1])] = p
        elif fields[0] == 't':
            assert int(fields[4])+int(fields[5]) <= files[int(fields[3])].stat().st_size
            types[fields[2]] = types.get(fields[2],0)+1
    assert sha(pack/'engram.bin') == sha(model/'maya-ds4/engram.bin')
    assert all(sha(Path(p)) == h for p,h in originals.items()), 'Maya metadata must remain unchanged'
    records.append({'quant':quant,'pack':str(pack),'model_dir':str(model),
                    'files':[{'path':str(p.resolve()),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in files.values()],
                    'types':types,'metadata':{n:sha(pack/n) for n in ('ds4.txt','tensors.txt','engram.bin')},
                    'maya_original_metadata':originals,'weights_copied':False,'weights_downloaded':False})
    print('PREPARED',quant,types,flush=True)
(OUT/'prepared.private.json').write_text(json.dumps(records,indent=2)+'\n')
