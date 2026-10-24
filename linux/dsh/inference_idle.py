"""Ten-minute idle shutdown for managed inference only; never system-wide cleanup."""
from contextlib import contextmanager
import fcntl
from functools import wraps
import json
import math
import os
from pathlib import Path
import subprocess
import threading
import time
import urllib.parse
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 600
PORTS = {'llama': (8080, 8081), 'sglang': (30000, 30001),
         'vllm': (30010, 30011), 'strata': (30020, 30021), 'maya': (30030, 30032)}
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
INFERENCE_POSTS = {'/v1/chat/completions', '/v1/completions', '/v1/messages',
                   '/v1/responses', '/completion', '/completions', '/chat/completions',
                   '/generate', '/infill', '/embedding', '/embeddings', '/v1/embeddings',
                   '/rerank', '/v1/rerank', '/models/load', '/models/unload', '/managed/models/load'}


class Activity:
    def __init__(self, directory=None, clock=time.monotonic):
        self.directory = Path(directory) if directory else ROOT / 'dsh/data/inference-idle'
        self.clock = clock

    def file(self, name):
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        file = (self.directory / name).open('a+')
        os.fchmod(file.fileno(), 0o600)
        return file

    def touch(self):
        with self.file('timestamp') as file:
            fcntl.flock(file, fcntl.LOCK_EX)
            file.seek(0); file.truncate()
            file.write(str(self.clock())); file.flush()

    def elapsed(self):
        with self.file('timestamp') as file:
            fcntl.flock(file, fcntl.LOCK_SH)
            file.seek(0)
            try:
                value = float(file.read())
                elapsed = self.clock() - value
                return elapsed if math.isfinite(elapsed) and elapsed >= 0 else 0
            except ValueError:
                return 0

    @contextmanager
    def request(self):
        with self.file('requests.lock') as file:
            fcntl.flock(file, fcntl.LOCK_SH)
            self.touch()
            try:
                yield
            finally:
                self.touch()

    @contextmanager
    def idle_guard(self, timeout=TIMEOUT):
        with self.file('requests.lock') as file:
            try:
                fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                yield False
                return
            yield self.elapsed() >= timeout


activity = Activity()


def inference_request(function):
    @wraps(function)
    def tracked(*args, **kwargs):
        if function.__name__ == 'do_POST':
            path = urllib.parse.urlsplit(args[0].path).path.rstrip('/')
            if path not in INFERENCE_POSTS:
                return function(*args, **kwargs)
        with activity.request():
            return function(*args, **kwargs)
    return tracked


def read_json(port, path, headers=None):
    request = urllib.request.Request(f'http://127.0.0.1:{port}{path}', headers=headers or {})
    with OPENER.open(request, timeout=3) as response:
        return json.load(response)


def engine_busy(kind):
    """Read native queue/slot state without loading a model. Unknown => exception."""
    public, native = PORTS[kind]
    managed = read_json(public, '/health')
    if kind in ('vllm', 'sglang'):
        if not managed.get('active_model'):
            return False
        names = (('vllm:num_requests_running', 'vllm:num_requests_waiting') if kind == 'vllm'
                 else ('sglang:num_running_reqs', 'sglang:num_queue_reqs'))
        found = {name: [] for name in names}
        with OPENER.open(f'http://127.0.0.1:{native}/metrics', timeout=3) as response:
            for line in response.read().decode().splitlines():
                if not line or line.startswith('#'):
                    continue
                key = line.split('{', 1)[0].split(' ', 1)[0]
                if key in found:
                    value = float(line.rsplit(' ', 1)[1])
                    if not math.isfinite(value) or value < 0:
                        raise ValueError('Invalid inference queue metric')
                    found[key].append(value)
        if not all(found.values()):
            raise ValueError('Inference queue metrics unavailable')
        return any(value > 0 for values in found.values() for value in values)
    if kind == 'llama':
        models = read_json(native, '/v1/models')['data']
        for model in models:
            status = model.get('status', {}).get('value')
            if status not in ('loaded', 'unloaded', 'loading', 'unloading'):
                raise ValueError('Unknown model loading state')
            if status in ('loading', 'unloading'):
                return True
            if status != 'loaded':
                continue
            query = urllib.parse.urlencode({'model': model['id'], 'autoload': 'false'})
            slots = read_json(native, '/slots?' + query)
            if not isinstance(slots, list) or not slots:
                raise ValueError('Inference slots unavailable')
            if any(type(slot.get('is_processing')) is not bool for slot in slots):
                raise ValueError('Unknown inference slot state')
            if any(slot['is_processing'] for slot in slots):
                return True
        return False
    model = managed.get('active_model')
    if not model:
        return False
    profiles = json.loads((ROOT / 'dsh' / (kind + '-profiles.json')).read_text())
    config = json.loads((ROOT / 'dsh' / profiles[model]['config']).read_text())
    keys = config.get('api_key', '')
    key = str((keys[0] if keys else '') if isinstance(keys, list) else keys).split(',')[0].strip()
    state = read_json(native, '/status', {'Authorization': 'Bearer ' + key} if key else {})
    if type(state.get('busy')) is not bool or 'queued' not in state:
        raise ValueError('Native inference activity unavailable')
    return bool(state['busy'] or state['queued'] or state.get('active'))


