#!/usr/bin/env python3
"""Download only pinned, published-checksum Maya assets to an explicit model root.

Run before inference tests: large file reads/writes can affect their timings.
Partial files resume with curl; a final filename is published only after SHA256.
Existing complete mismatches are preserved and cause a failure for review.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8*1024**2),b''):h.update(block)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--family',choices=('glm','deepseek','all'),default='all')
    ap.add_argument('--manifest',type=Path,default=Path(__file__).with_name('models.json'),
                    help='Explicit pinned asset manifest; defaults to the installed model set.')
    a=ap.parse_args();manifest=json.loads(a.manifest.read_text())
    if manifest.get('status') == 'retired':
        ap.error('This manifest is retired checksum history; no assets will be downloaded.')
    for row in manifest['files']:
        family=row.get('family') or ('glm' if Path(row['remote']).name.startswith('GLM-') else 'deepseek')
        if a.family not in (family,'all'):continue
        dst=a.root/row['file'];dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists():
            if dst.stat().st_size!=row['size'] or sha(dst)!=row['sha256']:
                raise RuntimeError(f'Existing asset differs; preserved for review: {dst}')
            print('verified',row['file'],flush=True);continue
        # The installer intentionally replaces this raw shard with its verified
        # lossless pack. Avoid downloading a second copy after conversion.
        if '/vision/' in row['file'] and (dst.parent/'vision.bin').exists() and (dst.parent/'vision.json').exists():
            packed=manifest.get('converted_assets',[])
            if len(packed)!=2 or not all((a.root/item['file']).stat().st_size==item['size'] and sha(a.root/item['file'])==item['sha256'] for item in packed):
                raise RuntimeError('Converted vision pack differs; preserved for review before downloading raw duplicates')
            print('verified converted vision pack; raw download skipped',row['file'],flush=True);continue
        partial=dst.with_name(dst.name+'.partial')
        url=f"https://huggingface.co/{row['repo']}/resolve/{row['revision']}/{row['remote']}"
        subprocess.run(['curl','--fail','--location','--retry','5','--continue-at','-','--output',str(partial),url],check=True)
        if partial.stat().st_size!=row['size'] or sha(partial)!=row['sha256']:
            raise RuntimeError(f'Download checksum failed; partial preserved: {partial}')
        partial.replace(dst);print('verified',row['file'],flush=True)

if __name__=='__main__':main()
