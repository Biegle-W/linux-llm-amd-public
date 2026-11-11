"""Public-suite adapter for run_suite.py; standard library only.

PUB_ITEMS overrides the item path. PUB_TIER is core (default), extended (the
additional items only), or all (core plus additional extended items).
"""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_items(path=None, tier=None):
    path = Path(path or os.environ.get('PUB_ITEMS', HERE / 'items.jsonl'))
    tier = tier or os.environ.get('PUB_TIER', 'core')
    if tier not in {'core', 'extended', 'all'}:
        raise ValueError(f'PUB_TIER must be core, extended, or all; got {tier!r}')
    data = path.read_bytes()
    manifest_path = path.with_suffix('.manifest.json')
    if not manifest_path.exists():
        raise RuntimeError(f'Missing manifest: {manifest_path}; rebuild items with build_items.py')
    manifest = json.loads(manifest_path.read_text())
    if (manifest.get('schema_version') != 3 or manifest.get('frozen') is not True
            or manifest.get('pending') or manifest.get('reference_validation_runs') != 3
            or not manifest.get('candidates_sha256')):
        raise RuntimeError('Items are draft/unvalidated; run build_items.py --validate-code on Linux before inference')
    digest = hashlib.sha256(data).hexdigest()
    if digest != manifest['items_sha256']:
        raise RuntimeError(f'ITEMS CHANGED: expected {manifest["items_sha256"]}, got {digest}')
    rows = [json.loads(line) for line in data.splitlines() if line.strip()]
    if len(rows) != manifest['item_count'] or len({r['id'] for r in rows}) != len(rows):
        raise RuntimeError('Item count mismatch or duplicate IDs')
    for row in rows:
        if 'reference_source' in row or 'candidate_rank' in row:
            raise RuntimeError('Candidate data found in frozen items')
        if row['tier'] not in {'core', 'extended'}:
            raise ValueError(f'Invalid item tier: {row["tier"]!r}')
        body = row['body']
        if 'model' in body or not body.get('messages') or not isinstance(body.get('max_tokens'),int) or body['max_tokens'] <= 0:
            raise ValueError(f'Invalid request body: {row["id"]}')
    rows.sort(key=lambda r:(r['tier'] != 'core', hashlib.sha256(f'20261110|order|{r["id"]}'.encode()).hexdigest(), r['id']))
    return [r for r in rows if tier == 'all' or r['tier'] == tier]


def requests():
    """Return (id, category, OpenAI body) triples, without sending answer keys."""
    return [(r['id'], r['category'], r['body']) for r in load_items()]
