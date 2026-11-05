"""Packaged Qwen workers have exact ownership; unrelated Python stays untouched."""
from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dsh'))
import backend_switch as switch


class Ownership(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'dsh').mkdir()
        self.binary = str(self.root / 'package/engine/strata')
        self.config = str(self.root / 'dsh/new.json')
        self.record = {'status': 'passed', 'family': 'strata-qwen', 'binary': self.binary,
                       'binary_sha256': 'a' * 64, 'control': str(self.root / 'package/control')}
        self.profile = {'enabled': True, 'config': 'new.json'}
        self.cfg = {'model_name': 'new', 'exe': self.binary, 'cwd': self.record['control']}
        self.write()

    def write(self):
        for filename, value in [('qualified-strata-qwen-profiles.json',
                                  {'schema_version': 1, 'profiles': {'new': self.record}}),
                                 ('strata-profiles.json', {'new': self.profile}), ('new.json', self.cfg)]:
            (self.root / 'dsh' / filename).write_text(json.dumps(value))

    def proc(self, args, pid=10, parent=1):
        return switch.Process(pid, parent, '123', tuple(args), '', 'S')

    def accepts(self, args):
        return switch.is_inference(self.proc(args), self.root)

    def wrapper(self, config=None):
        return ['python3', '-B', str(self.root / 'dsh/strata_qwen_backend.py'),
                '--config', config or self.config]

    def test_exact_binary_and_wrapper_are_recognized(self):
        self.assertTrue(self.accepts([self.binary]))
        self.assertTrue(self.accepts(self.wrapper()))

    def test_orphan_descendants_are_owned_but_training_is_preserved(self):
        processes = {10: self.proc([self.binary]), 11: self.proc(['python3', 'helper.py'], 11, 10),
                     12: self.proc(['python3', 'training.py'], 12)}
        self.assertEqual(set(switch.owned_processes(processes, self.root)), {10, 11})

    def test_mentioned_wrapper_is_not_an_entrypoint(self):
        self.assertFalse(self.accepts(['python3', 'training.py', *self.wrapper()[2:]]))

    def test_unregistered_config_is_not_owned(self):
        self.assertFalse(self.accepts(self.wrapper('/unrelated/config.json')))

    def test_held_or_disabled_profiles_are_not_owned(self):
        self.record['status'] = 'requires-local-validation'
        self.write()
        self.assertFalse(self.accepts([self.binary]))
        self.record['status'] = 'passed'
        self.profile['enabled'] = False
        self.write()
        self.assertFalse(self.accepts(self.wrapper()))

    def test_config_escape_is_not_owned(self):
        self.profile['config'] = '../outside.json'
        self.write()
        self.assertFalse(self.accepts([self.binary]))

    def test_other_package_config_cannot_claim_binary(self):
        self.cfg['exe'] = '/unrelated/strata'
        self.write()
        self.assertFalse(self.accepts([self.binary]))

    def test_malformed_registry_is_not_owned(self):
        (self.root / 'dsh/qualified-strata-qwen-profiles.json').write_text('{')
        self.assertFalse(self.accepts(self.wrapper()))


if __name__ == '__main__':
    unittest.main()
