"""CPU regressions for held sources, full unpinned coverage, rollback and public pins."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
UPDATER=Path(os.environ.get('LLAMA_TEST_UPDATER',ROOT/'hardware/daily-update/daily_update.py'))
PUBLISHER=Path(os.environ.get('LLAMA_TEST_PUBLISHER',ROOT/'hardware/daily-update/publish.py'))
OLD='a'*40
NEW='c'*40


class HeldSources(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/'dsh').mkdir();(self.root/'llama.cpp').mkdir()
        self.hold=self.root/'old-ornith';(self.hold/'build-hip/bin').mkdir(parents=True)
        (self.hold/'build-hip/bin/llama-server').touch()
        self.pin=self.root/'dsh/llama-runtime.json'
        self.cfg={'models':['empero','super','ornith','flint'],'source_commit':OLD,
                  'source_overrides':{'empero':{'path':'/qualified-vram','source_commit':'b'*40},
                    'ornith':{'path':str(self.hold),'source_commit':OLD,'manual_runtime_pin':OLD,
                              'runtime_pin_reason':'Retain normal profile on the stable source.'}}}
        self.save()
        tree=ast.parse(UPDATER.read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Llama')
        self.ns=dict(Engine=object,ROOT=self.root,Path=Path,json=json,re=re,Step=RuntimeError,
                     shutil=shutil,os=os,sh=Mock(),out=Mock(return_value=OLD),BUILD_JOBS='2')
        exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),str(UPDATER),'exec'),self.ns)
        self.engine=self.ns['Llama']()

    def save(self):self.pin.write_text(json.dumps(self.cfg))

    def test_only_explicit_valid_hold_is_excluded_and_ordinary_override_is_still_tested(self):
        self.assertEqual(self.engine.models(),['empero','super','flint'])

    def test_owner_paused_unpinned_model_is_excluded_from_qualification(self):
        self.cfg['paused_models']={'super':'Wait for owner RAM notice'};self.save()
        self.assertEqual(self.engine.models(),['empero','flint'])
        self.assertIn('ornith',self.engine.held_sources())

    def test_install_preserves_hold_clears_other_overrides_and_rollback_restores_exact_pin(self):
        original=self.pin.read_bytes();stage=self.root/'stage';stage.mkdir()
        self.engine.install(stage,NEW,self.root/'log')
        cfg=json.loads(self.pin.read_text())
        self.assertEqual(cfg['source_commit'],NEW)
        self.assertEqual(cfg['source_overrides'],{'ornith':self.cfg['source_overrides']['ornith']})
        self.assertEqual(self.engine.models(),['empero','super','flint'])
        self.engine.rollback(stage,self.root/'log')
        self.assertEqual(self.pin.read_bytes(),original)

    def test_invalid_hold_metadata_fails_before_any_production_mutation(self):
        for field,value in [('manual_runtime_pin',True),('manual_runtime_pin','b'*40),
                            ('path','relative'),('source_commit','b'*40)]:
            with self.subTest(field=field,value=value):
                saved=dict(self.cfg['source_overrides']['ornith'])
                self.cfg['source_overrides']['ornith'][field]=value;self.save()
                stage=self.root/'stage';stage.mkdir(exist_ok=True)
                with self.assertRaises(RuntimeError):self.engine.install(stage,NEW,self.root/'log')
                self.assertFalse((stage/'rollback').exists());self.ns['sh'].assert_not_called()
                self.cfg['source_overrides']['ornith']=saved;self.save()

    def test_missing_held_binary_and_changed_source_fail_closed(self):
        binary=self.hold/'build-hip/bin/llama-server';binary.unlink()
        with self.assertRaises(RuntimeError):self.engine.models()
        binary.touch();self.ns['out'].return_value='d'*40
        with self.assertRaises(RuntimeError):self.engine.models()

    def test_unknown_and_all_held_models_cannot_supply_global_coverage(self):
        self.cfg['source_overrides']['unknown']=dict(self.cfg['source_overrides']['ornith']);self.save()
        with self.assertRaises(RuntimeError):self.engine.models()
        del self.cfg['source_overrides']['unknown']
        for model in self.cfg['models']:self.cfg['source_overrides'][model]=dict(self.cfg['source_overrides']['ornith'])
        self.save()
        with self.assertRaisesRegex(RuntimeError,'No unpinned'):self.engine.models()


class PublicPins(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'private';(self.root/'dsh').mkdir(parents=True)
        self.public=Path(self.tmp.name)/'public';self.public.mkdir()
        spec=importlib.util.spec_from_file_location('tested_llama_publisher',PUBLISHER)
        self.publish=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.publish)
        self.publish.ROOT=self.root;self.publish.PUBLIC=self.public
        self.publish.PRIVATE=re.compile(r'/home/|/run/media/|192\.168\.')
        self.cfg={'models':['ornith'],'source_commit':NEW,'source_overrides':{'ornith':{
            'path':str(self.root/'llm-tools/old-ornith'),'source_commit':OLD,'manual_runtime_pin':OLD}}}
        self.source=self.root/'dsh/llama-runtime.json';self.source.write_text(json.dumps(self.cfg))

    def test_export_sanitizes_held_source_without_modifying_private_pin(self):
        original=self.source.read_bytes()
        self.assertEqual(self.publish.public_llama_pin(),['linux/dsh/llama-runtime.json'])
        result=json.loads((self.public/'linux/dsh/llama-runtime.json').read_text())
        self.assertEqual(result['source_overrides']['ornith']['path'],'/opt/local-llm/llm-tools/old-ornith')
        self.assertEqual(result['source_overrides']['ornith']['manual_runtime_pin'],OLD)
        self.assertIn('verify',result['reference_note']);self.assertEqual(self.source.read_bytes(),original)

    def test_export_refuses_unrecognized_private_path(self):
        self.cfg['source_overrides']['ornith']['path']='/home/private-outside-tree/old'
        self.source.write_text(json.dumps(self.cfg))
        with self.assertRaises(RuntimeError):self.publish.public_llama_pin()
        self.assertFalse((self.public/'linux/dsh/llama-runtime.json').exists())

    def test_handoff_versions_report_global_source_and_explicit_hold(self):
        (self.root/'dsh/vllm-profiles.json').write_text('{}')
        llama=Mock();llama.current.return_value=NEW
        llama.name='llama.cpp';llama.held_sources.return_value=self.cfg['source_overrides']
        with patch.dict(sys.modules,{'daily_update':types.SimpleNamespace(ENGINES={'llama':llama})}):
            rows=self.publish.versions()
        self.assertIn(f'| llama.cpp | `{NEW[:12]}` |',rows)
        self.assertIn(f'| llama.cpp ornith (manual source pin) | `{OLD[:12]}` |',rows)


if __name__=='__main__':unittest.main()
