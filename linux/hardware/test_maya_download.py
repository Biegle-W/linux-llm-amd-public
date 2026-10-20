"""Verify family-scoped downloads cannot touch retained DeepSeek assets."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('maya_download', ROOT / 'maya/download-models.py')
downloader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(downloader)


class MayaDownloadTests(unittest.TestCase):
    def test_explicit_glm_manifest_verifies_only_glm_and_leaves_deepseek_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            glm = root / 'Maya-S-v2/GLM-test.gguf'
            glm.parent.mkdir()
            glm.write_bytes(b'verified model fixture')
            ds = root / 'DeepSeek/Maya-S/DeepSeek-test.gguf'
            ds.parent.mkdir(parents=True)
            ds.write_bytes(b'retained DeepSeek fixture')
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'files': [
                {'remote': 'Maya-S-v2/GLM-test.gguf', 'file': str(glm.relative_to(root)),
                 'size': glm.stat().st_size, 'sha256': hashlib.sha256(glm.read_bytes()).hexdigest()},
                # Deliberately invalid metadata must never be evaluated by --family glm.
                {'remote': 'Maya-S/DeepSeek-test.gguf', 'file': str(ds.relative_to(root)),
                 'size': 0, 'sha256': 'bad'}]}))
            before = ds.read_bytes()
            with patch.object(sys, 'argv', ['download', '--root', str(root), '--family', 'glm',
                                           '--manifest', str(manifest)]), \
                    patch.object(downloader.subprocess, 'run') as network, \
                    contextlib.redirect_stdout(io.StringIO()):
                downloader.main()
            network.assert_not_called()
            self.assertEqual(ds.read_bytes(), before)

    def test_existing_corruption_is_preserved_instead_of_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            weight = root / 'GLM-test.gguf'
            weight.write_bytes(b'preserve this unexpected file')
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'files': [
                {'family': 'glm', 'remote': weight.name, 'file': weight.name,
                 'size': weight.stat().st_size, 'sha256': '0' * 64}]}))
            before = weight.read_bytes()
            with patch.object(sys, 'argv', ['download', '--root', str(root), '--manifest', str(manifest)]), \
                    patch.object(downloader.subprocess, 'run') as network:
                with self.assertRaisesRegex(RuntimeError, 'preserved for review'):
                    downloader.main()
            network.assert_not_called()
            self.assertEqual(weight.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
