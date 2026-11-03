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
    def test_new_static_models_use_sata1_checkpoint_directory(self):
        target = storage.SHARED / 'vLLM-Models'
        self.assertEqual(storage.NEW_MODEL_DIRS['static'], target)
        from types import SimpleNamespace
        with patch.object(storage, 'ensure_model_drive') as ensure, \
                patch.object(storage.shutil, 'disk_usage', return_value=SimpleNamespace(total=1000, used=100)):
            self.assertEqual(storage.new_model_dir('static', 200), target)
        ensure.assert_called_once_with(storage.SHARED, target, storage.UUID, 'sharedSATA1')

    def test_vllm_checkpoint_on_sata1_mounts_only_sata1(self):
        checkpoint = storage.SHARED / 'vLLM-Models' / 'Bolt'
        with patch.object(storage, 'ensure_model_drive') as ensure:
            storage.ensure_vllm_models({'bolt': {'model_path': str(checkpoint)}})
        ensure.assert_called_once_with(storage.SHARED, checkpoint.parent, storage.UUID, 'sharedSATA1')

    def test_retired_sata2_is_not_discovered_or_admitted(self):
        self.assertEqual({row[0] for row in storage.VOLUMES}, {'sharedSATA1'})
        with patch.object(storage, 'ensure_model_drive') as ensure, \
                patch.object(storage.Path, 'exists', return_value=True):
            self.assertEqual(storage.mount_all(wait=0), [])
        self.assertEqual(ensure.call_count, 1)
        old_path = storage.SHARED.with_name('sharedSATA2') / 'vLLM-Models' / 'Bolt'
        with patch.object(storage, 'ensure_model_drive') as ensure, self.assertRaises(RuntimeError):
            storage.ensure_model_paths([old_path])
        ensure.assert_not_called()

    def test_bolt_profile_and_launcher_use_sata1(self):
        root = Path(__file__).resolve().parents[1]
        model = storage.SHARED / 'vLLM-Models' / 'Nemotron-3.5-Bolt-74B-A9B-AutoRound-W4A16'
        profile = json.loads((root / 'dsh/vllm-profiles.json').read_text())['nemotron-3.5-bolt-vllm']
        self.assertEqual(profile['model_path'], str(model))
        launcher = (root / 'vllm/start-bolt-rocm').read_text()
        self.assertIn('MODEL=' + str(model), launcher)
        self.assertIn('"$MODEL/ultra_v3_reasoning_parser.py"', launcher)

    def test_static_placement_still_rejects_the_ninety_percent_boundary(self):
        from types import SimpleNamespace
        with patch.object(storage, 'ensure_model_drive'), \
                patch.object(storage.shutil, 'disk_usage', return_value=SimpleNamespace(total=1000, used=700)):
            with self.assertRaises(RuntimeError):
                storage.new_model_dir('static', 200)

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
            self.assertEqual(sorted(call.args[3] for call in ensure.call_args_list), ['sharedSATA1'])

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


    def test_system_streaming_requires_no_external_mount(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(storage, 'STREAM_MODELS', Path(folder)), patch.object(storage, 'ensure_model_drive') as mount:
                storage.ensure_streaming_models()
            mount.assert_not_called()

    def test_missing_system_streaming_root_is_refused_without_mounting(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(storage, 'STREAM_MODELS', Path(folder)/'absent'), patch.object(storage, 'ensure_model_drive') as mount:
                with self.assertRaisesRegex(RuntimeError, 'System-drive'):
                    storage.ensure_streaming_models()
            mount.assert_not_called()

    def test_retired_sabrent_path_is_not_admitted(self):
        with patch.object(storage, 'ensure_model_drive') as mount:
            with self.assertRaisesRegex(RuntimeError, 'outside'):
                storage.ensure_model_paths([storage.STREAM_SHARED/'LLM-Models/model.gguf'])
        mount.assert_not_called()


    def test_qwen_main_and_draft_share_one_sata_mount_check(self):
        cfg = {'model_path': str(storage.STATIC_MODELS/'Qwen/main'),
               'extra_args': ['--speculative-draft-model-path', str(storage.STATIC_MODELS/'drafts/Qwen')]}
        with patch.object(storage, 'ensure_model_drive') as ensure:
            storage.ensure_sglang_models(cfg)
        ensure.assert_called_once_with(storage.SHARED, storage.STATIC_MODELS, storage.UUID, 'sharedSATA1')

    def test_unknown_sglang_draft_is_refused_before_mounting(self):
        cfg = {'model_path': str(storage.STATIC_MODELS/'Qwen/main'),
               'extra_args': ['--speculative-draft-model-path=/tmp/unknown/draft']}
        with patch.object(storage, 'ensure_model_drive') as ensure, self.assertRaisesRegex(RuntimeError, 'outside'):
            storage.ensure_sglang_models(cfg)
        ensure.assert_not_called()

    def test_malformed_draft_option_is_refused_before_mounting(self):
        cfg = {'model_path': str(storage.STATIC_MODELS/'Qwen/main'),
               'extra_args': ['--speculative-draft-model-path', '--other-option']}
        with patch.object(storage, 'ensure_model_drive') as ensure, self.assertRaisesRegex(RuntimeError, 'Missing'):
            storage.ensure_sglang_models(cfg)
        ensure.assert_not_called()

    def test_vllm_preflight_admits_configured_sanitized_mount_root(self):
        mount = Path('/mnt/test-model-drive')
        with patch.object(storage, 'SHARED', mount), patch.object(storage, 'STATIC_MODELS', mount/'vLLM-Models'), \
                patch.object(storage, 'ensure_model_drive') as ensure:
            storage.ensure_vllm_models({'qwen': {'model_path': str(mount/'vLLM-Models/Qwen')}})
        ensure.assert_called_once_with(mount, mount/'vLLM-Models', storage.UUID, 'sharedSATA1')


    def test_new_streaming_placement_verifies_mount_before_creating_directory(self):
        with patch.object(storage, 'mounted_uuid', return_value='WRONG'), patch.object(Path, 'mkdir') as mkdir:
            with self.assertRaisesRegex(RuntimeError, 'different drive'):
                storage.new_model_dir('streaming', 100)
        mkdir.assert_not_called()

    def test_new_streaming_placement_keeps_capacity_limit(self):
        from types import SimpleNamespace
        with patch.object(storage, 'ensure_model_drive') as ensure, patch.object(Path, 'mkdir'), \
                patch.object(storage.shutil, 'disk_usage', return_value=SimpleNamespace(total=1000, used=800)):
            with self.assertRaisesRegex(RuntimeError, 'limit 90%'):
                storage.new_model_dir('streaming', 100)
        ensure.assert_called_once_with(storage.NEW_STREAM_SHARED, storage.NEW_STREAM_SHARED,
                                       storage.NEW_STREAM_UUID, 'new streaming NVMe')

    def test_new_streaming_paths_verify_the_new_volume(self):
        with patch.object(storage, 'ensure_model_drive') as ensure:
            storage.ensure_model_paths([storage.NEW_STREAM_MODELS/'Coder/model.gguf'])
        ensure.assert_called_once_with(storage.NEW_STREAM_SHARED, storage.NEW_STREAM_MODELS,
                                       storage.NEW_STREAM_UUID, 'new streaming NVMe')


if __name__ == '__main__':
    unittest.main()
