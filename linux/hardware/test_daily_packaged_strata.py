"""The source-tree updater must preserve independently qualified package pins."""
from pathlib import Path
import importlib.util
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
spec = importlib.util.spec_from_file_location('daily_package_test', ROOT / 'hardware/daily-update/daily_update.py')
daily = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily)


class PackagePin(unittest.TestCase):
    def test_source_update_selects_only_enabled_source_tree_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'dsh').mkdir()
            profiles = {'gsq': {'enabled': True},
                        'iq1m': {'enabled': True, 'qualified_qwen_package': True},
                        'held': {'enabled': False},
                        'deepseek': {'enabled': True, 'family': 'deepseek41'}}
            (root / 'dsh/strata-profiles.json').write_text(json.dumps(profiles))
            with patch.object(daily, 'ROOT', root):
                self.assertEqual(daily.Strata().models(), ['gsq'])


if __name__ == '__main__':
    unittest.main()
