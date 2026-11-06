"""Hardware-free fail-closed checks for independently qualified native routes."""
from pathlib import Path
import copy,importlib.util,json,tempfile,types,unittest
from unittest.mock import Mock,patch
import sys

class QualificationAdmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hardware=Mock()
        stubs={}
        for name in ['resource_policy','amd_device','llama_runtime','moe_memory','shared_storage']:
            stubs[name]=types.ModuleType(name)
        stubs['resource_policy'].active=lambda:True
        stubs['amd_device'].amd_devices=lambda:[]
        stubs['llama_runtime'].require_worker_scope=cls.hardware
        stubs['moe_memory'].host_memory=lambda:(64*2**30,56*2**30)
        stubs['shared_storage'].STREAM_MODELS=Path('/unused')
        stubs['shared_storage'].ensure_streaming_models=lambda:None
        spec=importlib.util.spec_from_file_location('qualification_under_test',Path(__file__).with_name('qualified_native_runtime.py'))
        cls.module=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,stubs):spec.loader.exec_module(cls.module)
        cls.backing_function=staticmethod(cls.module.backing_digest)

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);m=self.module
        self.source=self.root/'source';self.binary=self.source/'build-hip/maya-ds4';self.binary.parent.mkdir(parents=True);self.binary.write_bytes(b'known tested engine');self.binary.chmod(0o755)
        self.pack=self.root/'models/Maya/Coder/pack';self.pack.mkdir(parents=True);(self.pack/'tokenizer').mkdir();(self.pack/'ds4.txt').write_text('known pack metadata')
        self.cards=[]
        for name in ['one','two']:
            card=self.root/name;card.mkdir();(card/'mem_info_vram_total').write_text(str(24*2**30));(card/'mem_info_vram_used').write_text('0');self.cards.append(card)
        self.cfg={'backend':'hip','gpu':[0,1],'parallel':1,'model_name':'qualified-coder','exe':str(self.binary),'cwd':str(self.source),'args':['--max-context','32768','--reserve-mib','8192','--pack',str(self.pack),'--tp','2'],'env':{'STRATA_DS4_PROMPT_SKIP':'0'},'tokenizer':str(self.pack/'tokenizer'),'startup_free_vram_gib':0.125,'worker_swap_max_bytes':None}
        self.record={'status':'passed','family':'maya','source':str(self.source),'source_commit':'a'*40,'binary':str(self.binary),'binary_relative':'build-hip/maya-ds4','binary_sha256':m.digest(self.binary),'pack':str(self.pack),'pack_metadata_sha256':{'ds4.txt':m.digest(self.pack/'ds4.txt')},'tokenizer':str(self.pack/'tokenizer')}
        self.seal()
        self.patches=[patch.object(m,'ROOT',self.root),patch.object(m,'STREAM_MODELS',self.root/'models'),patch.object(m,'amd_devices',lambda:self.cards),patch.object(m,'host_memory',lambda:(64*2**30,56*2**30)),patch.object(m.subprocess,'check_output',return_value='a'*40),patch.object(m.subprocess,'run',return_value=types.SimpleNamespace(returncode=0))]
        for p in self.patches:p.start();self.addCleanup(p.stop)
        p=patch.object(m,'backing_digest',side_effect=m.digest);p.start();self.addCleanup(p.stop)

    def seal(self):self.record['config_sha256']=self.module.config_fingerprint(self.cfg)
    def require(self,**kwargs):return self.module.require_profile(self.cfg,self.record,**kwargs)
    def test_accepts_exact_profile(self):self.assertIs(self.require(),self.cfg);self.hardware.assert_called()
    def stable_filesystem_backing(self):
        path=self.pack/'ds4.txt';st=path.stat()
        self.record['backing_identity']={str(path):{'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,
            'inode':st.st_ino,'device':st.st_dev+1,'filesystem_uuid':'12345678-abcd-4321-abcd-123456789abc'}}
        return self.record['backing_identity'][str(path)]
    def test_device_alias_requires_verified_same_filesystem_and_same_inode(self):
        identity=self.stable_filesystem_backing()
        with patch.object(self.module,'filesystem_uuid',return_value=identity['filesystem_uuid']) as query:
            self.assertIs(self.require(),self.cfg);query.assert_called_once_with(str(self.pack/'ds4.txt'))
    def test_device_alias_on_another_filesystem_is_refused(self):
        self.stable_filesystem_backing()
        with patch.object(self.module,'filesystem_uuid',return_value='87654321-abcd-4321-abcd-123456789abc'):
            self.assertRaisesRegex(RuntimeError,'backing identity changed',self.require)
    def test_device_alias_without_recorded_filesystem_is_refused(self):
        identity=self.stable_filesystem_backing();identity.pop('filesystem_uuid')
        self.assertRaisesRegex(RuntimeError,'backing identity changed',self.require)
    def test_filesystem_uuid_cannot_waive_size_time_or_inode(self):
        for field in ['bytes','mtime_ns','inode']:
            with self.subTest(field=field):
                identity=self.stable_filesystem_backing();identity[field]+=1
                with patch.object(self.module,'filesystem_uuid',return_value=identity['filesystem_uuid']):
                    self.assertRaisesRegex(RuntimeError,'backing identity changed',self.require)
    def test_unavailable_filesystem_query_fails_closed(self):
        self.stable_filesystem_backing()
        with patch.object(self.module,'filesystem_uuid',side_effect=RuntimeError('Cannot verify filesystem')):
            self.assertRaisesRegex(RuntimeError,'Cannot verify',self.require)
    def test_changed_serving_setting_rejected(self):self.cfg['args'][1]='65536';self.assertRaises(RuntimeError,self.require)
    def test_registry_cannot_waive_context_bound(self):self.cfg['args'][1]='65536';self.seal();self.assertRaises(RuntimeError,self.require)
    def test_registry_cannot_waive_reserve(self):self.cfg['args'][3]='1024';self.seal();self.assertRaises(RuntimeError,self.require)
    def test_single_gpu_rejected(self):self.cfg['gpu']=[0];self.seal();self.assertRaises(RuntimeError,self.require)
    def test_registry_cannot_waive_dual_layer_groups(self):self.cfg['args'][-1]='1';self.seal();self.assertRaises(RuntimeError,self.require)
    def glm(self):
        self.binary=self.source/'build-hip/maya';self.binary.write_bytes(b'known GLM engine');self.binary.chmod(0o755)
        self.cfg.update(exe=str(self.binary),layer_split='auto',args=['--glm-pack',str(self.pack),'--max-context','32768','--vram-reserve-mib','8192','--vram-reserve-later-mib','8192'])
        self.cfg['env'].update(MAYA_GLM_PREFILL_FUSED='0',MAYA_GLM_RAM_GB='8')
        self.record.update(binary=str(self.binary),binary_relative='build-hip/maya',binary_sha256=self.module.digest(self.binary));self.seal()
    def test_accepts_tested_GLM_implicit_dual_card_layout(self):
        self.glm();self.assertIs(self.require(),self.cfg)
    def test_GLM_fused_prefill_cannot_be_enabled_by_resealing(self):
        self.glm();self.cfg['env']['MAYA_GLM_PREFILL_FUSED']='1';self.seal();self.assertRaises(RuntimeError,self.require)
    def test_GLM_RAM_tier_cannot_be_changed_by_resealing(self):
        self.glm();self.cfg['env']['MAYA_GLM_RAM_GB']='40';self.seal();self.assertRaises(RuntimeError,self.require)
    def test_GLM_24GB_tier_requires_its_own_explicit_record(self):
        self.glm();self.cfg['env']['MAYA_GLM_RAM_GB']='24';self.seal();self.assertRaises(RuntimeError,self.require)
        self.record['glm_ram_gb']=24;self.assertIs(self.require(),self.cfg)
    def test_GLM_unsupported_tier_is_refused_even_with_a_record(self):
        self.glm();self.cfg['env']['MAYA_GLM_RAM_GB']='48';self.record['glm_ram_gb']=48;self.seal();self.assertRaises(RuntimeError,self.require)
    def test_GLM_24GB_record_does_not_allow_lower_GPU_reserves(self):
        self.glm();self.cfg['env']['MAYA_GLM_RAM_GB']='24';self.record['glm_ram_gb']=24
        self.cfg['args'][-1]='128';self.seal();self.assertRaises(RuntimeError,self.require)
    def test_GLM_40GB_tier_requires_its_exact_record(self):
        self.glm();self.cfg['env']['MAYA_GLM_RAM_GB']='40';self.seal()
        self.assertRaises(RuntimeError,self.require)
        self.record['glm_ram_gb']=40;self.assertIs(self.require(),self.cfg)
    def test_GLM_40GB_record_cannot_waive_GPU_reserve(self):
        self.glm();self.cfg['env']['MAYA_GLM_RAM_GB']='40';self.record['glm_ram_gb']=40
        self.cfg['args'][-1]='128';self.seal();self.assertRaises(RuntimeError,self.require)
    def test_GLM_cannot_use_strata_family(self):
        self.glm();self.record['family']='strata';self.assertRaises(RuntimeError,self.require)
    def test_GLM_later_card_reserve_cannot_be_lowered(self):
        self.glm();self.cfg['args'][-1]='128';self.seal();self.assertRaises(RuntimeError,self.require)
    def test_direct_admission_rejects_held_record(self):
        self.record['status']='held';self.assertRaises(RuntimeError,self.require)
    def test_provisional_native_requires_matching_token_and_live_updater_owner(self):
        import os
        self.record.update(status='candidate',candidate_owner='test-owner-token')
        lock=self.root/'hardware/generated/GPU-LOCK';lock.parent.mkdir(parents=True)
        lock.write_text(json.dumps({'owner':'daily-update-test','pid':os.getpid()}))
        self.assertRaises(RuntimeError,self.require)
        with patch.dict(os.environ,{'LOCAL_LLM_UPDATE_CANDIDATE':'test-owner-token'}):
            self.assertIs(self.require(),self.cfg)
            lock.write_text(json.dumps({'owner':'other-owner','pid':os.getpid()}))
            self.assertRaises(RuntimeError,self.require)
            lock.write_text(json.dumps({'owner':'daily-update-test','pid':999999999}))
            self.assertRaises(RuntimeError,self.require)
    def test_quality_skipping_rejected(self):self.cfg['env']['STRATA_DS4_PROMPT_SKIP']='1';self.seal();self.assertRaises(RuntimeError,self.require)
    def test_binary_change_rejected(self):self.binary.write_bytes(b'changed binary');self.assertRaises(RuntimeError,self.require)
    def test_source_revision_change_rejected(self):
        with patch.object(self.module.subprocess,'check_output',return_value='b'*40):self.assertRaises(RuntimeError,self.require)
    def test_dirty_source_rejected(self):
        with patch.object(self.module.subprocess,'run',return_value=types.SimpleNamespace(returncode=1)):self.assertRaises(RuntimeError,self.require)
    def test_pack_change_rejected(self):(self.pack/'ds4.txt').write_text('changed');self.assertRaises(RuntimeError,self.require)
    def test_pack_escape_rejected(self):self.record['pack_metadata_sha256']={'../escape':'0'*64};self.assertRaises(RuntimeError,self.require)
    def test_low_physical_RAM_always_rejected(self):
        with patch.object(self.module,'host_memory',return_value=(32*2**30,28*2**30)):self.assertRaises(RuntimeError,self.require,before_handover=True)
    def test_available_RAM_enforced_after_handover(self):
        with patch.object(self.module,'host_memory',return_value=(64*2**30,40*2**30)):
            self.assertIs(self.require(before_handover=True),self.cfg);self.assertRaises(RuntimeError,self.require)
    def test_startup_GPU_admission_enforced(self):
        (self.cards[0]/'mem_info_vram_used').write_text(str(12*2**30));self.assertRaises(RuntimeError,self.require)
    def test_missing_telemetry_fails_closed(self):(self.cards[0]/'mem_info_vram_total').unlink();self.assertRaises(FileNotFoundError,self.require)
    def test_registry_holds_and_family_binding(self):
        p=self.root/'dsh/qualified-native-profiles.json';p.parent.mkdir();p.write_text(json.dumps({'schema_version':1,'profiles':{'qualified-coder':self.record}}))
        self.assertEqual(self.module.record_for(self.cfg,'maya'),self.record)
        self.assertRaises(RuntimeError,self.module.record_for,self.cfg,'strata')
        self.record['status']='held';p.write_text(json.dumps({'schema_version':1,'profiles':{'qualified-coder':self.record}}));self.assertRaises(RuntimeError,self.module.record_for,self.cfg)

    def backing(self):
        path=self.pack/'weights.bin';path.write_bytes(b'known original backing');stat=path.stat()
        self.record['backing_identity']={str(path):{'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns,'inode':stat.st_ino-1,'device':stat.st_dev,'sha256':self.module.digest(path)}}
        return path
    def test_inode_only_change_requires_original_content_hash(self):
        self.backing();self.assertIs(self.require(),self.cfg)
    def test_inode_only_change_without_hash_fails_closed(self):
        path=self.backing();self.record['backing_identity'][str(path)].pop('sha256');self.assertRaises(RuntimeError,self.require)
    def test_changed_content_cannot_be_resealed_after_inode_change(self):
        path=self.backing();self.record['backing_identity'][str(path)]['sha256']='0'*64;self.assertRaises(RuntimeError,self.require)
    def test_size_or_timestamp_change_is_not_an_inode_cache_exception(self):
        path=self.backing();self.record['backing_identity'][str(path)]['mtime_ns']-=1;self.assertRaises(RuntimeError,self.require)

    def hash_health(self,path,storage_error=None,thermal_error=None):
        monitor=Mock()
        if storage_error:monitor.check.side_effect=RuntimeError(storage_error)
        stubs={name:types.ModuleType(name) for name in ['storage_health','gpu_telemetry','temperature_policy']}
        stubs['storage_health'].StorageHealthMonitor=lambda:monitor
        stubs['gpu_telemetry'].snapshot=lambda:{}
        stubs['temperature_policy'].TEMPERATURE_LIMIT_C=100
        stubs['temperature_policy'].temperature_failure=lambda _:thermal_error
        with patch.dict(sys.modules,stubs):value=self.backing_function(path)
        return value,monitor
    def test_large_identity_recheck_keeps_storage_monitor_active(self):
        path=self.backing();value,monitor=self.hash_health(path)
        self.assertEqual(value,self.module.digest(path));self.assertGreaterEqual(monitor.check.call_count,2)
    def test_identity_recheck_fails_closed_on_storage_monitor_fault(self):
        path=self.backing()
        with self.assertRaisesRegex(RuntimeError,'monitor unavailable'):self.hash_health(path,storage_error='monitor unavailable')
    def test_identity_recheck_fails_closed_on_temperature_fault(self):
        path=self.backing()
        with self.assertRaisesRegex(RuntimeError,'100C'):self.hash_health(path,thermal_error='100C ceiling')

if __name__=='__main__':unittest.main()
