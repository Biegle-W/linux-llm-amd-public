"""CPU fixtures for traceable telemetry failures without weakening memory gates."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(os.environ.get('SAMPLER_TEST_ROOT',Path(__file__).resolve().parents[1]))
sys.path[:0]=[str(ROOT/'hardware'),str(ROOT/'dsh')]
source=Path(os.environ.get('SAMPLER_TEST_SOURCE',ROOT/'hardware/inference_memory.py'))
sys.path.insert(0,str(source.parent))
spec=importlib.util.spec_from_file_location('diagnostic_memory_target',source)
mem=importlib.util.module_from_spec(spec);spec.loader.exec_module(mem)
from backend_switch import Process


class Diagnostics(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.pid=4321
        base=self.root/str(self.pid);(base/'fdinfo').mkdir(parents=True)
        self.status=base/'status';self.status.write_text('State:\tS (sleeping)\nVmSwap:\t0 kB\n')
        self.fd=base/'fdinfo/9'
        self.fd.write_text('drm-driver:\tamdgpu\ndrm-pdev:\t0000:03:00.0\ndrm-client-id:\t22\ndrm-total-vram:\t1 KiB\ndrm-resident-vram:\t1 KiB\n')
        self.snapshot={self.pid:Process(self.pid,0,'1',('python3',str(ROOT/'dsh/vllm-router.py')),'','S')}
        self.env=patch.dict(os.environ,{'LOCAL_LLM_SWAP_POLICY':'loading-swap-v4'});self.env.start();self.addCleanup(self.env.stop)

    def monitor_sample(self,phase='inference'):
        monitor=mem.MemoryMonitor();monitor.set_phase(phase)
        reader=mem.sample_memory
        host=dict(timestamp=0.,swapin_bytes=0,swapout_bytes=0,available_bytes=8*1024**3,memory_full_psi_avg10=0.)
        with patch.object(mem,'sample_memory',side_effect=lambda:reader(self.snapshot,self.root)),patch.object(mem,'read_host_activity',return_value=host):
            monitor.sample()
        return monitor

    def test_missing_live_swap_counter_records_exact_key_process_phase_and_sample(self):
        self.status.write_text('State:\tS (sleeping)\n')
        monitor=self.monitor_sample();d=monitor.summary['sampling_error_details'][0]
        self.assertEqual(monitor.summary['sampling_errors'],1)
        self.assertEqual(d['missing_key'],'VmSwap');self.assertEqual(d['pid'],self.pid)
        self.assertEqual(d['phase'],'inference');self.assertEqual(d['sample_index'],1)
        self.assertEqual(d['reader'],'proc_status');self.assertEqual(d['error_type'],'KeyError')
        self.assertTrue(d['timestamp_utc'].endswith('+00:00'));self.assertTrue(d['frames'])
        self.assertIn('lifecycle_sampling_errors',mem.lifecycle_failures({'lifecycle_memory':monitor.summary}))

    def test_each_missing_drm_counter_identifies_fd_and_key_without_claiming_zero(self):
        original=self.fd.read_text()
        for key in ('drm-pdev','drm-client-id','drm-total-vram','drm-resident-vram'):
            with self.subTest(key=key):
                self.fd.write_text('\n'.join(line for line in original.splitlines()if not line.startswith(key+':'))+'\n')
                monitor=self.monitor_sample();d=monitor.summary['sampling_error_details'][0]
                self.assertEqual(d['missing_key'],key);self.assertEqual(d['reader'],'drm_fdinfo')
                self.assertEqual(d['fd'],9);self.assertEqual(d['pid'],self.pid)
                self.assertEqual(monitor.summary['sampling_errors'],1)

    def test_confirmed_process_exit_remains_normal(self):
        self.status.write_text('State:\tZ (zombie)\n')
        monitor=self.monitor_sample('shutdown')
        self.assertEqual(monitor.summary['sampling_errors'],0)
        self.assertEqual(monitor.summary['sampling_error_details'],[])

    def test_error_records_are_bounded_and_do_not_export_messages_paths_or_locals(self):
        monitor=mem.MemoryMonitor();error=KeyError('/home/private/SECRET-token')
        with patch.object(mem,'sample_memory',side_effect=error),patch.object(mem,'read_host_activity',side_effect=[dict(timestamp=float(i),swapin_bytes=0,swapout_bytes=0,available_bytes=8*1024**3,memory_full_psi_avg10=0.)for i in range(20)]):
            for _ in range(20):monitor.sample()
        self.assertEqual(monitor.summary['sampling_errors'],20)
        self.assertEqual(len(monitor.summary['sampling_error_details']),8)
        self.assertEqual(monitor.summary['sampling_error_details_dropped'],12)
        text=json.dumps(monitor.summary['sampling_error_details'])
        self.assertNotIn('SECRET',text);self.assertNotIn('/home/',text)
        self.assertEqual(monitor.summary['sampling_error_details'][0]['missing_key'],'<redacted>')

    def test_returned_evidence_is_detached(self):
        self.status.write_text('State:\tS (sleeping)\n');monitor=self.monitor_sample()
        monitor.thread=SimpleNamespace(join=lambda **kwargs:None,is_alive=lambda:False)
        result=monitor.stop();result['sampling_error_details'][0]['phase']='changed'
        self.assertEqual(monitor.summary['sampling_error_details'][0]['phase'],'inference')


if __name__=='__main__':unittest.main()
