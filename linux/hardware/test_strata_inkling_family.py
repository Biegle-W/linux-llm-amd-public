"""The Strata backend's Inkling 2 Mini family: one card, sealed package, its own asset list."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dsh'))
import strata_runtime

GIB = 1024**3


def config():
    return {'arch': 'inkling2_loop', 'backend': 'hip', 'gpu': 1, 'parallel': 1, 'worker_swap_max_bytes': None,
            'minimum_host_ram_gib': 29, 'tokenizer': '/t', 'env': {'ROCR_VISIBLE_DEVICES': '0,1', 'HIP_VISIBLE_DEVICES': '0,1'},
            'args': ['--native', '/m/a.strata', '--vision', '/m/v.strata', '--max-context', '32768', '--gpu', '1']}


class InklingFamily(unittest.TestCase):
    def test_assets_are_the_checkpoint_vision_and_tokenizer(self):
        names = [str(p) for p in strata_runtime.inkling_weight_assets(config())]
        self.assertEqual(names, ['/m/a.strata', '/m/v.strata', '/t/vocab.json', '/t/merges.txt', '/t/chat_template.jinja'])

    def test_vision_is_optional(self):
        cfg = config(); cfg['args'] = ['--native', '/m/a.strata', '--max-context', '32768', '--gpu', '1']
        self.assertEqual(len(strata_runtime.inkling_weight_assets(cfg)), 4)

    def test_single_card_profile_is_admitted(self):
        strata_runtime.check_inkling_config(config(), 63 * GIB, 40 * GIB)

    def test_two_cards_parallel_or_other_card_are_refused(self):
        for change in ({'gpu': [0, 1]}, {'parallel': 2}, {'backend': 'cuda'}, {'arch': 'flash_next'}, {'worker_swap_max_bytes': 1}):
            cfg = config(); cfg.update(change)
            with self.assertRaises(RuntimeError):
                strata_runtime.check_inkling_config(cfg, 63 * GIB, 40 * GIB)
        for extra in (['--gpus', '2'], ['--parallel', '4']):
            cfg = config(); cfg['args'] += extra
            with self.assertRaises(RuntimeError):
                strata_runtime.check_inkling_config(cfg, 63 * GIB, 40 * GIB)
        for env in ({}, {'ROCR_VISIBLE_DEVICES': '1,0', 'HIP_VISIBLE_DEVICES': '0,1'}):
            cfg = config(); cfg['env'] = env
            with self.assertRaises(RuntimeError):
                strata_runtime.check_inkling_config(cfg, 63 * GIB, 40 * GIB)
        cfg = config(); cfg['args'][-1] = '0'
        with self.assertRaises(RuntimeError):
            strata_runtime.check_inkling_config(cfg, 63 * GIB, 40 * GIB)

    def test_free_ram_floor_and_physical_ram_apply(self):
        with self.assertRaises(RuntimeError):
            strata_runtime.check_inkling_config(config(), 16 * GIB, 12 * GIB)
        with self.assertRaises(RuntimeError):
            strata_runtime.check_inkling_config(config(), 63 * GIB, GIB // 2)


if __name__ == '__main__':
    unittest.main()
