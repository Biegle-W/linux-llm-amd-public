"""Regression checks for local model configuration across DSH's settings migration."""
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
        for name in ('models.json', 'sglang-profiles.json', 'vllm-profiles.json', 'strata-profiles.json'):
            shutil.copy2(source / name, self.root / name)
        self.home = self.root / 'data'
        self.home.mkdir()
        self.provider = {'api': 'openai-completions', 'baseURL': 'http://127.0.0.1:9999/v1', 'models': []}
        self.selection = {'provider': 'external-test', 'model': 'preserved'}
        self.settings = {'llm-pi-ai': {'providers': {'external-test': self.provider}},
                         'agent-default-model': self.selection}

    def test_retired_deepseek_selection_moves_to_xs_in_same_provider(self):
        source = Path(__file__).resolve().parents[1]
        shutil.copy2(source / 'maya-profiles.json', self.root / 'maya-profiles.json')
        path = self.home / 'settings.yaml'
        for provider, retired, retained in [('maya-local', 'deepseek-v4.1-flash-1017-maya-s', 'deepseek-v4.1-flash-1017-maya'),
                                            ('strata-local', 'deepseek-v4.1-flash-1017-strata-s', 'deepseek-v4.1-flash-1017-strata-xs')]:
            with self.subTest(provider=provider):
                settings = dict(self.settings, **{'agent-default-model': {'provider': provider, 'model': retired}})
                path.write_text(yaml.safe_dump(settings)); self.module.configure()
                actual = yaml.safe_load(path.read_text())
                self.assertEqual(actual['agent-default-model'], {'provider': provider, 'model': retained})
                ids = {m['id'] for m in actual['llm-pi-ai']['providers'][provider]['models']}
                self.assertIn(retained, ids); self.assertNotIn(retired, ids)
                self.assertEqual(actual['llm-pi-ai']['providers']['external-test'], self.provider)

    def test_legacy_preserves_selection_and_unrelated_settings(self):
        path = self.home / 'settings.yaml'
        self.settings['ui-onboarding'] = {'welcomeNoticeVersion': 7}
        path.write_text(yaml.safe_dump(self.settings))
        self.module.configure()
        actual = yaml.safe_load(path.read_text())
        self.assertEqual(actual['agent-default-model'], self.selection)
        self.assertEqual(actual['llm-pi-ai']['providers']['external-test'], self.provider)
        self.assertEqual(actual['ui-onboarding'], self.settings['ui-onboarding'])
        self.assertIn('llama-local', actual['llm-pi-ai']['providers'])

    def test_profile_refresh_preserves_overrides_and_is_repeatable(self):
        path = self.home / 'profiles/web/cordis.patch.yml'
        path.parent.mkdir(parents=True)
        entries = [{'id': key, 'name': '@deepseek-ai/dsh-' + key, 'config': value}
                   for key, value in self.settings.items()]
        unrelated = {'id': 'unrelated', 'name': 'custom-plugin', 'disabled': True,
                     'config': {'preserve': True}}
        entries.append(unrelated)
        path.write_text(yaml.safe_dump(entries))
        self.module.configure()
        first = path.read_text()
        self.module.configure()
        self.assertEqual(path.read_text(), first)
        entries = yaml.safe_load(first)
        actual = {entry['id']: entry['config'] for entry in entries}
        self.assertEqual(entries[-1], unrelated)
        self.assertEqual(actual['agent-default-model'], self.selection)
        self.assertEqual(actual['llm-pi-ai']['providers']['external-test'], self.provider)
        self.assertFalse((self.home / 'settings.yaml').exists())
        self.module.configure('sglang-local')
        actual = {entry['id']: entry['config'] for entry in yaml.safe_load(path.read_text())}
        self.assertEqual(actual['agent-default-model'],
                         {'provider': 'sglang-local', 'model': 'qwen3.8-27b-sglang-dflash2'})


if __name__ == '__main__':
    unittest.main()
