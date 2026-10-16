"""Register all local backends without removing unrelated providers or settings."""
import json, os
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parent
LOCAL = {'llama-local': 'qwen3.8-27b-q4', 'sglang-local': 'qwen3.8-27b-sglang',
         'vllm-local': 'qwen3.8-27b-vllm', 'strata-local': 'qwen3.8-flash-next-iq3_xxs',
         'hyperqwen-local': 'qwen3.8-27b-hyperqwen-dflash2'}

def configure(default_provider=None):
    path = ROOT / 'data/settings.yaml'
    path.parent.mkdir(parents=True, exist_ok=True)
    settings = (yaml.safe_load(path.read_text()) or {}) if path.exists() else {}
    providers = settings.setdefault('llm-pi-ai', {}).setdefault('providers', {})
    catalogs = {
        'llama-local': ('Local llama.cpp', 8080, json.loads((ROOT / 'models.json').read_text())),
        'sglang-local': ('Local SGLang', 30000, [dict(id=k, **v) for k,v in json.loads((ROOT/'sglang-profiles.json').read_text()).items()]),
        'vllm-local': ('Local vLLM', 30010, [dict(id=k, **v) for k,v in json.loads((ROOT/'vllm-profiles.json').read_text()).items()]),
        'strata-local': ('Local Strata', 30020, [dict(id=k, **v) for k,v in json.loads((ROOT/'strata-profiles.json').read_text()).items()]),
        'hyperqwen-local': ('Local HyperQwen', 18020, [dict(id=k, **v) for k,v in json.loads((ROOT/'hyperqwen-profiles.json').read_text()).items()]),
    }
    for key, (name, port, models) in catalogs.items():
        models = [m for m in models if m.get('enabled', True)]
        if not models:
            providers.pop(key, None)
            continue
        compat = {'supportsDeveloperRole': False, 'maxTokensField': 'max_tokens'}
        if key in ('strata-local', 'hyperqwen-local'):
            compat.update(supportsStore=False, supportsReasoningEffort=False, supportsStrictMode=False,
                          thinkingFormat='chat-template', chatTemplateKwargs={'enable_thinking': False})
        providers[key] = {'displayName': name, 'api': 'openai-completions',
                          'baseURL': f'http://127.0.0.1:{port}/v1', 'apiKeyEnv': 'LOCAL_LLAMA_API_KEY',
                          'timeoutMs': 86400000, 'streamIdleTimeoutMs': 86400000, 'compat': compat,
                          'models': [{'id': m['id'], 'name': m['name'], 'contextWindow': m['context'],
                                      'maxTokens': 4096, 'input': ['text'], 'reasoningEfforts': False} for m in models]}
    selection = settings.get('agent-default-model', {})
    if selection.get('provider') == 'llama-local' and selection.get('model') in {'nemotron-3.5-lightning', 'gpt-oss-20b', 'gpt-oss-120b'}:
        settings['agent-default-model'] = selection = {'provider':'llama-local', 'model':'nemotron-3.5-bolt'}
    provider = selection.get('provider')
    invalid_local = provider in LOCAL and selection.get('model') not in {m['id'] for m in providers.get(provider, {}).get('models', [])}
    if default_provider or not selection or invalid_local:
        key = default_provider or (provider if invalid_local and provider in providers else 'llama-local')
        settings['agent-default-model'] = {'provider': key, 'model': LOCAL[key]}
    tmp = path.with_suffix('.yaml.tmp')
    tmp.write_text(yaml.safe_dump(settings, sort_keys=False)); os.replace(tmp, path)

if __name__ == '__main__':
    configure()
