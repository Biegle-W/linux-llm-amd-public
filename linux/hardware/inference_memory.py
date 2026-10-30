"""Read-only, de-duplicated memory evidence for managed inference processes."""
from pathlib import Path
import os
import sys
import threading
import copy
from datetime import datetime, timezone
import time
import traceback
from swap_activity import (SwapActivity, read_host_activity, validate_summary,
                           POLICY_NAME, MODERN_POLICIES, RATE_LIMIT_POLICY_NAME, LEGACY_POLICY_NAME, selected_policy,
                           WORKER_SWAP_LIMIT_BYTES as RELAXED_SWAP_LIMIT_BYTES)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dsh'))
from backend_switch import processes, is_inference
from amd_memory import vram_accounting

# Explicit legacy bounded-64mib override. The default loading-swap policy also
# requires host activity/pressure evidence and a complete inference window.
WORKER_SWAP_LIMIT_BYTES = 64 * 1024**2


def swap_policy():
    return selected_policy()


def worker_swap_limit_bytes():
    policy = swap_policy()
    return (None if policy in (*MODERN_POLICIES, RATE_LIMIT_POLICY_NAME) else RELAXED_SWAP_LIMIT_BYTES
            if policy == LEGACY_POLICY_NAME else WORKER_SWAP_LIMIT_BYTES)


def confirmed_process_exit(member, base):
    """Missing mm counters are normal only after a verified identity/exit check.

    proc_pid_status obtains task state and mm separately: exit_mm can clear mm
    while state still reads R. PF_EXITING is set before exit_mm. Never replace
    a missing live counter with zero or skip its DRM counters without proof.
    """
    try:
        fields = (base/'stat').read_text().rsplit(')', 1)[1].split()
    except (FileNotFoundError, ProcessLookupError):
        return True
    return (fields[19] != member.start or fields[0] in ('Z', 'X') or
            bool(int(fields[6]) & 0x00000004))  # Linux PF_EXITING


def sample_memory(snapshot=None, proc_root=Path('/proc')):
    """Sample owned workers; tag unreadable live counters without hiding failures."""
    snapshot = processes() if snapshot is None else snapshot
    owned = {p.pid for p in snapshot.values() if is_inference(p)}
    while True:
        children = {p.pid for p in snapshot.values() if p.parent in owned}
        if children <= owned:
            break
        owned |= children
    swap = spill = counted = 0
    clients = set()
    vram = {"schema": "amd-eviction-v1", "explicit_eviction_clients": 0, "legacy_fallback_clients": 0,
            "requested_vram_bytes": 0, "resident_vram_bytes": 0,
            "requested_nonresident_vram_bytes": 0, "explicit_evicted_vram_bytes": 0}
    for pid in sorted(owned):
        stage, fd = 'process_snapshot', None
        try:
            if snapshot[pid].state == 'Z':
                continue
            base = proc_root / str(pid)
            stage = 'proc_status'
            try:
                status = (base/'status').read_text()
            except (FileNotFoundError, ProcessLookupError):
                continue
            fields = dict(line.split(':', 1) for line in status.splitlines() if ':' in line)
            if fields.get('State', '').strip()[:1] in ('Z', 'X'):
                continue
            if 'VmSwap' not in fields and confirmed_process_exit(snapshot[pid], base):
                continue
            amount, unit = fields['VmSwap'].split()
            amount = int(amount)
            if amount < 0 or unit != 'kB':
                raise ValueError('Invalid VmSwap counter')
            swap += amount * 1024
            counted += 1
            stage = 'fdinfo_inventory'
            try:
                files = list((base/'fdinfo').iterdir())
            except (FileNotFoundError, ProcessLookupError):
                continue
            for file in files:
                stage = 'drm_fdinfo'
                fd = int(file.name) if file.name.isdecimal() else None
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
                row = vram_accounting(values)
                spill += row['spill']
                vram['explicit_eviction_clients' if row['explicit'] else 'legacy_fallback_clients'] += 1
                for dest, source in [('requested_vram_bytes', 'requested'), ('resident_vram_bytes', 'resident'),
                                     ('requested_nonresident_vram_bytes', 'requested_nonresident')]:
                    vram[dest] += row[source]
                if row['evicted'] is not None:
                    vram['explicit_evicted_vram_bytes'] += row['evicted']
        except Exception as error:
            error.sampler_context = {'reader': stage, 'pid': pid, 'fd': fd}
            raise
    if not counted:
        return None
    return {'swap': swap, 'spill': spill, 'processes': counted,
            **({'vram_accounting': vram} if clients else {})}


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
        elif limit is not None and value > limit:
            failures.append(name)
    if policy != 'bounded-64mib':
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


