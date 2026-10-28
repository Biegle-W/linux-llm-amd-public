"""Allow loading/parked swap; guard inference churn, not SSD lifetime guarantees.

Host swap counters measure system-wide I/O; they do not attribute it to workers.
The default observes rates; only an explicit write budget plus matched measured
slowdown can request a swap-related stop. Reads and PSI alone never do.
No sampling loop, process inspection, service changes, or dependencies.
"""
from pathlib import Path
from collections import deque
import math
import copy
import hashlib
import os
import time
from typing import Any

POLICY_NAME = 'loading-swap-v3'
RATE_LIMIT_POLICY_NAME = 'loading-swap-v2'
LEGACY_POLICY_NAME = 'low-churn-v1'

def selected_policy():
    value = os.environ.get('LOCAL_LLM_SWAP_POLICY', POLICY_NAME)
    if value not in (POLICY_NAME, RATE_LIMIT_POLICY_NAME, LEGACY_POLICY_NAME, 'bounded-64mib'):
        raise ValueError('Unknown inference swap policy')
    # Historical validation requires a second explicit opt-in. An old inherited
    # environment or frozen harness must not restore the superseded stop rules.
    if value != POLICY_NAME and os.environ.get('LOCAL_LLM_LEGACY_SWAP_VALIDATION') != '1':
        return POLICY_NAME
    return value

# Historical limits and current advisory levels. In v3 none is an automatic
# swap stop: that requires an explicit deployment write budget and matched slowdown.
# v2 has no occupancy or cumulative-write cap.
WORKER_SWAP_LIMIT_BYTES = 4 * 1024**3
SWAPOUT_BUDGET_BYTES = 4 * 1024**3
INFERENCE_SWAPOUT_RATE_LIMIT_BYTES = 1 * 1024**2
INFERENCE_IO_RATE_LIMIT_BYTES = 8 * 1024**2
RATE_WINDOW_SECONDS = 30
MIN_AVAILABLE_BYTES = 2 * 1024**3
MIN_PRESSURE_SAMPLES = 3
MEMORY_FULL_PSI_AVG10_LIMIT = 10.0


def _uint(value):
    if type(value) is not int or value < 0:
        raise ValueError('expected nonnegative integer')
    return _number(value)


def _number(value, maximum=None):
    try:
        valid = (type(value) in (int, float) and math.isfinite(value)
                 and value >= 0 and (maximum is None or value <= maximum))
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError('expected finite nonnegative number in range')
    return value


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate telemetry field')
        result[key] = value
    return result


def read_host_activity(proc_root=Path('/proc'), page_size=None):
    """Read vmstat pages, MemAvailable kB and full memory PSI avg10 percent.

    Returns timestamp (monotonic seconds), swapin_bytes, swapout_bytes,
    available_bytes and memory_full_psi_avg10. Missing telemetry raises.
    """
    root = Path(proc_root)
    size = _uint(os.sysconf('SC_PAGE_SIZE') if page_size is None else page_size)
    if size == 0:
        raise ValueError('page_size must be positive')
    vmstat = _unique_pairs(line.split() for line in (root / 'vmstat').read_text().splitlines())
    meminfo = _unique_pairs(line.split(':', 1) for line in (root / 'meminfo').read_text().splitlines())
    amount, unit = meminfo['MemAvailable'].split()
    if unit != 'kB':
        raise ValueError('invalid MemAvailable unit')
    full = [line.split()[1:] for line in (root / 'pressure/memory').read_text().splitlines()
            if line.startswith('full ')]
    if len(full) != 1:
        raise ValueError('missing or duplicate full memory PSI')
    psi = _unique_pairs(field.split('=', 1) for field in full[0])
    return dict(timestamp=time.monotonic(),
                swapin_bytes=_uint(int(vmstat['pswpin']) * size),
                swapout_bytes=_uint(int(vmstat['pswpout']) * size),
                available_bytes=_uint(int(amount) * 1024),
                memory_full_psi_avg10=_number(float(psi['avg10']), 100))


