import unittest
from cli import serve_defaults


class CliDefaultsTests(unittest.TestCase):
    def test_explicit_single_gpu_exception_defaults_to_second_card(self):
        args=serve_defaults(['serve','--model','example.gguf'])
        self.assertEqual(args[args.index('--gpu')+1],'1')
        self.assertEqual(args[args.index('--tensor-parallel-size')+1],'1')
        self.assertIn('--disable-pynccl',args)
        self.assertEqual(args[args.index('--max-prefill-length')+1],'128')
        self.assertEqual(args[args.index('--cuda-graph-max-bs')+1],'0')

    def test_cannot_silently_attempt_unsupported_tp2(self):
        with self.assertRaisesRegex(ValueError,'TP2'):
            serve_defaults(['serve','--tp-size','2'])
        with self.assertRaisesRegex(ValueError,'dual-GPU'):
            serve_defaults(['serve','--gpu','0,1'])

    def test_conflicting_repeated_settings_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'once'):
            serve_defaults(['serve','--tp-size','1','--tensor-parallel-size=2'])
        with self.assertRaisesRegex(ValueError,'once'):
            serve_defaults(['serve','--gpu=1','--gpu','0,1'])

    def test_reject_known_unsupported_prefill_shape(self):
        with self.assertRaisesRegex(ValueError,'128'):
            serve_defaults(['serve','--max-prefill-length','256'])

    def test_explicit_other_card_is_preserved(self):
        args=serve_defaults(['serve','--gpu','0','--tensor-parallel-size','1'])
        self.assertEqual(args.count('--gpu'),1)
        self.assertEqual(args[args.index('--gpu')+1],'0')


if __name__=='__main__':
    unittest.main()
