"""The Strata backend's Hy4-Flash family: both cards, expert parallel, capped VRAM experts, its own asset list."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dsh'))
import strata_runtime

GIB = 1024**3


def config():
    return {'arch': 'hy4flash', 'backend': 'hip', 'gpu': [0, 1], 'parallel': 1, 'worker_swap_max_bytes': None,
            'minimum_host_ram_gib': 29, 'tokenizer': '/t',
            'env': {'ROCR_VISIBLE_DEVICES': '0,1', 'HIP_VISIBLE_DEVICES': '0,1', 'HY4_DEC_PCIE_SHARE': '0', 'HY4_HIP_PEERS': '1'},
            'args': ['--native', '/m/a.strata', '--engram', '/m/e.strata', '--max-context', '32768', '--vision', '/m/v.strata',
                     '--vram-experts-gb', '32.0', '--ram-experts-gb', '24.5']}


class Hy4Family(unittest.TestCase):
    def test_assets_are_the_three_shards_and_tokenizer(self):
        names = [str(p) for p in strata_runtime.hy4_weight_assets(config())]
        self.assertEqual(names, ['/m/a.strata', '/m/e.strata', '/m/v.strata', '/t/vocab.json', '/t/merges.txt',
                                 '/t/chat_template.jinja', '/t/token_type.json', '/t/tokenizer.json'])

    def test_two_card_profile_is_admitted(self):
        strata_runtime.check_hy4_config(config(), 63 * GIB, 40 * GIB)

    def test_other_placements_are_refused(self):
        for change in ({'gpu': 1}, {'gpu': [1, 0]}, {'parallel': 2}, {'backend': 'cuda'}, {'arch': 'inkling2_loop'},
                       {'worker_swap_max_bytes': 1}, {'layer_split': 'auto'}):
            cfg = config(); cfg.update(change)
            with self.assertRaises(RuntimeError):
                strata_runtime.check_hy4_config(cfg, 63 * GIB, 40 * GIB)
        for extra in (['--gpus', '0,1'], ['--parallel', '2'], ['--layer-split', 'auto'], ['--gpu=1']):
            cfg = config(); cfg['args'] += extra
            with self.assertRaises(RuntimeError):
                strata_runtime.check_hy4_config(cfg, 63 * GIB, 40 * GIB)

    def test_expert_caps_are_required_and_bounded(self):
        for flag, value in (('--vram-experts-gb', '33'), ('--vram-experts-gb', 'x'), ('--ram-experts-gb', '30'), ('--vram-experts-gb', '0')):
            cfg = config(); cfg['args'][cfg['args'].index(flag) + 1] = value
            with self.assertRaises(RuntimeError):
                strata_runtime.check_hy4_config(cfg, 63 * GIB, 40 * GIB)
        cfg = config(); del cfg['args'][-4:-2]
        with self.assertRaises(RuntimeError):
            strata_runtime.check_hy4_config(cfg, 63 * GIB, 40 * GIB)

    def test_card_order_and_pcie_share_are_checked(self):
        for env in ({}, {'ROCR_VISIBLE_DEVICES': '1,0', 'HIP_VISIBLE_DEVICES': '0,1', 'HY4_DEC_PCIE_SHARE': '0'},
                    {'ROCR_VISIBLE_DEVICES': '0,1', 'HIP_VISIBLE_DEVICES': '0,1'}):
            cfg = config(); cfg['env'] = env
            with self.assertRaises(RuntimeError):
                strata_runtime.check_hy4_config(cfg, 63 * GIB, 40 * GIB)

    def test_free_ram_floor_and_physical_ram_apply(self):
        with self.assertRaises(RuntimeError):
            strata_runtime.check_hy4_config(config(), 16 * GIB, 12 * GIB)
        with self.assertRaises(RuntimeError):
            strata_runtime.check_hy4_config(config(), 63 * GIB, GIB // 2)


if __name__ == '__main__':
    unittest.main()
