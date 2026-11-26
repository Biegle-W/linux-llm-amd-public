"""Every enabled local model across backends: one source for the hub and the network gateway."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKENDS = {
    'llama': ('models.json', 8080, 'llama.cpp'),
    'sglang': ('sglang-profiles.json', 30000, 'SGLang'),
    'vllm': ('vllm-profiles.json', 30010, 'vLLM'),
    'strata': ('strata-profiles.json', 30020, 'Strata'),
    'maya': ('maya-profiles.json', 30030, 'Maya'),
}


def catalog(root=None):
    root = Path(root) if root is not None else ROOT
    models = {}
    for backend, (filename, port, label) in BACKENDS.items():
        path = root / 'dsh' / filename
        if not path.exists():
            continue
        source = json.loads(path.read_text())
        rows = source if isinstance(source, list) else [dict(id=k, **v) for k, v in source.items()]
        for row in rows:
            if not row.get('enabled', backend != 'maya'):
                continue
            if row['id'] in models:
                raise ValueError('Duplicate API model ID')
            models[row['id']] = {'id': row['id'], 'object': 'model', 'created': 0,
                                 'owned_by': 'local-' + backend, 'name': row['name'],
                                 'context_length': row['context'], 'backend': backend}
    return models


def api_names(root=None):
    """Shared API name -> this server's route (owner, November 26: the same names on both servers).

    Comes from benchmarks/shared/models.json, which is identical on the NVIDIA server.
    """
    root = Path(root) if root is not None else ROOT
    try:
        names = json.loads((root / 'benchmarks/shared/models.json').read_text()).get('api_names', {})
    except (OSError, ValueError):
        return {}
    return {public: servers['amd'] for public, servers in names.items() if servers.get('amd')}


def public_catalog(root=None):
    """The catalog as clients see it: shared API names where one exists, with the internal route in 'route'."""
    models = catalog(root)
    public = {route: name for name, route in api_names(root).items() if route in models}
    return {public.get(route, route): dict(model, id=public.get(route, route), route=route)
            for route, model in models.items()}


def resolve(name, root=None):
    """The internal route for a shared API name or an internal route id; None when unknown or retired."""
    models = catalog(root)
    route = name if name in models else api_names(root).get(name)
    return route if route in models else None
