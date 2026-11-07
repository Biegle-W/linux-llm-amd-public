"""Unit tests for the H3 TP2 prompt rewrite (no torch, no GPU)."""
import importlib.util
import json
import os
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.pop("H3_TP2_FOLLOWER", None)
os.environ["TP_RANK"] = "1"  # load as a non-leader: no server hooks
os.environ["H3_TP2_HALVES"] = ""
spec = importlib.util.spec_from_file_location("h3_tp2", HERE / "custom_nodes/h3_tp2/__init__.py")
glue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(glue)
WF = HERE.parent / "workflows"


class Rewrite(unittest.TestCase):
    def load(self, name):
        return json.loads((WF / name).read_text())

    def test_projected_h3_goes_tp2(self):
        p, f = glue.rewrite(self.load("minimax-h3-base-api.json"))
        self.assertEqual(p["1"]["class_type"], "H3TP2UNetLoader")
        devices = {v["inputs"]["device"] for v in p.values() if "device" in v["inputs"]}
        self.assertEqual(devices, {"cuda:0"})
        self.assertEqual(json.loads(p["1"]["inputs"]["follower_graph"]), f)
        classes = {v["class_type"] for v in f.values()}
        self.assertIn("H3TP2FollowerSink", classes)
        self.assertFalse(classes & {"SaveVideo", "VAEDecode", "VAEDecodeAudio", "CreateVideo"})
        self.assertEqual(f["1"]["inputs"]["follower_graph"], "")

    def test_native_encoder_stays_staged(self):
        src = self.load("minimax-h3-native32b-api.json")
        p, f = glue.rewrite(src)
        self.assertIsNone(f)
        self.assertEqual(p["1"]["class_type"], "H3StagedUNetLoader")
        self.assertEqual(p["3"]["inputs"]["device"], src["3"]["inputs"]["device"])

    def test_other_workflows_untouched(self):
        for name in ["flux3-klein-t2i-api.json", "flux3-klein-i2i-api.json", "qwen-image-2.1-base-api.json"]:
            self.assertIsNone(glue.rewrite(self.load(name)), name)


if __name__ == "__main__":
    unittest.main()
