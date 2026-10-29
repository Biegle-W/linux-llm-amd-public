"""Prove unbacked requests do not trip spill and real eviction still stops workers."""
import ast
from contextlib import nullcontext
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'dsh'),str(ROOT/'hardware')]
from amd_memory import vram_accounting,memory_counter
from backend_switch import Process
import inference_memory as mem
import inference_swap as owned
import moe_memory

class CounterSemantics(unittest.TestCase):
    def fields(self,evicted='0 KiB',total='128 MiB',resident='6 MiB'):
        d={'drm-total-vram':total,'drm-resident-vram':resident}
        if evicted is not None:d['amd-evicted-vram']=evicted
        return d
    def test_unbacked_requests_are_diagnostic_not_eviction(self):
        row=vram_accounting(self.fields());self.assertEqual(row['spill'],0);self.assertEqual(row['requested_nonresident'],122*1024**2)
    def test_one_byte_actual_eviction_trips_even_without_requested_resident_gap(self):
        row=vram_accounting(self.fields('1','100','120'));self.assertEqual(row['spill'],1);self.assertEqual(row['requested_nonresident'],0)
    def test_older_driver_keeps_conservative_nonresident_check(self):
        row=vram_accounting(self.fields(None));self.assertFalse(row['explicit']);self.assertEqual(row['spill'],122*1024**2)
    def test_legacy_driver_keeps_fail_closed_resident_above_requested_case(self):
        with self.assertRaises(ValueError):vram_accounting(self.fields(None,total='100',resident='120'))
    def test_bytes_kib_mib_and_optional_default_unit(self):
        for text,value in [('7',7),('7 B',7),('7 KiB',7168),('7 MiB',7*1024**2)]:self.assertEqual(memory_counter({'key':text},'key'),value)
    def test_malformed_present_counter_never_falls_back_to_zero(self):
        for value in ['', '-1 KiB','1 KB','nan KiB','1 KiB trailing','129 MiB']:
            with self.subTest(value=value),self.assertRaises(ValueError):vram_accounting(self.fields(value))
    def test_required_counters_remain_required(self):
        for key in ['drm-total-vram','drm-resident-vram']:
            d=self.fields();del d[key]
            with self.assertRaises(KeyError):vram_accounting(d)

