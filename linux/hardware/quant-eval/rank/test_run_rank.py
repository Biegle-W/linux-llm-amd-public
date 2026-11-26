"""Offline runner integration tests with a local HTTP stub and a simulated clock."""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import threading
import unittest
from unittest.mock import MagicMock, patch

import run_rank
import grade_pub


class Clock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def wall(self):
        return 1_700_000_000 + self.now


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        server = self.server
        server.requests.append(body)
        message = body["messages"][-1]["content"]
        server.clock.now += server.durations.get(message, 1)
        if message == server.abort_at:
            server.abort_file.touch()
            server.release.wait(5)
        reply = {"choices": [{"message": {"content": "synthetic"}, "finish_reason":
                              "length" if message == "second" else "stop"}],
                 "usage": {"prompt_tokens": 8, "completion_tokens": 5}}
        if message == server.malformed_at:
            reply = {}
        data = json.dumps(reply).encode()
        try:
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except OSError:
            pass


class RunnerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root / "output"
        self.items = self.root / "items.jsonl"
        self.rank = self.root / "rank-items.json"
        self.speeds = self.root / "speeds.json"
        self.clock = Clock()
        self.server = ThreadingHTTPServer(("localhost", 0), Handler)
        self.server.clock = self.clock
        self.server.abort_file = self.root / "hold"
        self.server.requests = []
        self.server.durations = {}
        self.server.abort_at = self.server.malformed_at = None
        self.server.release = threading.Event()
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": .01},
                         daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.addCleanup(self.server.release.set)
        self.ids = ["q:first", "q:second", "q:third"]
        # Reverse pool order deliberately. Gold data can never be sent in a request.
        rows = [{"id": item, "category": "knowledge", "tier": "core", "grader": "mcq",
                 "gold": {"answer": "A", "choices": ["A", "B"]},
                 "body": {"messages": [{"role": "user", "content": item.split(":")[1]}],
                          "max_tokens": 80}} for item in reversed(self.ids)]
        self.items.write_text("".join(json.dumps(r) + "\n" for r in rows))
        self.items.with_suffix(".manifest.json").write_text(json.dumps(
            {"frozen": True, "schema_version": 3, "reference_validation_runs": 3,
             "candidates_sha256": "synthetic", "item_count": 3,
             "items_sha256": hashlib.sha256(self.items.read_bytes()).hexdigest()}))
        self.rank.write_text(json.dumps({"order": self.ids, "core_n": 2, "prefix_checkpoints": [2, 3],
                                         "predicted_prefix": {"stub": {"typical": 3, "conservative": 3}},
                                         "caps": {"knowledge": 5},
                                         "item_costs": {i: {"prompt_tokens": 8, "completion_tokens": 10}
                                                        for i in self.ids}}))
        self.speeds.write_text(json.dumps({"routes": {"stub": {"class": "small", "budget_min": 15,
                                           "decode_tok_s": 1, "prefill_tok_s": 8, "overhead_s": 4,
                                           "verbosity": 1}}}))

    def invoke(self, route="stub"):
        url = f"http://localhost:{self.server.server_port}/"
        code = run_rank.main([str(self.out), route, "--items", str(self.items), "--rank-items",
                              str(self.rank), "--speeds", str(self.speeds), "--class", "small",
                              "--url", url, "--abort-file", str(self.server.abort_file)],
                             wall=self.clock.wall, monotonic=self.clock.monotonic)
        self.report = json.loads((self.out / "run.json").read_text())
        self.answers = json.loads((self.out / f"{route}.json").read_text())
        return code

    def grade(self, item):
        rows = run_rank.run_pub.suite_pub.load_items(self.items, "all")
        row = next(r for r in rows if r["id"] == item)
        return grade_pub.grade_item(row, self.answers.get(item))

    def test_warmup_order_caps_and_answer_schema(self):
        self.server.durations["Reply OK."] = 1000
        self.assertEqual(self.invoke(), 0)
        self.assertEqual(self.report["ready_utc"], run_rank.run_pub.iso(1_700_001_000))
        self.assertEqual(self.report["budget_s"], 900)
        self.assertEqual(self.report["elapsed_s"], 3)
        self.assertTrue(self.report["complete"])
        self.assertTrue(self.report["core_complete"])
        self.assertEqual(self.report["answered_prefix"], 3)
        self.assertEqual(self.report["counts"], {"attempted": 3, "ok": 2, "error": 0,
                                                "capped": 1, "not_run": 0})
        requests = self.server.requests
        self.assertEqual([b["messages"][-1]["content"] for b in requests],
                         ["Reply OK.", "first", "second", "third"])
        self.assertEqual([b["max_tokens"] for b in requests], [32, 5, 5, 5])
        for body in requests:
            self.assertEqual(body["model"], "stub")
            self.assertEqual(body["temperature"], 0)
            self.assertEqual(body["chat_template_kwargs"], run_rank.run_pub.THINKING_OFF)
            self.assertNotIn("gold", body)
        graded = self.grade(self.ids[1])
        self.assertEqual(graded["status"], "capped")
        self.assertFalse(graded["correct"])
        self.assertEqual(self.answers["q:second"]["finish"], "length")
        self.assertEqual(self.report["items"]["q:first"]["completion_tokens"], 5)

    def test_pace_update_stops_suffix_and_pending_is_ungraded(self):
        # Base cost is 10s. After taking 650s, 250s remain. The new estimate
        # is 330s, so admission should refuse even the immediately following item.
        self.server.durations["first"] = 650
        self.assertEqual(self.invoke(), 3)
        self.assertEqual(self.report["not_run"], self.ids[1:])
        self.assertFalse(self.report["complete"])
        self.assertFalse(self.report["core_complete"])
        self.assertEqual(self.report["answered_prefix"], 1)
        self.assertEqual(self.report["counts"], {"attempted": 1, "ok": 1, "capped": 0,
                                                "error": 0, "not_run": 2})
        self.assertEqual(set(self.answers), {"_meta", self.ids[0]})
        self.assertEqual(len(self.server.requests), 2)
        self.assertEqual(self.grade(self.ids[1])["status"], "pending")

    def test_finished_core_and_unaffordable_extension_is_normal(self):
        self.server.durations["second"] = 800
        self.assertEqual(self.invoke(), 0)
        self.assertEqual(self.report["stop_reason"], "estimate_exceeds_remaining")
        self.assertTrue(self.report["core_complete"])
        self.assertFalse(self.report["complete"])
        self.assertEqual(self.report["answered_prefix"], 2)
        self.assertEqual(self.report["not_run"], self.ids[2:])
        self.assertEqual(self.grade(self.ids[2])["status"], "pending")
        self.assertEqual(self.report["counts"]["attempted"], 2)
        self.assertEqual(len(self.server.requests), 3)  # warm-up + two core requests

    def test_extension_runs_past_predicted_prefix_if_it_fits(self):
        ranked = json.loads(self.rank.read_text())
        ranked.update(core_n=1, prefix_checkpoints=[1, 3],
                      predicted_prefix={"stub": {"typical": 1, "conservative": 1}})
        self.rank.write_text(json.dumps(ranked))
        self.server.durations["second"] = 800
        self.assertEqual(self.invoke(), 0)
        self.assertTrue(self.report["core_complete"])
        self.assertFalse(self.report["complete"])
        self.assertEqual(self.report["answered_prefix"], 2)  # not rounded to a checkpoint
        self.assertEqual(self.report["not_run"], self.ids[2:])

    def test_invalid_core_boundary_rejected_before_warmup(self):
        ranked = json.loads(self.rank.read_text())
        args = SimpleNamespace(rank_items=self.rank, speeds=self.speeds, items=self.items,
                               route="stub", route_class="small")
        for invalid in (False, 0, -1, 4, "2", 1.5):
            with self.subTest(core_n=invalid), self.assertRaisesRegex(ValueError, "core_n"):
                self.rank.write_text(json.dumps(dict(ranked, core_n=invalid)))
                run_rank.load_plan(args)

    def test_deadline_terminates_started_item(self):
        self.server.durations["first"] = 901
        self.assertEqual(self.invoke(), 3)
        self.assertTrue(self.answers[self.ids[0]]["fleet_deadline"])
        self.assertEqual(self.report["stop_reason"], "deadline")
        self.assertEqual(self.report["not_run"], self.ids[1:])
        self.assertEqual(self.report["counts"]["error"], 1)
        self.assertFalse(self.report["core_complete"])
        self.assertEqual(self.report["answered_prefix"], 1)

    def test_frozen_route_estimate_takes_precedence(self):
        ranked = json.loads(self.rank.read_text())
        ranked["item_seconds"] = {"stub": {self.ids[1]: 2000}}
        ranked["speeds_sha256"] = hashlib.sha256(self.speeds.read_bytes()).hexdigest()
        self.rank.write_text(json.dumps(ranked))
        self.assertEqual(self.invoke(), 3)
        self.assertEqual(self.report["not_run"], self.ids[1:])

    def test_missing_digest_ignores_cached_seconds(self):
        ranked = json.loads(self.rank.read_text())
        ranked["item_seconds"] = {"stub": {i: 901 for i in self.ids}}
        self.rank.write_text(json.dumps(ranked))
        self.assertEqual(self.invoke(), 0)
        self.assertEqual(self.report["counts"]["attempted"], len(self.ids))

    def test_shipped_estimates_and_in_place_speed_edit(self):
        self.rank.write_bytes((run_rank.HERE / "rank-items.json").read_bytes())
        self.speeds.write_bytes((run_rank.HERE / "speeds.json").read_bytes())
        ranked = json.loads(self.rank.read_text())
        speeds = json.loads(self.speeds.read_text())
        self.assertEqual(ranked["speeds_sha256"], hashlib.sha256(self.speeds.read_bytes()).hexdigest())
        # Only the IDs and caps matter here; no public benchmark prompts are required.
        rows = [{"id": i, "category": "knowledge", "body": {"max_tokens": 4096,
                 "messages": [{"role": "user", "content": "synthetic"}]}} for i in ranked["order"]]
        with patch.object(run_rank.run_pub.suite_pub, "load_items", return_value=rows):
            for route, model in speeds.items():
                with self.subTest(route=route):
                    args = SimpleNamespace(rank_items=self.rank, speeds=self.speeds, items=self.items,
                                           route=route, route_class=model["class"])
                    plan = run_rank.load_plan(args)
                    estimates = {i: seconds for i, _, _, seconds in plan.entries}
                    self.assertEqual(estimates, ranked["item_seconds"][route])
                    self.assertEqual(plan.speeds_sha256, ranked["speeds_sha256"])
                    core_seconds = sum(estimates[i] for i in ranked["order"][:plan.core_n])
                    self.assertAlmostEqual(core_seconds / 60, ranked["predicted_minutes"][route]["typical"], places=3)
            route = "qwen3.8-27b-vllm"
            speeds[route]["overhead_s"] = 901
            self.speeds.write_text(json.dumps(speeds))
            self.assertEqual(self.invoke(route), 3)
        self.assertEqual(self.report["stop_reason"], "estimate_exceeds_remaining")
        self.assertEqual(self.report["not_run"], ranked["order"])
        self.assertFalse(self.report["core_complete"])
        self.assertEqual(self.report["answered_prefix"], 0)
        self.assertEqual(self.report["counts"]["attempted"], 0)
        self.assertEqual([b["messages"][-1]["content"] for b in self.server.requests], ["Reply OK."])

    def test_estimate_blocks_first_item(self):
        ranked = json.loads(self.rank.read_text())
        ranked["item_costs"][self.ids[0]]["prompt_tokens"] = 8 * 901
        self.rank.write_text(json.dumps(ranked))
        self.assertEqual(self.invoke(), 3)
        self.assertEqual(len(self.server.requests), 1)
        self.assertEqual(self.report["not_run"], self.ids)

    def test_gpu_hold_before_warmup(self):
        self.server.abort_file.touch()
        self.assertEqual(self.invoke(), 4)
        self.assertEqual(self.server.requests, [])
        self.assertIsNone(self.report["ready_utc"])
        self.assertFalse(self.report["core_complete"])
        self.assertEqual(self.report["answered_prefix"], 0)
        self.assertEqual(self.report["not_run"], self.ids)

    def test_gpu_hold_during_request(self):
        self.server.abort_at = "second"
        self.assertEqual(self.invoke(), 4)
        self.assertEqual(self.report["stop_reason"], "abort_file")
        self.assertEqual(self.report["counts"]["attempted"], 1)
        self.assertEqual(self.report["not_run"], self.ids[1:])
        self.assertFalse(self.report["core_complete"])
        self.assertEqual(self.report["answered_prefix"], 1)
        self.assertNotIn(self.ids[1], self.answers)
        self.assertEqual(self.report["items"][self.ids[1]]["status"], "not_run")
        self.assertEqual(self.grade(self.ids[1])["status"], "pending")

    def test_early_request_timeout_continues(self):
        reply = {"choices": [{"finish_reason": "stop", "message": {"content": "OK"}}]}
        success = (reply, None, 0)
        pipe = MagicMock()
        pipe.recv.side_effect = [success, (None, "TimeoutError: read timed out", 0), success, success]
        with patch.object(run_rank, "client") as client:
            client.return_value.__enter__.return_value = (pipe, MagicMock())
            self.assertEqual(self.invoke(), 0)
        self.assertEqual(self.report["items"][self.ids[0]]["status"], "error")
        self.assertEqual(self.report["stop_reason"], "complete")
        self.assertEqual(self.report["answered_prefix"], 3)

    def test_warmup_failure_never_starts_clock(self):
        self.server.malformed_at = "Reply OK."
        self.assertEqual(self.invoke(), 4)
        self.assertEqual(self.report["stop_reason"], "warmup_failed")
        self.assertIsNone(self.report["ready_utc"])
        self.assertEqual(self.report["not_run"], self.ids)


if __name__ == "__main__":
    unittest.main()
