"""Public-suite runner with a persisted fleet time guard (stdlib only).

Usage:
  run_pub.py <out_dir> <route[,route]> [--tier core|extended|all] [--url URL]
             [--budget-hours 20] [--stop-new-hours 19.5] [--only id,id]
             [--warmup] [--max-request-seconds 1200]

Keeps run_suite.py's per-route result schema (<out_dir>/<route>.json, an object
mapping item id -> row) and resume behaviour (existing ids, including failed or
capped first attempts, are never re-requested or overwritten). Adds:

* <out_dir>/fleet.json: fleet start wall timestamp, persisted across
  invocations; elapsed time never decreases within a process (monotonic guard).
* Before every request: refuse to start once elapsed >= --stop-new-hours; the
  client deadline is min(--max-request-seconds, remaining fleet budget) and is
  enforced as a hard wall deadline (socket shut down), not a per-read timeout.
* <out_dir>/attempts.jsonl: append-only log of every attempt (incl. warmup),
  projections, and stop events.
* Reserved "_meta" key in each route file (route, start time, items SHA-256).
  Item ids starting with "_" are rejected so they cannot collide. grade_pub.py
  only looks up item ids, so it ignores "_meta".
* After the first 24 stored items of a route/tier: emitted completion tokens,
  seconds and projected route duration are printed and logged.

Note: closing the client connection may not stop backend generation; the chair
must stop/drain the server to enforce a physical compute ceiling.
Exit codes: 0 all requested items stored; 3 stopped by fleet time guard.
"""
import argparse
import fcntl
import hashlib
import http.client
import json
import os
import socket
import sys
import threading
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import suite_pub  # noqa: E402

DEFAULT_URL = "http://127.0.0.1:30100/v1/chat/completions"
META_KEY = "_meta"
PROJECTION_AFTER = 24
THINKING_OFF = {"enable_thinking": False, "thinking": False}


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds")


class FleetClock:
    """Elapsed seconds since the persisted fleet start; never goes backwards."""

    def __init__(self, out_dir, budget_h, stop_new_h):
        self.path = out_dir / "fleet.json"
        now = time.time()
        if self.path.exists():
            self.data = json.loads(self.path.read_text())
        else:
            self.data = {"fleet_start": now, "fleet_start_iso": iso(now), "invocations": []}
        self.budget = budget_h * 3600.0
        self.stop_new = stop_new_h * 3600.0
        self.base = max(0.0, now - float(self.data["fleet_start"]),
                        float(self.data.get("max_elapsed_seen", 0.0)))
        self.mono0 = time.monotonic()
        self.data["invocations"].append({"start": now, "start_iso": iso(now), "elapsed_at_start": round(self.base, 3),
                                         "budget_hours": budget_h, "stop_new_hours": stop_new_h, "argv": sys.argv[1:]})
        self.save()

    def elapsed(self):
        wall = time.time() - float(self.data["fleet_start"])
        return max(wall, self.base + (time.monotonic() - self.mono0))

    def remaining(self):
        return self.budget - self.elapsed()

    def may_start(self):
        e = self.elapsed()
        return e < self.stop_new and e < self.budget

    def save(self):
        self.data["max_elapsed_seen"] = round(max(float(self.data.get("max_elapsed_seen", 0.0)),
                                                  self.elapsed()), 3)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, indent=1))
        os.replace(tmp, self.path)


def post(url, body, deadline):
    """POST JSON with a hard wall deadline. Returns (parsed_json|None, error|None, http_status)."""
    u = urllib.parse.urlsplit(url)
    cls = http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection
    conn = cls(u.hostname, u.port, timeout=max(deadline, 0.001))
    path = u.path + (("?" + u.query) if u.query else "")
    out = {}

    def work():
        try:
            conn.request("POST", path or "/", json.dumps(body).encode(), {"Content-Type": "application/json"})
            resp = conn.getresponse()
            out["status"], out["data"] = resp.status, resp.read()
        except BaseException as e:  # noqa: BLE001 - surfaced as an error row
            out["exc"] = e

    t = threading.Thread(target=work, daemon=True)
    t.start()
    t.join(deadline)
    if t.is_alive():
        try:
            if conn.sock is not None:
                conn.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conn.close()
        t.join(5)
        return None, f"TimeoutError: client deadline {deadline:.1f}s exceeded", None
    conn.close()
    if "exc" in out:
        e = out["exc"]
        if isinstance(e, (TimeoutError, socket.timeout)):
            return None, f"TimeoutError: {e} (deadline {deadline:.1f}s)", None
        return None, f"{type(e).__name__}: {e}", None
    if not 200 <= out["status"] < 300:
        return None, f"HTTP {out['status']}: {out['data'][:300]!r}", out["status"]
    try:
        return json.loads(out["data"]), None, out["status"]
    except ValueError as e:
        return None, f"{type(e).__name__}: {e}", out["status"]