def backend_connections():
    ports = sorted({port for pair in PORTS.values() for port in pair} | {30031})
    expression = ' or '.join(f'sport = :{port}' for port in ports)
    result = subprocess.run(['ss', '-Htn', 'state', 'established', f'( {expression} )'],
                            capture_output=True, text=True, timeout=5, check=True)
    return bool(result.stdout.strip())


class IdleUnloader:
    def __init__(self, stop, backend, tracker=None, root=ROOT, timeout=TIMEOUT):
        self.root, self.stop_backend, self.backend = Path(root), stop, backend
        self.activity = tracker or activity
        self.timeout = timeout
        self.done = threading.Event()
        self.identity = None
        self.status = 'waiting'

    def tick(self):
        from backend_switch import read_owner
        owner = read_owner(self.root / 'dsh/data/backend-owner.json')
        identity = (owner or {}).get('pid'), (owner or {}).get('start')
        if identity != self.identity:
            self.identity = identity
            self.activity.touch()  # Every newly launched backend gets a full ten minutes.
        if not owner and self.backend() is None:
            if self.status != 'unloaded':
                self.status = 'no managed backend'
            return False
        lock_path = self.root / 'hardware/generated/GPU-LOCK'
        if lock_path.exists():
            self.status = 'GPU reserved'
            return False
        with self.activity.idle_guard(self.timeout) as due:
            if not due:
                self.status = 'request active or timeout not reached'
                return False
            # Serialize with every normal backend launch, not just hub requests.
            start_path = self.root / 'dsh/data/backend-start.lock'
            start_path.parent.mkdir(parents=True, exist_ok=True)
            with start_path.open('a') as launch_lock:
                os.fchmod(launch_lock.fileno(), 0o600)
                try:
                    fcntl.flock(launch_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    self.status = 'backend starting'
                    return False
                # Recheck ownership after taking the launch lock.
                if read_owner(self.root / 'dsh/data/backend-owner.json') != owner:
                    self.activity.touch()
                    return False
                kind = (owner or {}).get('backend') or self.backend()
                if kind not in PORTS:
                    self.status = 'no managed backend'
                    return False
                if engine_busy(kind):
                    self.activity.touch()
                    self.status = 'engine busy'
                    return False
                if backend_connections():
                    self.status = 'backend connection active'
                    return False
                claim = {'owner': 'idle-timeout', 'pid': os.getpid(), 'token': uuid.uuid4().hex}
                try:
                    fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                except FileExistsError:
                    self.status = 'GPU reserved'
                    return False
                try:
                    with os.fdopen(fd, 'w') as file:
                        json.dump(claim, file)
                    stopped = self.stop_backend()
                    self.status = 'unloaded' if stopped else 'request active'
                    if stopped:
                        self.activity.touch()
                        print('Idle timeout: managed inference unloaded after 10 minutes; DSH and gateway remain available.', flush=True)
                    return stopped
                finally:
                    if read_owner(lock_path) == claim:
                        lock_path.unlink()

    def start(self):
        self.activity.touch()
        def watch():
            while not self.done.wait(5):
                try:
                    self.tick()
                except Exception as error:
                    # Missing activity, queue or ownership evidence never authorizes a kill.
                    self.status = 'deferred: ' + type(error).__name__
        threading.Thread(target=watch, daemon=True).start()
        return self
