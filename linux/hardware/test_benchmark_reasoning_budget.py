"""CPU checks for bounded reasoning allowance and retained marker failures."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

ROOT=Path(os.environ.get('BENCHMARK_TEST_ROOT',Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(ROOT/'hardware'));sys.path.insert(0,str(ROOT/'dsh'))
source=Path(os.environ.get('BENCHMARK_TEST_SOURCE',ROOT/'hardware/benchmark-current-amd.py'))
spec=importlib.util.spec_from_file_location('tested_reasoning_benchmark',source)
bench=importlib.util.module_from_spec(spec);spec.loader.exec_module(bench)


class ReasoningBudget(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'dsh').mkdir()
        (self.root/'dsh/llama-runtime.json').write_text(json.dumps({'backend':'hip-amd'}))
        self.ini=self.root/'dsh/models-hip.ini'
        self.ini.write_text('version = 1\n[*]\nreasoning=off\n[flint]\nreasoning=on\nreasoning-budget=128\n[empero]\nreasoning=off\n')
        self.patch=patch.object(bench,'ROOT',self.root);self.patch.start();self.addCleanup(self.patch.stop)

    def test_configured_reasoning_budget_is_added_to_answer_allowance_without_changing_profile(self):
        original=hashlib.sha256(self.ini.read_bytes()).hexdigest()
        self.assertEqual(bench.marker_output_limit('llama','flint'),192)
        self.assertEqual(hashlib.sha256(self.ini.read_bytes()).hexdigest(),original)
        self.assertEqual(bench.marker_output_limit('llama','empero'),64)
        self.assertEqual(bench.marker_output_limit('vllm','flint'),64)
        self.assertEqual(bench.marker_output_limit('llama','muse-glimmer-30b'),1024)

    def test_unbounded_missing_and_invalid_reasoning_budgets_fail_closed(self):
        for setting in ('reasoning-budget=-1','', 'reasoning-budget=garbage'):
            self.ini.write_text('[*]\nreasoning=off\n[flint]\nreasoning=on\n'+setting+'\n')
            with self.subTest(setting=setting),self.assertRaises(ValueError):
                bench.marker_output_limit('llama','flint')

    def test_selected_backend_and_default_budget_are_respected(self):
        (self.root/'dsh/models-amd.ini').write_text('[*]\nreasoning=on\nreasoning-budget=96\n[flint]\n')
        (self.root/'dsh/llama-runtime.json').write_text(json.dumps({'backend':'hip-amd','runtime_overrides':{'flint':'vulkan-amd'}}))
        self.assertEqual(bench.marker_output_limit('llama','flint'),160)

    def test_stream_retains_reasoning_only_length_finish_and_visible_success(self):
        def reply(visible):
            events=[{'choices':[{'delta':{'reasoning_content':'reasoning'}}]},
                    {'choices':[{'delta':{'content':visible},'finish_reason':'stop' if visible else 'length'}],
                     'usage':{'prompt_tokens':6000,'completion_tokens':145 if visible else 64}}]
            return io.BytesIO(''.join('data: '+json.dumps(e)+'\n'for e in events).encode())
        with patch.object(bench,'metrics',return_value={}),patch.object(bench.urllib.request,'urlopen',side_effect=[reply(''),reply('ALPHA-734 BRAVO-915 CHARLIE-268')])as opener:
            failed,text=bench.stream.__wrapped__('llama','flint','prompt',limit=64,sampled=False)
            self.assertEqual(text,'');self.assertTrue(failed['reasoning_tokens_present'])
            self.assertFalse(failed['visible_content_present']);self.assertEqual(failed['finish_reason'],'length')
            passed,text=bench.stream.__wrapped__('llama','flint','prompt',limit=192,sampled=False)
            self.assertTrue(passed['visible_content_present']);self.assertEqual(passed['finish_reason'],'stop')
            self.assertEqual(json.loads(opener.call_args.args[0].data)['max_tokens'],192)

    def test_missing_marker_still_fails_and_trial_is_saved_before_assertion(self):
        output=self.root/'out.json'
        def stream(kind,model,prompt,**kwargs):
            trial={'usage':{'completion_tokens':256,'prompt_tokens':6000},'ttft_seconds':1.,'decode_tps_sse':100.,'cached_tokens':0,'finish_reason':'stop'}
            if '17 times' in prompt:return trial,'323'
            if prompt=='marker-prompt':return trial,'ALPHA-734 CHARLIE-268'
            return trial,'long output'
        monitor=Mock();monitor.stop.return_value={'worker_samples':2,'sampling_errors':0,'max_worker_swap_bytes':0,'max_nonresident_vram_bytes':0}
        thermal=Mock();thermal.start.return_value=SimpleNamespace(stop=lambda:{})
        argv=['benchmark','--kind','llama','--model','flint','--runs','1','--output',str(output)]
        with patch.object(sys,'argv',argv),patch.object(bench,'amd_devices'),patch.object(bench,'profiles',return_value=[('flint',32768)]),patch.object(bench,'stream',side_effect=stream),patch.object(bench,'prefill_prompt',return_value='marker-prompt'),patch.object(bench,'MemoryMonitor',return_value=monitor),patch.object(bench,'ThermalRecorder',return_value=thermal),patch.object(bench.threading,'Thread'),contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as exit_status:bench.main()
            self.assertEqual(exit_status.exception.code,1)
        row=json.loads(output.read_text())['profiles'][0]
        self.assertEqual(row['status'],'failed');self.assertEqual(row['error_type'],'AssertionError')
        self.assertEqual(row['prefill_output_cap'],192);self.assertEqual(len(row['prefill']),1)
        self.assertFalse(row['prefill'][0]['markers_passed'])


if __name__=='__main__':unittest.main()
