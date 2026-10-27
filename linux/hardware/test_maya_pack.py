"""CPU-only XS verification preserves shared Engram dependencies after S retirement."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dsh'))
from maya_runtime import config_fingerprint, pack_metadata_fingerprint


class PackVerificationTests(unittest.TestCase):
    def test_xs_needs_shared_engram_and_drafter_but_not_s_only_weights(self):
        spec = importlib.util.spec_from_file_location('maya_pack_verifier', ROOT / 'maya/verify-xs-pack.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'dsh').mkdir()
            models = root / 'models'; base = models / 'DeepSeek-V4.1-Flash-1017-GGUF'
            pack = base / 'Maya-XS/maya-ds4'; pack.mkdir(parents=True)
            paths = ['xs.gguf', '../Maya-S/engram5.gguf', '../Maya-S/engram6.gguf', '../dspark/dspark-xs2.bin']
            for relative in paths:
                file = pack.parent / relative; file.parent.mkdir(parents=True, exist_ok=True); file.write_bytes(b'retained dependency')
            (pack / 'tensors.txt').write_text(''.join(f'file {i} {name}\n' for i, name in enumerate(paths)))
            (pack / 'ds4.txt').write_text('sealed descriptor\n'); (pack / 'engram.bin').write_bytes(b'sealed metadata')
            cfg = {'args': ['--pack', str(pack)]}
            cfg['local_validation'] = {'status': 'passed', 'config_sha256': config_fingerprint(cfg),
                                      'pack_metadata_sha256': pack_metadata_fingerprint(pack)}
            (root / 'dsh/maya-deepseek-profile.json').write_text(json.dumps(cfg))
            with patch.object(module, 'ROOT', root), patch.object(sys, 'argv', ['verify-xs-pack.py', '--root', str(models)]), contextlib.redirect_stdout(io.StringIO()):
                module.main()  # No S-only weights, old drafter or S profile exists.
                for relative in paths:
                    with self.subTest(dependency=relative):
                        file = pack.parent / relative; file.unlink()
                        with self.assertRaisesRegex(RuntimeError, 'dependency is missing'): module.main()
                        file.write_bytes(b'retained dependency')
                (pack / 'ds4.txt').write_text('unvalidated descriptor\n')
                with self.assertRaisesRegex(RuntimeError, 'Prepare and validate'): module.main()

    def test_retired_s_selection_is_rejected_before_reading_a_profile(self):
        spec = importlib.util.spec_from_file_location('maya_pack_verifier', ROOT / 'maya/verify-xs-pack.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with patch.object(sys, 'argv', ['verify-xs-pack.py', '--root', '/missing', '--profile', 's']), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as result: module.main()
            self.assertEqual(result.exception.code, 2)