class SwapActivity:
    """Accumulate host deltas and separately supplied aggregate worker swap.

    Reading keys are those of read_host_activity(). observe() is synchronous;
    the caller owns cadence and lifetime. Returned evidence is a detached copy.
    Totals are deltas from the first accepted sample, not lifetime host totals.
    Each inference endpoint uses the shortest sampled interval >=30s, entirely
    within one uninterrupted inference phase. Sparse cadence can miss bursts.
    inference_window_samples counts evaluated windows, not raw observations.
    """
    def __init__(self, *, write_budget_bytes_per_second=None):
        # No arbitrary rate is evidence of SSD damage. Without an explicit
        # deployment write budget, rates and matched slowdowns are advisories.
        if write_budget_bytes_per_second is not None:
            _number(write_budget_bytes_per_second)
            if write_budget_bytes_per_second == 0:
                raise ValueError('write budget must be positive or None')
        self.write_budget = write_budget_bytes_per_second
        self.policy = selected_policy()
        self.legacy = self.policy in (LEGACY_POLICY_NAME, 'bounded-64mib')
        self._first = self._last = None
        self._failures = []
        self._advisories = []
        self._pressure_runs = [0, 0]
        self._phase = None
        self._window = deque()
        self._last_progress = None
        self._progress_epoch = 0
        self._data: dict[str, Any] = dict(policy=self.policy, samples=0, sampling_errors=0,
                          elapsed_seconds=0.0, worker_swap_peak_bytes=0,
                          total_swapin_bytes=0, total_swapout_bytes=0,
                          inference_window_samples=0,
                          max_inference_swapout_bytes_per_second=0.0,
                          max_inference_swap_io_bytes_per_second=0.0,
                          min_available_bytes=None, max_memory_full_psi_avg10=None if self.legacy else 0.0,
                          max_low_memory_consecutive_samples=0,
                          max_full_psi_consecutive_samples=0)
        if self.policy == POLICY_NAME:
            self._data.update(write_budget_bytes_per_second=self.write_budget,
                              progress_samples=0, measured_slowdown_windows=0,
                              confirmed_write_slowdown_windows=0,
                              last_confirmed_write_slowdown=None)


    def _fail(self, name):
        if name not in self._failures:
            self._failures.append(name)

    def _advise(self, name):
        if name not in self._advisories:
            self._advisories.append(name)

    def _progress(self, progress):
        if progress is None:
            return None
        try:
            if not isinstance(progress, dict):
                raise ValueError('progress must be an object')
            for key in ('workload_id', 'baseline_id', 'baseline_workload_id'):
                value = progress[key]
                if type(value) is not str or not value or value.strip() != value or len(value) > 128:
                    raise ValueError('progress IDs must be short opaque identifiers')
            _number(progress['completed_units'])
            _number(progress['baseline_units_per_second'])
            if progress['baseline_units_per_second'] == 0:
                raise ValueError('baseline rate must be positive')
            if progress['baseline_workload_id'] != progress['workload_id']:
                raise ValueError('baseline workload does not match')
            return {key: progress[key] for key in ('workload_id', 'baseline_id',
                    'baseline_workload_id', 'completed_units', 'baseline_units_per_second')}
        except (ValueError, TypeError, KeyError):
            self._advise('invalid_or_unmatched_progress_evidence')
            return None

    def set_phase(self, phase):
        """Record transitions even without a sample; retain latched evidence.

        As with observe(), the caller owns synchronization. Repeating the same
        phase is not a transition and must not discard an active rate window.
        """
        if phase != self._phase:
            self._window.clear()
            if not self.legacy:
                self._pressure_runs[1] = 0
            self._phase = phase

    def observe(self, reading, phase='loading', worker_swap_bytes=0, progress=None):
        """Latch invalid readings (including None after reader failure), never skip silently.

        phase is a nonempty, trimmed string; only exact 'inference' gates rates.
        samples counts accepted readings; sampling_errors counts rejected ones.
        Invalid observations reset rate history. Errors cannot be cleared.
        """
        data = self._data
        try:
            if (not isinstance(reading, dict) or type(phase) is not str or
                    not phase or phase.strip() != phase):
                raise ValueError('invalid reading or phase')
            _uint(worker_swap_bytes)
            _number(reading['timestamp'])
            for field in ('swapin_bytes', 'swapout_bytes', 'available_bytes'):
                _uint(reading[field])
            _number(reading['memory_full_psi_avg10'], 100)
        except (ValueError, TypeError, KeyError, OverflowError):
            data['sampling_errors'] += 1
            self._fail('invalid_observation')
            self._window.clear()
            self._phase = None
            return
        if self._last is not None:
            invalid = []
            if reading['timestamp'] <= self._last['timestamp']:
                invalid.append('nonmonotonic_time')
            if any(reading[key] < self._last[key] for key in ('swapin_bytes', 'swapout_bytes')):
                invalid.append('swap_counter_reset')
            if invalid:
                data['sampling_errors'] += 1
                for name in invalid:
                    self._fail(name)
                self._window.clear()
                self._phase = None
                return
        if self._first is None:
            self._first = dict(reading)
        self._last = dict(reading)
        data['samples'] += 1
        data['elapsed_seconds'] = reading['timestamp'] - self._first['timestamp']
        data['worker_swap_peak_bytes'] = max(data['worker_swap_peak_bytes'], worker_swap_bytes)
        for direction in ('swapin', 'swapout'):
            data['total_' + direction + '_bytes'] = (
                reading[direction + '_bytes'] - self._first[direction + '_bytes'])
        if self.legacy and data['worker_swap_peak_bytes'] > WORKER_SWAP_LIMIT_BYTES:
            self._fail('worker_swap_limit')
        if self.legacy and data['total_swapout_bytes'] > SWAPOUT_BUDGET_BYTES:
            self._fail('swapout_budget')
        previous = data['min_available_bytes']
        data['min_available_bytes'] = (reading['available_bytes'] if previous is None else
                                       min(previous, reading['available_bytes']))
        self.set_phase(phase)
        # v2 pressure associated with swap thrashing is an inference check.
        # Lifecycle RAM availability remains an independent host safety check.
        inference_pressure = self.legacy or phase == 'inference'
        previous = data['max_memory_full_psi_avg10']
        if inference_pressure:
            data['max_memory_full_psi_avg10'] = (reading['memory_full_psi_avg10']
                                               if previous is None else
                                               max(previous, reading['memory_full_psi_avg10']))
        for index, (bad, peak, failure) in enumerate([
                (reading['available_bytes'] < MIN_AVAILABLE_BYTES,
                 'max_low_memory_consecutive_samples', 'low_host_memory'),
                (inference_pressure and reading['memory_full_psi_avg10'] > MEMORY_FULL_PSI_AVG10_LIMIT,
                 'max_full_psi_consecutive_samples', 'memory_full_psi')]):
            self._pressure_runs[index] = self._pressure_runs[index] + 1 if bad else 0
            data[peak] = max(data[peak], self._pressure_runs[index])
            if data[peak] >= MIN_PRESSURE_SAMPLES:
                if self.policy == POLICY_NAME and failure == 'memory_full_psi':
                    self._advise('active_memory_pressure_observed')
                else:
                    self._fail(failure)
        self.set_phase(phase)
        if phase == 'inference':
            endpoint = dict(reading)
            if self.policy == POLICY_NAME:
                endpoint['progress'] = self._progress(progress)
                current, prior = endpoint['progress'], self._last_progress
                keys = ('workload_id', 'baseline_id', 'baseline_workload_id', 'baseline_units_per_second')
                if prior is not None and (current is None or
                        any(current[key] != prior[key] for key in keys) or
                        current['completed_units'] < prior['completed_units']):
                    self._progress_epoch += 1
                self._last_progress = current
                endpoint['progress_epoch'] = self._progress_epoch
                if current is not None:
                    data['progress_samples'] += 1
            self._window.append(endpoint)
            while (len(self._window) > 1 and
                   reading['timestamp'] - self._window[1]['timestamp'] >= RATE_WINDOW_SECONDS):
                self._window.popleft()
            start = self._window[0]
            elapsed = reading['timestamp'] - start['timestamp']
            if elapsed >= RATE_WINDOW_SECONDS:
                out = reading['swapout_bytes'] - start['swapout_bytes']
                incoming = reading['swapin_bytes'] - start['swapin_bytes']
                numerator, denominator = elapsed.as_integer_ratio()
                data['inference_window_samples'] += 1
                for key, rate, limit, failure in [
                        ('max_inference_swapout_bytes_per_second', out / elapsed,
                         INFERENCE_SWAPOUT_RATE_LIMIT_BYTES, 'inference_swapout_rate'),
                        ('max_inference_swap_io_bytes_per_second',
                         (out + incoming) * denominator / numerator,
                         INFERENCE_IO_RATE_LIMIT_BYTES, 'inference_swap_io_rate')]:
                    data[key] = max(data[key], rate)
                    if rate > limit:
                        if self.policy == POLICY_NAME:
                            self._advise(failure + '_observed')
                        else:
                            self._fail(failure)
                if self.policy == POLICY_NAME:
                    first, last = start.get('progress'), endpoint.get('progress')
                    comparable = (first is not None and last is not None and
                                  start.get('progress_epoch') == endpoint.get('progress_epoch') and
                                  all(first[key] == last[key] for key in
                                      ('workload_id', 'baseline_id', 'baseline_workload_id',
                                       'baseline_units_per_second')) and
                                  last['completed_units'] >= first['completed_units'])
                    if comparable:
                        measured = (last['completed_units'] - first['completed_units']) / elapsed
                        ratio = measured / last['baseline_units_per_second']
                        if ratio < .95:
                            data['measured_slowdown_windows'] += 1
                            self._advise('matched_inference_slowdown_observed')
                            if self.write_budget is not None and out / elapsed > self.write_budget:
                                data['confirmed_write_slowdown_windows'] += 1
                                data['last_confirmed_write_slowdown'] = dict(
                                    window_seconds=elapsed, measured_units_per_second=measured,
                                    baseline_units_per_second=last['baseline_units_per_second'],
                                    throughput_ratio=ratio, swapout_bytes_per_second=out / elapsed,
                                    write_budget_bytes_per_second=self.write_budget,
                                    workload_sha256=hashlib.sha256(last['workload_id'].encode()).hexdigest(),
                                    baseline_sha256=hashlib.sha256(last['baseline_id'].encode()).hexdigest())
                                self._fail('sustained_writes_with_measured_slowdown')

    def summary(self):
        result = dict(self._data, failures=self.failures())
        if self.policy == POLICY_NAME:
            result['advisories'] = list(self._advisories)
        return copy.deepcopy(result)

    def failures(self):
        return list(self._failures) + ([] if self._data['samples'] else ['no_samples'])