class EndToEndGuards(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.pid=123
        base=self.root/str(self.pid);(base/'fdinfo').mkdir(parents=True);(base/'status').write_text('State: S\nVmSwap: 0 kB\n');(base/'stat').write_text('123 (worker) S 0 0 0')
        self.fd=base/'fdinfo/9';self.reader=mem.sample_memory;self.write('0 KiB');self.snapshot={123:Process(123,0,'1',('python3',str(ROOT/'dsh/vllm-router.py')),'','S')}
        env=patch.dict(os.environ,{'LOCAL_LLM_SWAP_POLICY':'loading-swap-v4'});env.start();self.addCleanup(env.stop)
    def write(self,evicted):
        self.fd.write_text('drm-driver: amdgpu\ndrm-pdev: 0000:03:00.0\ndrm-client-id: 7\ndrm-total-vram: 128 MiB\ndrm-resident-vram: 6 MiB\namd-evicted-vram: '+evicted+'\n')
    def read(self):return self.reader(self.snapshot,self.root)
    def test_lifecycle_records_large_request_gap_but_enforces_actual_eviction(self):
        sample=self.read();self.assertEqual(sample['spill'],0);self.assertEqual(sample['vram_accounting']['explicit_eviction_clients'],1)
        callback=Mock();monitor=mem.MemoryMonitor(on_violation=callback)
        host={'timestamp':0.,'swapin_bytes':0,'swapout_bytes':0,'available_bytes':8*1024**3,'memory_full_psi_avg10':0.}
        with patch.object(mem,'sample_memory',side_effect=self.read),patch.object(mem,'read_host_activity',return_value=host):
            monitor.sample();callback.assert_not_called();self.write('1');monitor.sample()
        callback.assert_called_once();self.assertIn('vram_spill',callback.call_args.args[0]);self.assertEqual(monitor.summary['max_nonresident_vram_bytes'],1);self.assertEqual(monitor.summary['vram_accounting']['max_requested_nonresident_vram_bytes'],122*1024**2)
    def test_owned_worker_watch_ignores_request_gap_but_stops_actual_eviction(self):
        callback=Mock();proc=Mock(poll=Mock(return_value=None));host=lambda:{'timestamp':0.,'swapin_bytes':0,'swapout_bytes':0,'available_bytes':8*1024**3,'memory_full_psi_avg10':0.}
        watch=owned.OwnedWorkerWatch(proc,callback,host_reader=host,memory_reader=self.read)
        watch.sample();callback.assert_not_called();self.write('1');watch.sample();self.assertIn('vram_spill',watch.fault);callback.assert_called_once()
    def test_fault_evidence_contains_only_known_counters(self):
        self.write('1');reading=self.read();reading['private']='must-never-log'
        reading['vram_accounting']['private']='must-never-log'
        callback=Mock();proc=Mock(poll=Mock(return_value=None));host=lambda:{'timestamp':0.,'swapin_bytes':0,'swapout_bytes':0,'available_bytes':8*1024**3,'memory_full_psi_avg10':0.}
        watch=owned.OwnedWorkerWatch(proc,callback,host_reader=host,memory_reader=lambda:reading);watch.sample()
        self.assertEqual(watch.last_reading['spill'],1);self.assertEqual(watch.last_reading['vram_accounting']['explicit_evicted_vram_bytes'],1)
        self.assertNotIn('must-never-log',json.dumps(watch.last_reading));callback.assert_called_once()
    def test_moe_reader_uses_actual_counter_and_malformed_data_is_not_zero(self):
        self.assertEqual(moe_memory.worker_memory(self.pid,proc_root=self.root),(0,0));self.write('1');self.assertEqual(moe_memory.worker_memory(self.pid,proc_root=self.root),(0,1));self.write('bad')
        with self.assertRaises(ValueError):moe_memory.worker_memory(self.pid,proc_root=self.root)
    def test_gpu_client_deduplication_remains_per_device(self):
        (self.fd.parent/'10').write_text(self.fd.read_text());second=self.fd.parent/'11';second.write_text(self.fd.read_text().replace('0000:03:00.0','0000:06:00.0').replace('0 KiB','1 KiB'))
        sample=self.read();self.assertEqual(sample['spill'],1024);self.assertEqual(sample['vram_accounting']['explicit_eviction_clients'],2)
    def test_moe_watch_stops_owned_worker_on_unreadable_live_counter(self):
        proc=Mock(poll=Mock(return_value=None));stop=Mock();event=Mock(wait=Mock(return_value=False))
        class Immediate:
            def __init__(self,target,**kwargs):self.target=target
            def start(self):self.target()
        with patch.object(moe_memory.threading,'Event',return_value=event),patch.object(moe_memory.threading,'Thread',Immediate),patch.object(moe_memory,'profiles',return_value={'active':{'memory_placement':'vram_only'}}),patch.object(moe_memory,'host_memory',return_value=(32*1024**3,24*1024**3)),patch.object(moe_memory,'worker_memory',side_effect=ValueError('invalid')):
            moe_memory.watch_worker(proc,lambda:'active',stop)
        stop.assert_called_once_with(proc)
    def test_streaming_watchdogs_stop_only_owned_worker_on_unreadable_counter(self):
        for name in ['strata-router.py','maya-router.py']:
            with self.subTest(name=name):
                tree=ast.parse((ROOT/'dsh'/name).read_text());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='watch_memory');proc=Mock(poll=Mock(return_value=None));stop=Mock();ns={'MemoryGuard':Mock(),'stopping':Mock(wait=Mock(side_effect=[False,True])),'worker':proc,'memory_fault':None,'lifecycle':nullcontext(),'host_memory':lambda:(32*1024**3,24*1024**3),'worker_memory':Mock(side_effect=ValueError('invalid')),'stop_worker':stop,'vram_snapshot':Mock()}
                exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),name,'exec'),ns);ns['watch_memory']();stop.assert_called_once_with(timeout=3);self.assertIn('ValueError',ns['memory_fault']);ns['vram_snapshot'].assert_not_called()

if __name__=='__main__':unittest.main()
