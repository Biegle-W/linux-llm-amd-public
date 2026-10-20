"""Model-volume safety: reject wrong disks and preserve backend-specific mounts."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dsh'))
import shared_storage as storage


class ModelVolumeTests(unittest.TestCase):
    def test_wrong_uuid_never_attempts_mount_or_creates_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(storage, 'mounted_uuid', return_value='OTHER-DISK'), \
                    patch.object(storage.subprocess, 'run') as run, self.assertRaises(RuntimeError):
                storage.ensure_model_drive(root, root/'models', 'EXPECTED', 'Test')
            run.assert_not_called()
            self.assertFalse((root/'models').exists())

    def test_missing_model_directory_is_not_silently_created(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(storage, 'mounted_uuid', return_value='EXPECTED'), self.assertRaises(RuntimeError):
                storage.ensure_model_drive(root, root/'models', 'EXPECTED', 'Test')
            self.assertFalse((root/'models').exists())

    def test_unmounted_volume_is_mounted_by_uuid_and_rechecked(self):
        with tempfile.TemporaryDirectory(prefix='shared nvme ') as directory:
            root = Path(directory)
            models = root/'LLM-Models'
            models.mkdir()
            with patch.object(storage, 'mounted_uuid', side_effect=['', 'EXPECTED']) as inspect, \
                    patch.object(storage.Path, 'exists', return_value=True), \
                    patch.object(storage.subprocess, 'run') as run:
                storage.ensure_model_drive(root, models, 'EXPECTED', 'Test NVMe')
            self.assertEqual(inspect.call_args_list, [unittest.mock.call(root), unittest.mock.call(root)])
            self.assertEqual(run.call_args.args[0],
                             ['udisksctl', 'mount', '--block-device',
                              '/dev/disk/by-uuid/EXPECTED', '--no-user-interaction'])
            self.assertNotIn('shell', run.call_args.kwargs)

    def test_strata_uses_only_its_configured_volume(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory)/'profile.json'
            for model_root, selected in ((storage.STREAM_MODELS, 'nvme'), (storage.MODELS, 'sata')):
                with self.subTest(selected=selected):
                    config.write_text(json.dumps({'args':['--pack',str(model_root/'Strata/packs/iq3_xxs')]}))
                    with patch.object(storage, 'ensure_streaming_models') as nvme, \
                            patch.object(storage, 'ensure_shared_models') as sata:
                        storage.ensure_strata_models(config)
                    (nvme if selected=='nvme' else sata).assert_called_once_with()
                    (sata if selected=='nvme' else nvme).assert_not_called()

    def test_unknown_strata_volume_does_not_mount_either_disk(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory)/'profile.json'
            config.write_text(json.dumps({'args':['--pack',str(Path(directory)/'unexpected')]}))
            with patch.object(storage, 'ensure_streaming_models') as nvme, \
                    patch.object(storage, 'ensure_shared_models') as sata, self.assertRaises(RuntimeError):
                storage.ensure_strata_models(config)
            nvme.assert_not_called(); sata.assert_not_called()


if __name__ == '__main__':
    unittest.main()
