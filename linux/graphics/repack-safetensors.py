#!/usr/bin/env python3
"""Merge/relabel safetensors without casting, bounded RAM, with byte verification."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct


def header(path):
    with path.open('rb') as stream:
        length = struct.unpack('<Q', stream.read(8))[0]
        if length > 16 * 1024 * 1024:
            raise ValueError('Unexpected safetensors header size')
        result = json.loads(stream.read(length))
    return result, 8 + length


def repack(inputs, output, mapping):
    records = []
    names = set()
    for source in inputs:
        info, start = header(source)
        entries = [(k, v) for k, v in info.items() if k != '__metadata__']
        end = 0
        for name, spec in sorted(entries, key=lambda pair: pair[1]['data_offsets'][0]):
            first, last = spec['data_offsets']
            assert first == end and last >= first, (source, name, 'noncontiguous data')
            end = last
            target = mapping.get(name, {'name': name, 'shape': spec['shape']})
            assert math.prod(target['shape']) == math.prod(spec['shape'])
            assert target['name'] not in names, ('duplicate', target['name'])
            names.add(target['name'])
            records.append(dict(source=source, source_offset=start + first,
                name=target['name'], dtype=spec['dtype'], shape=target['shape'],
                length=last - first))
        assert start + end == source.stat().st_size, source
    if mapping:
        assert len(mapping) == len(records), 'Mapping must cover exactly every source tensor'
    result = {'__metadata__': {'format': 'pt', 'conversion': 'lossless merge/key-shape mapping; no dtype casts'}}
    offset = 0
    for item in records:
        result[item['name']] = dict(dtype=item['dtype'], shape=item['shape'],
            data_offsets=[offset, offset + item['length']])
        offset += item['length']
    raw = json.dumps(result, separators=(',', ':')).encode()
    raw += b' ' * (-len(raw) % 8)
    prefix = struct.pack('<Q', len(raw)) + raw
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + '.repacking')
    if output.exists() or temporary.exists():
        raise FileExistsError(output)
    with temporary.open('xb') as out:
        out.write(prefix)
        for item in records:
            digest = hashlib.sha256()
            with item['source'].open('rb') as stream:
                stream.seek(item['source_offset'])
                remaining = item['length']
                while remaining:
                    chunk = stream.read(min(16 * 1024 * 1024, remaining))
                    if not chunk:
                        raise EOFError(item['source'])
                    out.write(chunk)
                    digest.update(chunk)
                    remaining -= len(chunk)
            item['sha256'] = digest.hexdigest()
    print(f'{output.name}: wrote {len(records)} tensors; independently verifying payloads', flush=True)
    whole = hashlib.sha256()
    with temporary.open('rb') as stream:
        assert stream.read(len(prefix)) == prefix
        whole.update(prefix)
        for item in records:
            digest = hashlib.sha256()
            remaining = item['length']
            while remaining:
                chunk = stream.read(min(16 * 1024 * 1024, remaining))
                if not chunk:
                    raise EOFError(temporary)
                digest.update(chunk)
                whole.update(chunk)
                remaining -= len(chunk)
            assert digest.hexdigest() == item['sha256'], item['name']
        assert stream.read(1) == b''
    temporary.rename(output)
    summary = dict(file=output.name, bytes=output.stat().st_size,
        sha256=whole.hexdigest(), tensors=len(records), lossless=True,
        sources=[p.name for p in inputs], all_tensor_payloads_verified=True)
    output.with_suffix('.verification.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--key-map', type=Path)
    parser.add_argument('--rename-prefix', nargs=2, action='append', default=[],
        metavar=('OLD', 'NEW'), help='Rename a leading tensor-key prefix without changing its data')
    args = parser.parse_args()
    mapping = json.loads(args.key_map.read_text()) if args.key_map else {}
    if args.rename_prefix:
        if mapping:
            parser.error('Use a key map or prefix renaming, not both')
        for source in args.inputs:
            for name, spec in header(source)[0].items():
                if name == '__metadata__':
                    continue
                renamed = name
                for old, new in args.rename_prefix:
                    if renamed.startswith(old):
                        renamed = new + renamed[len(old):]
                        break
                mapping[name] = dict(name=renamed, shape=spec['shape'])
    repack(args.inputs, args.output, mapping)
