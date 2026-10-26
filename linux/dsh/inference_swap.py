"""Low-churn watch for one explicitly owned worker; never a global process guard.

Additional ceiling, not permission to relax engine no-swap cgroups, 256 MiB
watchdogs, RAM/VRAM admission, or sealed profile fingerprints. Host swap I/O is
system-wide and conservative, not worker attribution or an SSD-life guarantee.
"""
from pathlib import Path
import sys
import threading
import subprocess
from backend_switch import Process, process, send
import signal
import os
import errno
import time
import uuid


class OwnedScope:
    """A unique user cgroup, pinned by fd before the worker is released.

    Fork, reparenting and setsid cannot leave this boundary. This is ownership
    containment for cooperative inference programs, not a sandbox against a
    same-UID program deliberately asking systemd to migrate to another cgroup.
    No global process discovery or global/user-manager kill operation is used.
    """
    def __init__(self, directory, unit):
        self.directory = directory
        self.unit = unit
        self.fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            self.kill_fd = os.open('cgroup.kill', os.O_WRONLY, dir_fd=self.fd)
        except BaseException:
            os.close(self.fd)
            raise
        self.closed = False

    def populated(self):
        if self.closed:
            return False
        try:
            fd = os.open('cgroup.events', os.O_RDONLY, dir_fd=self.fd)
            with os.fdopen(fd) as stream:
                values = dict(line.split() for line in stream)
            if values.get('populated') not in ('0', '1'):
                raise RuntimeError('Invalid owned cgroup population telemetry')
            return values['populated'] == '1'
        except OSError as error:
            # A populated cgroup cannot be removed. The fd is still the old
            # inode, never a newly created/reused pathname.
            if error.errno in (errno.ENOENT, errno.ENODEV):
                return False
            raise

    def snapshot(self):
        if not self.populated():
            return {}
        selected = {}
        relative = '/' + str(self.directory.relative_to('/sys/fs/cgroup'))
        # Include any nested cgroups (engine subscopes are forbidden at launch).
        for path in (self.directory, *self.directory.rglob('*')):
            if not path.is_dir():
                continue
            try:
                pids = (path/'cgroup.procs').read_text().split()
            except FileNotFoundError:
                continue
            for value in pids:
                member = process(int(value))
                if member is None:
                    continue
                try:
                    membership = (Path('/proc')/value/'cgroup').read_text().strip()
                except FileNotFoundError:
                    continue
                # Recheck membership after the identity read; all later signals
                # also use identity-checked pidfds, never a numeric PID alone.
                if membership == '0::' + relative or membership.startswith('0::' + relative + '/'):
                    selected[member.pid] = member
        return selected

    def terminate(self):
        if self.closed:
            return
        # Graceful first pass is intentionally not the final ownership proof.
        # A TERM handler may fork and its parent may disappear during this wait.
        for member in self.snapshot().values():
            send(member, signal.SIGTERM)
        deadline = time.monotonic() + .3
        while self.populated() and time.monotonic() < deadline:
            time.sleep(.01)
        if self.populated():
            # Kernel cgroup.kill kills the entire pinned subtree atomically
            # against fork, unlike a single userspace descendant snapshot.
            try:
                os.write(self.kill_fd, b'1')
            except OSError as error:
                if error.errno not in (errno.ENOENT, errno.ENODEV):
                    raise
        deadline = time.monotonic() + 3
        while self.populated():
            if time.monotonic() >= deadline:
                raise RuntimeError('Owned cgroup still populated; shutdown unverified')
            time.sleep(.01)
        # Refresh kernel population after KILL, rather than checking only the
        # initial PID list. A still-owned rank prevents a successful return.

    def close(self):
        if not self.closed:
            if self.populated():
                raise RuntimeError('Refusing to retire a populated owned cgroup')
            os.close(self.kill_fd)
            os.close(self.fd)
            self.closed = True


