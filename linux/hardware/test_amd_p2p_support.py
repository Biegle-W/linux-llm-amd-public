import importlib.util,json,shlex,struct,subprocess,tempfile,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('support',Path(__file__).with_name('amd_p2p_support.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def report():
 return {'selected_bridges':[{'selector':x} for x in ['0000:00:01.0/00.0/04.0','0000:00:01.0/00.0/04.0/00.0/00.0','0000:00:01.0/00.0/08.0','0000:00:01.0/00.0/08.0/00.0/00.0','0000:00:01.0/00.0/04.0/00.0/00.0/00.0/00.0','0000:00:01.0/00.0/08.0/00.0/00.0/00.0/00.0']],'request_completion_redirect_present':True}

class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.config=self.root/'config';self.state=self.root/'state';self.grub=self.root/'grub';self.grub.write_text('original grub\n');self.r=report()
 def good(self,cmd,check):
  if cmd[0]=='update-grub':self.grub.write_text("linux /vmlinuz root=UUID=test '"+m.parameter(self.r)+"'\n")
 def stage(self,run=None,**kw):return m.stage(self.r,self.config,self.state,self.grub,self.root,run=run or self.good,**kw)
 def test_exact_mask_and_scoped_paths(self):
  p=m.parameter(self.r);self.assertEqual(p.count('xxx00xx@'),6);self.assertNotIn('iommu',p);self.assertNotIn('pcie_acs_override',p)
  mask=sum(1<<i for i,x in enumerate(m.FLAGS[::-1]) if x!='x');self.assertEqual(mask,0x0c)
 def test_grub_shell_and_grub_parser_quoting(self):
  f=self.root/'cfg';param=m.parameter(self.r);f.write_text(m.dropin(param));v=subprocess.check_output(['sh','-c','GRUB_CMDLINE_LINUX="quiet splash"; . "$1"; printf "%s" "$GRUB_CMDLINE_LINUX"','sh',str(f)],text=True)
  self.assertEqual(shlex.split(v),['quiet','splash',param])
 def test_invalid_or_broad_selectors_rejected(self):
  for value in ['pci:1000:c010','*','0000:00:01.0/00.0;reboot','0000:00:01.0/00.0\n']:
   r=report();r['selected_bridges'][0]['selector']=value
   with self.assertRaises(RuntimeError):m.parameter(r)
 def test_missing_or_duplicate_selection_rejected(self):
  r=report();r['selected_bridges'].pop()
  with self.assertRaises(RuntimeError):m.parameter(r)
  r=report();r['selected_bridges'][0]=r['selected_bridges'][1]
  with self.assertRaises(RuntimeError):m.parameter(r)
 def test_acs_parse(self):
  data=bytearray(4096);struct.pack_into('<I',data,0x100,0x0001000d);struct.pack_into('<HH',data,0x104,0x7f,0x1d);self.assertEqual(m.acs(data),{'offset':256,'capability':127,'control':29})
 def test_acs_absent(self):self.assertIsNone(m.acs(bytes(4096)))
 def test_truncated_config_refused(self):
  with self.assertRaises(RuntimeError):m.acs(bytes(256))
 def test_cyclic_extended_capabilities_refused(self):
  b=bytearray(4096);struct.pack_into('<I',b,0x100,(0x100<<20)|1)
  with self.assertRaises(RuntimeError):m.acs(b)
 def test_standard_pcie_type(self):
  b=bytearray(4096);b[0x34]=0x40;b[0x40]=0x10;struct.pack_into('<H',b,0x42,6<<4);self.assertEqual(m.pcie_type(b),6)
 def test_stage_preserves_original_and_metadata(self):
  d=self.stage();self.assertTrue(d['reboot_required']);self.assertEqual((Path(d['backup'])/'grub.cfg').read_text(),'original grub\n');self.assertEqual(self.config.stat().st_mode&0o777,0o644);self.assertEqual(self.state.stat().st_mode&0o777,0o600)
 def test_generation_failure_restores_boot_files(self):
  def fail(cmd,check):self.grub.write_text('broken');raise RuntimeError('generation failed')
  with self.assertRaises(RuntimeError):self.stage(fail)
  self.assertFalse(self.config.exists());self.assertFalse(self.state.exists());self.assertEqual(self.grub.read_text(),'original grub\n')
 def test_missing_or_split_kernel_parameter_refused(self):
  def bad(cmd,check):
   if cmd[0]=='update-grub':self.grub.write_text('linux /vmlinuz quiet\n')
  with self.assertRaises(RuntimeError):self.stage(bad)
  self.assertFalse(self.config.exists());self.assertEqual(self.grub.read_text(),'original grub\n')
 def test_admission_errors_preserved_without_staging(self):
  self.r['admission_errors']=['Additional redirecting bridge 0000:0a:00.0 ACS=0x1d']
  with self.assertRaisesRegex(RuntimeError,'0000:0a:00.0'):self.stage()
  self.assertFalse(self.config.exists())
 def test_existing_config_refused(self):
  self.config.write_text('unmanaged')
  with self.assertRaises(RuntimeError):self.stage()
  self.assertEqual(self.config.read_text(),'unmanaged')
 def test_existing_acs_boot_policy_refused(self):
  with self.assertRaises(RuntimeError):self.stage(existing_args='pci=disable_acs_redir=0000:01:00.0')
  self.assertFalse(self.config.exists())
 def test_clear_controls_dont_stage_unnecessary_change(self):
  self.r['request_completion_redirect_present']=False
  with self.assertRaises(RuntimeError):self.stage()
  self.assertFalse(self.config.exists())
 def test_symlink_refused(self):
  other=self.root/'other';other.write_text('keep');self.config.symlink_to(other)
  with self.assertRaises(RuntimeError):self.stage()
  self.assertEqual(other.read_text(),'keep')
 def test_rollback_failure_restores_managed_state(self):
  self.stage();before=self.config.read_bytes();oldgrub=self.grub.read_bytes()
  def fail(*a,**kw):raise RuntimeError('failed')
  with self.assertRaises(RuntimeError):m.rollback(self.config,self.state,self.grub,run=fail)
  self.assertEqual(self.config.read_bytes(),before);self.assertEqual(self.grub.read_bytes(),oldgrub);self.assertTrue(self.state.exists())
 def test_modified_policy_rollback_refused(self):
  self.stage();self.config.write_text('modified')
  with self.assertRaises(RuntimeError):m.rollback(self.config,self.state,self.grub,run=self.good)
  self.assertTrue(self.state.exists())
class TopologyTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.pci=self.base/'pci';self.pci.mkdir();self.driver=self.base/'amdgpu';self.driver.mkdir();self.nodes={}
  root=self.device(self.base,'0000:00:01.0','0x8086',4)
  common=self.device(root,'0000:01:00.0','0x1000',5)
  for ids in [('0000:02:04.0','0000:07:00.0','0000:08:00.0','0000:09:00.0','0000:0a:00.0','0000:0b:00.0'),('0000:02:08.0','0000:0f:00.0','0000:10:00.0','0000:11:00.0','0000:12:00.0','0000:13:00.0')]:
   parent=common
   for i,bdf in enumerate(ids):
    parent=self.device(parent,bdf,'0x1000' if i<3 else '0x1002',6 if i in (0,2,4) else 5 if i!=5 else 0,acs_control=0x1d if i in (0,2,4) else None,gpu=i==5)
 def device(self,parent,bdf,vendor,ptype,acs_control=None,gpu=False):
  p=parent/bdf;p.mkdir();self.nodes[bdf]=p;(self.pci/bdf).symlink_to(p,target_is_directory=True)
  for k,v in {'vendor':vendor,'device':'0x744c' if gpu else '0xc010' if vendor=='0x1000' else ('0x1479' if ptype==6 else '0x1478'),'class':'0x030000' if gpu else '0x060400'}.items():(p/k).write_text(v)
  b=bytearray(4096);b[0x34]=0x40;b[0x40]=0x10;struct.pack_into('<H',b,0x42,ptype<<4)
  if acs_control is not None:struct.pack_into('<IHH',b,0x100,0x0001000d,0x7f,acs_control)
  (p/'config').write_bytes(b)
  if gpu:(p/'driver').symlink_to(self.driver);(p/'mem_info_vram_total').write_text(str(24*m.GIB))
  return p
 def test_audit_selects_only_four_relevant_broadcom_downstream(self):
  r=m.audit(self.pci);self.assertEqual([x['pci'] for x in r['selected_bridges']],['0000:02:04.0','0000:08:00.0','0000:02:08.0','0000:10:00.0','0000:0a:00.0','0000:12:00.0']);self.assertTrue(r['request_completion_redirect_present']);self.assertEqual(r['common_switch'],'0000:01:00.0');self.assertNotIn('0000:00:01.0',[x['pci'] for x in r['bridges']])
 def test_full_selector_ignores_changing_secondary_bus_numbers(self):
  r=m.audit(self.pci);self.assertEqual(r['selected_bridges'][1]['selector'],'0000:00:01.0/00.0/04.0/00.0/00.0')
 def test_unexpected_redirecting_upstream_bridge_is_refused(self):
  p=self.nodes['0000:09:00.0']/'config';b=bytearray(p.read_bytes());struct.pack_into('<IHH',b,0x100,0x0001000d,0x7f,0x1d);p.write_bytes(b)
  r=m.audit(self.pci);self.assertTrue(any('0000:09:00.0' in e for e in r['admission_errors']))
 def test_unexpected_control_refuses_installation(self):
  p=self.nodes['0000:08:00.0']/'config';b=bytearray(p.read_bytes());struct.pack_into('<H',b,0x106,0x7f);p.write_bytes(b)
  r=m.audit(self.pci);self.assertTrue(any('Unexpected ACS' in e for e in r['admission_errors']))

class InternalIdentityTests(unittest.TestCase):
 setUp=TopologyTests.setUp
 device=TopologyTests.device
 def test_missing_expected_amd_parent_refused(self):
  (self.nodes['0000:0a:00.0']/'device').write_text('0x9999')
  with self.assertRaisesRegex(RuntimeError,'AMD 1479'):m.audit(self.pci)
 def test_internal_controls_preserve_other_bits(self):
  r=m.audit(self.pci);self.assertEqual(len(r['selected_bridges']),6);self.assertFalse(r['admission_errors'])
  for row in r['selected_bridges']:self.assertEqual(row['acs']['control'] & ~0x0c,0x11)

if __name__=='__main__':unittest.main()
