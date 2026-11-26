#!/usr/bin/env python3
"""Check that this server follows the shared model set and benchmark definitions.

    python3 benchmarks/shared/check_shared.py --server amd|nvidia [--tooluse-manifest PATH]

Run from the repository root (on AMD's public mirror, from linux/). Stdlib only; reads files, starts nothing.
Checks:
  1. the shared files are intact (hashes recorded in benchmarks.json);
  2. every shared model has an enabled route here, every enabled route is in models.json, and every shared
     API name points at an enabled route here without hiding another route;
  3. the short tool-use test here uses the shared 55 items in the shared order, with the same core episodes;
  4. the gBench part of the engine-update check runs the six shared cases.
Routes listed under "extra" in models.json are reported as notes, not failures.
--skip-routes leaves out check 2, for a public mirror whose registries are not kept current.
Exit 0 when everything matches, 1 otherwise.
"""
import argparse, ast, hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NVIDIA_HARNESS_MANIFEST = Path.home() / 'quality-eval-build/quality/fast/manifest.json'


def load(name):
    return json.loads((HERE / name).read_text())


def enabled_routes(server, root):
    if server == 'amd':
        sys.path.insert(0, str(root / 'dsh'))
        import model_catalog
        return set(model_catalog.catalog(root))
    profiles = json.loads((root / 'config/maintained-profiles.json').read_text())['profiles']
    return {p['id'] for p in profiles if p.get('status') == 'selected'}


def tooluse_ids(path):
    m = json.loads(Path(path).read_text())
    if 'entries' in m:  # NVIDIA harness format
        return [(e['id'], e['tier'] == 'core') for e in m['entries']]
    return [(i['id'], i['core']) for i in m['items']]  # AMD fast_amd format


def gbench_tasks(server, root):
    if server == 'nvidia':
        return json.loads((root / 'config/gbench-template-check.json').read_text())['tasks']
    tree = ast.parse((root / 'hardware/quant-eval/quick/run_golden.py').read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) == 'FIRST' for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError('FIRST not found in run_golden.py')


def check(server, root=ROOT, tooluse_manifest=None, check_routes=True):
    errors, notes = [], []
    spec, models = load('benchmarks.json'), load('models.json')
    q = spec['quality_ranking']
    data = (HERE / q['items']).read_bytes()
    if hashlib.sha256(data).hexdigest() != q['items_file_sha256']:
        errors.append(f"{q['items']} differs from the hash in benchmarks.json")
    shared = tooluse_ids(HERE / q['items'])
    if json.loads(data)['sha256'] != q['items_sha256'] or json.loads(data)['seed'] != q['seed']:
        errors.append('shared tool-use manifest id hash or seed differs from benchmarks.json')

    routes = enabled_routes(server, root) if check_routes else set()
    listed = set()
    for m in models['models']:
        want = set(m[server]['routes']); listed |= want
        missing = want - routes
        if missing and check_routes:
            errors.append(f"{m['model']}: route(s) not enabled here: {', '.join(sorted(missing))}")
    pending = {r for u in models['extra'] if u['server'] == server for r in u['routes']}
    for r in sorted(routes - listed):
        (notes if r in pending else errors).append(
            f"{r}: enabled here, {'server-specific extra route (models.json "extra")' if r in pending else 'not in models.json'}")

    for public, servers in models.get('api_names', {}).items():
        internal = servers[server]
        if check_routes and internal not in routes:
            errors.append(f'API name {public}: route {internal} is not enabled here')
        if check_routes and public != internal and public in routes:
            errors.append(f'API name {public} would hide the route of the same id here')

    path = tooluse_manifest
    if path is None:
        path = root / 'hardware/quant-eval/tooluse/fast_amd/manifest.json' if server == 'amd' else NVIDIA_HARNESS_MANIFEST
    if Path(path).exists():
        if tooluse_ids(path) != shared:
            errors.append(f'{path}: tool-use items differ from the shared list')
    else:
        notes.append(f'{path}: not found, tool-use items not checked')

    if gbench_tasks(server, root) != spec['engine_update_check']['gbench_tasks']:
        errors.append('gBench engine-check cases differ from the shared six')
    return errors, notes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--server', required=True, choices=['amd', 'nvidia'])
    ap.add_argument('--root', type=Path, default=ROOT)
    ap.add_argument('--tooluse-manifest', type=Path)
    ap.add_argument('--skip-routes', action='store_true', help='skip check 2 (for a public mirror whose registries are not current)')
    a = ap.parse_args(argv)
    errors, notes = check(a.server, a.root, a.tooluse_manifest, not a.skip_routes)
    for n in notes: print('note:', n)
    for e in errors: print('MISMATCH:', e)
    print('shared models and benchmarks: ' + ('OK' if not errors else f'{len(errors)} mismatch(es)'))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
