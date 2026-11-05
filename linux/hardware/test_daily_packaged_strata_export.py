"""Packaged Qwen exports remain portable references and cannot carry local seals."""
import json
from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent/'daily-update'))
import publish

class Export(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'private';self.public=Path(self.temp.name)/'public'
        (self.root/'dsh').mkdir(parents=True);self.model='new-qwen'
        self.record={'status':'passed','family':'strata-qwen','binary':'/home/operator/package/engine/strata',
                     'binary_sha256':'a'*64,'control':'/home/operator/package/control',
                     'backing_identity':{'/home/operator/package/engine/libhip.so':
                         {'bytes':10,'sha256':'b'*64,'inode':123,'device':1,'mtime_ns':2}}}
        self.put('qualified-native-profiles.json',{'schema_version':1,'profiles':{}})
        self.put('qualified-strata-qwen-profiles.json',{'schema_version':1,'profiles':{self.model:self.record}})
        self.put('strata-profiles.json',{self.model:{'enabled':True,'qualified_qwen_package':True,'config':'new.json'}})
        self.put('maya-profiles.json',{})
        self.put('llama-runtime.json',{'path':str(self.root/'llama'),'source_commit':'c'*40})
        self.put('new.json',{'model_name':self.model,'exe':self.record['binary'],'cwd':self.record['control'],
                 'local_validation':{'status':'passed'},'runtime_validation':{'status':'passed'}})
        for key,value in [('ROOT',self.root),('PUBLIC',self.public)]:
            p=patch.object(publish,key,value);p.start();self.addCleanup(p.stop)
    def put(self,name,data):(self.root/'dsh'/name).write_text(json.dumps(data))
    def test_registry_and_config_are_included_and_sanitized(self):
        paths=publish.public_runtime_references()
        self.assertIn('linux/dsh/qualified-strata-qwen-profiles.json',paths)
        self.assertIn('linux/dsh/new.json',paths)
        record=json.loads((self.public/'linux/dsh/qualified-strata-qwen-profiles.json').read_text())['profiles'][self.model]
        self.assertEqual(record['status'],'requires-local-validation')
        self.assertTrue(record['binary'].startswith('/opt/local-llm/qualified-packages/'))
        self.assertEqual(set(next(iter(record['backing_identity'].values()))),{'bytes','sha256'})
        cfg=json.loads((self.public/'linux/dsh/new.json').read_text())
        self.assertEqual(cfg['runtime_validation']['status'],'requires-local-validation')
        self.assertEqual(cfg['local_validation']['status'],'requires-local-validation')
        self.assertNotIn('/home/',json.dumps(record)+json.dumps(cfg))
    def test_unqualified_record_is_refused_before_export(self):
        self.record['status']='candidate'
        self.put('qualified-strata-qwen-profiles.json',{'schema_version':1,'profiles':{self.model:self.record}})
        with self.assertRaises(RuntimeError):publish.public_runtime_references()
        self.assertFalse((self.public/'linux/dsh/new.json').exists())
    def test_catalog_path_traversal_is_refused(self):
        self.put('strata-profiles.json',{self.model:{'qualified_qwen_package':True,'config':'../new.json'}})
        with self.assertRaisesRegex(RuntimeError,'Unreviewed'):publish.runtime_paths()

if __name__=='__main__':unittest.main()
