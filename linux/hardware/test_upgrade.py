"""Verify missing GPUs fail before shutdown and candidates preserve retained weights."""
import importlib.util
import json
from pathlib import Path
import runpy
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
import hardware_guard
import backend_switch
import llama_runtime
import rocm_runtime

spec = importlib.util.spec_from_file_location('candidates', ROOT / 'hardware/prepare-candidates.py')
candidates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidates)


def card(name):
    return {'name': 'NVIDIA GeForce ' + name, 'memory_mib': 12288}


class UpgradeTests(unittest.TestCase):
    def test_vulkan_reordering_is_resolved_before_using_preset(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, amd = base / 'dsh', base / 'amd'
            root.mkdir(); amd.mkdir()
            (amd / 'vendor').write_text('0x1002')
            (amd / 'mem_info_vram_total').write_text(str(24 * 1024**3))
            (amd / 'driver').symlink_to(base / 'amdgpu')
            (root / 'llama-runtime.json').write_text(json.dumps({'backend':'vulkan-amd', 'models':['bolt']}))
            (root / 'models-amd.ini').touch()
            binary = base / 'llama.cpp/build-vulkan/bin/llama-server'
            binary.parent.mkdir(parents=True); binary.touch()
            inventories = [
                'Vulkan0: NVIDIA GeForce RTX 4070\nVulkan1: AMD Radeon RX 7900 XTX (RADV NAVI31)\nVulkan2: AMD Radeon RX 7900 XTX (RADV NAVI31)\n',
                'Vulkan0: AMD Radeon RX 7900 XTX (RADV NAVI31)\nVulkan1: AMD Radeon RX 7900 XTX (RADV NAVI31)\n',
            ]
            with patch.object(llama_runtime, 'ROOT', root), patch.object(llama_runtime, 'amd_devices', return_value=[amd, amd]), \
                 patch.object(llama_runtime, 'require_worker_scope'), \
                 patch.object(llama_runtime.subprocess, 'run', side_effect=[
                     subprocess.CompletedProcess([], 0, text, '') for text in inventories]) as run:
                selected, preset, env, models = llama_runtime.launch_spec()
            self.assertEqual(run.call_count, 2)
            self.assertEqual(env['GGML_VK_VISIBLE_DEVICES'], '1,2')
            self.assertEqual(preset, root / 'models-amd.ini')
            self.assertEqual(models, {'bolt'})

    def test_candidate_llama_dir_selects_isolated_binary(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, amd, candidate = base / 'dsh', base / 'amd', base / 'candidate'
            root.mkdir(); amd.mkdir()
            (root / 'llama-runtime.json').write_text(json.dumps({'backend':'vulkan-amd', 'models':['bolt']}))
            (root / 'models-amd.ini').touch()
            binary = candidate / 'build-vulkan/bin/llama-server'
            binary.parent.mkdir(parents=True); binary.touch()
            inventory = 'Vulkan0: AMD Radeon RX 7900 XTX (RADV NAVI31)\nVulkan1: AMD Radeon RX 7900 XTX (RADV NAVI31)\n'
            with patch.dict(llama_runtime.os.environ, {'LLAMA_CPP_DIR': str(candidate)}), \
                 patch.object(llama_runtime, 'ROOT', root), patch.object(llama_runtime, 'amd_devices', return_value=[amd, amd]), \
                 patch.object(llama_runtime, 'require_worker_scope'), \
                 patch.object(llama_runtime.subprocess, 'run', side_effect=[
                     subprocess.CompletedProcess([], 0, inventory, '')] * 2):
                selected, _, _, _ = llama_runtime.launch_spec()
            self.assertEqual(selected, binary)

    def test_rocm_profile_headroom_can_be_stricter_than_default(self):
        with tempfile.TemporaryDirectory() as directory:
            amd = Path(directory)
            (amd / 'mem_info_vram_total').write_text(str(24 * 1024**3))
            (amd / 'mem_info_vram_used').write_text(str(int(1.5 * 1024**3)))
            with patch.object(rocm_runtime, 'amd_devices', return_value=[amd, amd]), patch.object(rocm_runtime.time, 'sleep'):
                rocm_runtime.require_rocm_headroom()
                with self.assertRaisesRegex(RuntimeError, '23 GiB'):
                    rocm_runtime.require_rocm_headroom(23)
                (amd / 'mem_info_vram_used').write_text(str(int(.5 * 1024**3)))
                rocm_runtime.require_rocm_headroom(23)

    def test_disabled_hyperqwen_preserves_active_backend(self):
        with self.assertRaisesRegex(RuntimeError, 'HyperQwen is retired'):
            hardware_guard.require_hyperqwen()

    def test_disabled_hyperqwen_not_advertised(self):
        gateway_spec = importlib.util.spec_from_file_location('gateway', ROOT / 'network/gateway.py')
        gateway = importlib.util.module_from_spec(gateway_spec)
        gateway_spec.loader.exec_module(gateway)
        self.assertFalse(any('hyperqwen' in model for model in gateway.catalog()))
        self.assertIn('qwen3.8-flash-next-iq3_xxs', gateway.catalog())

    def test_current_pair_is_accepted(self):
        hardware_guard.require_current_cuda_pair([card('RTX 4070'), card('RTX 3060')])

    def test_missing_wrong_and_reordered_devices_are_blocked(self):
        for devices in ([], [card('RTX 4070')], [card('RTX 3060'), card('RTX 4070')],
                        [card('RTX 4070'), card('RTX 4090')]):
            with self.subTest(devices=devices), self.assertRaises(RuntimeError):
                hardware_guard.require_current_cuda_pair(devices)

    def test_all_stale_launchers_fail_without_handover(self):
        for kind in ('strata', 'hyperqwen'):
            with self.subTest(kind=kind), \
                 patch.object(sys, 'argv', ['launch-backend.py', kind]), \
                 patch.object(hardware_guard, 'nvidia_inventory', return_value=[card('RTX 4070')]), \
                 patch('strata_runtime.amd_devices', side_effect=RuntimeError('AMD unavailable')), \
                 patch.object(backend_switch, 'startup_handover') as handover, \
                 patch.object(backend_switch, 'clear_owner'), \
                 self.assertRaises(SystemExit) as result:
                runpy.run_path(str(ROOT / 'dsh/launch-backend.py'), run_name='__main__')
            self.assertEqual(result.exception.code, 1)
            handover.assert_not_called()

    def test_missing_rocm_device_fails_before_handover(self):
        for kind in ('sglang', 'vllm'):
            with self.subTest(kind=kind), \
                 patch.object(sys, 'argv', ['launch-backend.py', kind]), \
                 patch.object(rocm_runtime, 'require_rocm', side_effect=RuntimeError('AMD unavailable')) as probe, \
                 patch.object(hardware_guard, 'require_current_cuda_pair') as cuda_guard, \
                 patch.object(backend_switch, 'startup_handover') as handover, \
                 patch.object(backend_switch, 'clear_owner'), self.assertRaises(SystemExit):
                runpy.run_path(str(ROOT / 'dsh/launch-backend.py'), run_name='__main__')
            probe.assert_called_once_with(kind)
            handover.assert_not_called()
            cuda_guard.assert_not_called()

    def test_nvme_rocm_launchers_do_not_require_shared_mount(self):
        import shared_storage
        for kind in ('sglang', 'vllm'):
            with self.subTest(kind=kind), \
                 patch.object(sys, 'argv', ['launch-backend.py', kind]), \
                 patch.object(rocm_runtime, 'require_rocm'), \
                 patch.object(shared_storage, 'ensure_shared_models', side_effect=RuntimeError('Shared absent')) as mount, \
                 patch.object(backend_switch, 'startup_handover', side_effect=RuntimeError('Reached handover')) as handover, \
                 patch.object(backend_switch, 'clear_owner'), self.assertRaises(SystemExit):
                runpy.run_path(str(ROOT / 'dsh/launch-backend.py'), run_name='__main__')
            mount.assert_not_called()
            handover.assert_called_once_with(kind)

    def test_invalid_amd_runtime_fails_without_handover(self):
        with patch.object(sys, 'argv', ['launch-backend.py', 'llama']), \
             patch.object(llama_runtime, 'launch_spec', side_effect=RuntimeError('AMD unavailable')), \
             patch.object(backend_switch, 'startup_handover') as handover, \
             patch.object(backend_switch, 'clear_owner'), self.assertRaises(SystemExit) as result:
            runpy.run_path(str(ROOT / 'dsh/launch-backend.py'), run_name='__main__')
        self.assertEqual(result.exception.code, 1)
        handover.assert_not_called()

    def test_strata_preserves_weights_mtp_and_source(self):
        source = json.loads((ROOT / 'dsh/strata-iq3-profile.json').read_text())
        original = json.dumps(source)
        cfg = candidates.strata_candidate(source)
        self.assertEqual(json.dumps(source), original)
        self.assertEqual(cfg['gpu'], [0, 1])
        self.assertFalse(cfg['split_skip_if_fits'])
        self.assertEqual(cfg['parallel'], 1)
        self.assertEqual(cfg['backend'], 'hip')
        for option in ('--native', '--pack', '--ple-gguf', '--mtp', '--spec'):
            self.assertEqual(cfg['args'][cfg['args'].index(option)+1],
                             source['args'][source['args'].index(option)+1])
        self.assertIn('--resident-cpu-experts', cfg['args'])
        self.assertTrue(any('rocm-sdk' in path for path in cfg['lib_dirs']))
        self.assertFalse(any(path.endswith('cuda-build/lib64') for path in cfg['lib_dirs']))
        self.assertEqual(cfg['minimum_host_ram_gib'], 29)
        future = candidates.strata_candidate(source, 64)
        self.assertEqual(future['minimum_host_ram_gib'], 60)
        self.assertIn('262144', future['args'])
        for candidate in (cfg, future):
            self.assertGreaterEqual(int(candidate['args'][candidate['args'].index('--vram-reserve-mib')+1]), 6144)
            self.assertEqual(candidate['layer_split'], source['layer_split'])
            self.assertEqual(candidate['env'], source['env'])

    def test_llama_does_not_inherit_dual_cuda_overrides(self):
        text = candidates.llama_candidate((ROOT / 'dsh/models.ini').read_text())
        self.assertIn('AMD_VULKAN_DEVICE', text)
        self.assertNotIn('CUDA', text)
        self.assertNotIn('tensor-split', text)
        self.assertIn('ctx-size = 32768', text)


if __name__ == '__main__':
    unittest.main()
