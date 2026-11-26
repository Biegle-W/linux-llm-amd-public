"""The shared benchmark folder: this server matches it, and the shared files are intact. No model, no GPU."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location("check_shared", ROOT / "benchmarks/shared/check_shared.py")
check_shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_shared)


class SharedBenchmarkTests(unittest.TestCase):
    def test_amd_matches_shared_definitions(self):
        # The public mirror (linux/) does not keep its route registries current, so it checks items and cases only.
        errors, _ = check_shared.check("amd", ROOT, check_routes=ROOT.name != "linux")
        self.assertEqual(errors, [])

    def test_shared_items_are_nvidia_frozen_list(self):
        ids = check_shared.tooluse_ids(ROOT / "benchmarks/shared/tooluse-short-manifest.json")
        self.assertEqual(len(ids), 55)
        self.assertEqual(sum(core for _, core in ids), 49)


if __name__ == "__main__":
    unittest.main()
