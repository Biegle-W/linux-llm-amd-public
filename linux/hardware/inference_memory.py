"""Read-only, de-duplicated memory evidence for managed inference processes."""
from pathlib import Path
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dsh'))
from backend_switch import processes, is_inference

# User-authorized minor-swap allowance (October 25). Applied to the aggregate
# owned-process peak in every model record and the full inference lifecycle.
WORKER_SWAP_LIMIT_BYTES = 64 * 1024**2


def sample_memory(snapshot=None, proc_root=Path('/proc')):
    """Count each managed PID and shared DRM client once, excluding other apps.

    Process exits are normal; unreadable live-process counters fail the sample.
    This never signals a process or changes system/worker swap settings.
    """
    snapshot = processes() if snapshot is None else snapshot
    owned = {p.pid for p in snapshot.values() if is_inference(p)}
    while True:
        children = {p.pid for p in snapshot.values() if p.parent in owned}
        if children <= owned:
            break
        owned |= children
    swap = spill = counted = 0
    clients = set()
    for pid in sorted(owned):
        if snapshot[pid].state == 'Z':
            continue
        base = proc_root / str(pid)
        try:
            status = (base / 'status').read_text()
        except (FileNotFoundError, ProcessLookupError):
            continue
        fields = dict(line.split(':', 1) for line in status.splitlines() if ':' in line)
        # Missing VmSwap is unknown, never evidence of zero swap.
        amount, unit = fields['VmSwap'].split()
        amount = int(amount)
        if amount < 0 or unit != 'kB':
            raise ValueError('Invalid VmSwap counter')
        swap += amount * 1024
        counted += 1
        try:
            files = list((base / 'fdinfo').iterdir())
        except (FileNotFoundError, ProcessLookupError):
            continue
        for file in files:
            try:
                values = dict(line.split(':', 1) for line in file.read_text().splitlines() if ':' in line)
            except (FileNotFoundError, ProcessLookupError):
                continue
            if values.get('drm-driver', '').strip() != 'amdgpu':
                continue
            client = (values['drm-pdev'].strip(), values['drm-client-id'].strip())
            if client in clients:
                continue
            clients.add(client)
            total = int(values['drm-total-vram'].split()[0]) * 1024
            resident = int(values['drm-resident-vram'].split()[0]) * 1024
            if total < 0 or not 0 <= resident <= total:
                raise ValueError('Invalid DRM residency counter')
            spill += max(0, total - resident)
    return {'swap': swap, 'spill': spill, 'processes': counted} if counted else None


def memory_failures(memory):
    if not isinstance(memory, dict):
        return ['memory_telemetry_missing']
    failures = []
    for field, name, limit in [('max_worker_swap_bytes', 'worker_swap', WORKER_SWAP_LIMIT_BYTES),
                               ('max_nonresident_vram_bytes', 'vram_spill', 0)]:
        value = memory.get(field)
        if type(value) is not int or value < 0:
            failures.append(name + '_telemetry_invalid')
        elif value > limit:
            failures.append(name)
    return failures


def lifecycle_failures(record):
    memory = record.get('lifecycle_memory')
    failures = memory_failures(memory)
    if not isinstance(memory, dict):
        return failures
    samples, errors = memory.get('worker_samples'), memory.get('sampling_errors')
    if type(samples) is not int or samples <= 0:
        failures.append('no_lifecycle_worker_samples')
    if type(errors) is not int or errors != 0:
        failures.append('lifecycle_sampling_errors')
    return failures


class MemoryMonitor:
    """Latch sampled peaks/errors from before launch until after worker shutdown."""
    def __init__(self, interval=0.5):
        self.interval = interval
        self.done = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.summary = {'scope': 'managed inference: launch, load, warmup, benchmark, shutdown',
                        'interval_seconds': interval, 'worker_samples': 0, 'sampling_errors': 0,
                        'max_worker_swap_bytes': 0, 'max_nonresident_vram_bytes': 0}

    def sample(self):
        try:
            reading = sample_memory()
            if reading:
                self.summary['worker_samples'] += 1
                for field, source in [('max_worker_swap_bytes', 'swap'),
                                      ('max_nonresident_vram_bytes', 'spill')]:
                    self.summary[field] = max(self.summary[field], reading[source])
        except Exception as error:
            # A sampler bug must not kill this thread and leave a false zero.
            self.summary['sampling_errors'] += 1
            # Do not print process data or private paths in curated results.
            self.summary.setdefault('first_error_type', type(error).__name__)

    def _run(self):
        while not self.done.is_set():
            self.sample()
            self.done.wait(self.interval)

    def start(self):
        self.thread.start()
        return self

    def stop(self):
        self.done.set()
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            self.summary['sampling_errors'] += 1
            self.summary.setdefault('first_error_type', 'MonitorStopTimeout')
        return dict(self.summary)
