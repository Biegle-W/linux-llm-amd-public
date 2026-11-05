"""A public reference or changed source must not become a normal graphics runtime."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys,tempfile,unittest
spec=importlib.util.spec_from_file_location('graphics_selection',Path(__file__).with_name('runtime_selection.py'));runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)

class Selection(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);(self.root/'graphics').mkdir();self.config=self.root/'graphics/runtime-versions.json';self.config.write_text('{}')
 def write(self,record):self.config.write_text(json.dumps({'runtime_selection':record}))
 def candidate(self):
  source=self.root/'candidate';source.mkdir();(source/'main.py').write_text('# candidate\n');(source/'.venv/bin').mkdir(parents=True);(source/'.venv/bin/python').symlink_to(sys.executable);(source/'python-overlay').mkdir()
  for args in [['init'],['config','user.name','Selection test'],['config','user.email','selection@example.invalid'],['add','main.py'],['commit','-m','Candidate']]:subprocess.run(['git','-C',str(source),*args],check=True,capture_output=True)
  revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
  return {'status':'passed-six-normal-workflows','source_path':str(source),'source_commit':revision,'dependency_overlay':str(source/'python-overlay'),'qualified_device_order':'1,0','files':{'main.py':hashlib.sha256((source/'main.py').read_bytes()).hexdigest()}}
 def test_absent_selection_retains_existing_runtime(self):self.assertEqual(runtime.selection(self.root),{'runtime':str(self.root/'runtime/comfyui'),'overlay':'','devices':'0,1'})
 def test_public_reference_cannot_launch_as_locally_qualified(self):
  self.write({'status':'requires-local-validation'})
  with self.assertRaisesRegex(RuntimeError,'independent qualification'):runtime.selection(self.root)
 def test_qualified_source_selects_and_changed_source_is_rejected(self):
  record=self.candidate();self.write(record);self.assertEqual(runtime.selection(self.root)['runtime'],record['source_path'])
  (Path(record['source_path'])/'main.py').write_text('# changed\n')
  with self.assertRaises(subprocess.CalledProcessError):runtime.selection(self.root)
 def test_outside_overlay_and_changed_device_order_are_rejected(self):
  record=self.candidate();record['dependency_overlay']=str(self.root/'elsewhere');self.write(record)
  with self.assertRaisesRegex(RuntimeError,'source/overlay'):runtime.selection(self.root)
  record['dependency_overlay']=str(Path(record['source_path'])/'python-overlay');record['qualified_device_order']='0,1';self.write(record)
  with self.assertRaisesRegex(RuntimeError,'device order'):runtime.selection(self.root)

if __name__=='__main__':unittest.main()
