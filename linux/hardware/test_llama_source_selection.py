#!/usr/bin/env python3
"""CPU regression checks for mixed validated llama source revisions."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
# Tests may also run against an isolated prepared copy.
DSH = Path(os.environ.get('LLAMA_TEST_DSH', ROOT / 'dsh'))
sys.path.insert(0, str(ROOT / 'dsh'))
spec = importlib.util.spec_from_file_location('tested_llama_runtime', DSH / 'llama_runtime.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

class Selection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'dsh'; self.root.mkdir()
        self.commit = 'a' * 40
        self.source = Path(self.tmp.name) / 'qualified'
        self.settings = {'source_overrides': {'sage': {'path': str(self.source), 'source_commit': self.commit}}}
        (self.root / 'llama-runtime.json').write_text(json.dumps(self.settings))
        self.patches = [patch.object(runtime, 'ROOT', self.root), patch.dict(os.environ, {}, clear=True)]
        for p in self.patches: p.start()
    def tearDown(self):
        for p in reversed(self.patches): p.stop()
        self.tmp.cleanup()
    def test_cpu_profile_retains_default_source(self):
        self.assertEqual(runtime.runtime_source('ornith'), (self.root.parent / 'llama.cpp', None))
    def test_qualified_model_uses_its_pinned_source(self):
        self.assertEqual(runtime.runtime_source('sage'), (self.source, self.commit))
    def test_isolated_validation_override_wins(self):
        os.environ['LLAMA_CPP_DIR'] = str(self.root.parent / 'test')
        self.assertEqual(runtime.runtime_source('sage'), (self.root.parent / 'test', None))
    def test_changed_pin_changes_runtime_identity(self):
        with patch.object(runtime, 'verify_source_pin'):
            before = runtime.runtime_identity('hip-amd', 'sage')
            self.settings['source_overrides']['sage']['source_commit'] = 'b' * 40
            (self.root / 'llama-runtime.json').write_text(json.dumps(self.settings))
            self.assertNotEqual(before, runtime.runtime_identity('hip-amd', 'sage'))
    def test_identity_checks_pin_before_reusing_worker(self):
        with patch.object(runtime.subprocess, 'check_output', return_value='b' * 40):
            with self.assertRaisesRegex(RuntimeError, 'revision changed'):
                runtime.runtime_identity('hip-amd', 'sage')
    def test_moved_revision_fails_before_worker_change(self):
        with patch.object(runtime.subprocess, 'check_output', return_value='b' * 40):
            with self.assertRaisesRegex(RuntimeError, 'revision changed'):
                runtime.verify_source_pin(self.source, self.commit)
    def test_exact_revision_accepted(self):
        with patch.object(runtime.subprocess, 'check_output', return_value=self.commit + '\n'):
            runtime.verify_source_pin(self.source, self.commit)
    def test_invalid_override_rejected(self):
        self.settings['source_overrides']['sage']['path'] = 'relative'
        (self.root / 'llama-runtime.json').write_text(json.dumps(self.settings))
        with self.assertRaisesRegex(RuntimeError, 'Invalid qualified'):
            runtime.runtime_source('sage')

class Router(unittest.TestCase):
    def namespace(self, identity):
        tree = ast.parse((DSH / 'llama-router.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'activate_native')
        fn.decorator_list = []
        native = Mock(); native.poll.return_value = None
        guard = Mock(); guard.spawn.return_value = native
        limits = {'memory.high': 4, 'memory.max': 5, 'memory.swap.max': 0}
        ns = dict(native=native, active_runtime=('hip-amd','/old',None), active_mode='hip-amd',
                  active_model='old', active_limits=limits, memory_watch=None, native_port=8081,
                  swap_guard=guard, require_model_capacity=Mock(), worker_limits_for_model=lambda _:limits,
                  runtime_identity=lambda *_:identity, launch_spec=Mock(return_value=(Path('/new/bin/llama-server'),Path('/preset'),{}, {'sage'})),
                  stop_process=Mock(), require_amd_headroom=Mock(), ready=Mock(), watch_worker=Mock(),
                  print=Mock())
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(DSH/'llama-router.py'),'exec'),ns)
        return ns
    def test_same_backend_and_limits_still_switch_changed_source(self):
        ns=self.namespace(('hip-amd','/new','a'*40))
        ns['activate_native']('hip-amd',model='sage')
        ns['stop_process'].assert_called_once()
        ns['launch_spec'].assert_called_once_with('hip-amd',model='sage')
        ns['swap_guard'].spawn.assert_called_once()
        self.assertEqual(ns['active_runtime'],('hip-amd','/new','a'*40))
    def test_same_source_and_limits_reuse_owned_worker(self):
        ns=self.namespace(('hip-amd','/old',None))
        ns['activate_native']('hip-amd',model='sage')
        ns['stop_process'].assert_not_called();ns['swap_guard'].spawn.assert_not_called()

class Updater(unittest.TestCase):
    def test_full_catalog_install_clears_overrides_and_rollback_restores_them(self):
        updater = Path(os.environ.get('LLAMA_TEST_UPDATER', ROOT / 'hardware/daily-update/daily_update.py'))
        tree = ast.parse(updater.read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Llama')
        functions = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in ('install','rollback')]
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root / 'source'; source.mkdir()
            pin = root / 'runtime.json'
            original = json.dumps({'source_commit':'a'*40,'source_overrides':{'sage':{'path':'/qualified','source_commit':'b'*40}}})
            pin.write_text(original)
            stage = root / 'stage'; stage.mkdir()
            ns = dict(ROOT=root,shutil=shutil,json=json,os=os,sh=Mock(),out=Mock(return_value='a'*40),BUILD_JOBS='2')
            exec(compile(ast.fix_missing_locations(ast.Module(body=functions,type_ignores=[])),str(updater),'exec'),ns)
            engine = types.SimpleNamespace(src=source,pin=pin)
            ns['install'](engine,stage,'c'*40,root/'log')
            self.assertEqual(json.loads(pin.read_text()),{'source_commit':'c'*40})
            ns['rollback'](engine,stage,root/'log')
            self.assertEqual(pin.read_text(),original)

if __name__ == '__main__': unittest.main()
