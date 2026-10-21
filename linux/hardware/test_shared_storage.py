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
            with patch.object(storage, 'mounted_uuid', side_effect=['', 'EXPECTED', 'EXPECTED']) as inspect, \
                    patch.object(storage.Path, 'exists', return_value=True), \
                    patch.object(storage.subprocess, 'run') as run:
                storage.ensure_model_drive(root, models, 'EXPECTED', 'Test NVMe')
            self.assertEqual(inspect.call_args_list, [unittest.mock.call(root)] * 3)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0],
                             ['udisksctl', 'mount', '--block-device',
                              '/dev/disk/by-uuid/EXPECTED', '--no-user-interaction'])
            self.assertNotIn('shell', run.call_args.kwargs)

    def test_refused_session_mount_retries_through_user_manager(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'models').mkdir()
            # SSH: the direct mount leaves it unmounted; the user-manager retry mounts it.
            with patch.object(storage, 'mounted_uuid', side_effect=['', '', 'EXPECTED', 'EXPECTED']), \
                    patch.object(storage.Path, 'exists', return_value=True), \
                    patch.object(storage.subprocess, 'run') as run:
                storage.ensure_model_drive(root, root/'models', 'EXPECTED', 'Test')
            direct, retry = (call.args[0] for call in run.call_args_list)
            self.assertEqual(direct[:2], ['udisksctl', 'mount'])
            self.assertEqual(retry[:2], ['systemd-run', '--user'])
            self.assertEqual(retry[-len(direct):], direct)
            self.assertIn('--no-user-interaction', retry)

    def test_failed_mount_explains_session_requirement_without_creating_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(storage, 'mounted_uuid', return_value=''), \
                    patch.object(storage.Path, 'exists', return_value=True), \
                    patch.object(storage.subprocess, 'run'), \
                    self.assertRaisesRegex(RuntimeError, 'active local session'):
                storage.ensure_model_drive(root, root/'models', 'EXPECTED', 'Test')
            self.assertFalse((root/'models').exists())

    def test_llama_presets_mount_every_referenced_volume_once(self):
        with tempfile.TemporaryDirectory() as directory:
            preset = Path(directory)/'models.ini'
            preset.write_text('[a]\nmodel = ' + str(storage.MODELS/'A/a.gguf') + '\n'
                              '[b]\nmodel = ' + str(storage.MODELS/'B/b.gguf') + '\n'
                              '[super]\nmodel = ' + str(storage.STREAM_MODELS/'Nemotron-Super/x.gguf') + '\n')
            with patch.object(storage, 'ensure_model_drive') as ensure:
                storage.ensure_llama_models([preset])
            self.assertEqual(sorted(call.args[3] for call in ensure.call_args_list), ['Shared NVMe', 'sharedSATA1'])

    def test_model_outside_configured_volumes_is_refused_before_mounting(self):
        with patch.object(storage, 'ensure_model_drive') as ensure, self.assertRaisesRegex(RuntimeError, 'outside'):
            storage.ensure_model_paths([storage.MODELS/'ok.gguf', Path('/tmp/elsewhere/model.gguf')])
        ensure.assert_not_called()

    def test_login_mount_reports_required_failures_and_skips_absent_spare(self):
        volumes = (('Required', 'REQ', Path('/r'), Path('/r/models'), True),
                   ('Spare', 'SPARE', Path('/s'), None, False))
        def ensure(mount, models, uuid, label):
            raise RuntimeError(label + ' unavailable')
        with patch.object(storage, 'VOLUMES', volumes), \
                patch.object(storage.Path, 'exists', return_value=False), \
                patch.object(storage.time, 'sleep'), \
                patch.object(storage, 'ensure_model_drive', side_effect=ensure), \
                patch.object(storage, 'mount_by_uuid') as mount:
            self.assertEqual(storage.mount_all(wait=0), ['Required'])
        mount.assert_not_called()

    def test_login_mount_waits_for_a_late_device(self):
        volumes = (('Required', 'REQ', Path('/r'), Path('/r/models'), True),)
        appearances = iter([False, False, True])
        with patch.object(storage, 'VOLUMES', volumes), \
                patch.object(storage.Path, 'exists', side_effect=lambda: next(appearances, True)), \
                patch.object(storage.time, 'sleep') as sleep, \
                patch.object(storage, 'ensure_model_drive') as ensure:
            self.assertEqual(storage.mount_all(wait=60), [])
        self.assertEqual(sleep.call_count, 2)
        ensure.assert_called_once_with(Path('/r'), Path('/r/models'), 'REQ', 'Required')

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
