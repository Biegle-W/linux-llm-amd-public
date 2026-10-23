"""CPU-only pack verification must not download or overwrite either quant."""
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
    def test_each_profile_is_sealed_and_checks_shared_dependencies(self):
        spec = importlib.util.spec_from_file_location('maya_pack_verifier', ROOT / 'maya/verify-xs-pack.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'dsh').mkdir()
            for profile, quant, filename in [('xs', 'Maya-XS', 'maya-deepseek-profile.json'),
                                             ('s', 'Maya-S', 'maya-deepseek-s-profile.json')]:
                with self.subTest(profile=profile):
                    models = root / 'models'
                    pack = models / 'DeepSeek-V4.1-Flash-1017-GGUF' / quant / 'maya-ds4'
                    pack.mkdir(parents=True)
                    weight = pack.parent / 'retained.gguf'; weight.write_bytes(b'retained model')
                    (pack / 'tensors.txt').write_text('file 0 retained.gguf\n')
                    (pack / 'ds4.txt').write_text('sealed descriptor\n')
                    (pack / 'engram.bin').write_bytes(b'sealed engram metadata')
                    cfg = {'args': ['--pack', str(pack)]}
                    cfg['local_validation'] = {'status': 'passed', 'config_sha256': config_fingerprint(cfg),
                                               'pack_metadata_sha256': pack_metadata_fingerprint(pack)}
                    target = root / 'dsh' / filename; target.write_text(json.dumps(cfg))
                    with patch.object(module, 'ROOT', root), patch.object(sys, 'argv',
                            ['verify-xs-pack.py', '--root', str(models), '--profile', profile]), contextlib.redirect_stdout(io.StringIO()):
                        module.main()
                        weight.unlink()
                        with self.assertRaisesRegex(RuntimeError, 'dependency is missing'):
                            module.main()
                        weight.write_bytes(b'retained model')
                        (pack / 'ds4.txt').write_text('unvalidated descriptor\n')
                        with self.assertRaisesRegex(RuntimeError, 'Prepare and validate'):
                            module.main()
