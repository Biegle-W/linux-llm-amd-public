"""Peer opt-in is per-model and changes live-worker reuse identity."""
import importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'dsh'))
spec=importlib.util.spec_from_file_location('qualified_peer_runtime',ROOT/'dsh/llama_runtime.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)

class PeerSelection(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'dsh';self.root.mkdir()
        self.source=self.root.parent/'source';self.binary=self.source/'build-hip/bin/llama-server'
        self.binary.parent.mkdir(parents=True);self.binary.touch();(self.root/'models-hip.ini').touch()
        self.cfg={'models':['qualified','other'],'p2p_models':['qualified']}
        self.write();p=patch.object(runtime,'ROOT',self.root);p.start();self.addCleanup(p.stop)
    def write(self):(self.root/'llama-runtime.json').write_text(json.dumps(self.cfg))
    def launch(self,model):
        inventory='ROCm0: AMD Radeon RX 7900 XTX\nROCm1: AMD Radeon RX 7900 XTX\n'
        def run(cmd,**kw):
            if cmd[0]=='bash':return types.SimpleNamespace(stdout=b'GGML_CUDA_P2P=0\0LD_LIBRARY_PATH=/sdk\0KEEP_ME=yes\0')
            self.assertEqual('GGML_CUDA_P2P' in kw['env'],model=='qualified')
            return types.SimpleNamespace(stdout=inventory,stderr='')
        with patch.object(runtime,'runtime_source',return_value=(self.source,None)),patch.object(runtime,'verify_source_pin'), \
             patch.object(runtime,'validate_profiles'),patch.object(runtime,'require_worker_scope'), \
             patch.object(runtime,'amd_devices',return_value=[1,2]),patch.object(runtime.subprocess,'run',side_effect=run):
            return runtime.launch_spec('hip-amd',model)[2]
    def test_only_qualified_model_enables_presence_based_peer_flag(self):
        env=self.launch('qualified');self.assertEqual(env['GGML_CUDA_P2P'],'1');self.assertEqual(env['KEEP_ME'],'yes')
    def test_unlisted_model_strips_inherited_zero_which_would_enable_peer(self):
        self.assertNotIn('GGML_CUDA_P2P',self.launch('other'))
    def test_transport_change_invalidates_cached_worker_identity(self):
        with patch.object(runtime,'runtime_source',return_value=(self.source,None)),patch.object(runtime,'verify_source_pin'):
            before=runtime.runtime_identity('hip-amd','qualified');self.cfg['p2p_models']=[];self.write()
            self.assertNotEqual(before,runtime.runtime_identity('hip-amd','qualified'))

if __name__=='__main__':unittest.main()
