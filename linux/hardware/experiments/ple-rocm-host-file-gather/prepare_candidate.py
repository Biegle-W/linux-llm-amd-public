#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prepare an isolated, exact-hash Python overlay. Never modifies the wheel."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def prepare(wheel_root,output):
    manifest=json.loads((HERE/'base-manifest.json').read_text())
    wheel_root=wheel_root.resolve();output=output.resolve()
    if output.exists():raise ValueError('Output must be a new directory')
    if output.is_relative_to(wheel_root):
        raise ValueError('Output must be outside the installed wheel root')
    for rel,digest in manifest['base_files'].items():
        p=wheel_root/rel
        if not p.is_file() or sha(p)!=digest:
            raise ValueError('Wheel file does not match the reviewed base: '+rel)
    payload=output/'payload';payload.mkdir(parents=True)
    for rel in manifest['base_files']:
        dest=payload/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(wheel_root/rel,dest)
    patch=HERE/'rocm-host-file-gather.patch'
    args=['patch','--batch','--fuzz=0','-p1','-i',str(patch)]
    subprocess.run(args+['--dry-run'],cwd=payload,check=True,capture_output=True)
    subprocess.run(args,cwd=payload,check=True,capture_output=True)
    for rel,digest in manifest['candidate_files'].items():
        if sha(payload/rel)!=digest:raise ValueError('Patched result hash mismatch: '+rel)
    def overlay(live,dest,changes):
        dest.mkdir(parents=True)
        names={p.name for p in live.iterdir()}|{p.name for p in changes.iterdir()}
        for name in names:
            if name=='__pycache__':continue
            source=live/name;change=changes/name;target=dest/name
            if change.is_dir():overlay(source,target,change)
            elif change.is_file():target.symlink_to(change)
            else:target.symlink_to(source,target_is_directory=source.is_dir())
    overlay(wheel_root/'vllm',output/'overlay/vllm',payload/'vllm')
    print('Prepared isolated overlay:',output/'overlay')
    print('No installed file was modified. No model or GPU was initialized.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel-root',required=True,type=Path,help='site-packages containing the reviewed vllm wheel')
    parser.add_argument('--output',required=True,type=Path,help='New isolated working directory')
    a=parser.parse_args();prepare(a.wheel_root,a.output)
