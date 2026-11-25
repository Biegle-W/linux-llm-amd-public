import ast
from contextlib import contextmanager, redirect_stderr
import io
import json
import multiprocessing
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import tempfile
from threading import Thread
from time import monotonic, sleep
import unittest
from unittest.mock import patch

from fast_amd import build_manifest, episode, report, run
from fast_amd.bfcl.prompts import DEFAULT_USER_PROMPT_FOR_ADDITIONAL_FUNCTION_FC
from fast_amd.bfcl.environments.math_api import MathAPI
from fast_amd.tooling import normalize_name, openai_tools

WORKSPACE = build_manifest.PACKAGE.parent


def completion(content=None, calls=None, finish="stop"):
    return {
        "choices": [{
            "finish_reason": finish,
            "message": {"role": "assistant", "content": content, "tool_calls": calls},
        }],
        "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
    }


def tool_call(name, args, call_id="call_0"):
    return {
        "id": call_id, "type": "function",
        "function": {"name": normalize_name(name), "arguments": json.dumps(args)},
    }


@contextmanager
def mock_server(reply):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append((self.path, body))
            response = reply(body)
            try:
                if response == "drip":
                    self.send_response(200)
                    self.end_headers()
                    while True:
                        self.wfile.write(b" ")
                        sleep(0.01)
                else:
                    data = json.dumps(response).encode()
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
            except OSError:
                pass

        def do_GET(self):
            requests.append((self.path, None))
            self.send_response(200 if self.path == "/health" else 404)
            self.end_headers()

        def log_message(self, format, *args):
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}", requests
        finally:
            server.shutdown()
            thread.join()


def replay_steps(gold, remove_call=False):
    steps = []
    removed = False
    for turn in gold:
        for text in turn:
            if remove_call and not removed:
                removed = True
                continue
            call = ast.parse(text, mode="eval").body
            if call.args:
                raise AssertionError("Expected named arguments in replay")
            args = {arg.arg: ast.literal_eval(arg.value) for arg in call.keywords}
            steps.append(completion(
                calls=[tool_call(call.func.id, args, f"call_{len(steps)}")], finish="tool_calls",
            ))
        steps.append(completion("Done."))
    return steps


class BenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.data, cls.docs = build_manifest.verify(
            build_manifest.SOURCE, build_manifest.MANIFEST,
        )
        cls.small = [item for item in cls.manifest["items"] if item["core"]]

    def setUp(self):
        folder = tempfile.TemporaryDirectory(dir=WORKSPACE)
        self.addCleanup(folder.cleanup)
        self.out = Path(folder.name)

    def invoke(self, url, *options):
        return run.main(["test-model", "small", "--base-url", url, "--out", str(self.out), *options])

    def outputs(self):
        result = json.loads((self.out / "fast-result.json").read_bytes())
        records = [json.loads(line) for line in (self.out / "fast.jsonl").read_bytes().splitlines()]
        return result, records

    def test_manifest_order_and_tamper_refusal(self):
        other = self.out / "manifest.json"
        build_manifest.main(["--src", str(build_manifest.SOURCE), "--out", str(other)])
        self.assertEqual(other.read_bytes(), build_manifest.MANIFEST.read_bytes())
        items = self.manifest["items"]
        self.assertEqual(len(items), 55)
        self.assertEqual(len(self.small), 49)
        self.assertEqual(self.manifest["groups"]["small"], [item["id"] for item in self.small])
        self.assertEqual(self.manifest["groups"]["large"], [item["id"] for item in items])
        self.assertEqual(
            [item["pool"] for item in items],
            ["parallel"] * 15 + ["irrelevance"] * 15 + ["simple"] * 10
            + ["mt_base", "mt_miss_param", "mt_miss_func"] * 5,
        )
        for pool in build_manifest.POOLS:
            pool_items = [item for item in items if item["pool"] == pool]
            ranks = [build_manifest.sha(f"20261122|{pool}|{item['id']}".encode()) for item in pool_items]
            self.assertEqual(ranks, sorted(ranks))

        source = self.out / "bfcl-src"
        shutil.copytree(build_manifest.SOURCE, source)
        tampered = source / "data/BFCL_v4_parallel.json"
        with tampered.open("ab") as file:
            file.write(b"\n")
        real_run = run.run
        with mock_server(lambda _: completion("OK")) as (url, requests):
            with patch.object(run, "run", lambda args: real_run(args, source, other)):
                with redirect_stderr(io.StringIO()) as stderr:
                    self.assertEqual(self.invoke(url), 2)
                    self.assertIn("hash mismatch", stderr.getvalue())
            self.assertEqual(requests, [])

    def test_single_turn_grading(self):
        gold = [{"api.fetch": {"value": [1]}}]
        good = tool_call("api.fetch", {"value": 1})
        cases = [
            ("simple", completion(calls=[good], finish="tool_calls"), True),
            ("parallel", completion(calls=[tool_call("api.fetch", {"value": True})]), False),
            ("parallel", completion(calls=[good, good]), False),
            ("simple", completion("api.fetch(value=1)"), False),
            ("simple", completion(calls=[good], finish="length"), False),
            ("irrelevance", completion("I can explain this."), True),
            ("irrelevance", completion("Unexpected tool call", calls=[good]), False),
            ("irrelevance", completion(""), False),
        ]
        responses = iter(reply for _, reply, _ in cases)
        with mock_server(lambda _: next(responses)) as (url, requests):
            for pool, _, expected in cases:
                with self.subTest(pool=pool, expected=expected):
                    message, finish = run.chat(url + "/v1/chat/completions", monotonic() + 1, {})
                    self.assertEqual(run.grade_single(pool, message, finish, gold), expected)
        self.assertEqual(len(requests), len(cases))

    def test_ground_truth_replays_and_holdouts(self):
        selected = self.manifest["items"][40:]
        for index, item in enumerate(selected):
            row, answer = self.data[item["id"]]
            gold = answer["ground_truth"]
            for remove in (False, True) if index < 3 else (False,):
                with self.subTest(item=item["id"], remove=remove):
                    replies = iter(replay_steps(gold, remove))
                    with mock_server(lambda _: next(replies)) as (url, requests):
                        record = run.item_record(item)

                        def ask(messages, tools):
                            deadline = monotonic() + 1
                            body = run.chat_body("test-model", messages, tools)
                            return run.chat(url + "/v1/chat/completions", deadline, body, record)

                        self.assertEqual(episode.evaluate(row, gold, self.docs, ask), not remove)
                        self.assertIsNone(next(replies, None))
                        self.assertEqual(record["usage"]["total_tokens"], 12 * len(requests))
                    for _, body in requests:
                        self.assertEqual(body["tool_choice"], "auto")
                        self.assertEqual(body["seed"], 20261122)
                        self.assertNotIn("chat_template_kwargs", body)
                        self.assertNotIn("system", [m["role"] for m in body["messages"]])
                        for names in row.get("missed_function", {}).values():
                            revealed = any(
                                m.get("content") == DEFAULT_USER_PROMPT_FOR_ADDITIONAL_FUNCTION_FC
                                for m in body["messages"]
                            )
                            available = {tool["function"]["name"] for tool in body["tools"]}
                            self.assertEqual(set(map(normalize_name, names)) <= available, revealed)
                    for _, body in requests:
                        for assistant, tool in zip(body["messages"], body["messages"][1:]):
                            if assistant.get("tool_calls"):
                                self.assertEqual(tool["role"], "tool")
                                self.assertEqual(tool["tool_call_id"], assistant["tool_calls"][0]["id"])

    def math_episode(self):
        return {
            "id": "multi_turn_base_test",
            "question": [
                [{"role": "user", "content": "First turn."}],
                [{"role": "user", "content": "Second turn."}],
            ],
            "involved_classes": ["MathAPI"],
            "initial_config": {},
        }

    def episode_over_http(self, row, gold, respond):
        with mock_server(respond) as (url, requests):
            def ask(messages, tools):
                return run.chat(
                    url + "/v1/chat/completions", monotonic() + 2,
                    run.chat_body("test-model", messages, tools),
                )
            valid = episode.evaluate(row, gold, self.docs, ask)
        return valid, [body for _, body in requests]

    def test_final_assistant_reply_is_in_next_turn_history(self):
        replies = iter([completion("First reply."), completion()])
        valid, requests = self.episode_over_http(
            self.math_episode(), [[], []], lambda _: next(replies),
        )
        self.assertTrue(valid)
        self.assertEqual(requests[1]["messages"], [
            {"role": "user", "content": "First turn."},
            {"role": "assistant", "content": "First reply."},
            {"role": "user", "content": "Second turn."},
        ])

    def test_step_limit_executes_round_21_and_skips_later_turns(self):
        calls = []
        original = MathAPI.absolute_value

        def count(self, number):
            calls.append(number)
            return original(self, number)

        def respond(body):
            if body["messages"][-1] == {"role": "user", "content": "Second turn."}:
                return completion("Later turn was reached.")
            return completion(calls=[tool_call("absolute_value", {"number": -7})], finish="tool_calls")

        with patch.object(MathAPI, "absolute_value", count):
            valid, requests = self.episode_over_http(
                self.math_episode(), [["absolute_value(number=-7)"], []], respond,
            )
        self.assertFalse(valid)
        self.assertEqual(len(requests), 21)
        self.assertEqual(calls, [-7] * 21)

        # Force-quit also fails when the checker could otherwise pass the final turn.
        row = self.math_episode()
        row["question"] = row["question"][:1]
        valid, _ = self.episode_over_http(row, [["absolute_value(number=-7)"]], respond)
        self.assertFalse(valid)

    def test_unknown_or_invalid_call_returns_error_and_bad_json_ends_the_turn(self):
        unknown = tool_call("not_available", {})
        del unknown["id"]
        invalid = tool_call("absolute_value", {"bad-key": 5}, "invalid")
        broken = tool_call("absolute_value", {"number": 7}, "broken")
        broken["function"]["arguments"] = "{"
        good = tool_call("absolute_value", {"number": -7}, "good")
        replies = iter([
            completion(calls=[unknown, invalid], finish="tool_calls"),
            completion(calls=[broken], finish="tool_calls"),
            completion(calls=[good], finish="tool_calls"),
            completion("Done."),
        ])
        valid, requests = self.episode_over_http(
            self.math_episode(), [[], ["absolute_value(number=-7)"]], lambda _: next(replies),
        )
        self.assertTrue(valid)
        self.assertEqual(len(requests), 4)
        assistant, missing, rejected = requests[1]["messages"][-3:]
        self.assertEqual(assistant["tool_calls"][0]["id"], "call_0_0")
        self.assertEqual(missing, {
            "role": "tool", "tool_call_id": "call_0_0",
            "content": "Error during execution: name 'not_available' is not defined",
        })
        self.assertEqual(rejected["tool_call_id"], "invalid")
        self.assertTrue(rejected["content"].startswith("Error during execution:"))
        self.assertEqual(requests[2]["messages"][-1]["content"], "Second turn.")
        self.assertEqual(requests[2]["messages"][-2]["tool_calls"][0]["id"], "broken")

    def test_withheld_function_returns_error_before_reveal(self):
        row = self.math_episode()
        row["missed_function"] = {"1": ["absolute_value"]}
        replies = iter([
            completion(calls=[tool_call("absolute_value", {"number": -7})], finish="tool_calls"),
            completion(),
            completion(calls=[tool_call("absolute_value", {"number": -7})], finish="tool_calls"),
            completion(),
        ])
        valid, requests = self.episode_over_http(
            row, [[], ["absolute_value(number=-7)"]], lambda _: next(replies),
        )
        self.assertTrue(valid)
        self.assertTrue(requests[1]["messages"][-1]["content"].startswith("Error during execution:"))
        self.assertEqual(json.loads(requests[3]["messages"][-1]["content"]), {"result": 7})

    def test_bfcl_float_and_untyped_schema(self):
        function = {
            "name": "math.example", "description": "Example",
            "parameters": {
                "type": "dict", "required": ["amount"],
                "properties": {
                    "amount": {"type": "float", "description": "Amount."},
                    "label": {"description": "Untyped."},
                    "metadata": {"type": "custom", "description": "Unknown type."},
                },
            },
            "response": {"type": "float"},
        }
        expected = {
            "type": "function",
            "function": {
                "name": "math_example", "description": "Example",
                "parameters": {
                    "type": "object", "required": ["amount"],
                    "properties": {
                        "amount": {
                            "type": "number", "format": "float",
                            "description": "Amount. This is a float type value.",
                        },
                        "label": {"type": "string", "description": "Untyped."},
                        "metadata": {"type": "string", "description": "Unknown type."},
                    },
                },
                "response": {"type": "float"},
            },
        }
        self.assertEqual(openai_tools([function]), [expected])
        self.assertEqual(function["parameters"]["properties"]["amount"]["type"], "float")
        self.assertEqual(function["name"], "math.example")
        with self.assertRaisesRegex(ValueError, "colliding"):
            openai_tools([function, {**function, "name": "math_example"}])

    def test_warmup_accepts_null_content_and_finish_reason(self):
        abort = self.out / "abort"
        abort.touch()
        with mock_server(lambda _: completion(finish=None)) as (url, requests):
            self.assertEqual(self.invoke(url, "--abort-file", str(abort)), 4)
        result, _ = self.outputs()
        self.assertEqual(result["status"], "aborted")
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0][1]["max_tokens"], 64)
        self.assertNotIn("tools", requests[0][1])

    def test_cpu_bound_episode_is_killed_at_each_deadline(self):
        row = self.math_episode()
        later = {**row, "id": "multi_turn_base_later"}
        items = [
            {"id": entry["id"], "pool": "mt_base", "part": "multi", "core": True}
            for entry in (row, later)
        ]
        manifest = {
            "groups": {"small": [item["id"] for item in items]},
            "items": items, "manifest_hash": "test",
        }
        data = {item["id"]: (item, {"ground_truth": [[], []]}) for item in (row, later)}
        blocked = self.out / "blocked"
        original = MathAPI.absolute_value

        def busy(self, number):
            if number == 999:
                blocked.write_text(str(os.getpid()))
                while True:
                    pass
            return original(self, number)

        for label, item_limit, budget, hard, expected in (
            ("per episode", 0.5, 2, 2, "wrong"),
            ("item budget", 2, 0.5, 2, "cut"),
            ("hard limit", 2, 2, 0.5, "cut"),
        ):
            with self.subTest(deadline=label):
                blocked.unlink(missing_ok=True)
                replies = iter([
                    completion("OK"),
                    completion(calls=[tool_call("absolute_value", {"number": 999})], finish="tool_calls"),
                    completion("Next episode."),
                    completion("Done."),
                ])
                with (
                    mock_server(lambda _: next(replies)) as (url, _),
                    patch.object(MathAPI, "absolute_value", busy),
                    patch.object(build_manifest, "verify", return_value=(manifest, data, self.docs)),
                    patch.dict(run.ITEM_LIMIT, multi=item_limit),
                ):
                    started = monotonic()
                    self.assertEqual(self.invoke(
                        url, "--item-budget", str(budget), "--hard-limit", str(hard),
                    ), 0)
                    elapsed = monotonic() - started
                _, records = self.outputs()
                self.assertTrue(blocked.exists())
                pid = int(blocked.read_text())
                self.assertNotEqual(pid, os.getpid())
                self.assertNotIn(pid, [child.pid for child in multiprocessing.active_children()])
                self.assertLess(elapsed, min(hard, 1) + 0.25)
                self.assertEqual(records[0]["outcome"], expected)
                self.assertEqual(records[0]["timeout"], label == "per episode")
                self.assertEqual(records[0]["cut"], expected == "cut")
                self.assertEqual(records[0]["finish_reasons"], ["tool_calls"])
                self.assertEqual(records[1]["outcome"], "correct" if expected == "wrong" else "not_run")

    def test_per_item_deadline_counts_wrong(self):
        def reply(body):
            if body["max_tokens"] == 64:
                return completion("OK")
            if not seen:
                seen.append(True)
                return "drip"
            return completion("No tool needed.")

        seen = []
        with mock_server(reply) as (url, requests):
            with patch.dict(run.ITEM_LIMIT, single=0.20):
                self.assertEqual(self.invoke(url, "--hard-limit", "5"), 0)
        result, records = self.outputs()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["timeouts"], 1)
        self.assertEqual(records[0]["outcome"], "wrong")
        self.assertTrue(records[0]["timeout"])
        self.assertEqual(requests[0], ("/v1/chat/completions", run.chat_body(
            "test-model", [{"role": "user", "content": "Reply with OK."}],
        )))

    def test_large_run_end_to_end(self):
        responses = [completion("OK")]
        for item in self.manifest["items"]:
            _, answer = self.data[item["id"]]
            if item["part"] == "multi":
                responses.extend(replay_steps(answer["ground_truth"]))
            elif item["pool"] == "irrelevance":
                responses.append(completion("No tool needed."))
            else:
                calls = [
                    tool_call(name, {key: values[0] for key, values in args.items()}, f"call_{index}")
                    for index, gold_call in enumerate(answer["ground_truth"])
                    for name, args in gold_call.items()
                ]
                responses.append(completion(calls=calls, finish="tool_calls"))
        replies = iter(responses)
        with mock_server(lambda _: next(replies)) as (url, requests):
            self.assertEqual(run.main([
                "test-model", "large", "--base-url", url, "--out", str(self.out),
            ]), 0)
        self.assertEqual(len(requests), len(responses))
        result, records = self.outputs()
        self.assertEqual([row["id"] for row in records], self.manifest["groups"]["large"])
        self.assertTrue(all(row["outcome"] == "correct" for row in records))
        self.assertEqual(result["score"], 100.0)
        self.assertEqual(result["score15"], 100.0)
        self.assertEqual(result["status"], "completed")

    def test_budget_cut_stops_dripping_response_and_checks_health(self):
        with mock_server(
            lambda body: completion("OK") if body["max_tokens"] == 64 else "drip",
        ) as (url, requests):
            started = monotonic()
            self.assertEqual(self.invoke(url + "/v1", "--item-budget", "0.12", "--hard-limit", "1"), 0)
            self.assertLess(monotonic() - started, 0.85)
        result, records = self.outputs()
        self.assertEqual(result["status"], "cut")
        self.assertTrue(result["health_answered"])
        self.assertEqual(result["coverage"], "single 0/40, episodes 0/9")
        self.assertEqual(records[0]["outcome"], "cut")
        self.assertTrue(records[0]["cut"])
        self.assertFalse(records[0]["timeout"])
        self.assertTrue(all(row["outcome"] == "not_run" for row in records[1:]))
        self.assertEqual([path for path, _ in requests], [
            "/v1/chat/completions", "/v1/chat/completions", "/health",
        ])

    def test_hard_limit_takes_priority_over_budget(self):
        with mock_server(
            lambda body: completion("OK") if body["max_tokens"] == 64 else "drip",
        ) as (url, _):
            self.assertEqual(self.invoke(url, "--item-budget", "3", "--hard-limit", "0.35"), 0)
        result, records = self.outputs()
        self.assertEqual(result["status"], "cut")
        self.assertFalse(result["health_answered"])
        self.assertEqual(records[0]["outcome"], "cut")

    def test_load_failure_and_abort(self):
        with mock_server(lambda _: "drip") as (url, requests):
            self.assertEqual(self.invoke(url, "--load-cap", "0.10"), 3)
            self.assertEqual(len(requests), 1)
        result, records = self.outputs()
        self.assertEqual(result["status"], "setup-failure")
        self.assertIsNone(result["score"])
        self.assertTrue(all(row["outcome"] == "not_run" for row in records))

        abort = self.out / "abort"
        abort.touch()
        with mock_server(lambda _: completion("OK")) as (url, requests):
            self.assertEqual(self.invoke(url, "--abort-file", str(abort)), 4)
            self.assertEqual(len(requests), 1)
        result, records = self.outputs()
        self.assertEqual(result["status"], "aborted")
        self.assertTrue(all(row["outcome"] == "not_run" for row in records))

    def test_score_and_report(self):
        large = self.manifest["items"]
        records = [run.item_record(item) for item in large]
        for record in records[:20] + records[40:42]:
            record["outcome"] = "correct"
        for record in records[20:40]:
            record["outcome"] = "wrong"
        partial = run.score(large, records, "large")
        self.assertEqual(partial["score"], 36.1)
        self.assertEqual(partial["score15"], 31.7)
        self.assertEqual(partial["covered_score"], 75.0)
        self.assertEqual(partial["coverage"], "single 40/40, episodes 2/9, episodes15 2/15")
        self.assertFalse(partial["complete"])
        self.assertFalse(partial["score_meaningful"])
        for record in records[42:49]:
            record["outcome"] = "correct"
        complete = run.score(self.small, records[:49], "small")
        self.assertEqual(complete["score"], 75.0)
        self.assertTrue(complete["complete"])
        self.assertTrue(complete["score_meaningful"])

        for name, group, status, scores in (
            ("short", "small", "completed", complete),
            ("big", "large", "cut", partial),
        ):
            folder = self.out / name
            folder.mkdir()
            build_manifest.write_json(folder / "fast-result.json", {
                "model": "fake-model", "group": group, "status": status,
                "load_seconds": 2, "item_seconds": 180, **scores,
            })
        report.main([
            "--out", str(self.out), f"Short={self.out / 'short'}", f"Big={self.out / 'big'}",
        ])
        markdown = (self.out / "report.md").read_text()
        self.assertIn("| Short | fake-model | small | 2 | 3.0 | 20/40 | 9/9 |", markdown)
        self.assertIn("| Big | fake-model | large | 2 | 3.0 | 20/40 | 2/9 | 2/15 |", markdown)
        self.assertIn("| Big | mt_miss_func |", markdown)
        summary = json.loads((self.out / "report.json").read_bytes())
        self.assertEqual([model["name"] for model in summary["models"]], ["Short", "Big"])
        self.assertEqual(summary["models"][1]["covered_score"], 75.0)
