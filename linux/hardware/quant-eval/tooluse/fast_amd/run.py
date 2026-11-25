"""Run the frozen benchmark against an OpenAI-compatible endpoint."""

import argparse
from datetime import datetime, timezone
import json
import math
import multiprocessing
from pathlib import Path
import sys
from threading import Thread
from time import monotonic, sleep
from urllib.parse import urlsplit

from fast_amd import build_manifest, episode
from fast_amd.http_client import DeadlineExceeded, RequestError, request
from fast_amd.tooling import grade_single, openai_tools

LOAD_CAP = 180
ITEM_BUDGET = {"small": 690, "large": 3360}
HARD_LIMIT = {"small": 900, "large": 3600}
ITEM_LIMIT = {"single": 120, "multi": 480}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def chat_body(model, messages, tools=None):
    body = {
        "model": model, "messages": messages, "temperature": 0.6, "top_p": 0.95,
        "max_tokens": 2048, "seed": build_manifest.SEED, "stream": False,
    }
    if tools is None:
        body["max_tokens"] = 64
    else:
        body.update(tools=tools, tool_choice="auto")
    return body


def chat(url, deadline, body, record=None, *, warmup=False):
    response = request(url, deadline, body, require_ok=warmup)
    try:
        choice = response["choices"][0]
        message = choice["message"]
        if not isinstance(message, dict):
            raise ValueError("Invalid message")
        if warmup:
            return message, choice.get("finish_reason")
        finish = choice["finish_reason"]
        content = message.get("content")
        calls = message.get("tool_calls")
        if not isinstance(finish, str):
            raise ValueError("Missing finish reason")
        if content is not None and not isinstance(content, str):
            raise ValueError("Invalid message content")
    except (KeyError, IndexError, AttributeError, TypeError, ValueError) as exc:
        raise RequestError("Invalid chat completion") from exc
    if record is not None:
        record["finish_reasons"].append(finish)
        record["requests"].append({"content": content, "tool_calls": calls})
        usage = response.get("usage")
        if isinstance(usage, dict):
            for name, tokens in usage.items():
                if type(tokens) is int and tokens >= 0:
                    record["usage"][name] = record["usage"].get(name, 0) + tokens
    return message, finish


def health(url, hard_end):
    deadline = min(monotonic() + 30, hard_end)
    while monotonic() < deadline:
        try:
            request(url, deadline)
            return True
        except RequestError:
            sleep(max(0, min(0.1, deadline - monotonic())))
    return False


def item_record(item):
    return {
        "id": item["id"], "pool": item["pool"], "outcome": "not_run",
        "cut": False, "timeout": False, "seconds": 0.0,
        "finish_reasons": [], "usage": {}, "requests": [],
    }


def score(items, records, group, setup_failure=False):
    def counts(rows):
        return {
            "correct": sum(row["outcome"] == "correct" for row in rows),
            "scored": sum(row["outcome"] in ("correct", "wrong") for row in rows),
            "total": len(rows),
            "timeouts": sum(row["timeout"] for row in rows),
        }

    singles = counts([row for item, row in zip(items, records) if item["part"] == "single"])
    episodes = counts([row for item, row in zip(items, records) if item["part"] == "multi"])
    core = counts([
        row for item, row in zip(items, records) if item["part"] == "multi" and item["core"]
    ])
    single, passed = singles["correct"], core["correct"]
    coverage = f"single {singles['scored']}/40, episodes {core['scored']}/9"
    if group == "large":
        coverage += f", episodes15 {episodes['scored']}/15"
    complete = singles["scored"] + episodes["scored"] == len(items)
    result = {
        "single_correct": single, "episodes_passed": passed, "coverage": coverage,
        "complete": complete, "score_meaningful": core["scored"] >= 3,
        "score": None if setup_failure else round(50 * single / 40 + 50 * passed / 9, 1),
        "timeouts": singles["timeouts"] + episodes["timeouts"],
        "pools": {
            pool: counts([row for row in records if row["pool"] == pool])
            for pool in build_manifest.POOLS
        },
    }
    if group == "large":
        result["episodes15_passed"] = episodes["correct"]
        result["score15"] = (
            None if setup_failure else round(50 * single / 40 + 50 * episodes["correct"] / 15, 1)
        )
    if not complete:
        result["covered_score"] = (
            round(50 * single / singles["scored"] + 50 * passed / core["scored"], 1)
            if singles["scored"] and core["scored"] else None
        )
    return result


