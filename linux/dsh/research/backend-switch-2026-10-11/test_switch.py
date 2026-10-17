"""Ownership, cleanup and startup-serialization regression checks."""
import contextlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import backend_switch as switch


def p(pid, parent, args, start='1'):
    return switch.Process(pid, parent, start, tuple(args), '', 'S')


class SwitchTests(unittest.TestCase):
    def test_backend_tree_includes_monitor_and_rank_but_not_frontend(self):
        root = Path('/test-local-llm')
        launch = p(10, 1, ['python3', str(root/'dsh/launch-backend.py'), 'vllm'])
        router = p(11, 10, ['python3', str(root/'dsh/vllm-router.py')])
        rank = p(12, 11, ['VLLM::Worker_TP0'])
        monitor = p(13, 10, ['tail', 'model.log'])
        dsh = p(20, 1, ['python3', str(root/'dsh/start-dsh.py')])
        gateway = p(21, 1, ['python3', str(root/'network/gateway.py')])
        other = p(22, 1, ['python3', 'training.py'])
        snap = {x.pid:x for x in [launch, router, rank, monitor, dsh, gateway, other]}
        self.assertEqual(set(switch.owned_processes(snap, root)), {10,11,12,13})

    def test_waiting_launcher_without_worker_is_not_stopped(self):
        root=Path('/test-local-llm')
        waiter=p(10,1,['python3',str(root/'dsh/launch-backend.py'),'sglang'])
        self.assertEqual(switch.owned_processes({10:waiter},root),{})

    def test_legacy_direct_workers_are_recognized(self):
        root=Path('/test-local-llm')
        args=[['python3',str(root/'dsh/strata-router.py')],
              [str(root/'llama.cpp/build/bin/llama-server')],
              [str(root/'llama.cpp/build-vulkan/bin/llama-server')],
              [str(root/'llama.cpp/build-hip/bin/llama-server')],
              [str(root/'strata/engine/strata')],
              [str(root/'sglang/.venv/bin/python'),'-m','sglang.launch_server'],
              [str(root/'vllm/.venv/bin/python'),'-m','vllm.entrypoints.openai.api_server'],
              [str(root/'hyperqwen/upstream/venv/bin/python'),str(root/'hyperqwen/upstream/venv/bin/vllm'),'serve']]
        for argv in args:
            self.assertTrue(switch.is_inference(p(1,0,argv),root),argv)
        self.assertFalse(switch.is_inference(p(1,0,['python3','-c','example '+str(root/'dsh/strata-router.py')]),root))

    def test_stale_owner_pid_identity_is_ignored(self):
        root=Path('/test-local-llm')
        launcher=p(10,1,['python3',str(root/'dsh/launch-backend.py'),'llama'],start='new')
        self.assertEqual(switch.owned_processes({10:launcher},root,{'pid':10,'start':'old'}),{})
        self.assertEqual(set(switch.owned_processes({10:launcher},root,{'pid':10,'start':'new'})),{10})

    def test_rocm_servers_are_owned_but_probes_and_clients_are_not(self):
        root = Path('/test-local-llm')
        for kind, args in [('vllm', ['serve', '/model']), ('sglang', ['--model-path', '/model'])]:
            python = str(root / kind / '.venv-rocm/bin/python')
            bootstrap = str(root / kind / 'rocm-bootstrap.py')
            self.assertTrue(switch.is_inference(p(1, 0, [python, bootstrap, *args]), root))
            self.assertFalse(switch.is_inference(p(1, 0, [python, bootstrap, '--help']), root))
            self.assertFalse(switch.is_inference(p(1, 0, [python, str(root/'hardware/rocm-probe.py')]), root))
            self.assertFalse(switch.is_inference(p(1, 0, [python, 'client.py', bootstrap, *args]), root))

    def test_other_apps_and_non_serving_runtime_commands_are_not_selected(self):
        root=Path('/test-local-llm')
        examples=[['python3','training.py'],
                  ['python3',str(root/'dsh/start-dsh.py')],
                  ['python3',str(root/'network/gateway.py')],
                  [str(root/'vllm/.venv/bin/python'),str(root/'vllm/.venv/bin/vllm'),'collect-env'],
                  [str(root/'vllm/.venv/bin/python'),'training.py','vllm.entrypoints.openai.api_server'],
                  ['python3','some-client.py',str(root/'dsh/vllm-router.py')],
                  ['python3','some-client.py',str(root/'dsh/launch-backend.py'),'vllm'],
                  ['/usr/bin/ollama','serve'], ['/usr/bin/ptyxis'], ['/usr/bin/blender']]
        for index,argv in enumerate(examples):
            candidate=p(index+100,1,argv)
            self.assertFalse(switch.is_launcher(candidate,root),argv)
            self.assertFalse(switch.is_inference(candidate,root),argv)
            self.assertEqual(switch.owned_processes({candidate.pid:candidate},root),{},argv)

    def test_strata_mock_server_is_not_selected(self):
        root=Path('/test-local-llm')
        mock=switch.Process(1,0,'1',('python3','serve/server.py','--engine','mock'),str(root/'strata'),'S')
        actual=switch.Process(2,0,'1',('python3','serve/server.py','--engine','strata'),str(root/'strata'),'S')
        self.assertFalse(switch.is_inference(mock,root))
        self.assertTrue(switch.is_inference(actual,root))

    def test_launchers_allow_only_configured_backend_names(self):
        root=Path('/test-local-llm')
        for backend in ['llama','vllm','sglang','hyperqwen','strata']:
            self.assertTrue(switch.is_launcher(p(1,0,['python3','-u',str(root/'dsh/launch-backend.py'),backend]),root))
        self.assertFalse(switch.is_launcher(p(1,0,['python3',str(root/'dsh/launch-backend.py'),'training']),root))

    def test_reused_pid_is_not_signalled(self):
        old=p(100,1,['python3'],start='old')
        with patch.object(os,'pidfd_open',return_value=55),patch.object(os,'close'), \
             patch.object(switch,'process',return_value=p(100,1,['python3'],start='new')), \
             patch.object(signal,'pidfd_send_signal') as send:
            switch.send(old,signal.SIGKILL)
            send.assert_not_called()

    def test_gpu_release_can_lag_process_exit(self):
        with patch.object(switch,'processes',return_value={}), \
             patch.object(switch,'gpu_compute_pids',side_effect=[{123},set()]), \
             patch.object(time,'sleep'),contextlib.redirect_stdout(io.StringIO()):
            switch.stop_other_backends()

    def test_gui_compute_graphics_context_is_not_an_inference_job(self):
        xml='<nvidia_smi_log><gpu><processes><process_info><pid>11</pid><type>C</type></process_info><process_info><pid>12</pid><type>C+G</type></process_info><process_info><pid>13</pid><type>G</type></process_info></processes></gpu></nvidia_smi_log>'
        with patch.object(switch, 'graphics_devices', return_value=[Path('/fake')]), patch.object(subprocess,'run',return_value=subprocess.CompletedProcess([],0,xml,'')):
            self.assertEqual(switch.gpu_compute_pids(),{11})

    def test_unknown_gpu_process_blocks_new_load_without_being_killed(self):
        with patch.object(switch,'processes',return_value={}), \
             patch.object(switch,'gpu_compute_pids',return_value={123}), \
             patch.object(time,'monotonic',side_effect=[0,91]), \
             patch.object(switch,'send') as send,contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError,'No unrecognized process was killed'):
                switch.stop_other_backends()
            send.assert_not_called()

    def test_stubborn_orphan_is_killed_unrelated_process_survives(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'dsh').mkdir()
            child_pid=root/'rank.pid';script=root/'dsh/llama-router.py'
            child="import os,signal,time,pathlib; signal.signal(signal.SIGTERM,signal.SIG_IGN);pathlib.Path(%r).write_text(str(os.getpid()));time.sleep(300)" % str(child_pid)
            script.write_text('import subprocess,sys,time\nsubprocess.Popen([sys.executable,"-c",'+repr(child)+'],start_new_session=True)\ntime.sleep(300)\n')
            unrelated=subprocess.Popen([sys.executable,'-c','import time;time.sleep(300)'])
            router=subprocess.Popen([sys.executable,str(script)],start_new_session=True)
            try:
                for _ in range(100):
                    if child_pid.exists():break
                    time.sleep(.02)
                self.assertTrue(child_pid.exists())
                child_old=switch.process(int(child_pid.read_text()))
                with patch.object(switch,'gpu_compute_pids',return_value=set()),contextlib.redirect_stdout(io.StringIO()):
                    switch.stop_other_backends(root,grace=.1)
                router.wait(timeout=2)
                self.assertFalse(switch.alive(child_old))
                self.assertIsNone(unrelated.poll())
            finally:
                for proc in (router,unrelated):
                    if proc.poll() is None:proc.kill()
                    proc.wait()
                if child_pid.exists():
                    old=switch.process(int(child_pid.read_text()))
                    if old and old.state!='Z':switch.send(old,signal.SIGKILL)

    def test_concurrent_startups_are_serialized(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            code='''import sys,time,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import backend_switch as s
s.stop_other_backends=lambda *args,**kwargs:None
with s.startup_handover('llama',Path(sys.argv[2])):
 with open(sys.argv[3],'a') as f:f.write(sys.argv[4]+' start\\n');f.flush()
 time.sleep(.2)
 with open(sys.argv[3],'a') as f:f.write(sys.argv[4]+' end\\n');f.flush()
'''
            log=root/'events'
            workers=[subprocess.Popen([sys.executable,'-c',code,str(Path(switch.__file__).parent),tmp,str(log),name]) for name in ['A','B']]
            for worker in workers:self.assertEqual(worker.wait(timeout=5),0)
            rows=log.read_text().splitlines()
            self.assertEqual(rows[0].split()[0],rows[1].split()[0])
            self.assertEqual(rows[2].split()[0],rows[3].split()[0])
            self.assertNotEqual(rows[0].split()[0],rows[2].split()[0])


if __name__=='__main__':unittest.main()
