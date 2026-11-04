"""SSD health/thermal stop checks, independent of swap rate and wear budgets."""
import json
import math
import re
from pathlib import Path
import subprocess
import time
from temperature_policy import TEMPERATURE_LIMIT_C

SMART_MAX_AGE_SECONDS = 1200


def read_health():
    reader = Path(__file__).resolve().parents[1] / 'hardware/storage_health_read.py'
    proc = subprocess.run(['/usr/bin/python3', str(reader)], check=True,
                          capture_output=True, text=True, timeout=15)
    return json.loads(proc.stdout)


def nvme_temperatures():
    result = {}
    for controller in Path('/sys/class/nvme').glob('nvme*'):
        paths = list(controller.glob('hwmon*/temp1_input'))
        if not paths:
            raise RuntimeError('NVMe temperature telemetry missing: ' + controller.name)
        result[controller.name] = float(paths[0].read_text()) / 1000
    if not result:
        raise RuntimeError('No NVMe temperature telemetry available')
    return result


def evaluate(records, temperatures, now):
    if not isinstance(records, list) or not records or not any(r.get('nvme') for r in records):
        raise ValueError('SSD SMART inventory unavailable')
    if not temperatures:
        raise ValueError('Live NVMe temperatures unavailable')
    covered = {re.match(r'^(nvme[0-9]+)n[0-9]+$', r.get('device', '')).group(1)
               for r in records if r.get('nvme') and re.match(r'^(nvme[0-9]+)n[0-9]+$', r.get('device', ''))}
    if covered != set(temperatures):
        raise ValueError('NVMe SMART and temperature inventories differ')
    for name, value in temperatures.items():
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value < -20:
            raise ValueError('Invalid NVMe temperature: ' + name)
        if value >= TEMPERATURE_LIMIT_C:
            return f'SSD temperature at or above {TEMPERATURE_LIMIT_C:g} C: ' + name
    for record in records:
        stamp = record.get('updated')
        if type(stamp) is not int or not -60 <= now - stamp <= SMART_MAX_AGE_SECONDS:
            raise ValueError('SSD SMART telemetry stale or missing: ' + record.get('device', '?'))
        if not isinstance(record.get('critical_warning'), list):
            raise ValueError('SSD SMART warning telemetry missing')
        if record.get('critical_warning') or record.get('failing') or record.get('failing_attributes'):
            return 'SSD SMART health warning: ' + record['device']
        temp = record.get('temperature_K')
        if not isinstance(temp, (int, float)) or not math.isfinite(temp) or temp <= 0:
            raise ValueError('Invalid SSD SMART temperature')
        if temp - 273.15 >= TEMPERATURE_LIMIT_C:
            return f'SSD SMART temperature at or above {TEMPERATURE_LIMIT_C:g} C: ' + record['device']
        if record.get('nvme'):
            if any(type(record.get(k)) is not int or record[k] < 0
                   for k in ['media_errors', 'spare', 'spare_threshold']):
                raise ValueError('Invalid NVMe SMART counters')
            if record['media_errors'] or record['spare'] < record['spare_threshold']:
                return 'SSD media/spare health warning: ' + record['device']
    return None


class StorageHealthMonitor:
    def __init__(self, reader=read_health, temperatures=nvme_temperatures,
                 clock=time.monotonic, wall=time.time):
        self.reader, self.temperatures, self.clock, self.wall = reader, temperatures, clock, wall
        self.records = None
        self.last_read = -math.inf

    def check(self):
        now = self.clock()
        if self.records is None or now - self.last_read >= 30:
            self.records = self.reader()
            self.last_read = now
        reason = evaluate(self.records, self.temperatures(), self.wall())
        if reason:
            raise RuntimeError(reason)