def spawn_owned(args, **kwargs):
    """Start a gated command in a unique cgroup or refuse before exec.

    Preserve the existing engine-specific scope properties verbatim. Never
    nest a second systemd scope: that would move ranks out of our boundary.
    """
    command = list(args)
    properties = []
    if command and command[0] == 'systemd-run':
        prefix = ['systemd-run', '--user', '--scope', '--quiet']
        if command[:4] != prefix:
            raise RuntimeError('Unsupported owned-worker systemd scope invocation')
        command = command[4:]
        while command:
            if command[0].startswith('--property='):
                properties.append(command.pop(0))
            elif command[0] in ('-p', '--property') and len(command) >= 2:
                properties.extend((command.pop(0), command.pop(0)))
            else:
                break
        if not command or command[0].startswith('-'):
            raise RuntimeError('Unsupported owned-worker scope options')
    if not command or kwargs.get('shell') or 'executable' in kwargs or 'preexec_fn' in kwargs:
        raise RuntimeError('Unsupported owned-worker spawn; explicit argv required')
    unit = 'dsh-worker-' + uuid.uuid4().hex + '.scope'
    read_fd, write_fd = os.pipe()
    scope = proc = None
    try:
        kwargs['pass_fds'] = (*kwargs.get('pass_fds', ()), read_fd)
        proc = subprocess.Popen(['systemd-run', '--user', '--scope', '--quiet',
                                 '--unit=' + unit, *properties, sys.executable,
                                 str(Path(__file__).resolve()), '--owned-exec',
                                 str(read_fd), *command], **kwargs)
        os.close(read_fd)
        read_fd = -1
        deadline = time.monotonic() + 5
        while scope is None:
            result = subprocess.run(['systemctl', '--user', 'show', unit,
                                     '--property=ControlGroup', '--value'],
                                    capture_output=True, text=True, timeout=2)
            relative = Path(result.stdout.strip())
            prefix = Path('/user.slice')/('user-' + str(os.getuid()) + '.slice')/('user@' + str(os.getuid()) + '.service')
            if result.returncode == 0 and relative.name == unit and relative.is_relative_to(prefix):
                scope = OwnedScope(Path('/sys/fs/cgroup')/str(relative).lstrip('/'), unit)
                if not scope.populated():
                    raise RuntimeError('Owned worker scope empty before exec')
                break
            if proc.poll() is not None or time.monotonic() >= deadline:
                raise RuntimeError('Owned worker cgroup unavailable; command not released')
            time.sleep(.02)
        os.write(write_fd, b'1')
        return proc, scope
    except BaseException:
        if scope is not None:
            scope.terminate()
            scope.close()
        elif proc is not None:
            # Exact random unit only, including startup failures before its
            # cgroup path became readable. The payload gate is never released.
            subprocess.run(['systemctl', '--user', 'stop', unit],
                           capture_output=True, timeout=5)
        if proc is not None:
            proc.wait(timeout=5)
        raise
    finally:
        if read_fd >= 0:
            os.close(read_fd)
        os.close(write_fd)

HARDWARE = Path(__file__).resolve().parents[1] / 'hardware'
if str(HARDWARE) not in sys.path:
    sys.path.insert(0, str(HARDWARE))
from swap_activity import SwapActivity, read_host_activity  # pyright: ignore[reportMissingImports]
from backend_switch import processes
import importlib.util

# Isolate the sampler's root selector: here ownership is the explicit Popen
# tree, not executable-name discovery. Never change the shared hardware module
# or its ordinary managed-inference collector. All supplied entries are owned.
_spec = importlib.util.spec_from_file_location('_dsh_worker_memory', HARDWARE / 'inference_memory.py')
assert _spec is not None and _spec.loader is not None
_worker_memory = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_worker_memory)
setattr(_worker_memory, 'is_inference', lambda proc: True)


def owned_tree(owner, snapshot):
    current = snapshot.get(owner.pid)
    if current is None or current.start != owner.start:
        raise RuntimeError('Owned worker identity missing or changed')
    selected = {owner.pid}
    while True:
        children = {p.pid for p in snapshot.values() if p.parent in selected}
        if children <= selected:
            return {pid: snapshot[pid] for pid in selected}
        selected |= children


def sample_owned_memory(owner, *, snapshot=None, proc_root=Path('/proc')):
    scoped = owner.snapshot() if isinstance(owner, OwnedScope) else owned_tree(owner, processes() if snapshot is None else snapshot)
    return _worker_memory.sample_memory(snapshot=scoped, proc_root=proc_root)


def stop_owned_worker(owner):
    """Only a verified kernel ownership boundary can prove final shutdown."""
    if not isinstance(owner, OwnedScope):
        raise RuntimeError('Owned worker containment unavailable; shutdown unverified')
    owner.terminate()


class OwnedWorkerWatch:
    """Loading budget and, after actual readiness, rolling serving I/O limits.

    The llama model-server is ready before its lazy model loads: those later
    loads conservatively retain serving rate checks for this worker lifetime.
    """
    owner: Process | OwnedScope

    def __init__(self, proc, on_fault, *, host_reader=read_host_activity,
                 memory_reader, interval=.5):
        self.proc = proc
        self.on_fault = on_fault
        self.host_reader = host_reader
        self.memory_reader = memory_reader
        self.interval = interval
        self.activity = SwapActivity()
        self.phase = 'loading'
        self.fault = None
        self.done = threading.Event()
        self.lock = threading.RLock()
        self.thread = None

    def start(self):
        def run():
            while not self.done.wait(self.interval):
                self.sample()
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        return self

    def ready(self):
        with self.lock:
            self.phase = 'inference'
            self.activity.set_phase(self.phase)

    def sample(self):
        with self.lock:
            if self.done.is_set() or self.fault:
                return
            failures = []
            try:
                if self.proc.poll() is not None:
                    # Parent exit is not proof that its ranks exited. Retain
                    # ownership and fail closed through the ordinary callback.
                    raise RuntimeError('owned_parent_exit')
                reading = self.memory_reader()
                if not isinstance(reading, dict):
                    raise ValueError('missing worker telemetry')
                for key in ('swap', 'spill', 'processes'):
                    if type(reading[key]) is not int or reading[key] < 0:
                        raise ValueError('invalid worker telemetry')
                if not reading['processes']:
                    raise ValueError('no owned worker telemetry')
                self.activity.observe(self.host_reader(), self.phase, reading['swap'])
                failures.extend(self.activity.failures())
                if reading['spill']:
                    failures.append('vram_spill')
            except Exception as error:
                self.activity.observe(None, self.phase)
                failures.append('telemetry_error:' + type(error).__name__)
            if not failures:
                return
            self.fault = ', '.join(failures)
            self.done.set()
        # Never call termination under the sample lock or join this thread.
        try:
            self.on_fault(self.proc, self.fault)
        except Exception as error:
            with self.lock:
                self.fault += '; termination_error:' + type(error).__name__


