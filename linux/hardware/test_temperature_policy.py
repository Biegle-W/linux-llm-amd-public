"""Thermal boundary checks without GPU access, process launch or sensor I/O."""
from pathlib import Path
import copy
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dsh'))
from temperature_policy import temperature_failure


class TemperaturePolicy(unittest.TestCase):
    def reading(self):
        return {
            'cards': [
                {'temperature_c': {'edge': 99.99, 'junction': 99.99, 'mem': 99.99},
                 'temperature_critical_c': {'edge': 95, 'junction': 110, 'mem': 108}},
                {'temperature_c': {'edge': 99.99, 'junction': 99.99, 'mem': 99.99}}],
            'cpu_package_c': {'Package id 0': 99.99}}

    def test_all_sampled_sensors_stop_at_100(self):
        baseline = self.reading()
        self.assertIsNone(temperature_failure(baseline))
        for card_index in range(2):
            for sensor in ['edge', 'junction', 'mem']:
                for temperature in [100, 100.01]:
                    with self.subTest(card=card_index, sensor=sensor, temperature=temperature):
                        reading = copy.deepcopy(baseline)
                        reading['cards'][card_index]['temperature_c'][sensor] = temperature
                        self.assertIn('GPU temperature', temperature_failure(reading))
        for temperature in [100, 100.01]:
            reading = copy.deepcopy(baseline)
            reading['cpu_package_c']['Package id 0'] = temperature
            self.assertIn('CPU temperature', temperature_failure(reading))

    def test_cpu_check_remains_scoped_to_controllers_that_enable_it(self):
        reading = self.reading()
        reading['cpu_package_c']['Package id 0'] = 100
        self.assertIsNone(temperature_failure(reading, check_cpu=False))

    def test_critical_sensor_values_are_not_rewritten(self):
        reading = self.reading()
        original = copy.deepcopy(reading)
        self.assertIsNone(temperature_failure(reading))
        self.assertEqual(reading, original)

    def test_existing_optional_sensor_values_remain_optional(self):
        reading = self.reading()
        reading['cards'][0]['temperature_c']['mem'] = None
        reading['cpu_package_c']['Package id 0'] = None
        self.assertIsNone(temperature_failure(reading))


if __name__ == '__main__':
    unittest.main()
