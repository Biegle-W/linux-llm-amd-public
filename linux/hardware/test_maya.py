"""Maya admission and process-ownership safety boundaries; no GPU required."""
import copy
import contextlib
import io
import runpy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dsh'))
import backend_switch as switch
import maya_runtime as runtime

class MayaTests(unittest.TestCase):
    def test_maya_shutdown_ownership_is_scoped_to_configured_inference(self):
        root=Path('/test-local-llm');base=root/'maya/upstream'
        def proc(args,cwd=''):
            return switch.Process(10,1,'1',tuple(args),cwd,'S')
        yes=[[str(base/'build-hip/maya')],[str(base/'build-hip/maya-ds4')],
             ['python3',str(root/'dsh/maya-router.py')],
             [str(base/'.venv/bin/python'),'serve/server.py','--engine','strata']]
        for args in yes:self.assertTrue(switch.is_inference(proc(args,str(base)),root),args)
        no=[['python3',str(base/'serve/frontend.py')],
            ['python3',str(base/'serve/server.py'),'--engine','mock'],
            [str(base/'.venv/bin/python'),'training.py'],
            ['python3','other.py',str(base/'serve/server.py'),'--engine','strata'],
            ['python3',str(root/'network/gateway.py')],
            ['/usr/autodesk/maya2026/bin/maya'],
            ['python3','/opt/ComfyUI/main.py'],
            ['python3','serve/server.py','--engine','strata']]
        for args in no:self.assertFalse(switch.is_inference(proc(args,'/unrelated'),root),args)

    def test_help_and_invalid_selection_never_handover_a_running_backend(self):
        launcher=Path(__file__).resolve().parents[1]/'dsh/launch-backend.py'
        for extra,code in [(['--help'],0),(['--model','not-a-configured-model'],2)]:
            with patch.object(sys,'argv',[str(launcher),'maya',*extra]),patch.object(switch,'startup_handover') as handover,patch.object(runtime,'require_maya') as require,contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:runpy.run_path(str(launcher),run_name='__main__')
                self.assertEqual(raised.exception.code,code);handover.assert_not_called();require.assert_not_called()

    def test_admission_rejects_changed_binary_config_single_gpu_and_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'maya/upstream';exe=src/'build-hip/maya';exe.parent.mkdir(parents=True);exe.write_bytes(b'validated binary')
            (root/'maya/runtime.json').write_text(json.dumps({'source_commit':'reviewed'}))
            pack=root/'models/Maya/pack';pack.mkdir(parents=True)
            devices=[]
            for n in range(2):
                d=root/str(n);d.mkdir();(d/'mem_info_vram_total').write_text(str(24*runtime.GIB));(d/'mem_info_vram_used').write_text(str(runtime.GIB));devices.append(d)
            cfg={'exe':str(exe),'backend':'hip','gpu':[0,1],'parallel':1,'split_skip_if_fits':False,'args':['--glm-pack',str(pack),'--max-context','32768','--vram-reserve-mib','8192','--vram-reserve-later-mib','8192'],'env':{'MAYA_GLM_RAM_GB':'36'}}
            cfg['local_validation']={'status':'passed','binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'config_sha256':runtime.config_fingerprint(cfg)}
            with patch.object(runtime,'ROOT',root),patch.object(runtime,'STREAM_MODELS',root/'models'),patch.object(runtime.subprocess,'check_output',return_value='reviewed\n'),patch.object(runtime.subprocess,'run',return_value=__import__('subprocess').CompletedProcess([],0)),patch.object(runtime,'host_memory',return_value=(64*runtime.GIB,55*runtime.GIB)),patch.object(runtime,'amd_devices',return_value=devices),patch.object(runtime,'require_worker_scope'):
                runtime.check_config(cfg)
                bad=copy.deepcopy(cfg);bad['gpu']=[0]
                with self.assertRaisesRegex(RuntimeError,'both configured'):runtime.check_config(bad)
                bad=copy.deepcopy(cfg);bad['args'][3]='65536'
                with self.assertRaisesRegex(RuntimeError,'not passed'):runtime.check_config(bad)
                exe.write_bytes(b'untested replacement')
                with self.assertRaisesRegex(RuntimeError,'not passed'):runtime.check_config(cfg)
                exe.write_bytes(b'validated binary')
                ds=exe.with_name('maya-ds4');ds.write_bytes(b'validated binary')
                bad=copy.deepcopy(cfg);bad['exe']=str(ds);bad['args'][0]='--pack';bad['args'][4]='--reserve-mib';bad['args'][5]='8192'
                (pack/'tensors.txt').write_text('t experts.w2.weight Q4_K 0 0 0 0 0\n')
                bad['local_validation']['config_sha256']=runtime.config_fingerprint(bad)
                with self.assertRaisesRegex(RuntimeError,'parity remains unresolved'):runtime.check_config(bad)
                bad['args']=bad['args'][:6]
                (pack/'tensors.txt').write_text('t experts.w2.weight IQ2_S 0 0 0 0 0\n')
                (pack/'ds4.txt').write_text('model_dir /linux/model\n')
                (pack/'engram.bin').write_bytes(b'hash-table-metadata')
                bad['local_validation']['config_sha256']=runtime.config_fingerprint(bad)
                bad['local_validation']['pack_metadata_sha256']=runtime.pack_metadata_fingerprint(pack)
                runtime.check_config(bad)
                (pack/'ds4.txt').write_text('model_dir WINDOWS_MODEL_PATH\n')
                with self.assertRaisesRegex(RuntimeError,'pack metadata changed'):runtime.check_config(bad)
                bad=copy.deepcopy(cfg);bad['env']['MAYA_GLM_MISS_SKIP_W']='0.1'
                bad['local_validation']['config_sha256']=runtime.config_fingerprint(bad)
                with self.assertRaisesRegex(RuntimeError,'expert skipping'):runtime.check_config(bad)
                with patch.object(runtime,'host_memory',return_value=(64*runtime.GIB,35*runtime.GIB)):
                    with self.assertRaisesRegex(RuntimeError,'available RAM'):runtime.check_config(cfg)
                with patch.object(runtime.subprocess,'check_output',return_value='different\n'):
                    with self.assertRaisesRegex(RuntimeError,'source changed'):runtime.check_config(cfg)

    def test_dsh_registration_preserves_default_and_unrelated_settings(self):
        import yaml
        import configure_local as frontend
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir()
            (root/'models.json').write_text(json.dumps([{'id':'base','name':'Base','context':4096}]))
            for kind in ('sglang','vllm'):(root/(kind+'-profiles.json')).write_text('{}')
            ident='qwen3.8-flash-next-iq3_xxs'
            (root/'strata-profiles.json').write_text(json.dumps({ident:{'name':'Strata','context':262144}}))
            (root/'maya-profiles.json').write_text(json.dumps({'disabled':{'name':'Candidate','context':8192,'enabled':False},'implicit':{'name':'Candidate','context':8192},'validated':{'name':'Maya','context':32768,'enabled':True}}))
            settings={'agent-default-model':{'provider':'strata-local','model':ident},'theme':'dark','llm-pi-ai':{'providers':{'remote':{'displayName':'Keep this provider'}}}}
            (root/'data/settings.yaml').write_text(yaml.safe_dump(settings))
            with patch.object(frontend,'ROOT',root):frontend.configure()
            actual=yaml.safe_load((root/'data/settings.yaml').read_text())
            self.assertEqual(actual['agent-default-model'],settings['agent-default-model'])
            self.assertEqual(actual['theme'],'dark')
            self.assertEqual(actual['llm-pi-ai']['providers']['remote'],settings['llm-pi-ai']['providers']['remote'])
            maya=actual['llm-pi-ai']['providers']['maya-local']
            self.assertEqual([(m['id'],m['contextWindow']) for m in maya['models']],[('validated',32768)])
            self.assertFalse(maya['compat']['chatTemplateKwargs']['enable_thinking'])

    def test_disabled_model_is_not_advertised_by_gateway(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('gateway',Path(__file__).resolve().parents[1]/'network/gateway.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'dsh').mkdir();p=root/'dsh/maya-profiles.json'
            p.write_text(json.dumps({'untested':{'name':'Candidate','context':8192,'enabled':False},'implicit':{'name':'Missing validation flag','context':8192},'passed':{'name':'Validated','context':32768,'enabled':True}}))
            with patch.object(g,'ROOT',root):
                self.assertNotIn('untested',g.catalog());self.assertNotIn('implicit',g.catalog());self.assertEqual(g.catalog()['passed']['backend'],'maya')

if __name__=='__main__':unittest.main()
