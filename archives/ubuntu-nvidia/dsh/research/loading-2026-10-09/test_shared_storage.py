"""Regression checks for missing and incorrect Shared mounts."""
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import shared_storage as storage


class SharedStorageTests(unittest.TestCase):
    def setUp(self):
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def test_existing_mount_does_not_call_udisks(self):
        with patch.object(storage, 'mounted_uuid', return_value=storage.UUID), \
             patch.object(Path, 'is_dir', return_value=True), \
             patch.object(subprocess, 'run') as run:
            storage.ensure_shared_models()
            run.assert_not_called()

    def test_wrong_drive_is_rejected(self):
        with patch.object(storage, 'mounted_uuid', return_value='WRONG'), \
             patch.object(subprocess, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'different drive'):
                storage.ensure_shared_models()
            run.assert_not_called()

    def test_disconnected_drive_is_reported(self):
        with patch.object(storage, 'mounted_uuid', return_value=''), \
             patch.object(Path, 'exists', return_value=False):
            with self.assertRaisesRegex(RuntimeError, 'unavailable'):
                storage.ensure_shared_models()

    def test_mount_recovery(self):
        with patch.object(storage, 'mounted_uuid', side_effect=['', storage.UUID]), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'is_dir', return_value=True), \
             patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')) as run:
            storage.ensure_shared_models()
            self.assertIn('--no-user-interaction', run.call_args.args[0])
            self.assertIn('/dev/disk/by-uuid/' + storage.UUID, run.call_args.args[0])

    def test_mount_failure_is_clear(self):
        with patch.object(storage, 'mounted_uuid', return_value=''), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'Not authorized')):
            with self.assertRaisesRegex(RuntimeError, 'Cannot mount Shared.*Not authorized'):
                storage.ensure_shared_models()

    def test_missing_model_directory_is_reported(self):
        with patch.object(storage, 'mounted_uuid', return_value=storage.UUID), \
             patch.object(Path, 'is_dir', return_value=False):
            with self.assertRaisesRegex(RuntimeError, 'GGUF-Models is missing'):
                storage.ensure_shared_models()


if __name__ == '__main__':
    unittest.main()
