"""Additional Qwen packages cannot inherit the existing GSQ qualification."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import Mock, patch

from qualified_native_runtime import config_fingerprint, digest
from strata_runtime import required_weight_assets
from strata_qwen_qualification import require_package
import strata_runtime
import strata_qwen_qualification


class PackageAdmission(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'dsh').mkdir()
        self.control = self.root / 'control'
        server = self.control / 'serve/server.py'
        server.parent.mkdir(parents=True)
        server.write_text('# verified package\n')
        binary = self.root / 'engine/strata'
        binary.parent.mkdir()
        binary.write_bytes(b'verified engine')
        self.cfg = {'model_name': 'new-qwen', 'exe': str(binary), 'cwd': str(self.control),
                    'args': ['--pack', str(self.root / 'pack'), '--native', str(self.root / 'a.gguf'),
                             '--ple-gguf', str(self.root / 'b.gguf'), '--mtp', str(self.root / 'mtp'),
                             '--mmap-experts'], 'tokenizer': str(self.root / 'tokenizer')}
        paths = required_weight_assets(self.cfg)
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'verified weights')
        identities = {}
        for path in paths:
            st = path.stat()
            identities[str(path)] = {'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns,
                                     'inode': st.st_ino, 'device': st.st_dev, 'sha256': digest(path)}
        self.record = {'status': 'passed', 'family': 'strata-qwen', 'config_sha256': config_fingerprint(self.cfg),
                       'binary': str(binary), 'binary_sha256': digest(binary),
                       'control': str(self.control), 'control_sha256': {'serve/server.py': digest(server)},
                       'gguf_files': [str(self.root / 'a.gguf'), str(self.root / 'b.gguf')],
                       'backing_identity': identities}
        self.registry = self.root / 'dsh/qualified-strata-qwen-profiles.json'
        self.save()

    def save(self):
        self.registry.write_text(json.dumps({'schema_version': 1, 'profiles': {'new-qwen': self.record}}))

    def admit(self):
        return require_package(self.cfg, root=self.root)

    def test_exact_qualified_inputs_are_admitted(self):
        self.assertEqual(self.admit()['status'], 'passed')

    def test_missing_registry_is_refused(self):
        self.registry.unlink()
        with self.assertRaisesRegex(RuntimeError, 'registry'):
            self.admit()

    def test_candidates_and_public_exports_are_refused(self):
        for state in ['candidate', 'requires-local-validation', 'failed']:
            with self.subTest(status=state):
                self.record['status'] = state
                self.save()
                with self.assertRaisesRegex(RuntimeError, 'qualification'):
                    self.admit()

    def test_unknown_model_cannot_inherit_another_seal(self):
        self.cfg['model_name'] = 'other'
        with self.assertRaisesRegex(RuntimeError, 'qualification'):
            self.admit()

    def test_changed_runtime_settings_are_refused(self):
        self.cfg['parallel'] = 8
        with self.assertRaisesRegex(RuntimeError, 'profile changed'):
            self.admit()

    def test_changed_engine_is_refused(self):
        Path(self.cfg['exe']).write_bytes(b'another engine')
        with self.assertRaisesRegex(RuntimeError, 'package identity'):
            self.admit()

    def test_changed_control_source_is_refused(self):
        (self.control / 'serve/server.py').write_text('# modified\n')
        with self.assertRaisesRegex(RuntimeError, 'source changed'):
            self.admit()

    def test_new_control_source_is_refused(self):
        (self.control / 'extra.py').write_text('# new code\n')
        with self.assertRaisesRegex(RuntimeError, 'source set'):
            self.admit()

    def test_source_path_traversal_is_refused(self):
        self.record['control_sha256']['../outside.py'] = '0' * 64
        self.save()
        with self.assertRaises(RuntimeError):
            self.admit()

    def test_missing_backing_seal_is_refused(self):
        self.record['backing_identity'].pop(next(iter(self.record['backing_identity'])))
        self.save()
        with self.assertRaisesRegex(RuntimeError, 'incomplete'):
            self.admit()

    def test_modified_weights_are_refused(self):
        (self.root / 'a.gguf').write_bytes(b'modified weights')
        with self.assertRaisesRegex(RuntimeError, 'backing identity'):
            self.admit()

    def test_unsealed_gguf_shard_is_refused(self):
        self.record['gguf_files'].append(str(self.root / 'unsealed.gguf'))
        self.save()
        with self.assertRaisesRegex(RuntimeError, 'incomplete'):
            self.admit()

    def test_inode_only_change_requires_content_proof_and_reuses_that_exact_proof(self):
        path = str(self.root / 'a.gguf')
        self.record['backing_identity'][path]['inode'] += 1
        self.save()
        with patch.object(strata_qwen_qualification, 'backing_digest', return_value=digest(path)) as check:
            self.admit()
            self.admit()
            check.assert_called_once_with(Path(path))

    def test_inode_change_with_wrong_content_is_refused(self):
        path = str(self.root / 'a.gguf')
        self.record['backing_identity'][path]['inode'] += 1
        self.save()
        with patch.object(strata_qwen_qualification, 'backing_digest', return_value='0' * 64):
            with self.assertRaisesRegex(RuntimeError, 'content changed'):
                self.admit()


class SelectionAdmission(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'dsh').mkdir()
        self.baseline = 'qwen3.8-flash-next-iq3_xxs'
        self.cfg = {'model_name': self.baseline, 'exe': str(self.root / 'strata/build-hip/strata'),
                    'args': []}
        (self.root / 'dsh/old.json').write_text(json.dumps(self.cfg))
        (self.root / 'dsh/new.json').write_text(json.dumps(dict(self.cfg, model_name='new-qwen')))
        # Put the unqualified addition first: it must not become the default.
        profiles = {'new-qwen': {'enabled': True, 'config': 'new.json'},
                    self.baseline: {'enabled': True, 'config': 'old.json'}}
        (self.root / 'dsh/strata-profiles.json').write_text(json.dumps(profiles))
        self.addCleanup(patch.stopall)
        patch.object(strata_runtime, 'ROOT', self.root).start()
        patch.object(strata_qwen_qualification, 'ROOT', self.root).start()
        patch.dict(strata_runtime.os.environ, {}, clear=True).start()

    def test_unqualified_addition_is_refused_before_resource_or_handover_work(self):
        with patch.object(strata_runtime, 'check_config') as resources:
            with self.assertRaisesRegex(RuntimeError, 'qualification registry'):
                strata_runtime.require_strata(model='new-qwen', before_handover=True)
            resources.assert_not_called()

    def test_existing_gsq_remains_default_despite_unqualified_sibling(self):
        with patch.object(strata_runtime, 'check_config'), \
             patch.object(strata_runtime, 'host_memory', return_value=(64 * 2**30, 60 * 2**30)), \
             patch.object(strata_runtime, 'amd_devices'), \
             patch.object(strata_runtime.shutil, 'which', return_value='systemd-run'), \
             patch.object(strata_runtime.subprocess, 'run', return_value=Mock(returncode=0)), \
             patch.object(strata_runtime.os, 'access', return_value=True), \
             patch.object(strata_runtime, 'require_weight_assets'):
            self.assertEqual(strata_runtime.require_strata(), self.cfg)


if __name__ == '__main__':
    unittest.main()
