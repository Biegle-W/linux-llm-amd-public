"""Run one frozen ranking route. Use a fresh output directory for each timed run.

Exit codes: 0 mandatory core covered (a skipped extension suffix is normal),
3 time guard before core coverage, 4 GPU hold or failed warm-up. The answer
file is compatible with grade_pub. run.json tracks the timed prefix.
"""
import argparse
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import hashlib
import json
import math
import multiprocessing
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "pub"))
import run_pub

BUDGET_MIN = {"small": 15, "large": 30}
# Fallback for lists without item_costs: median per-item median answer length,
# across the 11 public core routes, rounded to whole tokens.
BASE_TOKENS = {"knowledge": 346, "math": 912, "reasoning": 384,
               "code": 234, "tools": 127, "instruction": 207}


def worker(pipe):
    """Keep HTTP in a killable process so a hold can close an in-flight socket."""
    with pipe:
        while True:
            try:
                request = pipe.recv()
            except EOFError:
                return
            pipe.send(run_pub.post(*request))


@contextmanager
def client():
    ctx = multiprocessing.get_context("spawn")
    pipe, remote = ctx.Pipe()
    proc = ctx.Process(target=worker, args=(remote,), daemon=True)
    proc.start()
    remote.close()
    try:
        yield pipe, proc
    finally:
        # Closing the process also closes outstanding HTTP connections.
        proc.terminate()
        proc.join()
        proc.close()
        pipe.close()


def held(path):
    return path is not None and path.exists()


def request(client_pair, url, cat, body, deadline, abort_file, monotonic):
    """Send one public request and enforce the absolute monotonic deadline."""
    pipe, proc = client_pair
    remaining = deadline - monotonic()
    if held(abort_file):
        return None, "abort_file"
    if remaining <= 0:
        return None, "deadline"
    pipe.send((url, body, remaining))
    while True:
        remaining = max(0, deadline - monotonic())
        ready = pipe.poll(min(remaining, 0.1))
        if monotonic() > deadline or (not ready and monotonic() >= deadline):
            proc.terminate()
            return {"cat": cat, "error": "TimeoutError: rank deadline exceeded"}, "deadline"
        if ready:
            reply, error, _ = pipe.recv()
            if error:
                return {"cat": cat, "error": error}, (
                    "deadline" if error.startswith("TimeoutError") and monotonic() >= deadline else None)
            try:
                row = run_pub.to_row(cat, reply)
                if row["finish"] not in ("stop", "length", "tool_calls"):
                    row["error"] = "malformed response: invalid finish reason"
                return row, None
            except (IndexError, KeyError, TypeError, AttributeError) as exc:
                return {"cat": cat, "error": f"{type(exc).__name__}: {exc}"}, None
        if held(abort_file):
            proc.terminate()
            return None, "abort_file"


def finite(value, name, *, positive=False):
    if (type(value) not in (float, int) or not math.isfinite(value)
            or value < 0 or (positive and value == 0)):
        raise ValueError(f"invalid {name}: {value!r}")
    return value


@dataclass
class Plan:
    entries: list
    budget_s: int
    core_n: int
    rank_items_sha256: str
    speeds_sha256: str


def load_plan(args):
    rank_data = args.rank_items.read_bytes()
    frozen = json.loads(rank_data)
    speed_data = args.speeds.read_bytes()
    speeds = json.loads(speed_data)
    # A missing digest (legacy freeze) is a cache miss, even at the default path.
    speed_hash = hashlib.sha256(speed_data).hexdigest()
    same_model = frozen.get("speeds_sha256") == speed_hash
    saved_seconds = frozen.get("item_seconds", {}).get(args.route, {}) if same_model else {}
    model = speeds.get("routes", speeds)[args.route]
    minutes = BUDGET_MIN[args.route_class]
    if model["budget_min"] != minutes or model.get("class", args.route_class) != args.route_class:
        raise ValueError("requested class disagrees with route speed model")
    for key in ("decode_tok_s", "prefill_tok_s", "verbosity", "overhead_s"):
        finite(model[key], key, positive=(key != "overhead_s"))

    rows = {r["id"]: r for r in run_pub.suite_pub.load_items(args.items, "all")}
    order = frozen["order"]
    if (not isinstance(order, list) or not order or len(order) != len(set(order))
            or any(not isinstance(i, str) or i.startswith("_") or i not in rows for i in order)):
        raise ValueError("rank order must be a nonempty list of distinct public item ids")
    # A legacy flat list had no optional suffix.
    core_n = frozen.get("core_n", len(order))
    if type(core_n) is not int or not 1 <= core_n <= len(order):
        raise ValueError("core_n must be an integer from 1 through len(order)")
    plan = []
    for item in order:
        row = rows[item]
        cat = row["category"]
        caps = frozen["caps"]
        kind = item.partition(":")[0]
        cap = next((caps[k] for k in (kind, cat, row.get("grader")) if isinstance(k, str) and k in caps), None)
        if type(cap) is not int or cap <= 0:
            raise ValueError(f"missing or invalid token cap for {item}")
        body = dict(row["body"], model=args.route, temperature=0, stream=False,
                    chat_template_kwargs=dict(run_pub.THINKING_OFF))
        body["max_tokens"] = min(cap, body["max_tokens"])
        saved = saved_seconds.get(item)
        if saved is not None:
            # Selector used saved lengths for this specific route and item.
            plan.append((item, cat, body, finite(saved, "item seconds", positive=True)))
            continue
        costs = frozen.get("item_costs", {}).get(item, {})
        prompt = costs.get("prompt_tokens")
        if prompt is None:
            # Approximate templated prompt size and include function schemas.
            fields = {k: body[k] for k in ("messages", "tools", "tool_choice") if k in body}
            prompt = len(json.dumps(fields, ensure_ascii=False).encode()) / 4
        answer = costs.get("completion_tokens", BASE_TOKENS.get(cat, cap))
        decode = min(body["max_tokens"], finite(answer, "completion tokens") * model["verbosity"])
        seconds = model["overhead_s"] + finite(prompt, "prompt tokens") / model["prefill_tok_s"]
        plan.append((item, cat, body, seconds + decode / model["decode_tok_s"]))
    return Plan(plan, minutes * 60, core_n, hashlib.sha256(rank_data).hexdigest(), speed_hash)


