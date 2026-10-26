"""Read-only, de-duplicated memory evidence for managed inference processes."""
from pathlib import Path
import os
import sys
import threading
from swap_activity import (SwapActivity, read_host_activity, validate_summary,
                           POLICY_NAME, WORKER_SWAP_LIMIT_BYTES as RELAXED_SWAP_LIMIT_BYTES)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dsh'))
from backend_switch import processes, is_inference

# Explicit legacy bounded-64mib override. The default low-churn policy also
# requires host activity/pressure evidence and a complete inference window.
WORKER_SWAP_LIMIT_BYTES = 64 * 1024**2


def swap_policy():
    policy = os.environ.get('LOCAL_LLM_SWAP_POLICY', POLICY_NAME)
    if policy not in ('bounded-64mib', POLICY_NAME):
        raise ValueError('Unknown inference swap policy')
    return policy


def worker_swap_limit_bytes():
    return RELAXED_SWAP_LIMIT_BYTES if swap_policy() == POLICY_NAME else WORKER_SWAP_LIMIT_BYTES


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
    try:
        policy, swap_limit = swap_policy(), worker_swap_limit_bytes()
    except ValueError:
        return ['memory_policy_invalid']
    failures = []
    enforcement_errors = memory.get('enforcement_errors', 0)
    if type(enforcement_errors) is not int or enforcement_errors < 0:
        failures.append('violation_callback_telemetry_invalid')
    elif enforcement_errors:
        failures.append('violation_callback_errors')
    for field, name, limit in [('max_worker_swap_bytes', 'worker_swap', swap_limit),
                               ('max_nonresident_vram_bytes', 'vram_spill', 0)]:
        value = memory.get(field)
        if type(value) is not int or value < 0:
            failures.append(name + '_telemetry_invalid')
        elif value > limit:
            failures.append(name)
    if policy == POLICY_NAME:
        activity = memory.get('swap_activity')
        failures += ['swap_activity_' + reason for reason in validate_summary(activity, require_inference=True)]
        if isinstance(activity, dict) and activity.get('worker_swap_peak_bytes') != memory.get('max_worker_swap_bytes'):
            failures.append('swap_activity_worker_peak_mismatch')
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
    """Latch sampled peaks/errors from before launch until after worker shutdown.

    Failed enforcement is retried once on the next sample, then terminally
    failed. Sampling continues; callback errors permanently fail validation.
    """
    MAX_ENFORCEMENT_ATTEMPTS = 2

    def __init__(self, interval=0.5, on_violation=None):
        self.interval = interval
        self._lock = threading.Lock()
        self.phase = 'loading'
        self.activity = SwapActivity() if swap_policy() == POLICY_NAME else None
        self.on_violation = on_violation
        self.notified = False
        self.done = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.summary = {'scope': 'managed inference: launch, load, warmup, benchmark, shutdown',
                        'interval_seconds': interval, 'worker_samples': 0, 'sampling_errors': 0,
                        'enforcement_attempts': 0, 'enforcement_errors': 0,
                        'enforcement_state': 'not_attempted',
                        'max_worker_swap_bytes': 0, 'max_nonresident_vram_bytes': 0}

    def sample(self):
        # Keep both readers and their attribution atomic with phase transitions.
        with self._lock:
            failures = self._sample_locked()
            if (not failures or self.on_violation is None or self.notified or
                    self.summary['enforcement_state'] in ('in_progress', 'failed_terminal')):
                return
            self.summary['enforcement_attempts'] += 1
            self.summary['enforcement_state'] = 'in_progress'
            callback = self.on_violation
        # Enforcement may itself request a phase transition. Never call user
        # code under the sampling lock or claim success before it returns.
        try:
            callback(failures)
        except Exception as error:
            with self._lock:
                self.summary['enforcement_errors'] += 1
                self.summary.setdefault('first_enforcement_error_type', type(error).__name__)
                self.summary['enforcement_state'] = (
                    'failed_terminal' if self.summary['enforcement_attempts'] >=
                    self.MAX_ENFORCEMENT_ATTEMPTS else 'retry_pending')
        else:
            with self._lock:
                self.notified = True
                self.summary['enforcement_state'] = 'notified'

    def _sample_locked(self):
        reading = None
        try:
            reading = sample_memory()
            if reading is None and self.phase == 'inference':
                raise ValueError('Missing inference worker observation')
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
        if self.activity is not None:
            try:
                # Absence is normal before launch/after shutdown, never proof
                # of a zero-swap worker or a qualifying inference endpoint.
                host = read_host_activity()
                self.activity.observe(None if reading is None and self.phase == 'inference' else host,
                                      self.phase, reading['swap'] if reading else 0)
            except Exception:
                self.activity.observe(None, self.phase)
            self.summary['swap_activity'] = self.activity.summary()
            failures = self.activity.failures()
            if self.summary['max_nonresident_vram_bytes']:
                failures.append('vram_spill')
            if self.summary['sampling_errors']:
                failures.append('worker_sampling_errors')
            return failures
        return []

    def set_phase(self, phase):
        with self._lock:
            if self.activity is not None:
                self.activity.set_phase(phase)
            self.phase = phase

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
        if self.activity is not None:
            self.summary['swap_activity'] = self.activity.summary()
        return dict(self.summary)
