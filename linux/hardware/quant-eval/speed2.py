"""Streaming speed probe. usage: speed2.py out.json model[,model...]
Per model: one warm-up, then 2x short prompt / 400-token answer (TTFT, decode tok/s) and
2x the ~4.5K-token register prompt / 40-token answer (TTFT -> prefill tok/s)."""
import json, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from suite2 import DOC
URL = "http://127.0.0.1:30100/v1/chat/completions"


def stream(model, prompt, max_tokens):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": 0,
            "stream": True, "stream_options": {"include_usage": True}, "ignore_eos": True,
            "chat_template_kwargs": {"enable_thinking": False, "thinking": False}}
    t0 = time.time(); first = None; usage = None; n = 0
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=7200) as r:
        for line in r:
            line = line.decode().strip()
            if not line.startswith("data:") or line == "data: [DONE]":
                continue
            d = json.loads(line[5:])
            if d.get("error"):
                return {"error": d["error"].get("message", str(d["error"]))[:200], "tokens_before_error": n, "total": round(time.time() - t0, 2)}
            if d.get("usage"):
                usage = d["usage"]
            for c in d.get("choices", []):
                delta = c.get("delta", {})
                if delta.get("content") or delta.get("reasoning_content"):
                    n += 1
                    if first is None:
                        first = time.time()
    end = time.time()
    if first is None:
        return {"error": "no content streamed", "total": round(end - t0, 2)}
    toks = (usage or {}).get("completion_tokens", n)
    return {"ttft": round(first - t0, 2), "decode_tps": round((toks - 1) / (end - first), 2) if toks > 1 else None,
            "prompt_tokens": (usage or {}).get("prompt_tokens"), "completion_tokens": toks, "total": round(end - t0, 2)}


out = Path(sys.argv[1]); res = json.loads(out.read_text()) if out.exists() else {}
essay = "Write a long, detailed history of the printing press, from Gutenberg to modern digital printing."
for m in sys.argv[2].split(","):
    t0 = time.time(); stream(m, "Say OK.", 4); load = round(time.time() - t0, 1)
    runs = {"load_and_first": load, "short": [stream(m, essay, 400) for _ in range(2)],
            "long": [stream(m, DOC + "\n\nSummarize the register in two sentences.", 40) for _ in range(2)]}
    for r in runs["long"]:
        r["prefill_tps"] = round(r["prompt_tokens"] / r["ttft"], 1) if r.get("prompt_tokens") and r.get("ttft") else None
    res[m] = runs; out.write_text(json.dumps(res, indent=1)); print(m, json.dumps(runs), flush=True)
