"""Read-only AMD/CPU thermal recording; never changes clocks, fans or workers.

gpu_metrics v1.3 offsets and SMU masks follow Linux v7.0 kgd_pp_interface.h
and amdgpu_smu.h. Unknown ABI/sentinels are unavailable, never zero/healthy.
Raw records stay in ignored dsh/logs/thermals; publish reviewed summaries only.
"""
from datetime import datetime, timezone
from functools import wraps
import json
import os
from pathlib import Path
import re
import struct
import sys
import tempfile
import threading
import time
import uuid

PCI_ROOT = Path('/sys/bus/pci/devices')
HWMON_ROOT = Path('/sys/class/hwmon')
LOG_ROOT = Path(__file__).resolve().parent / 'logs/thermals'


def _text(path):
    try:
        return path.read_text().strip()
    except OSError:
        return None


def _number(path, divisor=1):
    try:
        return int(_text(path)) / divisor
    except (TypeError, ValueError):
        return None


def decode_metrics(data):
    """Only decode the verified 120-byte v1.3 layout used by Navi31 here."""
    result = {'version': None, 'status': 'unavailable', 'independent_mask': None,
              'asic_mask': None, 'thermal_limit': None, 'hotspot_limit': None,
              'power_limit': None, 'current_limit': None}
    if len(data) < 4:
        return result
    size, major, minor = struct.unpack_from('<HBB', data)
    result['version'] = f'{major}.{minor}'
    if (size, major, minor) != (120, 1, 3) or len(data) < size:
        result['status'] = 'unsupported_or_truncated_abi'
        return result
    asic = struct.unpack_from('<I', data, 68)[0]
    mask = struct.unpack_from('<Q', data, 112)[0]
    result['asic_mask'] = None if asic == 2**32-1 else hex(asic)
    if mask == 2**64-1:
        result['status'] = 'unsupported_sentinel'
        return result
    result.update(status='available', independent_mask=hex(mask),
                  thermal_limit=bool(mask & (0xffff << 32)),
                  hotspot_limit=bool(mask & (1 << 36)),
                  power_limit=bool(mask & 0xff),
                  current_limit=bool(mask & (0xff << 16)))
    return result


def snapshot(pci_root=PCI_ROOT, hwmon_root=HWMON_ROOT):
    row = {'utc': datetime.now(timezone.utc).isoformat(),
           'monotonic_seconds': time.monotonic(), 'cards': [], 'cpu_package_c': {}}
    for device in sorted(Path(pci_root).glob('*')):
        if _text(device/'vendor') != '0x1002':
            continue
        try:
            if int(_text(device/'class'), 16) >> 16 != 3:
                continue
        except (TypeError, ValueError):
            continue
        gpu = {'pci': device.name, 'gpu_index': len(row['cards']),
               'temperature_c': {}, 'temperature_critical_c': {},
               'busy_percent': _number(device/'gpu_busy_percent'),
               'memory_busy_percent': _number(device/'mem_busy_percent')}
        for hw in device.glob('hwmon/hwmon*'):
            for sensor in hw.glob('temp*_input'):
                stem = sensor.name.removesuffix('_input')
                label = _text(hw/(stem+'_label')) or stem
                value = _number(sensor, 1000)
                gpu['temperature_c'][label] = value if value is not None and -273 <= value <= 200 else None
                gpu['temperature_critical_c'][label] = _number(hw/(stem+'_crit'), 1000)
            for key, filename, scale in [('fan_rpm','fan1_input',1),
                                         ('power_average_w','power1_average',1e6),
                                         ('power_input_w','power1_input',1e6),
                                         ('power_cap_w','power1_cap',1e6),
                                         ('gfx_clock_mhz','freq1_input',1e6),
                                         ('memory_clock_mhz','freq2_input',1e6)]:
                gpu[key] = _number(hw/filename, scale)
        try:
            gpu['throttle'] = decode_metrics((device/'gpu_metrics').read_bytes())
        except OSError:
            gpu['throttle'] = decode_metrics(b'')
        row['cards'].append(gpu)
    for hw in sorted(Path(hwmon_root).glob('hwmon*')):
        if _text(hw/'name') != 'coretemp':
            continue
        for label in hw.glob('temp*_label'):
            text = _text(label)
            if text and text.startswith('Package id'):
                row['cpu_package_c'][text] = _number(hw/label.name.replace('_label','_input'),1000)
    return row


