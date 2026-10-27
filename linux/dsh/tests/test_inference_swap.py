"""CPU-only low-churn guard and managed-router integration regressions."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch
import os

DSH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DSH))


class OwnedWatchTests(unittest.TestCase):
    def setUp(self):
        scope=patch.dict(os.environ, {'LOCAL_LLM_SWAP_POLICY':'low-churn-v1'})
        scope.start(); self.addCleanup(scope.stop)

    def test_settled_swap_at_inclusive_policy_bounds_is_allowed(self):
        spec = importlib.util.find_spec('inference_swap')
        self.assertIsNotNone(spec, 'Owned-worker low-churn enforcement is missing')
        from inference_swap import OwnedWorkerWatch
        proc = Mock(pid=123)
        proc.poll.return_value = None
        stop = Mock()
        readings = iter([dict(timestamp=0.0, swapin_bytes=0, swapout_bytes=0,
                              available_bytes=2*1024**3, memory_full_psi_avg10=10.0),
                         dict(timestamp=30.0, swapin_bytes=210*1024**2,
                              swapout_bytes=30*1024**2,
                              available_bytes=2*1024**3, memory_full_psi_avg10=10.0)])
        watch = OwnedWorkerWatch(proc, stop, host_reader=lambda: next(readings),
                                 memory_reader=lambda: dict(swap=4*1024**3, spill=0, processes=1))
        watch.ready()
        watch.sample()
        watch.sample()
        stop.assert_not_called()
        self.assertIsNone(watch.fault)
        self.assertEqual(watch.activity.summary()['inference_window_samples'], 1)

    def make_watch(self, *, swap=0, spill=0, available=4*1024**3, psi=0,
                   memory=None, stop=None):
        from inference_swap import OwnedWorkerWatch
        proc = Mock(pid=123)
        proc.poll.return_value = None
        self.host = dict(timestamp=0.0, swapin_bytes=0, swapout_bytes=0,
                         available_bytes=available, memory_full_psi_avg10=psi)
        self.stop = stop or Mock()
        self.memory = memory or (lambda: dict(swap=swap, spill=spill, processes=1))
        self.watch = OwnedWorkerWatch(proc, self.stop,
                                      host_reader=lambda: dict(self.host), memory_reader=self.memory)
        return self.watch

    def test_worker_over_four_gib_and_any_spill_fail_closed(self):
        for values, reason in [({'swap': 4*1024**3+1}, 'worker_swap_limit'),
                               ({'spill': 1}, 'vram_spill')]:
            with self.subTest(reason=reason):
                watch = self.make_watch(**values)
                watch.sample()
                self.assertIn(reason, watch.fault or '')
                self.stop.assert_called_once_with(watch.proc, watch.fault)
                watch.sample()
                self.stop.assert_called_once()

    def test_loading_cumulative_write_budget_is_not_reset_by_ready(self):
        watch = self.make_watch()
        watch.sample()
        self.host.update(timestamp=1.0, swapout_bytes=4*1024**3)
        watch.sample()
        self.stop.assert_not_called()
        watch.ready()
        self.host.update(timestamp=2.0, swapout_bytes=4*1024**3+1)
        watch.sample()
        self.assertIn('swapout_budget', watch.fault or '')

    def test_loading_write_budget_stops_before_ready(self):
        watch = self.make_watch()
        watch.sample()
        self.host.update(timestamp=1.0, swapout_bytes=4*1024**3+1)
        watch.sample()
        self.assertIn('swapout_budget', watch.fault or '')
        self.stop.assert_called_once()

    def test_serving_write_rate_and_total_io_fail(self):
        for out, incoming, reason in [(30*1024**2+1, 0, 'inference_swapout_rate'),
                                      (0, 240*1024**2+1, 'inference_swap_io_rate')]:
            with self.subTest(reason=reason):
                watch = self.make_watch()
                watch.ready()
                watch.sample()
                self.host.update(timestamp=30.0, swapout_bytes=out, swapin_bytes=incoming)
                watch.sample()
                self.assertIn(reason, watch.fault or '')

    def test_rates_begin_only_at_readiness_without_discarding_loading_budget(self):
        watch = self.make_watch()
        watch.sample()
        self.host.update(timestamp=40.0, swapout_bytes=1024**3)
        watch.sample()
        self.stop.assert_not_called()
        watch.ready()
        self.host.update(timestamp=41.0)
        watch.sample()
        self.host.update(timestamp=71.0)
        watch.sample()
        self.stop.assert_not_called()
        self.assertEqual(watch.activity.summary()['total_swapout_bytes'], 1024**3)
        self.assertEqual(watch.activity.summary()['inference_window_samples'], 1)

    def test_pressure_requires_three_consecutive_samples(self):
        for values, reason in [({'available': 2*1024**3-1}, 'low_host_memory'),
                               ({'psi': 10.01}, 'memory_full_psi')]:
            with self.subTest(reason=reason):
                watch = self.make_watch(**values)
                for stamp in (0.0, 1.0):
                    self.host['timestamp'] = stamp
                    watch.sample()
                self.stop.assert_not_called()
                self.host['timestamp'] = 2.0
                watch.sample()
                self.assertIn(reason, watch.fault or '')

    def test_background_poll_failure_latches_and_requests_owned_stop(self):
        import threading
        watch = self.make_watch()
        called = threading.Event()
        watch.proc.poll.side_effect = OSError('poll failed')
        watch.on_fault = lambda proc, reason: called.set()
        watch.interval = .001
        watch.start()
        assert watch.thread is not None
        self.assertTrue(called.wait(1), 'Poll errors must not silently kill the watch thread')
        watch.thread.join(timeout=1)
        self.assertIn('telemetry', watch.fault or '')

    def test_missing_and_invalid_worker_telemetry_stop(self):
        for reading in (None, {}, dict(swap=0, spill=0, processes=0),
                        dict(swap=-1, spill=0, processes=1),
                        dict(swap=0, spill=-1, processes=1)):
            with self.subTest(reading=reading):
                watch = self.make_watch(memory=lambda: reading)
                watch.sample()
                self.assertIsNotNone(watch.fault)
                self.stop.assert_called_once()

    def test_sampler_exception_and_termination_exception_are_latched(self):
        for source in ('host_reader', 'memory_reader'):
            with self.subTest(source=source):
                watch = self.make_watch(stop=Mock(side_effect=OSError('termination failed')))
                setattr(watch, source, Mock(side_effect=OSError('sampler failed')))
                watch.sample()
                self.assertIn('telemetry', watch.fault or '')
                self.assertIn('termination', watch.fault or '')
                self.assertTrue(watch.done.is_set())
                watch.sample()
                self.stop.assert_called_once()


class OwnershipTests(unittest.TestCase):
    def test_sampler_includes_only_supplied_root_and_descendants_even_if_unrecognized(self):
        import inference_swap as swap
        from backend_switch import Process
        import tempfile
        root = Process(123, 1, '100', ('systemd-run',), '', 'S')
        child = Process(124, 123, '101', ('python',), '', 'S')
        unrelated = Process(200, 1, '200', (str(DSH.parent/'llama.cpp/llama-server'),), '', 'S')
        hub = Process(201, 1, '201', ('python', str(DSH/'model_hub.py')), '', 'S')
        snapshot = {p.pid:p for p in (root, child, unrelated, hub)}
        with tempfile.TemporaryDirectory() as tmp:
            proc_root = Path(tmp)
            for proc in snapshot.values():
                base = proc_root/str(proc.pid)
                (base/'fdinfo').mkdir(parents=True)
                (base/'status').write_text('VmSwap: 1024 kB\n')
            self.assertTrue(hasattr(swap, 'sample_owned_memory'), 'Scoped memory adapter missing')
            result = swap.sample_owned_memory(root, snapshot=snapshot, proc_root=proc_root)
            self.assertEqual(result, dict(swap=2*1024**2, spill=0, processes=2))
            reused = dict(snapshot, **{})
            from dataclasses import replace
            reused[123] = replace(root, start='999')
            with self.assertRaises(RuntimeError):
                swap.sample_owned_memory(root, snapshot=reused, proc_root=proc_root)


class LifecycleTests(unittest.TestCase):
    def test_detected_fault_latches_when_stop_wins_callback_race(self):
        import inference_swap as swap
        import threading
        from backend_switch import Process
        from unittest.mock import patch
        proc = Mock(pid=123)
        proc.poll.return_value = None
        owner = Process(123, 1, '100', ('worker',), '', 'S')
        host = dict(timestamp=0.0, swapin_bytes=0, swapout_bytes=0,
                    available_bytes=4*1024**3, memory_full_psi_avg10=0.0)
        memory = Mock(return_value=dict(swap=0, spill=0, processes=1))
        terminator = Mock()
        def host_reader():
            host['timestamp'] += 1.0
            return dict(host)
        guard = swap.WorkerSwapGuard(host_reader=host_reader,
                                    memory_reader=memory, terminator=terminator)
        detected, release = threading.Event(), threading.Event()
        with patch.object(swap, 'spawn_owned', side_effect=lambda *a, **kw: (swap.subprocess.Popen(*a, **kw), owner)), \
             patch.object(swap.subprocess, 'Popen', return_value=proc) as spawn, \
             patch.object(swap.OwnedWorkerWatch, 'start', lambda self: self):
            guard.spawn(['owned'])
            watch = guard.watch
            assert watch is not None
            def blocked_callback(proc, reason):
                detected.set()
                self.assertTrue(release.wait(2))
                guard._violation(proc, reason)
            watch.on_fault = blocked_callback
            memory.return_value = dict(swap=0, spill=1, processes=1)
            sampler = threading.Thread(target=watch.sample)
            sampler.start()
            self.assertTrue(detected.wait(2))
            try:
                guard.stop(proc)
                with self.assertRaisesRegex(RuntimeError, 'vram_spill'):
                    guard.spawn(['replacement'])
                spawn.assert_called_once()
            finally:
                release.set()
                sampler.join(2)
            self.assertFalse(sampler.is_alive())
            self.assertIn('vram_spill', guard.fault or '')
            terminator.assert_not_called()  # Retired callback cannot act on a new generation.

    def test_default_termination_refuses_uncontained_or_reused_pid_without_signals(self):
        import inference_swap as swap
        from backend_switch import Process
        from unittest.mock import patch
        from dataclasses import replace
        owner = Process(123, 1, '100', ('worker',), '', 'S')
        for current in (owner, replace(owner, start='999')):
            with patch.object(swap, 'processes', return_value={123: current}), \
                 patch.object(swap, 'send') as send:
                with self.assertRaisesRegex(RuntimeError, 'containment unavailable'):
                    swap.stop_owned_worker(owner)
                send.assert_not_called()

    def test_switch_cleanup_rejects_stale_callback_without_self_join(self):
        import inference_swap as swap
        from backend_switch import Process
        from unittest.mock import patch
        owner = Process(123, 1, '100', ('worker',), '', 'S')
        proc, replacement = Mock(pid=123), Mock(pid=124)
        proc.poll.return_value = replacement.poll.return_value = None
        stamp = iter(float(x) for x in range(20))
        def host():
            return dict(timestamp=next(stamp), swapin_bytes=0, swapout_bytes=0,
                        available_bytes=4*1024**3, memory_full_psi_avg10=0.0)
        stop = Mock()
        guard = swap.WorkerSwapGuard(host_reader=host,
            memory_reader=lambda owner: dict(swap=0, spill=0, processes=1), terminator=stop)
        with patch.object(swap, 'spawn_owned', side_effect=lambda *a, **kw: (swap.subprocess.Popen(*a, **kw), owner)), \
             patch.object(swap.subprocess, 'Popen', side_effect=[proc, replacement]), \
             patch.object(swap.OwnedWorkerWatch, 'start', lambda self: self):
            guard.spawn(['one'])
            old = guard.watch
            assert old is not None
            guard.stop(proc)
            self.assertTrue(old.done.is_set())
            guard.spawn(['two'])
            guard._violation(proc, 'late old callback')
            self.assertIsNone(guard.fault)
            assert guard.watch is not None
            self.assertIs(guard.watch.proc, replacement)
            stop.assert_not_called()
            # Callback is permitted to stop its own watch; stop() never joins.
            guard.terminator = lambda owner: guard.stop(replacement)
            guard._violation(replacement, 'new breach')
            self.assertIn('new breach', guard.fault or '')
            self.assertIsNone(guard.watch)

    def test_host_baseline_failure_latches_before_spawn(self):
        import inference_swap as swap
        from unittest.mock import patch
        guard = swap.WorkerSwapGuard(host_reader=Mock(side_effect=OSError('unreadable')))
        with patch.object(swap.subprocess, 'Popen') as spawn:
            with self.assertRaises(RuntimeError):
                guard.spawn(['never-start'])
            self.assertIn('telemetry', guard.fault or '')
            guard.host_reader = Mock(return_value={})
            with self.assertRaises(RuntimeError):
                guard.spawn(['still-blocked'])
            spawn.assert_not_called()

    def test_thread_start_failure_stops_owned_worker_and_latches(self):
        import inference_swap as swap
        from backend_switch import Process
        from unittest.mock import patch
        owner = Process(123, 1, '100', ('worker',), '', 'S')
        proc = Mock(pid=123)
        proc.poll.return_value = None
        stamp = iter(float(x) for x in range(10))
        def host():
            return dict(timestamp=next(stamp), swapin_bytes=0, swapout_bytes=0,
                        available_bytes=4*1024**3, memory_full_psi_avg10=0.0)
        stop = Mock(side_effect=OSError('signal denied'))
        guard = swap.WorkerSwapGuard(host_reader=host,
            memory_reader=lambda owner: dict(swap=0, spill=0, processes=1), terminator=stop)
        with patch.object(swap, 'spawn_owned', side_effect=lambda *a, **kw: (swap.subprocess.Popen(*a, **kw), owner)), \
             patch.object(swap.subprocess, 'Popen', return_value=proc), \
             patch.object(swap.OwnedWorkerWatch, 'start', side_effect=RuntimeError('thread unavailable')):
            with self.assertRaises(RuntimeError):
                guard.spawn(['owned-worker'])
            stop.assert_called_once_with(owner)
            self.assertIn('watch_start', guard.fault or '')
            self.assertIn('termination', guard.fault or '')
            with self.assertRaises(RuntimeError):
                guard.check()

    def test_real_cpu_owned_worker_is_guard_stopped_unrelated_child_survives(self):
        import inference_swap as swap
        import subprocess
        import time
        unrelated = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
        self.addCleanup(lambda: (unrelated.terminate(), unrelated.wait()))
        # Actual /proc memory and pidfd termination; no model/GPU/service startup.
        guard = swap.WorkerSwapGuard()
        proc = guard.spawn([sys.executable, '-c', 'import time; time.sleep(60)'],
                           start_new_session=True)
        self.addCleanup(lambda: (guard.stop(proc), proc.kill() if proc.poll() is None else None, proc.wait()))
        watch = guard.watch
        watch.interval = .01
        guard.ready(proc)
        watch.host_reader = Mock(side_effect=OSError('lost telemetry'))
        deadline = time.monotonic()+5
        while proc.poll() is None and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertIsNotNone(proc.poll())
        self.assertIsNone(unrelated.poll())
        self.assertIn('telemetry', guard.fault or '')
        watch.thread.join(timeout=2)
        self.assertFalse(watch.thread.is_alive())
        with self.assertRaises(RuntimeError):
            guard.check()

    def test_spawn_watch_latches_fault_and_refuses_implicit_reload(self):
        import inference_swap as swap
        from backend_switch import Process
        from unittest.mock import patch
        self.assertTrue(hasattr(swap, 'WorkerSwapGuard'), 'Router lifecycle guard missing')
        owner = Process(123, 1, '100', ('worker',), '', 'S')
        proc = Mock(pid=123)
        proc.poll.return_value = None
        host = dict(timestamp=0.0, swapin_bytes=0, swapout_bytes=0,
                    available_bytes=4*1024**3, memory_full_psi_avg10=0.0)
        stop = Mock()
        memory = Mock(return_value=dict(swap=0, spill=0, processes=1))
        def host_reader():
            host['timestamp'] += .1
            return dict(host)
        guard = swap.WorkerSwapGuard(host_reader=host_reader, memory_reader=memory,
                                    terminator=stop)
        with patch.object(swap, 'spawn_owned', side_effect=lambda *a, **kw: (swap.subprocess.Popen(*a, **kw), owner)), \
             patch.object(swap.subprocess, 'Popen', return_value=proc) as spawn, \
             patch.object(swap.OwnedWorkerWatch, 'start', lambda self: self):
            host['timestamp'] = 1.0
            self.assertIs(guard.spawn(['owned-worker']), proc)
            watch = guard.watch
            assert watch is not None
            self.assertEqual(watch.phase, 'loading')
            guard.ready(proc)
            self.assertEqual(watch.phase, 'inference')
            memory.return_value = dict(swap=0, spill=1, processes=1)
            host['timestamp'] = 2.0
            watch.sample()
            stop.assert_called_once()
            self.assertIn('vram_spill', guard.fault or '')
            guard.stop(proc)
            self.assertTrue(watch.done.is_set())
            with self.assertRaises(RuntimeError):
                guard.spawn(['replacement'])
            spawn.assert_called_once()


class ContainmentTests(unittest.TestCase):
    def cpu_worker(self, tmp, body):
        import inference_swap as swap
        from unittest.mock import patch
        script = Path(tmp)/'worker.py'
        script.write_text(body)
        guard = swap.WorkerSwapGuard()
        # Drive each sample deterministically, rather than racing the sampler.
        with patch.object(swap.OwnedWorkerWatch, 'start', lambda self: self):
            proc = guard.spawn([sys.executable, str(script), tmp], start_new_session=True)
        self.addCleanup(self.cleanup_worker, guard, proc, Path(tmp))
        return guard, proc

    def cleanup_worker(self, guard, proc, directory):
        import signal
        from backend_switch import process, send
        # Explicit identities from this test only; never broad process cleanup.
        for name in ('child', 'forked'):
            path = directory/name
            if path.exists():
                pid, start = path.read_text().split()
                member = process(int(pid))
                if member is not None and member.start == start:
                    send(member, signal.SIGKILL)
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=5)
        guard.stop(proc)

    def wait_for(self, predicate, description):
        import time
        deadline = time.monotonic()+5
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(.01)
        self.fail(description)

    def live_child(self, path):
        from backend_switch import process
        pid, start = path.read_text().split()
        current = process(int(pid))
        return current is not None and current.start == start and current.state != 'Z'

    def test_unsupported_cgroup_kill_refuses_before_payload_exec_and_latches(self):
        import inference_swap as swap
        import tempfile
        import subprocess
        import uuid
        from unittest.mock import patch
        tmp = self.enterContext(tempfile.TemporaryDirectory())
        marker = Path(tmp)/'must-not-run'
        token = uuid.uuid4()
        unit = 'dsh-worker-' + token.hex + '.scope'
        original_open = swap.os.open
        def unsupported(path, *args, **kwargs):
            if path == 'cgroup.kill':
                raise PermissionError('CPU fixture: cgroup.kill unavailable')
            return original_open(path, *args, **kwargs)
        guard = swap.WorkerSwapGuard()
        with patch.object(swap.os, 'open', unsupported), \
             patch.object(swap.uuid, 'uuid4', return_value=token):
            with self.assertRaisesRegex(RuntimeError, 'containment_error'):
                guard.spawn([sys.executable, '-c',
                             'from pathlib import Path; Path(__import__("sys").argv[1]).touch()',
                             str(marker)], start_new_session=True)
        self.assertFalse(marker.exists(), 'Unsupported containment still executed payload')
        with self.assertRaisesRegex(RuntimeError, 'router restart required'):
            guard.check()
        state = subprocess.run(['systemctl', '--user', 'show', unit,
                                '--property=ActiveState', '--value'],
                               capture_output=True, text=True, timeout=5)
        self.assertEqual(state.stdout.strip(), 'inactive', state.stderr)

    def test_populated_boundary_cannot_report_verified_shutdown_or_retire(self):
        import inference_swap as swap
        from unittest.mock import patch
        scope = object.__new__(swap.OwnedScope)
        scope.closed = False
        scope.kill_fd = -1
        with patch.object(scope, 'snapshot', return_value={}), \
             patch.object(scope, 'populated', return_value=True), \
             patch.object(swap.time, 'monotonic', side_effect=[0, 1, 1, 5]), \
             patch.object(swap.os, 'write') as kill:
            with self.assertRaisesRegex(RuntimeError, 'shutdown unverified'):
                scope.terminate()
            kill.assert_called_once_with(-1, b'1')
            with self.assertRaisesRegex(RuntimeError, 'populated'):
                scope.close()
            self.assertFalse(scope.closed)

    def test_scope_keeps_stricter_properties_without_nested_scope(self):
        import inference_swap as swap
        proc, scope = swap.spawn_owned(['systemd-run', '--user', '--scope', '--quiet',
                                      '-p', 'MemoryMax=64M', '--property=MemorySwapMax=0',
                                      '/usr/bin/sleep', '60'], start_new_session=True,
                                      expected_memory_limits={'memory.max':64*1024**2, 'memory.swap.max':0})
        try:
            self.assertEqual((scope.directory/'memory.max').read_text().strip(), str(64*1024**2))
            self.assertEqual((scope.directory/'memory.swap.max').read_text().strip(), '0')
            self.assertTrue(scope.populated())
        finally:
            scope.terminate()
            proc.wait(timeout=5)
            self.assertFalse(scope.populated())
            scope.close()

    def test_required_limit_mismatch_never_releases_payload(self):
        import inference_swap as swap
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp)/'must-not-run'
            with self.assertRaisesRegex(RuntimeError, 'differs from the required limit'):
                swap.spawn_owned(['systemd-run', '--user', '--scope', '--quiet',
                    '--property=MemoryMax=64M', '--property=MemorySwapMax=0',
                    sys.executable, '-c', 'from pathlib import Path; import sys; Path(sys.argv[1]).touch()',
                    str(marker)], start_new_session=True,
                    expected_memory_limits={'memory.max':128*1024**2, 'memory.swap.max':0})
            self.assertFalse(marker.exists(), 'A mismatched worker limit still executed the payload')

    def test_gate_accepts_explicit_command_without_arguments(self):
        import inference_swap as swap
        proc, scope = swap.spawn_owned(['/usr/bin/true'], start_new_session=True)
        try:
            self.assertEqual(proc.wait(timeout=5), 0)
        finally:
            scope.terminate()
            scope.close()

    def test_parent_exit_does_not_abandon_detached_cpu_child(self):
        import inference_swap as swap
        import tempfile
        tmp = self.enterContext(tempfile.TemporaryDirectory())
        with self.subTest():
            directory = Path(tmp)
            guard, proc = self.cpu_worker(tmp, '''import os, sys, time
from pathlib import Path
root = Path(sys.argv[1])
if os.fork() == 0:
    os.setsid()
    start = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]
    (root/'child').write_text(str(os.getpid())+' '+start)
    while True: time.sleep(.01)
while not (root/'exit').exists(): time.sleep(.01)
os._exit(0)
''')
            self.wait_for(lambda: (directory/'child').exists(), 'CPU child never started')
            self.assertTrue(self.live_child(directory/'child'))
            watch = guard.watch
            assert watch is not None
            scope = watch.owner
            (directory/'exit').touch()
            assert isinstance(scope, swap.OwnedScope)
            proc.wait(timeout=5)
            child_pid = int((directory/'child').read_text().split()[0])
            self.assertIn(child_pid, scope.snapshot(), 'Reparented child lost from owned telemetry')
            watch.sample()
            self.assertIsNotNone(guard.fault, 'Parent exit silently disabled enforcement')
            self.wait_for(lambda: not self.live_child(directory/'child'), 'Owned orphan survived guard shutdown')
            self.assertFalse(scope.populated())
            print('CPU parent-exit cleanup verified; populated=0:', (directory/'child').read_text())

    def test_termination_catches_cpu_child_forked_by_term_handler(self):
        import tempfile
        import inference_swap as swap
        tmp = self.enterContext(tempfile.TemporaryDirectory())
        with self.subTest():
            directory = Path(tmp)
            guard, proc = self.cpu_worker(tmp, '''import os, signal, sys, time
from pathlib import Path
root = Path(sys.argv[1])
def term(sig, frame):
    if os.fork() == 0:
        os.setsid()
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        start = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]
        (root/'forked').write_text(str(os.getpid())+' '+start)
        while True: time.sleep(.01)
    while not (root/'forked').exists(): time.sleep(.01)
    os._exit(0)
signal.signal(signal.SIGTERM, term)
(root/'ready').touch()
while True: time.sleep(.01)
''')
            self.wait_for(lambda: (directory/'ready').exists(), 'TERM fixture never ready')
            watch = guard.watch
            assert watch is not None
            scope = watch.owner
            swap.stop_owned_worker(scope)
            assert isinstance(scope, swap.OwnedScope)
            proc.wait(timeout=5)
            self.assertTrue((directory/'forked').exists(), 'TERM handler did not exercise fork race')
            self.assertFalse(self.live_child(directory/'forked'), 'Shutdown returned verified while a new owned rank survived')
            self.assertFalse(scope.populated())
            print('CPU fork-during-TERM cleanup verified; populated=0:', (directory/'forked').read_text())


class RouterIntegrationTests(unittest.TestCase):
    def load_router(self, name):
        from unittest.mock import patch
        spec = importlib.util.spec_from_file_location('swap_test_' + name, DSH/(name+'-router.py'))
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        read_text = Path.read_text

        def fixture_config(path, *args, **kwargs):
            # Installed launcher roots are host-specific; load the real checkout
            # catalogs for this CPU-only test, including sanitized public copies.
            if path.name in ('vllm-profiles.json', 'sglang-profiles.json'):
                path = DSH / path.name
            return read_text(path, *args, **kwargs)

        with patch.object(Path, 'read_text', fixture_config):
            spec.loader.exec_module(module)
        return module

    def assert_stop_only_reaps_parent(self, already_reaped):
        from contextlib import ExitStack
        import io
        from unittest.mock import patch
        for name in ('vllm', 'sglang'):
            with self.subTest(router=name), ExitStack() as stack:
                module = self.load_router(name)
                proc = Mock(pid=123)
                proc.returncode = 0 if already_reaped else None
                proc.poll.return_value = proc.returncode
                proc.wait.return_value = 0
                log = io.StringIO()
                for key, value in (('worker', proc), ('active', 'model'), ('logfile', log)):
                    setattr(module, key, value)
                setattr(module, 'swap_guard', Mock())
                events = []

                def verified_stop(process):
                    self.assertIs(process, proc)
                    self.assertIs(module.worker, proc)
                    events.append('verified-empty-cgroup')
                    proc.returncode = 0

                def reap(timeout=None):
                    self.assertEqual(events[0], 'verified-empty-cgroup')
                    events.append('reaped-parent')
                    return 0

                module.swap_guard.stop.side_effect = verified_stop
                proc.wait.side_effect = reap
                killpg = stack.enter_context(patch.object(module.os, 'killpg'))
                kill = stack.enter_context(patch.object(module.os, 'kill'))
                module.stop_worker()
                killpg.assert_not_called()
                kill.assert_not_called()
                proc.terminate.assert_not_called()
                proc.kill.assert_not_called()
                proc.send_signal.assert_not_called()
                proc.wait.assert_called_once_with(timeout=20)
                module.swap_guard.stop.assert_called_once_with(proc)
                self.assertEqual(events, ['verified-empty-cgroup', 'reaped-parent'])
                self.assertIsNone(module.worker)
                self.assertIsNone(module.active)
                self.assertIsNone(module.logfile)
                self.assertTrue(log.closed)

    def test_router_stop_only_reaps_running_parent_after_verified_cleanup(self):
        self.assert_stop_only_reaps_parent(already_reaped=False)

    def test_router_stop_only_reaps_already_reaped_parent_after_verified_cleanup(self):
        self.assert_stop_only_reaps_parent(already_reaped=True)

    def test_router_stop_cleanup_failure_preserves_worker_without_signal_fallback(self):
        import io
        from unittest.mock import patch
        for name in ('vllm', 'sglang'):
            with self.subTest(router=name):
                module = self.load_router(name)
                proc = Mock(pid=123)
                log = io.StringIO()
                self.addCleanup(log.close)
                for key, value in (('worker', proc), ('active', 'model'), ('logfile', log)):
                    setattr(module, key, value)
                setattr(module, 'swap_guard', Mock())
                failure = RuntimeError('Owned cgroup still populated; shutdown unverified')
                module.swap_guard.stop.side_effect = failure
                with patch.object(module.os, 'killpg') as killpg, \
                     patch.object(module.os, 'kill') as kill:
                    with self.assertRaises(RuntimeError) as raised:
                        module.stop_worker()
                    self.assertIs(raised.exception, failure)
                    killpg.assert_not_called()
                    kill.assert_not_called()
                module.swap_guard.stop.assert_called_once_with(proc)
                self.assertEqual(proc.mock_calls, [])
                self.assertIs(module.worker, proc)
                self.assertEqual(module.active, 'model')
                self.assertIs(module.logfile, log)
                self.assertFalse(log.closed)

    def test_router_stop_reap_timeout_preserves_worker_without_signal_fallback(self):
        import io
        import subprocess
        from unittest.mock import patch
        for name in ('vllm', 'sglang'):
            with self.subTest(router=name):
                module = self.load_router(name)
                proc = Mock(pid=123)
                log = io.StringIO()
                self.addCleanup(log.close)
                for key, value in (('worker', proc), ('active', 'model'), ('logfile', log)):
                    setattr(module, key, value)
                setattr(module, 'swap_guard', Mock())
                failure = subprocess.TimeoutExpired('owned-worker-parent', 20)
                proc.wait.side_effect = failure
                with patch.object(module.os, 'killpg') as killpg, \
                     patch.object(module.os, 'kill') as kill:
                    with self.assertRaises(subprocess.TimeoutExpired) as raised:
                        module.stop_worker()
                    self.assertIs(raised.exception, failure)
                    killpg.assert_not_called()
                    kill.assert_not_called()
                module.swap_guard.stop.assert_called_once_with(proc)
                proc.wait.assert_called_once_with(timeout=20)
                proc.terminate.assert_not_called()
                proc.kill.assert_not_called()
                proc.send_signal.assert_not_called()
                self.assertIs(module.worker, proc)
                self.assertEqual(module.active, 'model')
                self.assertIs(module.logfile, log)
                self.assertFalse(log.closed)

    def test_all_five_routers_guard_spawn_readiness_stop_and_latched_reentry(self):
        from contextlib import ExitStack
        import io
        import json
        from unittest.mock import patch
        for name in ('llama', 'vllm', 'sglang', 'strata', 'maya'):
            with self.subTest(router=name), ExitStack() as stack:
                module = self.load_router(name)
                self.assertTrue(hasattr(module, 'swap_guard'), name + ' lacks runtime swap enforcement')
                guard = Mock()
                module.swap_guard = guard
                proc = Mock(pid=123)
                proc.poll.return_value = None
                guard.spawn.return_value = proc
                stack.enter_context(patch.object(module.subprocess, 'Popen', side_effect=AssertionError('unguarded spawn')))
                stack.enter_context(patch.object(Path, 'open', return_value=Mock()))
                stack.enter_context(patch.object(module.os, 'killpg'))
                stack.enter_context(patch.object(module.time, 'sleep'))
                if name == 'llama':
                    module.require_amd_headroom = Mock()
                    module.runtime_identity = Mock(return_value=('hip-amd','/fake/source','a'*40))
                    module.watch_worker = Mock(return_value=Mock())
                    module.call = Mock(return_value={'status':'ok'})
                    ensure = lambda: module.activate_native.__wrapped__('hip-amd',
                        (Path('/fake/binary'), Path('/fake/preset'), {}, ['model']))
                    stop = lambda: module.stop_process(module.native)
                else:
                    model = next(iter(module.PROFILES))
                    cfg = module.PROFILES[model]
                    ensure = lambda: module.ensure_worker.__wrapped__(model)
                    stop = module.stop_worker
                    if name in ('vllm', 'sglang'):
                        module.require_rocm_headroom = Mock()
                        module.get_worker = Mock(return_value={'data':[{'max_model_len':cfg['context']}],
                                                               'max_total_num_tokens':cfg['context']})
                        if name == 'vllm':
                            module.ensure_vllm_models = Mock()
                            socket = stack.enter_context(patch.object(module.socket, 'socket'))
                            socket.return_value.__enter__.return_value.connect_ex.return_value = 1
                    else:
                        stack.enter_context(patch('hardware_guard.require_strata'))
                        if name == 'maya':
                            module.require_maya = Mock()
                        module.vram_snapshot = Mock(return_value=[{'free':8*1024**3}]*2)
                        health = {'loaded':True, 'unloaded':False, 'model':model, 'max_context':cfg['context']}
                        response = Mock()
                        response.__enter__ = Mock(side_effect=lambda: io.StringIO(json.dumps(health)))
                        response.__exit__ = Mock(return_value=False)
                        stack.enter_context(patch.object(module.urllib.request, 'urlopen', return_value=response))
                ensure()
                guard.check.assert_called()
                guard.spawn.assert_called_once()
                guard.ready.assert_called_once_with(proc, phase='idle')
                self.assertIs(module.native if name == 'llama' else module.worker, proc)
                guard.check.side_effect = RuntimeError('latched guard fault')
                with self.assertRaisesRegex(RuntimeError, 'latched guard fault'):
                    ensure()
                guard.spawn.assert_called_once()  # No implicit reload, including fast reuse.
                stop()
                guard.stop.assert_called_with(proc)


if __name__ == '__main__':
    unittest.main()
