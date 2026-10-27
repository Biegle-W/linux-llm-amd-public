"""Exact configured source ownership without broadening process termination."""
import json,os,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dsh'))
import backend_switch as switch

class Ownership(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        (self.root/'dsh').mkdir();self.config=self.root/'dsh/llama-runtime.json'
        self.source=self.root/'llm-tools/llama-vram-tested'
        self.write(self.source)
    def tearDown(self):self.tmp.cleanup()
    def write(self,source,commit='a'*40):
        self.config.write_text(json.dumps({'source_overrides':{'sage':{'path':str(source),'source_commit':commit}}}))
    def process(self,args):return switch.Process(123,1,'1',tuple(args),'','S')
    def binary(self,source=None):return str((source or self.source)/'build-hip/bin/llama-server')
    def test_orphaned_configured_binary_is_owned(self):
        p=self.process([self.binary()]);self.assertTrue(switch.is_inference(p,self.root))
        self.assertEqual(set(switch.owned_processes({p.pid:p},self.root)),{123})
    def test_path_mentioned_by_client_is_not_owned(self):
        self.assertFalse(switch.is_inference(self.process(['python3','client.py',self.binary()]),self.root))
    def test_other_versioned_source_is_not_owned(self):
        self.assertFalse(switch.is_inference(self.process([self.binary(self.root/'llm-tools/llama-vram-other')]),self.root))
    def test_config_change_refreshes_exact_allowlist(self):
        self.assertTrue(switch.is_inference(self.process([self.binary()]),self.root))
        before=self.config.stat().st_mtime_ns;other=self.root/'llm-tools/llama-vram-other'
        self.write(other);os.utime(self.config,ns=(before+1000000,before+1000000))
        self.assertFalse(switch.is_inference(self.process([self.binary()]),self.root))
        self.assertTrue(switch.is_inference(self.process([self.binary(other)]),self.root))
    def test_invalid_pin_does_not_expand_allowlist(self):
        self.write(self.source,'not-a-pin')
        self.assertFalse(switch.is_inference(self.process([self.binary()]),self.root))
    def test_missing_configuration_keeps_legacy_ownership(self):
        self.config.unlink()
        self.assertTrue(switch.is_inference(self.process([str(self.root/'llama.cpp/build-hip/bin/llama-server')]),self.root))
        self.assertFalse(switch.is_inference(self.process(['/usr/bin/blender']),self.root))

if __name__=='__main__':unittest.main()
