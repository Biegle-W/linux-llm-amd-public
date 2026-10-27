"""Guard explicit VRAM-only defaults without admitting CPU-backed models as GPU-only."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'dsh'),str(ROOT/'hardware')]
import moe_memory
GIB=1024**3
IDS=('empero-qwen3.8-35b-a3b','sage-a1.5','flint-40b-a2.5b')

class VramDefaults(unittest.TestCase):
    def setUp(self):
        self.plans=json.loads((ROOT/'dsh/moe-offload.json').read_text())['models']
        self.plan=copy.deepcopy(self.plans[IDS[0]])

    def test_installed_profiles_explicitly_validate_and_other_moe_stays_cpu_backed(self):
        moe_memory.validate_profiles(ROOT/'dsh')
        for ident in IDS:self.assertEqual(self.plans[ident]['memory_placement'],'vram_only')
        for ident in ['nemotron-3.5-super-iq3','ornith-1.5-122b']:
            self.assertTrue(self.plans[ident]['cpu_expert_layers'])
            self.assertGreater(self.plans[ident]['host_expert_bytes'],0)

    def test_gpu_weights_still_need_physical_staging_headroom(self):
        self.assertIsNone(moe_memory.memory_reason(self.plan,14*GIB,7*GIB))
        self.assertIn('staging',moe_memory.memory_reason(self.plan,14*GIB,6*GIB))
        self.assertIn('OS-visible',moe_memory.memory_reason(self.plan,10*GIB,8*GIB))
        self.assertIsNone(moe_memory.memory_reason(self.plan,14*GIB,3*GIB,True))
        self.assertIsNotNone(moe_memory.memory_reason(self.plan,14*GIB,2*GIB,True))

    def test_vram_label_cannot_relax_cgroup_cpu_weight_or_vram_guards(self):
        changes=[{'worker_memory_limits':{'memory.high':4*GIB,'memory.max':0,'memory.swap.max':0}},
                 {'host_expert_bytes':GIB},{'cpu_expert_layers':[0]},
                 {'gpu_expert_cache_mib':1},{'minimum_available_ram_gib':1},
                 {'memory_placement':'unknown'},
                 {'min_free_vram_gib':0},{'min_start_vram_gib':0}]
        for changeset in changes:
            with self.subTest(changeset=changeset),self.assertRaises(RuntimeError):
                moe_memory.vram_worker_limits({**self.plan,**changeset})

    def test_preset_mutations_reject_before_launch(self):
        base=(ROOT/'dsh/models-hip.ini').read_text()
        for old,new in [('override-tensor = token_embd.*=ROCm0','override-tensor = token_embd.*=CPU'),
                        ('moe-cache-mib = 0','moe-cache-mib = 4096'),
                        ('load-mode = dio','load-mode = mmap'),
                        ('spec-type = draft-mtp','spec-type = none'),
                        ('reasoning-budget = 128','reasoning-budget = -1'),
                        ('ctx-size = 262144','ctx-size = 32768'),
                        ('device = ROCm0,ROCm1','device = ROCm0')]:
            with self.subTest(setting=old),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)
                for name in ['models.json','moe-offload.json']:(p/name).write_bytes((ROOT/'dsh'/name).read_bytes())
                (p/'models-hip.ini').write_text(base.replace(old,new))
                with self.assertRaisesRegex(RuntimeError,'VRAM-only preset'):
                    moe_memory.validate_profiles(p)

    def router(self):
        spec=importlib.util.spec_from_file_location('vram_router_test',ROOT/'dsh/llama-router.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        m.swap_guard=Mock();m.require_amd_headroom=Mock();m.watch_worker=Mock();m.ready=Mock();m.stop_process=Mock()
        # Guard tests use an isolated identity, independent of installed source paths.
        m.runtime_identity=Mock(return_value=('hip-amd','/fake/qualified-source','a'*40))
        return m

    def test_cpu_target_refuses_before_replacing_working_gpu_worker(self):
        m=self.router();m.native=Mock();m.native.poll.return_value=None;m.active_mode='hip-amd';m.active_limits=moe_memory.vram_worker_limits(self.plan)
        with patch.object(moe_memory,'host_memory',return_value=(14*GIB,8*GIB)):
            with self.assertRaisesRegex(RuntimeError,'OS-visible'):
                m.activate_native.__wrapped__('hip-amd',model='nemotron-3.5-super-iq3')
        m.stop_process.assert_not_called();m.swap_guard.spawn.assert_not_called()
        with patch.object(moe_memory,'host_memory',return_value=(14*GIB,8*GIB)):
            with self.assertRaisesRegex(RuntimeError,'require HIP AMD'):
                m.activate_native.__wrapped__('vulkan-amd',model=IDS[0])
        m.stop_process.assert_not_called();m.swap_guard.spawn.assert_not_called()

    def test_compatible_gpu_switch_keeps_bounded_worker(self):
        m=self.router();m.native=Mock();m.native.poll.return_value=None;m.active_mode='hip-amd';m.active_limits=moe_memory.vram_worker_limits(self.plan)
        m.active_runtime=m.runtime_identity('hip-amd','sage-a1.5')
        with patch.object(moe_memory,'host_memory',return_value=(14*GIB,8*GIB)):
            m.activate_native.__wrapped__('hip-amd',model='sage-a1.5')
        m.stop_process.assert_not_called();m.swap_guard.spawn.assert_not_called()

    def test_gpu_spawn_carries_and_requires_exact_limits(self):
        m=self.router();m.native=None;proc=Mock();proc.poll.return_value=None;m.swap_guard.spawn.return_value=proc
        with patch.object(moe_memory,'host_memory',return_value=(14*GIB,8*GIB)):
            m.activate_native.__wrapped__('hip-amd',(Path('/fake/binary'),Path('/fake/preset'),{},set(IDS)),model=IDS[0])
        args=m.swap_guard.spawn.call_args.args[0];kwargs=m.swap_guard.spawn.call_args.kwargs
        self.assertIn('--property=MemoryHigh='+str(4*GIB),args)
        self.assertIn('--property=MemoryMax='+str(5*GIB),args)
        self.assertIn('--property=MemorySwapMax=max',args)
        self.assertEqual(kwargs['expected_memory_limits'],moe_memory.vram_worker_limits(self.plan))

if __name__=='__main__':unittest.main()
