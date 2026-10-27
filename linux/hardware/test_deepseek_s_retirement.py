"""Catalog and download invariants for retaining XS without a full S installation."""
import json
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
from model_catalog import catalog

class Retirement(unittest.TestCase):
    def test_both_xs_aliases_remain_and_retired_s_cannot_be_selected(self):
        models = catalog(ROOT)
        self.assertEqual(len(models), 11)
        self.assertIn('deepseek-v4.1-flash-1017-maya', models)
        self.assertIn('deepseek-v4.1-flash-1017-strata-xs', models)
        for model in ['deepseek-v4.1-flash-1017-maya-s', 'deepseek-v4.1-flash-1017-strata-s']:
            self.assertNotIn(model, models)

    def test_active_manifest_keeps_shared_engram_and_excludes_retired_assets(self):
        files = [row['file'] for row in json.loads((ROOT / 'maya/models.json').read_text())['files']]
        s = [name for name in files if '/Maya-S/' in name]
        self.assertEqual(len(s), 2)
        self.assertTrue(any('00005-of-00006.gguf' in name for name in s))
        self.assertTrue(any('00006-of-00006.gguf' in name for name in s))
        self.assertFalse(any(name.endswith('/dspark.bin') or name.endswith('/dspark.json') for name in files))
        self.assertTrue(any(name.endswith('/dspark-xs2.bin') for name in files))
        old = json.loads((ROOT / 'maya/deepseek-s-rollback-models.json').read_text())
        self.assertEqual(old['status'], 'retired'); self.assertEqual(old['files'], [])
        self.assertTrue(old['historical_files'])
