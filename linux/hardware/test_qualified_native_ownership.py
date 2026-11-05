"""Configured native ownership survives orphaning without matching unrelated Python."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dsh'))
spec=importlib.util.spec_from_file_location('native_ownership_under_test',ROOT/'dsh/backend_switch.py')
switch=importlib.util.module_from_spec(spec);sys.modules[spec.name]=switch;spec.loader.exec_module(switch)

class Ownership(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'dsh').mkdir()
        self.source=self.root/'source';self.binary=str(self.source/'build-hip/strata-dsv41')
        self.config=str(self.root/'dsh/coder.json')
        self.record={'status':'passed','family':'strata','source':str(self.source),
            'source_commit':'a'*40,'binary_relative':'build-hip/strata-dsv41','binary':self.binary}
        self.profile={'enabled':True,'config':'coder.json'}
        self.write()
    def write(self):
        for name,value in [('qualified-native-profiles.json',{'schema_version':1,'profiles':{'coder':self.record}}),
                ('strata-profiles.json',{'coder':self.profile}),('maya-profiles.json',{})]:
            (self.root/'dsh'/name).write_text(json.dumps(value))
    def proc(self,args,pid=10,parent=1):return switch.Process(pid,parent,'123',tuple(args),'','S')
    def accepts(self,args):return switch.is_inference(self.proc(args),self.root)
    def wrapper(self,config=None):return ['python3','-B',str(self.root/'dsh/qualified_native_backend.py'),'--config',config or self.config]
    def test_exact_binary_and_wrapper_owned(self):
        self.assertTrue(self.accepts([self.binary]));self.assertTrue(self.accepts(self.wrapper()))
    def test_orphan_and_descendant_owned_with_unrelated_training_preserved(self):
        a=self.proc([self.binary]);b=self.proc(['python3','helper.py'],11,10);c=self.proc(['python3','training.py'],12)
        self.assertEqual(set(switch.owned_processes({10:a,11:b,12:c},self.root)),{10,11})
    def test_mentioned_path_in_unrelated_script_is_not_owned(self):
        self.assertFalse(self.accepts(['python3','training.py',*self.wrapper()[2:]]))
    def test_unregistered_config_not_owned(self):self.assertFalse(self.accepts(self.wrapper('/unrelated/config.json')))
    def test_held_and_disabled_routes_not_owned(self):
        self.record['status']='held';self.write();self.assertFalse(self.accepts([self.binary]))
        self.record['status']='passed';self.profile['enabled']=False;self.write();self.assertFalse(self.accepts(self.wrapper()))
    def test_family_revision_and_binary_binding_fail_closed(self):
        for key,value in [('family','maya'),('source_commit','bad'),('source','relative'),('binary','/unrelated/worker')]:
            old=self.record[key];self.record[key]=value;self.write();self.assertFalse(self.accepts([self.binary]));self.record[key]=old
    def test_config_path_escape_is_not_owned(self):
        self.profile['config']='../other.json';self.write();self.assertFalse(self.accepts([self.binary]))
    def test_missing_or_malformed_registry_not_owned(self):
        p=self.root/'dsh/qualified-native-profiles.json';p.write_text('{');self.assertFalse(self.accepts([self.binary]))
        p.unlink();self.assertFalse(self.accepts(self.wrapper()))

if __name__=='__main__':unittest.main()
