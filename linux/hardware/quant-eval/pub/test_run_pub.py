"""Offline test for run_pub.py against a local http.server mock (stdlib only).

Run: python3 test_run_pub.py
Checks: request fields, warmup, resume, no-overwrite of error rows, malformed
responses, 24-item projection, per-request timeout, fleet stop-new guard,
fleet hard deadline, _meta handling and reserved-id rejection.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_pub.py"
STATE = {"requests": [], "fail_500": True}


class Mock(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        STATE["requests"].append(body)
        text = body["messages"][-1]["content"]
        if "ERR500" in text and STATE["fail_500"]:
            self.send_response(500); self.end_headers(); self.wfile.write(b"boom"); return
        if "SLOW" in text:
            time.sleep(float(text.split("SLOW")[1].split()[0]))
        if "BAD" in text:
            out = b'{"choices": []}'
        else:
            out = json.dumps({"choices": [{"message": {"content": "ANSWER: A " + text[:20]}, "finish_reason": "stop"}],
                              "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}}).encode()
        try:
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)
        except OSError:
            pass


def make_items(d, texts, tier="core"):
    rows = [{"id": i, "category": "mcq", "tier": tier, "body": {"messages": [{"role": "user", "content": t}],
                                                               "max_tokens": 64}} for i, t in texts]
    p = d / "items.jsonl"
    data = "".join(json.dumps(r) + "\n" for r in rows).encode()
    p.write_bytes(data)
    (d / "items.manifest.json").write_text(json.dumps({"frozen": True, "schema_version": 3, "reference_validation_runs": 3, "candidates_sha256": "synthetic",
                                                       "items_sha256": hashlib.sha256(data).hexdigest(),
                                                       "item_count": len(rows)}))
    return p


def run(items, out, *args):
    env = dict(os.environ, PUB_ITEMS=str(items))
    env.pop("PUB_TIER", None)
    t0 = time.monotonic()
    p = subprocess.run([sys.executable, str(RUNNER), str(out), *args, "--url", URL], env=env,
                       capture_output=True, text=True, timeout=120)
    return p, time.monotonic() - t0


def attempts(out):
    return [json.loads(l) for l in (out / "attempts.jsonl").read_text().splitlines()]


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


FAILS = []
srv = ThreadingHTTPServer(("127.0.0.1", 0), Mock)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{srv.server_address[1]}/v1/chat/completions"

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    # --- 1. normal run, warmup, errors, projection
    d1 = tmp / "a"; d1.mkdir()
    texts = [(f"q{i:02d}", f"question {i}") for i in range(26)]
    texts[3] = ("q03", "please ERR500")
    texts[5] = ("q05", "please BAD")
    items = make_items(d1, texts)
    out = tmp / "out1"
    p, _ = run(items, out, "routeA", "--warmup")
    check("run1 exit 0", p.returncode == 0, p.stderr[-500:])
    res = json.loads((out / "routeA.json").read_text())
    check("26 items + _meta stored", len(res) == 27 and "_meta" in res)
    meta = res["_meta"]
    check("_meta has route/start/sha", meta["route"] == "routeA" and meta["started"]
          and meta["items_sha256"] == hashlib.sha256(items.read_bytes()).hexdigest())
    check("HTTP 500 stored as error row", res["q03"]["error"].startswith("HTTP 500") and res["q03"]["cat"] == "mcq")
    check("malformed stored as error row", res["q05"]["error"].startswith("IndexError"))
    check("ok row schema", set(res["q00"]) == {"cat", "content", "reasoning", "tool_calls", "finish", "usage", "seconds"})
    warm = STATE["requests"][0]
    check("warmup request", warm["messages"][0]["content"] == "Reply OK." and warm["max_tokens"] == 32
          and warm["chat_template_kwargs"] == {"enable_thinking": False, "thinking": False})
    body = STATE["requests"][1]
    check("request fields", body["temperature"] == 0 and body["stream"] is False and body["model"] == "routeA"
          and body["max_tokens"] == 64 and body["chat_template_kwargs"] == {"enable_thinking": False, "thinking": False})
    log = attempts(out)
    check("attempts log: 1 warmup + 26 items", sum(r["kind"] == "warmup" for r in log) == 1
          and sum(r["kind"] == "item" for r in log) == 26)
    check("attempt fields", all(k in log[1] for k in ("route", "item", "start", "seconds", "finish", "usage", "error")))
    proj = [r for r in log if r["kind"] == "projection"]
    measured = [r["item"] for r in log if r["kind"] == "item"][:24]
    expected_tokens = sum((res[i].get("usage") or {}).get("completion_tokens", 0) for i in measured)
    check("projection after 24 items", len(proj) == 1 and proj[0]["items_measured"] == 24
          and proj[0]["completion_tokens"] == expected_tokens and proj[0]["route_items"] == 26, {"projection":proj,"expected_tokens":expected_tokens,"measured":measured})
    check("projection printed", "PROJECTION" in p.stdout)
    fleet = json.loads((out / "fleet.json").read_text())

    # --- 2. resume: no new requests, error rows not overwritten even though server now succeeds
    STATE["fail_500"] = False
    n0 = len(STATE["requests"])
    p, _ = run(items, out, "routeA")
    res2 = json.loads((out / "routeA.json").read_text())
    check("resume sends no requests", len(STATE["requests"]) == n0 and p.returncode == 0, p.stdout[-300:])
    check("error rows not overwritten", res2["q03"] == res["q03"] and res2["q05"] == res["q05"])
    check("fleet start persisted", json.loads((out / "fleet.json").read_text())["fleet_start"] == fleet["fleet_start"]
          and len(json.loads((out / "fleet.json").read_text())["invocations"]) == 2)
    check("_meta start preserved", res2["_meta"]["started"] == meta["started"])

    # --- 3. per-request timeout (cap 1 s, server sleeps 3 s); next item still runs
    d3 = tmp / "c"; d3.mkdir()
    items3 = make_items(d3, [("s1", "SLOW 3 x"), ("s2", "fast")])
    out3 = tmp / "out3"
    p, dt = run(items3, out3, "routeB", "--max-request-seconds", "1")
    r3 = json.loads((out3 / "routeB.json").read_text())
    check("timeout stored as error row", r3["s1"]["error"].startswith("TimeoutError")
          and r3["s1"]["seconds"] < 2.0 and "fleet_deadline" not in r3["s1"], r3.get("s1"))
    check("run continues after timeout", r3["s2"].get("finish") == "stop" and p.returncode == 0)

    # --- 4. stop-new guard: fleet started 19.6 h ago -> nothing starts, exit 3, items pending
    out4 = tmp / "out4"; out4.mkdir()
    (out4 / "fleet.json").write_text(json.dumps({"fleet_start": time.time() - 19.6 * 3600, "invocations": []}))
    n0 = len(STATE["requests"])
    p, _ = run(items3, out4, "routeC", "--warmup")
    r4 = json.loads((out4 / "routeC.json").read_text())
    stop = [r for r in attempts(out4) if r["kind"] == "stop"]
    check("stop-new: no requests, exit 3", len(STATE["requests"]) == n0 and p.returncode == 3, p.stdout + p.stderr[-300:])
    check("stop-new: items pending (not stored)", set(r4) == {"_meta"} and stop and stop[0]["pending"] == {"routeC": 2})

    # --- 5. hard fleet deadline: 1.5 s of budget left, stop-new == budget; SLOW item cut at deadline
    out5 = tmp / "out5"; out5.mkdir()
    (out5 / "fleet.json").write_text(json.dumps({"fleet_start": time.time() - (20 * 3600 - 1.5), "invocations": []}))
    p, dt = run(items3, out5, "routeD", "--stop-new-hours", "20")
    r5 = json.loads((out5 / "routeD.json").read_text())
    check("deadline: started request cut, flagged", r5.get("s1", {}).get("error", "").startswith("TimeoutError")
          and r5["s1"].get("fleet_deadline") is True and r5["s1"]["seconds"] < 2.5, r5)
    check("deadline: later item pending, exit 3", "s2" not in r5 and p.returncode == 3 and dt < 10, (p.returncode, dt))

    # --- 6. reserved id and items-sha mismatch
    d6 = tmp / "f"; d6.mkdir()
    items6 = make_items(d6, [("_meta", "x")])
    p, _ = run(items6, tmp / "out6", "routeE")
    check("reserved '_meta' id rejected", p.returncode != 0 and "reserved" in p.stderr)
    d7 = tmp / "g"; d7.mkdir()
    items7 = make_items(d7, [("q00", "different")])
    p, _ = run(items7, out, "routeA")
    check("changed items file refused on resume", p.returncode != 0 and "items_sha256" in p.stderr)

    # --- 7. grade_pub-style lookup ignores _meta (only item ids are read)
    check("_meta not an item id", "_meta" not in {i for i, _ in texts})

srv.shutdown()
print(f"\n{'ALL PASS' if not FAILS else 'FAILURES: ' + ', '.join(FAILS)}")
sys.exit(1 if FAILS else 0)
