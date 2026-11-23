"""The publish step accepts a sealed strata-inkling package next to the strata-qwen ones."""
import json, sys, tempfile, unittest
from pathlib import Path
from unittest import mock
sys.path[:0] = [str(Path(__file__).resolve().parent / 'daily-update')]
import publish


class InklingExport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name); d = self.root / 'dsh'; d.mkdir()
        for name in ('llama-runtime.json', 'vllm-profiles.json', 'maya-profiles.json'):
            (d / name).write_text('{}')
        (d / 'qualified-native-profiles.json').write_text(json.dumps({'schema_version': 1, 'profiles': {}}))
        (d / 'strata-profiles.json').write_text(json.dumps({'ink': {'config': 'ink.json', 'enabled': True, 'family': 'inkling2', 'qualified_qwen_package': True}}))
        self.record = {'status': 'passed', 'family': 'strata-inkling', 'binary': '/x/build/strata-inkling', 'control': '/x/terminal', 'binary_sha256': 'a' * 64}
        (d / 'qualified-strata-qwen-profiles.json').write_text(json.dumps({'schema_version': 1, 'profiles': {'ink': self.record}}))

    def tearDown(self):
        self.tmp.cleanup()

    def test_inkling_package_config_is_a_runtime_path(self):
        with mock.patch.object(publish, 'ROOT', self.root):
            self.assertIn('dsh/ink.json', publish.runtime_paths())

    def test_unknown_family_is_still_refused(self):
        self.record['family'] = 'other'
        (self.root / 'dsh/qualified-strata-qwen-profiles.json').write_text(json.dumps({'schema_version': 1, 'profiles': {'ink': self.record}}))
        with mock.patch.object(publish, 'ROOT', self.root), self.assertRaises(RuntimeError):
            publish.runtime_paths()


if __name__ == '__main__':
    unittest.main()
