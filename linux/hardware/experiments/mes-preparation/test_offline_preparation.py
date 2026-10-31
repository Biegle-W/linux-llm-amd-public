"""CPU-only tests: temporary text fixtures, patch checks and metadata parsing."""
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

from audit_mes_source import FILES, audit
from inspect_h3_readiness import inspect, inspect_asset, inspect_python, MAX_HEADER, MAX_SOURCE


class OfflinePreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self):
        source = self.root / "source"
        patch = self.root / "change.patch"
        text = ""
        for name in FILES:
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("old\n")
            text += f"--- a/{name}\n+++ b/{name}\n@@ -1 +1 @@\n-old\n+new\n"
        patch.write_text(text)
        return source, patch

    def test_pristine_source_and_no_mutation(self):
        source, patch = self.fixture()
        result = audit(source, patch)
        self.assertEqual(result["status"], "clean_source_candidate")
        self.assertTrue(all((source / f).read_text() == "old\n" for f in FILES))

    def test_applied_patch_is_distinguished(self):
        source, patch = self.fixture()
        for name in FILES:
            (source / name).write_text("new\n")
        self.assertEqual(audit(source, patch)["status"], "patch_present")

    def test_partial_patch_requires_review(self):
        source, patch = self.fixture()
        (source / FILES[0]).write_text("new\n")
        self.assertEqual(audit(source, patch)["status"], "needs_review")

    def test_unexpected_patch_path_is_rejected(self):
        source, patch = self.fixture()
        patch.write_text(patch.read_text().replace(FILES[0], "../../outside"))
        with self.assertRaises(ValueError):
            audit(source, patch)

    def test_ast_inspection_does_not_execute_source(self):
        path = self.root / "candidate.py"
        path.write_text("raise RuntimeError('must not execute')\nimport torch\nclass Example: pass\n")
        self.assertEqual(inspect_python(path)["classes"], ["Example"])

    def test_oversized_source_is_rejected(self):
        path = self.root / "large.py"
        with path.open("wb") as stream:
            stream.truncate(MAX_SOURCE + 1)
        with self.assertRaises(ValueError):
            inspect_python(path)

    def asset(self, offsets=None):
        path = self.root / "model.safetensors"
        header = json.dumps({"x": {"dtype": "F32", "shape": [1],
                                    "data_offsets": offsets or [0, 4]}}).encode()
        path.write_bytes(struct.pack("<Q", len(header)) + header + b"\x00" * 4)
        return path

    def test_safetensors_metadata_only(self):
        result = inspect_asset(self.asset())
        self.assertEqual(result["tensor_count"], 1)
        self.assertFalse(result["tensor_payload_read"])
        self.assertEqual(result["model_compatible"], "not_qualified")

    def test_out_of_bounds_offsets_are_rejected(self):
        with self.assertRaises(ValueError):
            inspect_asset(self.asset([0, 8]))

    def test_header_length_cap(self):
        path = self.root / "excess.safetensors"
        path.write_bytes(struct.pack("<Q", MAX_HEADER + 1))
        with self.assertRaises(ValueError):
            inspect_asset(path)

    def test_truncated_header(self):
        path = self.root / "truncated.safetensors"
        path.write_bytes(b"\x00")
        with self.assertRaises(ValueError):
            inspect_asset(path)

    def test_inventory_never_enables_launch(self):
        result = inspect(self.root, self.root, self.root)
        self.assertEqual(len(result["missing"]), 4)
        self.assertFalse(result["ready_to_launch"])
        self.assertFalse(result["GPU_work_submitted"])


if __name__ == "__main__":
    unittest.main()