def run_episode(row, gold, docs, ask, record, deadline):
    context = multiprocessing.get_context("fork")
    receive, send = context.Pipe(duplex=False)
    outcome = []

    def work():
        receive.close()
        with send:
            def ask_and_log(messages, tools):
                log = {"finish_reasons": [], "requests": [], "usage": {}}
                reply = ask(messages, tools, log)
                send.send(("reply", log))
                return reply

            try:
                correct = episode.evaluate(row, gold, docs, ask_and_log)
            except DeadlineExceeded:
                send.send(("timeout", None))
            except RequestError:
                send.send(("result", False))
            else:
                send.send(("result", correct))

    def collect():
        # A pipe can become readable before a full message has arrived.
        # Read on a separate thread so an incomplete message cannot delay kill.
        try:
            while True:
                kind, value = receive.recv()
                if kind != "reply":
                    outcome.append((kind, value))
                    return
                record["finish_reasons"].extend(value["finish_reasons"])
                record["requests"].extend(value["requests"])
                for name, tokens in value["usage"].items():
                    record["usage"][name] = record["usage"].get(name, 0) + tokens
        except (EOFError, OSError):
            return

    with receive, send:
        child = context.Process(target=work)
        child.start()
        send.close()
        reader = Thread(target=collect)
        reader.start()
        try:
            reader.join(max(0, deadline - monotonic()))
            if reader.is_alive():
                raise DeadlineExceeded("Episode deadline reached")
            if not outcome:
                raise RequestError("Episode worker exited without a result")
            kind, correct = outcome[0]
            if kind == "timeout":
                raise DeadlineExceeded("Episode deadline reached")
            return correct
        finally:
            child.join(max(0, deadline - monotonic()) if outcome else 0)
            if child.is_alive():
                child.kill()
                child.join()
            reader.join()
            child.close()


def evaluate_items(items, records, data, docs, args, chat_url, budget_end, hard_end):
    global_end = min(budget_end, hard_end)
    for item, record in zip(items, records, strict=True):
        if args.abort_file is not None and args.abort_file.exists():
            return "aborted"
        started = monotonic()
        if started >= global_end:
            return "cut"
        item_end = started + ITEM_LIMIT[item["part"]]
        deadline = min(item_end, global_end)
        row, answer = data[item["id"]]
        gold = answer["ground_truth"] if answer is not None else None

        def ask(messages, tools, reply_log=record):
            return chat(chat_url, deadline, chat_body(args.model, messages, tools), reply_log)

        try:
            if item["part"] == "single":
                message, finish = ask(row["question"][0], openai_tools(row["function"]))
                correct = grade_single(item["pool"], message, finish, gold)
            else:
                correct = run_episode(row, gold, docs, ask, record, deadline)
        except DeadlineExceeded:
            timed_out = True
            correct = False
        except RequestError:
            timed_out = False
            correct = False
        else:
            timed_out = False
        ended = monotonic()
        record["seconds"] = round(ended - started, 6)
        if timed_out or ended >= deadline:
            if global_end <= item_end:
                record.update(outcome="cut", cut=True)
                return "cut"
            record.update(outcome="wrong", timeout=True)
        else:
            record["outcome"] = "correct" if correct else "wrong"
    return "completed"


def run(args, src=build_manifest.SOURCE, manifest_path=build_manifest.MANIFEST):
    started = monotonic()
    start_utc = utc_now()
    hard_end = started + args.hard_limit
    manifest, data, docs = build_manifest.verify(src, manifest_path)
    group_ids = set(manifest["groups"][args.group])
    items = [item for item in manifest["items"] if item["id"] in group_ids]
    records = [item_record(item) for item in items]
    base = args.base_url.rstrip("/")
    root = base.removesuffix("/v1")
    chat_url = root + "/v1/chat/completions"
    load_start = monotonic()
    load_end = min(load_start + args.load_cap, hard_end)
    item_seconds = 0.0
    health_answered = None
    try:
        body = chat_body(args.model, [{"role": "user", "content": "Reply with OK."}])
        chat(chat_url, load_end, body, warmup=True)
        if monotonic() >= load_end:
            raise DeadlineExceeded("Warm-up deadline reached")
    except RequestError:
        load_seconds = monotonic() - load_start
        status = "setup-failure"
    else:
        item_start = monotonic()
        load_seconds = item_start - load_start
        status = evaluate_items(
            items, records, data, docs, args, chat_url, item_start + args.item_budget, hard_end
        )
        item_seconds = monotonic() - item_start
        if status == "cut":
            health_answered = health(root + "/health", hard_end)

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "fast.jsonl").open("w", encoding="utf-8") as output:
        for record in records:
            output.write(json.dumps(record, ensure_ascii=True) + "\n")
    result = {
        "model": args.model, "group": args.group, "manifest_hash": manifest["manifest_hash"],
        "start_utc": start_utc, "end_utc": utc_now(), "load_seconds": round(load_seconds, 6),
        "item_seconds": round(item_seconds, 6), "status": status,
        "health_answered": health_answered,
        **score(items, records, args.group, setup_failure=status == "setup-failure"),
    }
    build_manifest.write_json(args.out / "fast-result.json", result)
    return {"setup-failure": 3, "aborted": 4}.get(status, 0)


def seconds(value):
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise argparse.ArgumentTypeError("expected finite, nonnegative seconds")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model")
    parser.add_argument("group", choices=ITEM_BUDGET)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--abort-file", type=Path)
    parser.add_argument("--load-cap", type=seconds, default=LOAD_CAP)
    parser.add_argument("--item-budget", type=seconds)
    parser.add_argument("--hard-limit", type=seconds)
    args = parser.parse_args(argv)
    try:
        url = urlsplit(args.base_url)
        if url.scheme not in {"http", "https"} or not url.hostname or url.query or url.fragment:
            raise ValueError("Expected an HTTP(S) base URL without a query or fragment")
        _ = url.port
        if args.item_budget is None:
            args.item_budget = ITEM_BUDGET[args.group]
        if args.hard_limit is None:
            args.hard_limit = HARD_LIMIT[args.group]
        return run(args)
    except (OSError, ValueError, KeyError) as exc:
        print(f"fast_amd: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
