"""A failed dual-GPU profile must not unload a working model or be advertised."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
source = (ROOT / 'dsh/sglang-profiles.json').read_text()
spec = importlib.util.spec_from_file_location('sglang_router_test', ROOT / 'dsh/sglang-router.py')
router = importlib.util.module_from_spec(spec)
with patch.object(Path, 'read_text', return_value=source):
    spec.loader.exec_module(router)


class ProfileTests(unittest.TestCase):
    def test_disabled_profile_rejected_before_stopping_worker(self):
        with patch.object(router, 'stop_worker') as stop, \
                patch.object(router.subprocess, 'Popen') as start:
            with self.assertRaisesRegex(RuntimeError, 'blocked'):
                router.ensure_worker('qwen3.8-27b-sglang')
            stop.assert_not_called()
            start.assert_not_called()

    def test_catalog_hides_failed_profile_and_keeps_working_default(self):
        handler = object.__new__(router.Handler)
        handler.path = '/v1/models'
        handler.send_json = Mock()
        handler.do_GET()
        status, payload = handler.send_json.call_args.args
        self.assertEqual(status, 200)
        ids = {row['id'] for row in payload['data']}
        self.assertNotIn('qwen3.8-27b-sglang', ids)
        self.assertIn(router.DEFAULT, ids)
        self.assertTrue(router.PROFILES[router.DEFAULT].get('enabled', True))


if __name__ == '__main__':
    unittest.main()