class ThermalRecorder:
    """One-second bounded raw log plus periodically persisted cumulative peaks.

    Sampling is outside API timing and never an inference admission/stop gate.
    Missing sensors, unsupported throttle ABI and write errors remain explicit.
    """
    def __init__(self, label, directory=None, interval=1.0, max_raw_bytes=64*1024**2,
                 pci_root=PCI_ROOT, hwmon_root=HWMON_ROOT):
        self.directory = Path(directory) if directory is not None else LOG_ROOT
        self.interval = interval
        self.max_raw_bytes = max_raw_bytes
        self.pci_root, self.hwmon_root = pci_root, hwmon_root
        label = re.sub(r'[^a-zA-Z0-9_.-]+', '-', str(label))[:100]
        ident = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ') + f'-{os.getpid()}-{uuid.uuid4().hex[:8]}-{label}'
        self.raw_path = self.directory/(ident+'.jsonl')
        self.summary_path = self.directory/(ident+'.summary.json')
        self.state = {'schema': 1, 'label': label, 'status': 'not_started',
                      'interval_seconds': interval, 'samples': 0, 'sample_errors': 0,
                      'raw_samples_dropped': 0, 'raw_limit_bytes': max_raw_bytes,
                      'raw_log': str(self.raw_path), 'summary_file': str(self.summary_path),
                      'cards': {}, 'cpu_peak_package_c': {},
                      'limits': 'Sampled peaks, not guaranteed transient maxima; SMU flags are reported samples, not measured time throttled. Whole-card sensors include unrelated workloads.'}
        self._done = threading.Event()
        self._lock = threading.RLock()
        self._thread = self._file = None
        self._raw_bytes = 0
        self._last_save = 0

    def _save(self):
        with tempfile.NamedTemporaryFile(mode='w', dir=self.directory, prefix='.thermal-', delete=False) as tmp:
            name = tmp.name
            try:
                json.dump(self.state, tmp, indent=2, allow_nan=False)
                tmp.write('\n')
                tmp.close()
                os.replace(name, self.summary_path)
            finally:
                if os.path.exists(name):
                    os.unlink(name)

    def _sample(self):
        data = snapshot(self.pci_root, self.hwmon_root)
        with self._lock:
            self.state['samples'] += 1
            self.state.setdefault('started_utc', data['utc'])
            self.state['last_sample_utc'] = data['utc']
            for card in data['cards']:
                summary = self.state['cards'].setdefault(card['pci'], {
                    'gpu_index': card['gpu_index'], 'samples': 0, 'busy_samples': 0,
                    'sensor_samples': {}, 'peak_temperature_c': {}, 'peak_busy_temperature_c': {},
                    'throttle_samples_available': 0, 'thermal_limit_samples': None,
                    'hotspot_limit_samples': None, 'power_limit_samples': None,
                    'current_limit_samples': None})
                summary['samples'] += 1
                busy = card.get('busy_percent') is not None and card['busy_percent'] >= 10
                summary['busy_samples'] += busy
                for sensor, value in card['temperature_c'].items():
                    if value is None:
                        continue
                    summary['sensor_samples'][sensor] = summary['sensor_samples'].get(sensor, 0)+1
                    peaks = summary['peak_temperature_c']
                    peaks[sensor] = max(peaks.get(sensor, value), value)
                    if busy:
                        peaks = summary['peak_busy_temperature_c']
                        peaks[sensor] = max(peaks.get(sensor, value), value)
                for key in ('fan_rpm','power_average_w','power_input_w','gfx_clock_mhz','memory_clock_mhz','busy_percent'):
                    value = card.get(key)
                    if value is not None:
                        key = 'peak_'+key
                        summary[key] = max(summary.get(key, value), value)
                flags = card['throttle']
                summary['last_throttle_status'] = flags['status']
                if flags['status'] == 'available':
                    summary['throttle_samples_available'] += 1
                    for key in ('thermal_limit','hotspot_limit','power_limit','current_limit'):
                        name = key+'_samples'
                        summary[name] = (summary[name] or 0) + int(flags[key])
            for name, value in data['cpu_package_c'].items():
                if value is not None:
                    old = self.state['cpu_peak_package_c'].get(name, value)
                    self.state['cpu_peak_package_c'][name] = max(old, value)
            line = json.dumps(data, allow_nan=False)+'\n'
            size = len(line.encode())
            if self._file and self._raw_bytes+size <= self.max_raw_bytes:
                self._file.write(line)
                self._file.flush()
                self._raw_bytes += size
            else:
                self.state['raw_samples_dropped'] += 1
            if time.monotonic()-self._last_save >= 5:
                self._save()
                self._last_save = time.monotonic()

    def _safe_sample(self):
        try:
            self._sample()
        except Exception as error:
            with self._lock:
                self.state['sample_errors'] += 1
                self.state['last_error_type'] = type(error).__name__
                if self.state['sample_errors'] == 1:
                    print('Thermal sample failed: '+type(error).__name__, file=sys.stderr)

    def start(self):
        if self._thread is not None or self.state['status'] != 'not_started':
            return self
        try:
            self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            fd = os.open(self.raw_path, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
            self._file = os.fdopen(fd, 'w')
            self.state['status'] = 'recording'
            self._safe_sample()
            def run():
                while not self._done.wait(self.interval):
                    self._safe_sample()
            self._thread = threading.Thread(target=run, name='gpu-thermal-log', daemon=True)
            self._thread.start()
        except OSError as error:
            self.state.update(status='logging_unavailable', last_error_type=type(error).__name__)
            if self._file:
                self._file.close()
            print('Thermal logging unavailable: '+type(error).__name__, file=sys.stderr)
        return self

    def stop(self):
        self._done.set()
        if self._thread:
            self._thread.join(timeout=3)
            if self._thread.is_alive():
                self.state['status'] = 'collector_stop_timeout'
                return self.summary()
        if self.state['status'] == 'recording':
            self._safe_sample()
            with self._lock:
                self.state['status'] = 'complete' if not self.state['sample_errors'] else 'complete_with_errors'
                try:
                    self._save()
                except OSError as error:
                    self.state.update(status='summary_write_failed', last_error_type=type(error).__name__)
                if self._file:
                    self._file.close()
        return self.summary()

    def summary(self):
        with self._lock:
            return json.loads(json.dumps(self.state))

    def __enter__(self):
        return self.start()

    def __exit__(self, *_):
        self.stop()


def record_request(function):
    """Attach sampled thermals without changing a benchmark's API timing math."""
    @wraps(function)
    def measured(kind, model, *args, **kwargs):
        with ThermalRecorder(f'{kind}-{model}-request') as thermal:
            result, text = function(kind, model, *args, **kwargs)
        result['thermal'] = thermal.summary()
        return result, text
    return measured