def validate_summary(summary, require_inference=False):
    """Validate evidence for the selected policy; never reinterpret old versions.

    Pressure run peaks are required in addition to extrema so that transient
    pressure is not mistaken for a sustained violation. No raw samples needed.
    """
    if type(require_inference) is not bool:
        return ['invalid_require_inference']
    if not isinstance(summary, dict):
        return ['summary_missing']
    errors = []
    if summary.get('policy') != selected_policy():
        errors.append('invalid_policy')
    integer_fields = ('samples', 'sampling_errors', 'worker_swap_peak_bytes',
                      'total_swapin_bytes', 'total_swapout_bytes', 'inference_window_samples',
                      'min_available_bytes', 'max_low_memory_consecutive_samples',
                      'max_full_psi_consecutive_samples')
    number_fields = ('elapsed_seconds', 'max_inference_swapout_bytes_per_second',
                     'max_inference_swap_io_bytes_per_second', 'max_memory_full_psi_avg10')
    for field in integer_fields + number_fields:
        try:
            if field in integer_fields:
                _uint(summary[field])
            else:
                _number(summary[field], 100 if field == 'max_memory_full_psi_avg10' else None)
        except (ValueError, TypeError, KeyError, OverflowError):
            errors.append('invalid_' + field)
    failures = summary.get('failures')
    if (not isinstance(failures, list) or
            any(type(item) is not str or not item for item in failures)):
        errors.append('invalid_failures')
    if errors:
        return errors
    assert isinstance(failures, list)
    errors.extend(failures)
    if summary['samples'] <= 0:
        errors.append('no_samples')
    if summary['sampling_errors']:
        errors.append('sampling_errors')
    samples = summary['samples']
    windows = summary['inference_window_samples']
    elapsed = summary['elapsed_seconds']
    out_rate = summary['max_inference_swapout_bytes_per_second']
    io_rate = summary['max_inference_swap_io_bytes_per_second']
    inconsistent = (
        windows > max(0, samples - 1) or
        (windows > 0 and elapsed < RATE_WINDOW_SECONDS) or
        (windows == 0 and (out_rate != 0 or io_rate != 0)) or
        out_rate > io_rate or
        (summary['total_swapout_bytes'] == 0 and out_rate != 0) or
        (summary['total_swapin_bytes'] + summary['total_swapout_bytes'] == 0 and io_rate != 0) or
        (samples == 1 and (elapsed != 0 or summary['total_swapin_bytes'] != 0 or
                          summary['total_swapout_bytes'] != 0)) or
        (samples > 1 and elapsed <= 0))
    for peak, bad in [
            ('max_low_memory_consecutive_samples', summary['min_available_bytes'] < MIN_AVAILABLE_BYTES),
            ('max_full_psi_consecutive_samples',
             summary['max_memory_full_psi_avg10'] > MEMORY_FULL_PSI_AVG10_LIMIT)]:
        inconsistent |= summary[peak] > samples or ((summary[peak] > 0) != bad)
    if inconsistent:
        errors.append('inconsistent_evidence')
    if require_inference and windows == 0:
        errors.append('no_inference_window')
    for field, limit, failure in [
            ('worker_swap_peak_bytes', WORKER_SWAP_LIMIT_BYTES, 'worker_swap_limit'),
            ('total_swapout_bytes', SWAPOUT_BUDGET_BYTES, 'swapout_budget'),
            ('max_inference_swapout_bytes_per_second', INFERENCE_SWAPOUT_RATE_LIMIT_BYTES,
             'inference_swapout_rate'),
            ('max_inference_swap_io_bytes_per_second', INFERENCE_IO_RATE_LIMIT_BYTES,
             'inference_swap_io_rate')]:
        occupancy = field in ('worker_swap_peak_bytes', 'total_swapout_bytes')
        applies = (summary.get('policy') in (LEGACY_POLICY_NAME, 'bounded-64mib') if occupancy
                   else summary.get('policy') != POLICY_NAME)
        if applies and summary[field] > limit:
            errors.append(failure)
    for field, failure in [('max_low_memory_consecutive_samples', 'low_host_memory'),
                           ('max_full_psi_consecutive_samples', 'memory_full_psi')]:
        if summary[field] >= MIN_PRESSURE_SAMPLES:
            if failure != 'memory_full_psi' or summary.get('policy') != POLICY_NAME:
                errors.append(failure)
    if summary.get('policy') == POLICY_NAME:
        errors.extend(_validate_v3_evidence(summary))
    return list(dict.fromkeys(errors))


