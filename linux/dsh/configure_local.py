"""Register all local backends without removing unrelated providers or settings."""
import json, os
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parent
HUB_PORT = 30100
LOCAL = {'llama-local': 'empero-qwen3.8-35b-a3b', 'sglang-local': 'qwen3.8-27b-sglang-dflash2',
         'vllm-local': 'qwen3.8-27b-vllm', 'strata-local': 'qwen3.8-flash-next-iq3_xxs',
         'maya-local': 'glm-5.3-flash-maya',
         'hyperqwen-local': 'qwen3.8-27b-hyperqwen-dflash2'}

def configure(default_provider=None):
    path = ROOT / 'data/settings.yaml'
    profile_path = ROOT / 'data/profiles/web/cordis.patch.yml'
    use_profile = profile_path.exists() and not path.exists()
    entries = None
    if use_profile:
        entries = yaml.safe_load(profile_path.read_text()) or []
        if not isinstance(entries, list):
            raise ValueError('The DSH web profile patch must be a list')
        settings = {entry['id']: entry.get('config', {}) for entry in entries
                    if isinstance(entry, dict) and 'id' in entry}
        path = profile_path
    else:
        settings = (yaml.safe_load(path.read_text()) or {}) if path.exists() else {}
    path.parent.mkdir(parents=True, exist_ok=True)
    providers = settings.setdefault('llm-pi-ai', {}).setdefault('providers', {})
    providers.pop('hyperqwen-local', None)  # Remove the retired local provider.
    catalogs = {
        'llama-local': ('Local llama.cpp', 8080, json.loads((ROOT / 'models.json').read_text())),
        'sglang-local': ('Local SGLang', 30000, [dict(id=k, **v) for k,v in json.loads((ROOT/'sglang-profiles.json').read_text()).items()]),
        'vllm-local': ('Local vLLM', 30010, [dict(id=k, **v) for k,v in json.loads((ROOT/'vllm-profiles.json').read_text()).items()]),
        'strata-local': ('Local Strata', 30020, [dict(id=k, **v) for k,v in json.loads((ROOT/'strata-profiles.json').read_text()).items()]),
    }
    maya_catalog = ROOT / 'maya-profiles.json'
    if maya_catalog.exists():
        catalogs['maya-local'] = ('Local Maya', 30030, [dict(id=k, **v) for k,v in json.loads(maya_catalog.read_text()).items()])
    for key, (name, port, models) in catalogs.items():
        models = [m for m in models if m.get('enabled', key != 'maya-local')]
        if not models:
            providers.pop(key, None)
            continue
        compat = {'supportsDeveloperRole': False, 'maxTokensField': 'max_tokens'}
        if key in ('strata-local', 'maya-local'):
            compat.update(supportsStore=False, supportsReasoningEffort=False, supportsStrictMode=False,
                          thinkingFormat='chat-template', chatTemplateKwargs={'enable_thinking': False})
        providers[key] = {'displayName': name, 'api': 'openai-completions',
                          # The loopback model hub starts or switches this backend on demand.
                          'baseURL': f'http://127.0.0.1:{HUB_PORT}/v1', 'apiKeyEnv': 'LOCAL_LLAMA_API_KEY',
                          'timeoutMs': 86400000, 'streamIdleTimeoutMs': 86400000, 'compat': compat,
                          'models': [{'id': m['id'], 'name': m['name'], 'contextWindow': m['context'],
                                      'maxTokens': 4096, 'input': ['text'], 'reasoningEfforts': False} for m in models]}
    selection = settings.get('agent-default-model', {})
    # Retired llama.cpp IDs move to their faster vLLM replacements (October 21).
    replacements = {'nemotron-3.5-lightning': 'nemotron-3.5-bolt-vllm', 'gpt-oss-20b': 'nemotron-3.5-bolt-vllm',
                    'gpt-oss-120b': 'nemotron-3.5-bolt-vllm', 'nemotron-3.5-bolt': 'nemotron-3.5-bolt-vllm',
                    'qwen3.8-27b-q4': 'qwen3.8-27b-vllm'}
    if selection.get('provider') == 'llama-local' and selection.get('model') in replacements:
        settings['agent-default-model'] = selection = {'provider':'vllm-local', 'model':replacements[selection['model']]}
    # Qwen3.6-35B-A3B was retired October 23 at the user's request; Empero is its llama.cpp successor.
    if selection.get('provider') == 'llama-local' and selection.get('model') == 'qwen3.6-35b-a3b':
        settings['agent-default-model'] = selection = {'provider': 'llama-local', 'model': 'empero-qwen3.8-35b-a3b'}
    provider = selection.get('provider')
    invalid_local = provider in LOCAL and selection.get('model') not in {m['id'] for m in providers.get(provider, {}).get('models', [])}
    if default_provider or not selection or invalid_local:
        key = default_provider or (provider if invalid_local and provider in providers else 'llama-local')
        settings['agent-default-model'] = {'provider': key, 'model': LOCAL[key]}
    if use_profile:
        for entry_id in ('llm-pi-ai', 'agent-default-model'):
            entry = next((item for item in entries if isinstance(item, dict)
                          and item.get('id') == entry_id), None)
            if entry is None:
                entry = {'id': entry_id, 'name': '@deepseek-ai/dsh-' + entry_id}
                entries.append(entry)
            entry['config'] = settings[entry_id]
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(yaml.safe_dump(entries if use_profile else settings, sort_keys=False))
    os.replace(tmp, path)

if __name__ == '__main__':
    configure()
