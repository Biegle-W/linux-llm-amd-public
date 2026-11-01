"""Present enabled local backends through one AMD server route in DSH."""
import json
import os
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent
HUB_PORT = 30100
AMD_PROVIDER = 'amd-server'
LOCAL = {'llama-local': 'empero-qwen3.8-35b-a3b',
         'sglang-local': 'qwen3.8-27b-sglang-dflash2',
         'vllm-local': 'qwen3.8-27b-vllm',
         'strata-local': 'qwen3.8-flash-next-iq3_xxs',
         'maya-local': 'glm-5.3-flash-maya',
         'hyperqwen-local': 'qwen3.8-27b-hyperqwen-dflash2'}
REPLACEMENTS = {
    'nemotron-3.5-lightning': 'nemotron-3.5-bolt-vllm',
    'gpt-oss-20b': 'nemotron-3.5-bolt-vllm',
    'gpt-oss-120b': 'nemotron-3.5-bolt-vllm',
    'nemotron-3.5-bolt': 'nemotron-3.5-bolt-vllm',
    'qwen3.8-27b-q4': 'qwen3.8-27b-vllm',
    'qwen3.6-35b-a3b': 'empero-qwen3.8-35b-a3b',
    'deepseek-v4.1-flash-1017-maya-s': 'deepseek-v4.1-flash-1017-maya',
    'deepseek-v4.1-flash-1017-strata-s': 'deepseek-v4.1-flash-1017-strata-xs',
}
NAMES = {
    'empero-qwen3.8-35b-a3b': 'Empero Qwen3.8 35B A3B',
    'nemotron-3.5-super-iq3': 'Nemotron 3.5 Super VL 120B · IQ3',
    'ornith-1.5-122b': 'Ornith 1.5 122B',
    'flint-40b-a2.5b': 'Flint 40B A2.5B',
    'qwen3.8-27b-sglang-dflash2': 'Qwen3.8 27B · SGLang DFlash2',
    'qwen3.8-27b-vllm': 'Qwen3.8 27B · vLLM MTP',
    'nemotron-3.5-bolt-vllm': 'Nemotron 3.5 Bolt 74B A9B',
    'sage-a1.5': 'Sage A1.5',
    'qwen3.8-flash-next-iq3_xxs': 'Qwen3.8 Flash Next · Strata',
    'glm-5.3-flash-maya': 'GLM 5.3 Flash',
    'deepseek-v4.1-flash-1017-maya': 'DeepSeek V4.1 Flash 1017 XS · Maya',
    'deepseek-v4.1-flash-1017-strata-xs': 'DeepSeek V4.1 Flash 1017 XS · Strata',
}


def model_entries():
    models = []
    ids = set()
    for backend, filename in [('llama', 'models.json'), ('sglang', 'sglang-profiles.json'),
                              ('vllm', 'vllm-profiles.json'), ('strata', 'strata-profiles.json'),
                              ('maya', 'maya-profiles.json')]:
        path = ROOT / filename
        if not path.exists():
            continue
        source = json.loads(path.read_text())
        rows = source if isinstance(source, list) else [dict(id=k, **v) for k, v in source.items()]
        for row in rows:
            if not row.get('enabled', backend != 'maya'):
                continue
            if row['id'] in ids:
                raise ValueError('Duplicate AMD model ID: ' + row['id'])
            ids.add(row['id'])
            model = {'id': row['id'], 'name': NAMES.get(row['id'], row['name']),
                     'contextWindow': row['context'], 'maxTokens': min(4096, row['context']),
                     'input': ['text'], 'reasoningEfforts': False}
            if backend in ('strata', 'maya'):
                model['compat'] = {'supportsStore': False, 'supportsReasoningEffort': False,
                                   'supportsStrictMode': False, 'thinkingFormat': 'chat-template',
                                   'chatTemplateKwargs': {'enable_thinking': False}}
            models.append(model)
    return models


def configure(default_provider=None, *, profile='web'):
    path = ROOT / 'data/settings.yaml'
    profile_path = ROOT / 'data/profiles' / profile / 'cordis.patch.yml'
    use_profile = profile_path.exists() and not path.exists()
    entries = None
    if use_profile:
        entries = yaml.safe_load(profile_path.read_text()) or []
        if not isinstance(entries, list):
            raise ValueError('The DSH profile patch must be a list')
        settings = {entry['id']: entry.get('config', {}) for entry in entries
                    if isinstance(entry, dict) and 'id' in entry}
        path = profile_path
    else:
        settings = (yaml.safe_load(path.read_text()) or {}) if path.exists() else {}
    models = model_entries()
    ids = {m['id'] for m in models}
    if not models:
        raise ValueError('No enabled AMD models; existing settings were not changed')
    if default_provider is not None and default_provider not in {*LOCAL, AMD_PROVIDER}:
        raise ValueError('Unknown local provider: ' + default_provider)
    providers = settings.setdefault('llm-pi-ai', {}).setdefault('providers', {})
    for key in LOCAL:
        providers.pop(key, None)
    providers[AMD_PROVIDER] = {
        'displayName': 'AMD server', 'api': 'openai-completions',
        'baseURL': f'http://127.0.0.1:{HUB_PORT}/v1', 'apiKeyEnv': 'LOCAL_LLAMA_API_KEY',
        'timeoutMs': 86400000, 'streamIdleTimeoutMs': 86400000,
        'compat': {'supportsDeveloperRole': False, 'maxTokensField': 'max_tokens'},
        'models': models,
    }
    selection = settings.get('agent-default-model', {})
    is_local = selection.get('provider') in {*LOCAL, AMD_PROVIDER}
    if default_provider is not None or not selection or is_local:
        chosen = (LOCAL.get(default_provider) if default_provider else selection.get('model'))
        chosen = REPLACEMENTS.get(chosen, chosen)
        if chosen not in ids:
            chosen = 'empero-qwen3.8-35b-a3b' if 'empero-qwen3.8-35b-a3b' in ids else models[0]['id']
        settings['agent-default-model'] = {'provider': AMD_PROVIDER, 'model': chosen}
    if use_profile:
        for entry_id in ('llm-pi-ai', 'agent-default-model'):
            entry = next((item for item in entries if isinstance(item, dict)
                          and item.get('id') == entry_id), None)
            if entry is None:
                entry = {'id': entry_id, 'name': '@deepseek-ai/dsh-' + entry_id}
                entries.append(entry)
            entry['config'] = settings[entry_id]
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(yaml.safe_dump(entries if use_profile else settings, sort_keys=False))
    os.replace(tmp, path)
