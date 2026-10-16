"""Keep reduced-RAM machines blocked without treating swap as expert capacity."""
import importlib.util
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location('strata_ready', Path(__file__).with_name('check-strata-ready.py'))
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


class StrataMemoryTests(unittest.TestCase):
    def test_32gb_is_blocked_even_with_large_available_value(self):
        self.assertTrue(checks.memory_blockers(31*checks.GIB, 64*checks.GIB))

    def test_restored_but_busy_ram_is_blocked(self):
        self.assertTrue(checks.memory_blockers(61*checks.GIB, 30*checks.GIB))

    def test_restored_ram_with_headroom_clears_memory_only(self):
        self.assertEqual(checks.memory_blockers(61*checks.GIB, 50*checks.GIB), [])


if __name__ == '__main__':
    unittest.main()
