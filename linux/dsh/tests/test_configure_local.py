"""Check AMD provider migration without changing unrelated DSH settings or holds."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
import yaml


class ConfigureLocalTests(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('configure_local', source / 'configure_local.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.module.ROOT = self.root
        for name in ('models.json', 'sglang-profiles.json', 'vllm-profiles.json',
                     'strata-profiles.json', 'maya-profiles.json'):
            shutil.copy2(source / name, self.root / name)
        self.home = self.root / 'data'
        self.home.mkdir()
        self.external = {'api': 'openai-completions', 'baseURL': 'http://example.invalid/v1',
                         'apiKeyEnv': 'EXTERNAL_SECRET', 'models': []}

    def refresh(self, selection, *, profile=None, default=None):
        settings = {'llm-pi-ai': {'providers': {'external-test': self.external,
                     **{key: {'models': []} for key in self.module.LOCAL}}},
                    'agent-default-model': selection, 'unrelated': {'preserve': True}}
        if profile:
            path = self.home / 'profiles' / profile / 'cordis.patch.yml'
            entries = [{'id': k, 'name': '@deepseek-ai/dsh-' + k, 'config': v}
                       for k, v in settings.items()]
            entries.append({'id': 'custom', 'name': 'custom-plugin', 'disabled': True})
            data = entries
        else:
            path = self.home / 'settings.yaml'
            data = settings
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(data))
        self.module.configure(default, profile=profile or 'web')
        first = path.read_text()
        self.module.configure(default, profile=profile or 'web')
        self.assertEqual(path.read_text(), first)
        result = yaml.safe_load(first)
        if profile:
            self.assertEqual(result[-1], {'id': 'custom', 'name': 'custom-plugin', 'disabled': True})
            result = {e['id']: e.get('config') for e in result}
            self.assertFalse((self.home / 'settings.yaml').exists())
        self.assertEqual(result['unrelated'], {'preserve': True})
        self.assertEqual(result['llm-pi-ai']['providers']['external-test'], self.external)
        self.assertEqual(set(result['llm-pi-ai']['providers']), {'amd-server', 'external-test'})
        return result

    def test_existing_selection_migrates_to_single_server(self):
        result = self.refresh({'provider': 'llama-local', 'model': 'empero-qwen3.8-35b-a3b'})
        self.assertEqual(result['agent-default-model'],
                         {'provider': 'amd-server', 'model': 'empero-qwen3.8-35b-a3b'})
        provider = result['llm-pi-ai']['providers']['amd-server']
        self.assertEqual(provider['displayName'], 'AMD server')
        self.assertEqual(provider['baseURL'], 'http://127.0.0.1:30100/v1')
        self.assertEqual(len(provider['models']), 8)
        self.assertEqual(len({m['id'] for m in provider['models']}), 8)

    def test_external_selection_is_preserved(self):
        selection = {'provider': 'external-test', 'model': 'keep'}
        self.assertEqual(self.refresh(selection)['agent-default-model'], selection)

    def test_model_compat_and_context_are_preserved(self):
        result = self.refresh({'provider': 'maya-local', 'model': 'glm-5.3-flash-maya'})
        models = {m['id']: m for m in result['llm-pi-ai']['providers']['amd-server']['models']}
        self.assertEqual(models['glm-5.3-flash-maya']['compat']['chatTemplateKwargs'],
                         {'enable_thinking': False})
        self.assertNotIn('compat', models['qwen3.8-27b-vllm'])
        self.assertEqual(models['qwen3.8-27b-vllm']['contextWindow'], 163840)
        self.assertEqual(models['sage-a1.5']['contextWindow'], 65536)
        self.assertEqual(result['agent-default-model']['provider'], 'amd-server')

    def test_paused_models_stay_hidden_and_cannot_be_default(self):
        result = self.refresh({'provider': 'strata-local', 'model': 'qwen3.8-flash-next-iq3_xxs'})
        ids = {m['id'] for m in result['llm-pi-ai']['providers']['amd-server']['models']}
        self.assertNotIn('ornith-1.5-122b', ids)
        self.assertNotIn('deepseek-v4.1-flash-1017-maya', ids)
        self.assertEqual(result['agent-default-model']['model'], 'empero-qwen3.8-35b-a3b')

    def test_retired_ids_migrate_without_reenabling_models(self):
        result = self.refresh({'provider': 'llama-local', 'model': 'nemotron-3.5-bolt'})
        self.assertEqual(result['agent-default-model'],
                         {'provider': 'amd-server', 'model': 'nemotron-3.5-bolt-vllm'})

    def test_web_profile_migration_preserves_other_plugins(self):
        self.refresh({'provider': 'llama-local', 'model': 'sage-a1.5'}, profile='web')

    def test_headless_profile_uses_same_provider(self):
        result = self.refresh({}, profile='headless', default='sglang-local')
        self.assertEqual(result['agent-default-model'],
                         {'provider': 'amd-server', 'model': 'qwen3.8-27b-sglang-dflash2'})


if __name__ == '__main__':
    unittest.main()