def sampler_error_detail(error):
    """Safe counter names and source frames only; no messages, paths or locals."""
    context = getattr(error, 'sampler_context', {})
    context = context if isinstance(context, dict) else {}
    pid, fd = context.get('pid'), context.get('fd')
    reader = context.get('reader', 'aggregate_reading')
    if reader not in ('process_snapshot', 'proc_status', 'fdinfo_inventory', 'drm_fdinfo', 'aggregate_reading'):
        reader = 'unknown'
    missing = error.args[0] if isinstance(error, KeyError) and error.args else None
    if missing is not None and (not isinstance(missing, str) or missing not in MemoryMonitor.SAFE_COUNTER_NAMES):
        missing = '<redacted>'
    frames = [{'file': Path(frame.filename).name if Path(frame.filename).name in
               ('inference_memory.py', 'backend_switch.py', 'swap_activity.py', 'amd_memory.py') else '<external>',
               'function': frame.name[:80], 'line': frame.lineno}
              for frame in traceback.extract_tb(error.__traceback__)[-6:]]
    return {'error_type': type(error).__name__, 'reader': reader,
            'pid': pid if type(pid) is int and pid > 0 else None,
            'fd': fd if type(fd) is int and fd >= 0 else None,
            'missing_key': missing, 'frames': frames}


class MemoryMonitor:
    """Latch sampled peaks/errors from before launch until after worker shutdown.

    Failed enforcement is retried once on the next sample, then terminally
    failed. Sampling continues; callback errors permanently fail validation.
    """
    MAX_ENFORCEMENT_ATTEMPTS = 2
    MAX_ERROR_DETAILS = 8
    SAFE_COUNTER_NAMES = frozenset(('VmSwap', 'drm-pdev', 'drm-client-id',
                                    'drm-total-vram', 'drm-resident-vram', 'amd-evicted-vram',
                                    'swap', 'spill', 'processes'))

    def __init__(self, interval=0.5, on_violation=None, *, write_budget_bytes_per_second=None):
        self.interval = interval
        self._lock = threading.Lock()
        self.phase = 'loading'
        self.activity = SwapActivity(write_budget_bytes_per_second=write_budget_bytes_per_second) if swap_policy() != 'bounded-64mib' else None
        self.on_violation = on_violation
        self.notified = False
        self.done = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.summary = {'scope': 'managed inference: launch, load, warmup, benchmark, shutdown',
                        'interval_seconds': interval, 'worker_samples': 0, 'sampling_errors': 0,
                        'sample_attempts': 0, 'sampling_error_details': [],
                        'sampling_error_details_dropped': 0,
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

    def _record_error(self, error, component='worker_memory'):
        if component != 'host_activity':
            self.summary['sampling_errors'] += 1
            self.summary.setdefault('first_error_type', type(error).__name__)
        details = self.summary['sampling_error_details']
        if len(details) >= self.MAX_ERROR_DETAILS:
            self.summary['sampling_error_details_dropped'] += 1
            return
        details.append({'sample_index': self.summary['sample_attempts'],
                        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
                        'monotonic_seconds': time.monotonic(), 'phase': self.phase,
                        'component': component, **sampler_error_detail(error)})

    def _sample_locked(self):
        self.summary['sample_attempts'] += 1
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
                if 'vram_accounting' in reading:
                    stats = reading['vram_accounting']
                    target = self.summary.setdefault('vram_accounting', {'schema': 'amd-eviction-v1',
                        'explicit_counter_samples': 0, 'legacy_fallback_samples': 0,
                        'max_requested_nonresident_vram_bytes': 0, 'max_explicit_evicted_vram_bytes': 0})
                    target['explicit_counter_samples'] += int(stats['explicit_eviction_clients'] > 0)
                    target['legacy_fallback_samples'] += int(stats['legacy_fallback_clients'] > 0)
                    for dest, source in [('max_requested_nonresident_vram_bytes', 'requested_nonresident_vram_bytes'),
                                         ('max_explicit_evicted_vram_bytes', 'explicit_evicted_vram_bytes')]:
                        target[dest] = max(target[dest], stats[source])
        except Exception as error:
            # A sampler bug must not kill this thread and leave a false zero.
            self._record_error(error)
        if self.activity is not None:
            try:
                # Absence is normal before launch/after shutdown, never proof
                # of a zero-swap worker or a qualifying inference endpoint.
                host = read_host_activity()
                self.activity.observe(None if reading is None and self.phase == 'inference' else host,
                                      self.phase, reading['swap'] if reading else 0,
                                      progress=reading.get('progress') if reading else None)
            except Exception as error:
                self._record_error(error, 'host_activity')
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
        return copy.deepcopy(self.summary)