class WorkerSwapGuard:
    """Router-local fault latch. Only router restart clears a low-churn fault.

    Separate lock from router lifecycle locks; callbacks never acquire those.
    stop() invalidates the generation without joining a callback thread.
    """
    def __init__(self, *, host_reader=read_host_activity,
                 memory_reader=sample_owned_memory, terminator=stop_owned_worker):
        self.host_reader = host_reader
        self.memory_reader = memory_reader
        self.terminator = terminator
        self.lock = threading.RLock()
        self.watch = None
        self.fault = None

    def check(self):
        with self.lock:
            if self.fault:
                raise RuntimeError('Low-churn guard: ' + self.fault + '; router restart required')

    def spawn(self, *args, **kwargs):
        with self.lock:
            self.check()
            if self.watch is not None:
                raise RuntimeError('Previous owned-worker watch must be stopped before switching')
            # Baseline before Popen: loading writes belong to the same budget.
            try:
                baseline = self.host_reader()
                activity = SwapActivity()
                activity.observe(baseline, 'loading')
                if activity.failures():
                    raise ValueError('invalid host baseline')
            except Exception as error:
                self.fault = 'host_telemetry_error:' + type(error).__name__
                raise RuntimeError('Low-churn guard: ' + self.fault + '; router restart required') from error
            try:
                proc, owner = spawn_owned(*args, **kwargs)
            except Exception as error:
                self.fault = 'owned_worker_containment_error:' + type(error).__name__
                raise RuntimeError('Low-churn guard: ' + self.fault + '; router restart required') from error
            watch = OwnedWorkerWatch(proc, self._violation, host_reader=self.host_reader,
                                     memory_reader=lambda: self.memory_reader(owner))
            self.watch = watch
            watch.owner = owner
            watch.activity = activity
            watch.sample()
            self.check()
            try:
                watch.start()
            except Exception as error:
                watch.done.set()
                reason = 'watch_start_error:' + type(error).__name__
                try:
                    self._violation(proc, reason)
                except Exception:
                    pass  # _violation already latched the termination failure.
                self.check()
            return proc

    def _violation(self, proc, reason):
        with self.lock:
            watch = self.watch
            if watch is None or watch.proc is not proc:
                return  # A stale callback must not kill a replacement generation.
            self.fault = reason
            try:
                self.terminator(watch.owner)
            except Exception as error:
                self.fault += '; termination_error:' + type(error).__name__
                raise
            finally:
                print('Low-churn guard: ' + self.fault +
                      '; owned-worker shutdown requested; router restart required.', flush=True)

    def ready(self, proc):
        with self.lock:
            self.check()
            if self.watch is None or self.watch.proc is not proc:
                raise RuntimeError('Owned worker changed before readiness')
            self.watch.ready()
            self.watch.sample()
            self.check()

    def stop(self, proc):
        with self.lock:
            if self.watch is not None and self.watch.proc is proc:
                # Sampling publishes the generation fault before releasing this
                # lock; retire it atomically even if its callback has not run.
                with self.watch.lock:
                    if self.watch.fault:
                        self.fault = self.fault or self.watch.fault
                    self.watch.done.set()
                    if isinstance(self.watch.owner, OwnedScope):
                        try:
                            self.watch.owner.terminate()
                            self.watch.owner.close()
                        except Exception as error:
                            self.fault = (self.fault or '') + '; termination_error:' + type(error).__name__
                            raise
                    self.watch = None


if __name__ == '__main__':
    # The payload cannot execute before the parent has pinned and checked its
    # dedicated cgroup. EOF/failed admission means exit without running it.
    if len(sys.argv) < 4 or sys.argv[1] != '--owned-exec':
        raise SystemExit('Only the owned-worker exec gate is supported')
    gate = int(sys.argv[2])
    allowed = os.read(gate, 1) == b'1'
    os.close(gate)
    if not allowed:
        raise SystemExit(125)
    os.execvpe(sys.argv[3], sys.argv[3:], os.environ)
