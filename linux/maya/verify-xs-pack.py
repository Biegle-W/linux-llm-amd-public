#!/usr/bin/env python3
"""Verify a selected shared DeepSeek pack without rerunning stock setup.

This checks existing validated metadata and file presence, not a new full weight
checksum pass or activation. Initial assets require the pinned manifest checks.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
from maya_runtime import config_fingerprint, pack_metadata_fingerprint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--profile', choices=('xs', 's'), default='xs')
    args = parser.parse_args()
    filename = 'maya-deepseek-s-profile.json' if args.profile == 's' else 'maya-deepseek-profile.json'
    quant = 'Maya-S' if args.profile == 's' else 'Maya-XS'
    cfg = json.loads((ROOT / 'dsh' / filename).read_text())
    selected = cfg['args']
    pack = Path(selected[selected.index('--pack') + 1])
    expected = args.root.resolve() / 'DeepSeek-V4.1-Flash-1017-GGUF' / quant / 'maya-ds4'
    proof = cfg.get('local_validation', {})
    if (pack.resolve() != expected or proof.get('status') != 'passed' or
            proof.get('config_sha256') != config_fingerprint(cfg) or
            proof.get('pack_metadata_sha256') != pack_metadata_fingerprint(pack)):
        raise RuntimeError('Prepare and validate the selected DeepSeek pack at this location before selecting it.')
    model = pack.parent
    for line in (pack / 'tensors.txt').read_text().splitlines():
        if line.startswith('file '):
            if not (model / line.split(' ', 2)[2]).is_file():
                raise RuntimeError('A shared DeepSeek model dependency is missing; mount its model volume.')
    print('Selected ' + quant + ' metadata and shared dependencies verified; no download or inference started.')


if __name__ == '__main__':
    main()
