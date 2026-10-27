"""Verify family-scoped downloads cannot touch retained DeepSeek assets."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('maya_download', ROOT / 'maya/download-models.py')
downloader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(downloader)


class MayaDownloadTests(unittest.TestCase):
    def test_retired_s24_manifest_is_non_installable_checksum_history(self):
        manifest = ROOT / 'maya/glm-s24-rollback-models.json'
        history = json.loads(manifest.read_text())
        self.assertEqual(history['status'], 'retired')
        self.assertEqual(history['files'], [])
        self.assertEqual(len(history['historical_files']), 3)
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(sys, 'argv', ['download', '--root', tmp, '--manifest', str(manifest)]), \
                patch.object(downloader.subprocess, 'run') as curl, \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                downloader.main()
            self.assertEqual(result.exception.code, 2)
            curl.assert_not_called()
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_s24_installer_selection_rejected_before_preparation(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(['bash', str(ROOT / 'maya/install.sh'), 'glm'],
                env={**os.environ, 'MAYA_MODELS_ROOT': tmp, 'MAYA_GLM_QUANT': 'Maya-S24'},
                capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Maya-S24 rollback is retired', result.stderr)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_retired_manifest_cannot_download_or_recreate_s(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); manifest = root / 'retired.json'
            manifest.write_text(json.dumps({'status': 'retired', 'files': [{'file': 'retired.gguf'}]}))
            with patch.object(sys, 'argv', ['download', '--root', str(root), '--manifest', str(manifest)]), patch.object(downloader.subprocess, 'run') as curl, contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as result: downloader.main()
                self.assertEqual(result.exception.code, 2); curl.assert_not_called()
            self.assertFalse((root / 'retired.gguf').exists())

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
