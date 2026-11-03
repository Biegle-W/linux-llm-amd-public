"""CPU checks for native GGUF backing without a duplicate expert file."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dsh'))
from strata_runtime import required_weight_assets,require_weight_assets
class Assets(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);p=Path(self.tmp.name)
  self.cfg={'args':['--pack',str(p/'pack'),'--native',str(p/'model.gguf'),'--ple-gguf',str(p/'ple.gguf'),'--mtp',str(p/'mtp'),'--mmap-experts'],'tokenizer':str(p/'tokenizer')}
  for f in required_weight_assets(self.cfg):f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b'fixture')
 def test_native_does_not_require_copied_experts(self):
  self.assertFalse(any(p.name=='experts.bin' and p.parent.name=='pack' for p in required_weight_assets(self.cfg)));require_weight_assets(self.cfg)
 def test_non_mmap_keeps_copied_expert_requirement(self):
  self.cfg['args'].remove('--mmap-experts')
  with self.assertRaises(RuntimeError):require_weight_assets(self.cfg)
  f=Path(self.cfg['args'][1])/'experts.bin';f.write_bytes(b'fixture');require_weight_assets(self.cfg)
 def test_missing_each_dependency_is_refused(self):
  for f in required_weight_assets(self.cfg):
   with self.subTest(file=f.name):
    value=f.read_bytes();f.unlink()
    with self.assertRaises(RuntimeError):require_weight_assets(self.cfg)
    f.write_bytes(value)
 def test_empty_each_dependency_is_refused(self):
  for f in required_weight_assets(self.cfg):
   with self.subTest(file=f.name):
    value=f.read_bytes();f.write_bytes(b'')
    with self.assertRaises(RuntimeError):require_weight_assets(self.cfg)
    f.write_bytes(value)
if __name__=='__main__':unittest.main()
