"""The Strata backend's Inkling 2 Mini family: one card or second-card-led expert parallel, sealed package, its own asset list."""
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
        for extra in (['--gpus', '1,0', '--ep-split', '0.6'], ['--parallel', '4']):
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

    def two_card(self, gpus='1,0', split='0.6'):
        cfg = config(); a = cfg['args']; i = a.index('--gpu'); del a[i:i + 2]
        a += ['--gpus', gpus] + (['--ep-split', split] if split else []) + ['--kv', 'fp16']
        a[a.index('--max-context') + 1] = '262144'
        return cfg

    def test_two_card_expert_parallel_led_by_second_card_is_admitted(self):
        strata_runtime.check_inkling_config(self.two_card(), 63 * GIB, 40 * GIB)

    def test_two_card_must_lead_with_second_card_and_keep_most_experts_there(self):
        for kw in ({'gpus': '0,1'}, {'gpus': '1'}, {'split': None}, {'split': '0.4'}, {'split': '1'}):
            with self.assertRaises(RuntimeError):
                strata_runtime.check_inkling_config(self.two_card(**kw), 63 * GIB, 40 * GIB)
        cfg = self.two_card(); cfg['args'] += ['--gpu', '1']
        with self.assertRaises(RuntimeError):
            strata_runtime.check_inkling_config(cfg, 63 * GIB, 40 * GIB)
        cfg = self.two_card(); cfg['env'] = {'ROCR_VISIBLE_DEVICES': '1,0', 'HIP_VISIBLE_DEVICES': '1,0'}
        with self.assertRaises(RuntimeError):
            strata_runtime.check_inkling_config(cfg, 63 * GIB, 40 * GIB)

    def test_repeated_equals_form_dangling_or_stray_card_flags_are_refused(self):
        bad = []
        for extra in (['--gpus', '0,1'], ['--ep-split', '0.1'], ['--gpus=0,1'], ['--ep-split=0.1'], ['--parallel=2'], ['--ep-split']):
            cfg = self.two_card(); cfg['args'] += extra; bad.append(cfg)
        cfg = self.two_card(); a = cfg['args']; a[a.index('--ep-split') + 1] = '60%'; bad.append(cfg)
        cfg = self.two_card(); a = cfg['args']; a[a.index('--ep-split') + 1] = '--kv'; bad.append(cfg)
        for extra in (['--gpus=0,1'], ['--gpu', '0'], ['--ep-split', '0.2']):
            cfg = config(); cfg['args'] += extra; bad.append(cfg)
        cfg = config(); cfg['args'] = cfg['args'][:-1]; bad.append(cfg)
        for cfg in bad:
            with self.assertRaises(RuntimeError, msg=cfg['args']):
                strata_runtime.check_inkling_config(cfg, 63 * GIB, 40 * GIB)

    def test_free_ram_floor_and_physical_ram_apply(self):
        with self.assertRaises(RuntimeError):
            strata_runtime.check_inkling_config(config(), 16 * GIB, 12 * GIB)
        with self.assertRaises(RuntimeError):
            strata_runtime.check_inkling_config(config(), 63 * GIB, GIB // 2)


if __name__ == '__main__':
    unittest.main()