def run(args, monotonic=time.monotonic, wall=time.time):
    route = args.route
    if not route or Path(route).name != route or route.startswith(".") or "," in route or route == "run":
        raise ValueError("expected a single safe route name")
    loaded = load_plan(args)
    plan, budget = loaded.entries, loaded.budget_s
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    raw_path = out / f"{route}.json"
    report_path = out / "run.json"
    with (out / ".run_pub.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if report_path.exists() or raw_path.exists():
            raise ValueError("this timed run already has output; choose a fresh output directory")
        meta = {"route": route, "runner": "run_rank.py",
                "items_sha256": hashlib.sha256(args.items.read_bytes()).hexdigest(),
                "rank_items_sha256": loaded.rank_items_sha256,
                "speeds_sha256": loaded.speeds_sha256}
        raw = {"_meta": meta}
        details = {i: {"status": "not_run", "seconds": 0, "prompt_tokens": None,
                       "completion_tokens": None} for i, *_ in plan}
        report = {"route": route, "class": args.route_class, "budget_s": budget, "core_n": loaded.core_n,
                  "ready_utc": None, "items": details, "rank_items_sha256": meta["rank_items_sha256"]}
        start = None

        def save(reason):
            pending = [i for i, r in details.items() if r["status"] == "not_run"]
            counts = Counter(r["status"] for r in details.values())
            # A capped/error row is a scored attempt, not a skipped item. Walk
            # the frozen order rather than using the total number of attempts.
            prefix = next((k for k, r in enumerate(details.values()) if r["status"] == "not_run"), len(plan))
            report.update(complete=not pending, core_complete=prefix >= loaded.core_n,
                          answered_prefix=prefix, not_run=pending, stop_reason=reason,
                          elapsed_s=round(monotonic() - start, 3) if start is not None else 0,
                          counts={k: counts[k] for k in ("ok", "capped", "error", "not_run")})
            report["counts"]["attempted"] = len(plan) - len(pending)
            run_pub.save_route(report_path, report)

        run_pub.save_route(raw_path, raw)
        save("warming_up")
        if held(args.abort_file):
            save("abort_file")
            return 4
        with client() as transport:
            warm = {"messages": [{"role": "user", "content": "Reply OK."}], "max_tokens": 32,
                    "model": route, "temperature": 0, "stream": False,
                    "chat_template_kwargs": dict(run_pub.THINKING_OFF)}
            row, stop = request(transport, args.url, "warmup", warm, monotonic() + 1200,
                                args.abort_file, monotonic)
            if stop or row.get("error") or held(args.abort_file):
                report["warmup_error"] = (row or {}).get("error")
                save("abort_file" if held(args.abort_file) or stop == "abort_file" else "warmup_failed")
                return 4

            report["ready_utc"] = run_pub.iso(wall())
            start = monotonic()
            deadline = start + budget
            save("running")
            # Anchor pace to one typical request, then compare cumulative actual
            # seconds with the same completed items' unadjusted model estimates.
            predicted = observed = sum(entry[3] for entry in plan) / len(plan)
            reason = "complete"
            for item, cat, body, base in plan:
                estimate = base * (observed / predicted if predicted else 1)
                t0 = monotonic()
                if held(args.abort_file):
                    reason = "abort_file"
                    break
                if estimate > deadline - t0 or t0 >= deadline:
                    reason = "estimate_exceeds_remaining"
                    break
                row, stop = request(transport, args.url, cat, body, deadline, args.abort_file, monotonic)
                if row is not None:
                    seconds = monotonic() - t0
                    row["seconds"] = round(seconds, 3)
                    if stop == "deadline":
                        row["fleet_deadline"] = True
                    raw[item] = row
                    run_pub.save_route(raw_path, raw)
                    usage = row.get("usage")
                    usage = usage if isinstance(usage, dict) else {}
                    status = "error" if row.get("error") else "capped" if row["finish"] == "length" else "ok"
                    details[item] = {"status": status, "seconds": row["seconds"],
                                     "prompt_tokens": usage.get("prompt_tokens"),
                                     "completion_tokens": usage.get("completion_tokens"),
                                     "max_tokens": body["max_tokens"], "estimate_s": round(estimate, 3)}
                    if status != "error":
                        observed += seconds
                        predicted += base
                    save("running")
                if stop:
                    reason = stop
                    break
        save(reason)
        if reason == "abort_file":
            return 4
        return 0 if report["core_complete"] else 3


def main(argv=None, **clock):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("out_dir", type=Path)
    p.add_argument("route")
    p.add_argument("--items", type=Path, required=True)
    p.add_argument("--rank-items", type=Path, default=HERE / "rank-items.json")
    p.add_argument("--speeds", type=Path, default=HERE / "speeds.json")
    p.add_argument("--class", dest="route_class", choices=BUDGET_MIN, required=True)
    p.add_argument("--url", default=run_pub.DEFAULT_URL)
    p.add_argument("--abort-file", type=Path)
    args = p.parse_args(argv)
    try:
        return run(args, **clock)
    except (ValueError, KeyError, RuntimeError, OSError) as exc:
        p.error(str(exc))


if __name__ == "__main__":
    sys.exit(main())
