"""Owner-requested sustained inference ceilings; no real I/O or GPU work."""
import importlib
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock,patch
source=Path(os.environ.get('SWAP_TEST_SOURCE',Path(__file__).resolve().parent/'swap_activity.py'))
sys.path.insert(0,str(source.parent))
root=Path(os.environ.get('SWAP_TEST_ROOT',Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(root/'dsh'))
policy=importlib.import_module('swap_activity')
MiB=1024**2


def reading(t,write=0,read=0,psi=0):
    return dict(timestamp=float(t),swapin_bytes=read,swapout_bytes=write,available_bytes=8*1024**3,memory_full_psi_avg10=psi)


class OwnerRateLimits(unittest.TestCase):
    def setUp(self):
        p=patch.dict(os.environ,{'LOCAL_LLM_SWAP_POLICY':'loading-swap-v4'});p.start();self.addCleanup(p.stop)

    def series(self,write,read=0):
        a=policy.SwapActivity();a.observe(reading(0),'inference',12*1024**3)
        a.observe(reading(30,write,read),'inference',12*1024**3)
        return a

    def test_default_is_new_policy_and_exact_ceilings_are_inclusive(self):
        with patch.dict(os.environ):
            os.environ.pop('LOCAL_LLM_SWAP_POLICY',None)
            self.assertEqual(policy.selected_policy(),'loading-swap-v4')
        a=self.series(128*MiB*30,32*MiB*30)
        self.assertEqual(a.failures(),[]);self.assertEqual(policy.validate_summary(a.summary(),True),[])

    def test_write_one_byte_over_window_budget_fails_without_changing_performance_floor(self):
        a=self.series(128*MiB*30+1)
        self.assertIn('inference_swapout_rate',a.failures())
        forged=a.summary();forged['failures']=[]
        self.assertIn('inference_swapout_rate',policy.validate_summary(forged,True))

    def test_combined_limit_is_independent_and_includes_reads(self):
        a=self.series(128*MiB*30,32*MiB*30+1)
        self.assertNotIn('inference_swapout_rate',a.failures());self.assertIn('inference_swap_io_rate',a.failures())
        a=self.series(0,160*MiB*30+1);self.assertIn('inference_swap_io_rate',a.failures())

    def test_loading_and_parked_swap_are_allowed_but_window_restarts_for_inference(self):
        a=policy.SwapActivity();a.observe(reading(0),'loading',20*1024**3)
        a.observe(reading(30,20*1024**3,20*1024**3),'loading',20*1024**3)
        a.observe(reading(31,20*1024**3,20*1024**3),'inference',20*1024**3)
        a.observe(reading(61,20*1024**3,20*1024**3),'inference',20*1024**3)
        self.assertEqual(a.failures(),[]);self.assertEqual(policy.validate_summary(a.summary(),True),[])

    def test_short_burst_without_complete_window_is_not_sustained_evidence(self):
        a=policy.SwapActivity();a.observe(reading(0),'inference')
        a.observe(reading(1,1024*MiB),'inference');self.assertEqual(a.failures(),[])
        self.assertIn('no_inference_window',policy.validate_summary(a.summary(),True))

    def test_pressure_is_advisory_and_rate_metadata_cannot_be_forged_or_omitted(self):
        a=policy.SwapActivity()
        for t in (0,15,30):a.observe(reading(t,psi=50),'inference')
        self.assertEqual(a.failures(),[]);s=a.summary()
        self.assertIn('active_memory_pressure_observed',s['advisories'])
        for field in ('inference_write_limit_bytes_per_second','inference_io_limit_bytes_per_second','rate_window_seconds'):
            for value in (None,False,1):
                bad=dict(s);bad[field]=value
                self.assertIn('invalid_'+field,policy.validate_summary(bad,True))

    def test_historical_v3_remains_advisory_and_cannot_qualify_as_new_policy(self):
        with patch.dict(os.environ,{'LOCAL_LLM_SWAP_POLICY':'loading-swap-v3','LOCAL_LLM_LEGACY_SWAP_VALIDATION':'1'}):
            a=self.series(200*MiB*30);self.assertEqual(a.failures(),[])
            self.assertEqual(policy.validate_summary(a.summary(),True),[])
        self.assertIn('invalid_policy',policy.validate_summary(a.summary(),True))

    def test_owned_worker_watch_enforces_new_ceiling_without_signalling_other_processes(self):
        from inference_swap import OwnedWorkerWatch
        proc=Mock();proc.poll.return_value=None;stop=Mock();host=reading(0)
        watch=OwnedWorkerWatch(proc,stop,host_reader=lambda:host,memory_reader=lambda:dict(swap=12*1024**3,spill=0,processes=1))
        watch.ready();watch.sample();host.update(reading(30,128*MiB*30));watch.sample()
        stop.assert_not_called()
        host.update(reading(60,(128+129)*MiB*30));watch.sample()
        self.assertEqual(watch.fault,'inference_swapout_rate');stop.assert_called_once_with(proc,watch.fault)

    def test_dedicated_vram_spill_guard_is_unchanged_under_new_policy(self):
        from inference_swap import OwnedWorkerWatch
        proc=Mock();proc.poll.return_value=None;stop=Mock()
        watch=OwnedWorkerWatch(proc,stop,host_reader=lambda:reading(0),memory_reader=lambda:dict(swap=0,spill=1,processes=1))
        watch.sample();self.assertIn('vram_spill',watch.fault);stop.assert_called_once_with(proc,watch.fault)


if __name__=='__main__':unittest.main()
