"""Serialize local backend launches and stop only this project's inference processes."""
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import xml.etree.ElementTree as ET
from amd_device import graphics_devices

ROOT = Path(__file__).resolve().parent.parent
KINDS = {'llama', 'sglang', 'vllm', 'strata', 'hyperqwen', 'maya'}


def python_entrypoint(args):
    """Identify the executed script/module, not paths mentioned in arbitrary arguments."""
    if not args or not Path(args[0]).name.startswith('python'):
        return None
    i = 1
    while i < len(args) and args[i] in ('-u', '-B', '-E', '-I', '-s', '-S', '-O', '-OO'):
        i += 1
    if i < len(args) and args[i] == '--':
        i += 1
    if i >= len(args):
        return None
    if args[i] == '-m' and i + 1 < len(args):
        return 'module', args[i + 1], args[i + 2:]
    if args[i].startswith('-'):
        return None
    return 'script', args[i], args[i + 1:]


@dataclass(frozen=True)
class Process:
    pid: int
    parent: int
    start: str
    args: tuple
    cwd: str
    state: str


def process(pid):
    path = Path('/proc') / str(pid)
    try:
        if path.stat().st_uid != os.getuid():
            return None
        fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
        args = tuple(a.decode(errors='replace') for a in (path / 'cmdline').read_bytes().split(b'\0') if a)
        try:
            cwd = os.readlink(path / 'cwd')
        except OSError:
            cwd = ''
        return Process(pid, int(fields[1]), fields[19], args, cwd, fields[0])
    except (OSError, ValueError, IndexError):
        return None


def processes():
    return {p.pid: p for name in Path('/proc').iterdir()
            if name.name.isdecimal() and (p := process(int(name.name))) is not None}


def is_launcher(p, root=ROOT):
    script = str(root / 'dsh/launch-backend.py')
    entry = python_entrypoint(p.args)
    return bool(entry and entry[0] == 'script' and entry[1] == script and
                entry[2] and entry[2][0] in KINDS)


def is_inference(p, root=ROOT):
    if not p.args:
        return False
    entry = python_entrypoint(p.args)
    routers = {str(root / 'dsh' / name) for name in
               ('llama-router.py', 'sglang-router.py', 'vllm-router.py', 'strata-router.py', 'maya-router.py')}
    if entry and entry[0] == 'script' and entry[1] in routers:
        return True
    binaries = {str(root / name) for name in
                ('llama.cpp/llama-server', 'llama.cpp/build/bin/llama-server',
                 'llama.cpp/build-vulkan/bin/llama-server', 'llama.cpp/build-hip/bin/llama-server',
                 'strata/engine/strata', 'strata/build-hip/strata',
                 'maya/upstream/build-hip/maya', 'maya/upstream/build-hip/maya-ds4')}
    if p.args[0] in binaries:
        return True
    if entry and entry[0] == 'script':
        if entry[1] == str(root / 'dsh/native-ui-server.py'):
            args = entry[2]
            return any(arg == '--project' and i + 1 < len(args) and args[i + 1] in ('strata', 'maya')
                       for i, arg in enumerate(args))
        # Maya is the configured Strata fork; match its exact inference entry
        # point, never every Python process in its environment.
        projects = (root / 'strata', root / 'maya/upstream')
        is_strata_server = any(entry[1] == str(project / 'serve/server.py') or (
            entry[1] == 'serve/server.py' and p.cwd == str(project)) for project in projects)
        if is_strata_server:
            args = entry[2]
            return '--engine=strata' in args or any(
                arg == '--engine' and i + 1 < len(args) and args[i + 1] == 'strata'
                for i, arg in enumerate(args))
    environments = (root / 'sglang/.venv', root / 'vllm/.venv', root / 'hyperqwen/upstream/venv',
                    root / 'sglang/.venv-rocm', root / 'vllm/.venv-rocm')
    if any(str(p.args[0]).startswith(str(env) + '/') for env in environments):
        if entry and entry[0] == 'script':
            if (p.args[0] == str(root / 'sglang/.venv-rocm/bin/python')
                    and entry[1] == str(root / 'sglang/rocm-bootstrap.py')):
                return '--model-path' in entry[2]
            if (p.args[0] == str(root / 'vllm/.venv-rocm/bin/python')
                    and entry[1] == str(root / 'vllm/rocm-bootstrap.py')):
                return bool(entry[2]) and entry[2][0] == 'serve'
        if entry and entry[0] == 'module':
            if entry[1] in ('sglang.launch_server', 'vllm.entrypoints.openai.api_server'):
                return True
            return entry[1] == 'vllm.entrypoints.cli.main' and bool(entry[2]) and entry[2][0] == 'serve'
        scripts = {str(env / 'bin/vllm') for env in environments}
        if entry and entry[0] == 'script' and entry[1] in scripts:
            return bool(entry[2]) and entry[2][0] == 'serve'
        return p.args[0] in scripts and len(p.args) > 1 and p.args[1] == 'serve'
    return False