def _validate_v3_evidence(summary):
    errors = []
    try:
        budget = summary['write_budget_bytes_per_second']
        if budget is not None:
            _number(budget)
            if budget == 0:
                raise ValueError('zero budget')
        for key in ('progress_samples', 'measured_slowdown_windows',
                    'confirmed_write_slowdown_windows'):
            _uint(summary[key])
        if (summary['progress_samples'] > summary['samples'] or
                summary['measured_slowdown_windows'] > summary['inference_window_samples'] or
                summary['confirmed_write_slowdown_windows'] > summary['measured_slowdown_windows'] or
                (summary['measured_slowdown_windows'] > 0 and summary['progress_samples'] < 2)):
            raise ValueError('inconsistent progress counts')
        if not isinstance(summary['advisories'], list) or any(
                type(value) is not str or not value for value in summary['advisories']):
            raise ValueError('invalid advisories')
        evidence = summary['last_confirmed_write_slowdown']
        count = summary['confirmed_write_slowdown_windows']
        if not count:
            if evidence is not None or 'sustained_writes_with_measured_slowdown' in summary['failures']:
                raise ValueError('unsupported stop claim')
        else:
            if budget is None or not isinstance(evidence, dict):
                raise ValueError('missing stop evidence or write budget')
            for key in ('window_seconds', 'measured_units_per_second', 'baseline_units_per_second',
                        'throughput_ratio', 'swapout_bytes_per_second', 'write_budget_bytes_per_second'):
                _number(evidence[key])
            if (evidence['window_seconds'] < RATE_WINDOW_SECONDS or
                    evidence['baseline_units_per_second'] <= 0 or
                    evidence['write_budget_bytes_per_second'] != budget or
                    evidence['swapout_bytes_per_second'] <= budget or
                    evidence['throughput_ratio'] >= .95 or
                    evidence['measured_units_per_second'] / evidence['baseline_units_per_second'] != evidence['throughput_ratio'] or
                    not 0 < evidence['swapout_bytes_per_second'] <= summary['max_inference_swapout_bytes_per_second']):
                raise ValueError('unconfirmed stop evidence')
            for key in ('workload_sha256', 'baseline_sha256'):
                value = evidence[key]
                if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
                    raise ValueError('invalid evidence identifier')
            errors.append('sustained_writes_with_measured_slowdown')
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        errors.append('invalid_progress_or_write_budget_evidence')
    return errors
