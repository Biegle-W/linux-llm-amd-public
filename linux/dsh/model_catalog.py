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