def owned_processes(snapshot, root=ROOT, owner=None, exclude=None):
    """Find inference trees and their launcher, never unrelated Python/terminal apps."""
    selected = {p.pid for p in snapshot.values() if p.pid != exclude and is_inference(p, root)}
    if owner:
        p = snapshot.get(owner.get('pid'))
        if p and p.start == owner.get('start') and p.pid != exclude and is_launcher(p, root):
            selected.add(p.pid)
    for pid in list(selected):
        parent = snapshot[pid].parent
        seen = set()
        while parent in snapshot and parent not in seen:
            seen.add(parent)
            p = snapshot[parent]
            if parent != exclude and is_launcher(p, root):
                selected.add(parent)
                break
            parent = p.parent
    while True:
        children = {p.pid for p in snapshot.values() if p.parent in selected and p.pid != exclude}
        if children <= selected:
            break
        selected |= children
    return {pid: snapshot[pid] for pid in selected if snapshot[pid].state != 'Z'}


def alive(old):
    current = process(old.pid)
    return current is not None and current.start == old.start and current.state != 'Z'


def send(old, sig):
    # pidfd prevents a reused PID from being signalled after inspection.
    try:
        fd = os.pidfd_open(old.pid)
    except ProcessLookupError:
        return
    try:
        if alive(old):
            signal.pidfd_send_signal(fd, sig)
    except ProcessLookupError:
        pass
    finally:
        os.close(fd)


def wait_exit(owned, seconds):
    deadline = time.monotonic() + seconds
    while True:
        remaining = {pid: p for pid, p in owned.items() if alive(p)}
        if not remaining or time.monotonic() >= deadline:
            return remaining
        time.sleep(0.2)


def gpu_compute_pids():
    # An AMD-only host has no NVIDIA contexts to wait for. Owned AMD workers
    # are stopped above; each AMD launcher checks its own VRAM headroom.
    if not graphics_devices('0x10de'):
        return set()
    # --query-compute-apps also lists C+G Vulkan terminals. Those are graphics apps,
    # not our headless CUDA inference workers, and must not block their own startup.
    result = subprocess.run(['nvidia-smi', '-q', '-x'],
                            capture_output=True, text=True, timeout=10)
    if result.returncode:
        raise RuntimeError('Cannot check GPU release: ' + result.stderr.strip())
    try:
        report = ET.fromstring(result.stdout)
        return {int(p.findtext('pid')) for p in report.findall('gpu/processes/process_info')
                if p.findtext('type') == 'C' and (p.findtext('pid') or '').isdecimal()}
    except (ET.ParseError, ValueError) as error:
        raise RuntimeError('Cannot parse GPU process status') from error


def read_owner(state):
    try:
        value = json.loads(state.read_text())
        return value if isinstance(value, dict) else None
    except (OSError, ValueError):
        return None


def stop_other_backends(root=ROOT, state=None, grace=50):
    me = os.getpid()
    owner = read_owner(state) if state else None
    owned = owned_processes(processes(), root, owner, exclude=me)
    if owned:
        print('Stopping the previous local inference backend. Active replies will be interrupted.', flush=True)
        launchers = {pid: p for pid, p in owned.items() if is_launcher(p, root)}
        # Let launchers clean up their own worker groups and log monitors first.
        first = launchers or owned
        for p in first.values():
            send(p, signal.SIGTERM)
        remaining = wait_exit(owned, grace)
        # Discover any ranks created while the old backend was shutting down.
        remaining.update(owned_processes(processes(), root, owner, exclude=me))
        if remaining:
            print('Cleaning up remaining local inference workers...', flush=True)
            for p in remaining.values():
                send(p, signal.SIGTERM)
            remaining = wait_exit(remaining, 5)
        if remaining:
            for p in remaining.values():
                send(p, signal.SIGKILL)
            remaining = wait_exit(remaining, 5)
        if remaining:
            raise RuntimeError('Previous inference processes have not exited; refusing to load another model.')
    # Also catches detached ranks or unrelated CUDA jobs: do not kill unrecognized work.
    deadline = time.monotonic() + 90
    waiting = False
    while True:
        gpu = gpu_compute_pids()
        if not gpu:
            print('GPU inference memory released; starting the selected backend.', flush=True)
            return
        if not waiting:
            print('Waiting for the NVIDIA driver to release GPU compute contexts...', flush=True)
            waiting = True
        if time.monotonic() >= deadline:
            break
        time.sleep(0.5)
    raise RuntimeError('GPU compute processes still running (' + ', '.join(map(str, sorted(gpu))) +
                       '); refusing to overlap models. No unrecognized process was killed.')


class Startup:
    def __init__(self, state, kind):
        self.state, self.kind = state, kind

    def register(self):
        p = process(os.getpid())
        if p is None:
            raise RuntimeError('Cannot register inference launcher ownership')
        value = {'pid': p.pid, 'start': p.start, 'backend': self.kind}
        temp = self.state.with_suffix('.tmp')
        temp.write_text(json.dumps(value) + '\n')
        temp.chmod(0o600)
        temp.replace(self.state)


@contextmanager
def startup_handover(kind, root=ROOT, grace=50):
    state = root / 'dsh/data/backend-owner.json'
    state.parent.mkdir(parents=True, exist_ok=True)
    with (state.parent / 'backend-start.lock').open('a') as lock:
        os.fchmod(lock.fileno(), 0o600)
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        stop_other_backends(root, state, grace)
        yield Startup(state, kind)


def clear_owner(root=ROOT):
    state = root / 'dsh/data/backend-owner.json'
    owner, p = read_owner(state), process(os.getpid())
    if owner and p and owner.get('pid') == p.pid and owner.get('start') == p.start:
        state.unlink(missing_ok=True)
