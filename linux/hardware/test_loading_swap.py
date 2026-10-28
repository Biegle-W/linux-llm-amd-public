"""Historical v2 CPU regressions; current v3 behavior is in test_swap_user_policy."""
import importlib.util
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'hardware'),str(ROOT/'dsh')]
import inference_memory as mem
from swap_activity import SwapActivity, validate_summary
from inference_swap import OwnedWorkerWatch, WorkerSwapGuard
from strata_memory import MemoryGuard

G=1024**3
M=1024**2
def reading(t, incoming=0, outgoing=0, available=8*G, psi=0):
    return dict(timestamp=float(t),swapin_bytes=incoming,swapout_bytes=outgoing,
                available_bytes=available,memory_full_psi_avg10=psi)

class HistoricalLoadingSwapV2(unittest.TestCase):
    def setUp(self):
        env=patch.dict(os.environ)
        env.start(); self.addCleanup(env.stop)
        os.environ['LOCAL_LLM_SWAP_POLICY']='loading-swap-v2'
        os.environ['LOCAL_LLM_LEGACY_SWAP_VALIDATION']='1'

    def test_loading_large_swap_and_pressure_then_parked_inference_pass(self):
        activity=SwapActivity()
        activity.observe(reading(0),worker_swap_bytes=0)
        for t in (1,2,3):
            activity.observe(reading(t,incoming=t*G,outgoing=t*5*G,psi=80),worker_swap_bytes=12*G)
        activity.observe(reading(4,3*G,15*G),phase='inference',worker_swap_bytes=12*G)
        activity.observe(reading(34,3*G,15*G),phase='inference',worker_swap_bytes=12*G)
        self.assertEqual(activity.failures(),[])
        self.assertEqual(validate_summary(activity.summary(),require_inference=True),[])
        self.assertIsNone(mem.worker_swap_limit_bytes())
        memory=dict(max_worker_swap_bytes=12*G,max_nonresident_vram_bytes=0,swap_activity=activity.summary())
        self.assertEqual(mem.memory_failures(memory),[])
        self.assertEqual(activity.summary()['total_swapout_bytes'],15*G)

    def test_inference_churn_is_stopped_after_continuous_window(self):
        for incoming,outgoing,reason in [(0,30*M+1,'inference_swapout_rate'),
                                         (240*M+1,0,'inference_swap_io_rate')]:
            with self.subTest(reason=reason):
                activity=SwapActivity()
                activity.observe(reading(0),phase='inference')
                activity.observe(reading(30,incoming,outgoing),phase='inference')
                self.assertIn(reason,activity.failures())
                self.assertIn(reason,validate_summary(activity.summary(),True))

    def test_reload_discards_only_rate_history_and_loading_psi_run(self):
        activity=SwapActivity()
        activity.observe(reading(0),phase='inference')
        activity.set_phase('loading')
        for t in (5,6,7):activity.observe(reading(t,outgoing=8*G,psi=90))
        activity.observe(reading(10,outgoing=8*G,psi=11),phase='inference')
        activity.observe(reading(11,outgoing=8*G,psi=11),phase='inference')
        self.assertNotIn('memory_full_psi',activity.failures())
        self.assertEqual(activity.summary()['inference_window_samples'],0)
        activity.observe(reading(12,outgoing=8*G,psi=11),phase='inference')
        self.assertIn('memory_full_psi',activity.failures())

    def test_available_ram_and_telemetry_remain_fail_closed_during_loading(self):
        activity=SwapActivity()
        for t in (0,1,2): activity.observe(reading(t,available=G))
        self.assertIn('low_host_memory',activity.failures())
        activity.observe(None)
        self.assertIn('invalid_observation',activity.failures())

    def test_loading_only_or_old_policy_does_not_qualify_inference(self):
        activity=SwapActivity(); activity.observe(reading(0))
        self.assertIn('no_inference_window',validate_summary(activity.summary(),True))
        evidence=activity.summary(); evidence['policy']='low-churn-v1'
        self.assertIn('invalid_policy',validate_summary(evidence))

    def test_owned_watch_allows_loading_but_stops_inference_churn(self):
        proc=Mock(); proc.poll.return_value=None
        host=reading(0); terminate=Mock()
        watch=OwnedWorkerWatch(proc,terminate,host_reader=lambda:dict(host),
            memory_reader=lambda:dict(swap=12*G,spill=0,processes=1))
        watch.sample(); host.update(reading(1,outgoing=10*G)); watch.sample()
        terminate.assert_not_called()
        watch.ready(); host.update(reading(2,outgoing=10*G)); watch.sample()
        host.update(reading(32,outgoing=10*G+60*M)); watch.sample()
        self.assertIn('inference_swapout_rate',watch.fault)
        terminate.assert_called_once()

    def test_request_context_returns_to_idle_and_does_not_sample_idle_churn_as_inference(self):
        proc=Mock(); proc.poll.return_value=None
        clock=iter(range(20))
        watch=OwnedWorkerWatch(proc,Mock(),host_reader=lambda:reading(next(clock)),
            memory_reader=lambda:dict(swap=12*G,spill=0,processes=1))
        guard=WorkerSwapGuard();guard.watch=watch
        watch.ready('idle')
        with guard.inference(proc):
            self.assertEqual(watch.phase,'inference')
        self.assertEqual(watch.phase,'idle')
        self.assertEqual(watch.activity.summary()['inference_window_samples'],0)

    def test_parked_swap_does_not_trigger_secondary_guard(self):
        guard=MemoryGuard()
        self.assertIsNone(guard.check(8*G,12*G,0,[{'free':8*G},{'free':8*G}]))
        self.assertIsNotNone(guard.check(8*G,0,G,[{'free':8*G},{'free':8*G}]))

    def router(self):
        spec=importlib.util.spec_from_file_location('loading_swap_router',ROOT/'dsh/llama-router.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.native=Mock();module.native.poll.return_value=None
        module.swap_guard=Mock();module.time=Mock()
        return module

    def test_lazy_loading_enters_inference_only_after_loaded_status(self):
        router=self.router()
        router.call=Mock(side_effect=[{'data':[{'id':'x','status':{'value':'unloaded'}}]},
            {'success':True},{'data':[{'id':'x','status':{'value':'loading'}}]},
            {'data':[{'id':'x','status':{'value':'loaded'}}]}])
        router.ensure_loaded('x')
        self.assertEqual(router.swap_guard.ready.call_args_list[0].kwargs,{'phase':'loading'})
        self.assertEqual(router.swap_guard.ready.call_args_list[-1].kwargs,{})
        self.assertEqual(router.call.call_args_list[1].args[1],'/models/load')

    def test_failed_lazy_load_never_marks_inference_ready(self):
        router=self.router()
        router.call=Mock(side_effect=[{'data':[{'id':'x','status':{'value':'loading'}}]},
            {'data':[{'id':'x','status':{'value':'failed'}}]}])
        with self.assertRaisesRegex(RuntimeError,'loading failed'):router.ensure_loaded('x')
        self.assertEqual(router.swap_guard.ready.call_count,1)
        self.assertEqual(router.swap_guard.ready.call_args.kwargs,{'phase':'loading'})

if __name__=='__main__':unittest.main()