def to_row(cat, r):
    """Same row schema as ref/run_suite.py. Raises on malformed responses."""
    m = r["choices"][0]["message"]
    return {"cat": cat, "content": m.get("content"), "reasoning": m.get("reasoning_content") or m.get("reasoning"),
            "tool_calls": m.get("tool_calls"), "finish": r["choices"][0].get("finish_reason"), "usage": r.get("usage")}


class Log:
    def __init__(self, path):
        self.path = path

    def write(self, **rec):
        rec.setdefault("ts", iso(time.time()))
        with self.path.open("a") as f:
            f.write(json.dumps(rec) + "\n")
            f.flush()
            os.fsync(f.fileno())


def save_route(path, done):
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(done, indent=1))
    os.replace(tmp, path)


def completion_tokens(row):
    u = row.get("usage") if isinstance(row, dict) else None
    v = u.get("completion_tokens") if isinstance(u, dict) else None
    return v if isinstance(v, int) else 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("out_dir", type=Path)
    p.add_argument("routes")
    p.add_argument("--tier", choices=["core", "extended", "all"], default=None,
                   help="overrides PUB_TIER (default core)")
    p.add_argument("--url", default=DEFAULT_URL)
    p.add_argument("--budget-hours", type=float, default=20.0)
    p.add_argument("--stop-new-hours", type=float, default=19.5)
    p.add_argument("--only", default=None, help="comma-separated item ids")
    p.add_argument("--warmup", action="store_true", help="send one unscored 'Reply OK.' request per route")
    p.add_argument("--max-request-seconds", type=float, default=1200.0)
    p.add_argument("--abort-file", type=Path, default=None, help="stop (exit 4) if this file exists, e.g. a GPU hold")
    p.add_argument("--max-consecutive-errors", type=int, default=3, help="stop (exit 4) after this many error rows in a row")
    a = p.parse_args(argv)
    if a.stop_new_hours > a.budget_hours:
        p.error("--stop-new-hours must not exceed --budget-hours")

    tier = a.tier or os.environ.get("PUB_TIER", "core")
    items_path = Path(os.environ.get("PUB_ITEMS", suite_pub.HERE / "items.jsonl"))
    items = suite_pub.load_items(items_path, tier)  # verifies manifest SHA-256
    items_sha = hashlib.sha256(items_path.read_bytes()).hexdigest()
    bad = [r["id"] for r in items if not isinstance(r["id"], str) or r["id"].startswith("_")]
    if bad:
        raise SystemExit(f"item ids reserved/invalid (must be str not starting with '_'): {bad[:5]}")
    only = set(a.only.split(",")) if a.only else None

    a.out_dir.mkdir(parents=True, exist_ok=True)
    lock = open(a.out_dir / ".run_pub.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise SystemExit(f"another run_pub.py holds {a.out_dir}/.run_pub.lock")
    clock = FleetClock(a.out_dir, a.budget_hours, a.stop_new_hours)
    log = Log(a.out_dir / "attempts.jsonl")
    stopped = False
    aborted = None
    consecutive = 0

    def fleet_h():
        return round(clock.elapsed() / 3600, 4)

    for route in a.routes.split(","):
        if not route or Path(route).name != route or route.startswith("."):
            raise SystemExit(f"unsafe route name {route!r}")
        path = a.out_dir / f"{route}.json"
        done = json.loads(path.read_text()) if path.exists() else {}
        if not isinstance(done, dict):
            raise SystemExit(f"{path} is not a JSON object")
        meta = done.get(META_KEY)
        if meta is not None and meta.get("items_sha256") not in (None, items_sha):
            raise SystemExit(f"{path}: items_sha256 {meta.get('items_sha256')} != current {items_sha}; "
                             "refusing to mix item sets (use a new out_dir)")
        if meta is None:
            meta = {"route": route, "started": iso(time.time()), "fleet_elapsed_h_at_start": fleet_h(),
                    "items_sha256": items_sha, "items_path": str(items_path), "runner": "run_pub.py", "tiers": {}}
        meta["tiers"].setdefault(tier, iso(time.time()))
        done[META_KEY] = meta
        todo = [r for r in items if r["id"] not in done and (only is None or r["id"] in only)]
        if not todo:
            save_route(path, done)
            print(route, "nothing to do", flush=True)
            continue

        if a.warmup:
            if not clock.may_start():
                stopped = True
            else:
                dl = min(a.max_request_seconds, clock.remaining())
                body = {"messages": [{"role": "user", "content": "Reply OK."}], "max_tokens": 32, "model": route,
                        "temperature": 0, "stream": False, "chat_template_kwargs": dict(THINKING_OFF)}
                t0 = time.time(); m0 = time.monotonic()
                r, err, _ = post(a.url, body, dl)
                secs = round(time.monotonic() - m0, 2)
                finish = usage = None
                if r is not None:
                    try:
                        row = to_row("warmup", r); finish, usage = row["finish"], row["usage"]
                    except Exception as e:  # noqa: BLE001
                        err = f"{type(e).__name__}: {e}"
                log.write(kind="warmup", route=route, item=None, start=iso(t0), fleet_elapsed_h=fleet_h(),
                          seconds=secs, deadline=round(dl, 1), finish=finish, usage=usage, error=err)
                print(route, "WARMUP", secs, err or "ok", flush=True)

        for it in todo:
            if a.abort_file is not None and a.abort_file.exists():
                aborted = f"abort file present: {a.abort_file}"
            elif consecutive >= a.max_consecutive_errors:
                aborted = f"{consecutive} consecutive error rows"
            if aborted:
                break
            if stopped or not clock.may_start():
                stopped = True
                break
            item, cat = it["id"], it["category"]
            dl = min(a.max_request_seconds, clock.remaining())
            body = dict(it["body"], model=route, temperature=0, stream=False,
                        chat_template_kwargs=dict(THINKING_OFF))
            t0 = time.time(); m0 = time.monotonic()
            r, err, status = post(a.url, body, dl)
            if r is not None:
                try:
                    row = to_row(cat, r)
                except Exception as e:  # noqa: BLE001 - malformed response
                    row = {"cat": cat, "error": f"{type(e).__name__}: {e}"}
            else:
                row = {"cat": cat, "error": err}
                if err.startswith("TimeoutError") and dl < a.max_request_seconds:
                    row["fleet_deadline"] = True  # cut off by the fleet budget, not the per-request cap
            row["seconds"] = round(time.monotonic() - m0, 2)
            if item in done:  # never overwrite (defensive; todo excludes stored ids)
                raise SystemExit(f"refusing to overwrite stored result {route}/{item}")
            done[item] = row
            save_route(path, done)
            log.write(kind="item", route=route, item=item, tier=it.get("tier"), cat=cat, start=iso(t0),
                      fleet_elapsed_h=fleet_h(), seconds=row["seconds"], deadline=round(dl, 1), http_status=status,
                      finish=row.get("finish"), usage=row.get("usage"), error=row.get("error"))
            clock.save()
            consecutive = consecutive + 1 if row.get("error") else 0
            print(route, item, row["seconds"], (row.get("error") or (row.get("content") or "")[:60]).replace("\n", " "),
                  flush=True)

            tier_ids = [x["id"] for x in items if x["id"] in done]
            if len(tier_ids) == PROJECTION_AFTER:
                rows = [done[i] for i in tier_ids]
                toks = sum(completion_tokens(x) for x in rows)
                secs = sum(x.get("seconds", 0) for x in rows)
                n = len(items)
                proj = {"kind": "projection", "route": route, "tier": tier, "items_measured": PROJECTION_AFTER,
                        "completion_tokens": toks, "seconds": round(secs, 2),
                        "tok_per_s": round(toks / secs, 2) if secs else None, "route_items": n,
                        "projected_route_seconds": round(secs / PROJECTION_AFTER * n, 1),
                        "projected_route_hours": round(secs / PROJECTION_AFTER * n / 3600, 3),
                        "projected_route_completion_tokens": round(toks / PROJECTION_AFTER * n),
                        "fleet_elapsed_h": fleet_h()}
                log.write(**proj)
                print("PROJECTION", json.dumps(proj), flush=True)

        save_route(path, done)
        if aborted:
            log.write(kind="abort", reason=aborted, route=route, fleet_elapsed_h=fleet_h())
            print("ABORTED:", aborted, "on", route, flush=True)
            clock.save()
            return 4
        if stopped:
            break

    clock.save()
    if stopped:
        pending = {}
        for route in a.routes.split(","):
            path = a.out_dir / f"{route}.json"
            done = json.loads(path.read_text()) if path.exists() else {}
            pending[route] = [r["id"] for r in items if r["id"] not in done and (only is None or r["id"] in only)]
        log.write(kind="stop", reason="fleet time guard", fleet_elapsed_h=fleet_h(),
                  pending={k: len(v) for k, v in pending.items()}, pending_ids=pending)
        print(f"STOPPED by fleet time guard at {fleet_h()} h; pending:",
              json.dumps({k: len(v) for k, v in pending.items()}), flush=True)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
