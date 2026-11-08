import json, sys, time, urllib.request

URL = "http://127.0.0.1:%s/v1/chat/completions" % (sys.argv[1] if len(sys.argv) > 1 else "30011")
MODEL = sys.argv[2] if len(sys.argv) > 2 else "ripple-65b-vllm"


def stream(messages, max_tokens, tools=None, extra=None):
    body = {"model": MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0,
            "stream": True, "stream_options": {"include_usage": True}}
    if tools:
        body["tools"] = tools
    body.update(extra or {})
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    t0 = time.time(); first = None; text = ""; reasoning = ""; calls = {}; usage = None
    with urllib.request.urlopen(req, timeout=1800) as r:
        for line in r:
            line = line.decode().strip()
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            d = json.loads(line[6:])
            if d.get("usage"):
                usage = d["usage"]
            for c in d.get("choices", []):
                delta = c.get("delta", {})
                piece = (delta.get("content") or "") + (delta.get("reasoning_content") or delta.get("reasoning") or "")
                if (piece or delta.get("tool_calls")) and first is None:
                    first = time.time()
                text += delta.get("content") or ""
                reasoning += delta.get("reasoning_content") or delta.get("reasoning") or ""
                for tc in delta.get("tool_calls") or []:
                    e = calls.setdefault(tc["index"], {"name": "", "args": ""})
                    f = tc.get("function", {})
                    e["name"] += f.get("name") or ""
                    e["args"] += f.get("arguments") or ""
    t1 = time.time()
    pt, ct = usage["prompt_tokens"], usage["completion_tokens"]
    ttft = first - t0 if first else None
    dec = (ct - 1) / (t1 - first) if first and ct > 1 and t1 > first else None
    return {"prompt_tokens": pt, "completion_tokens": ct, "ttft_s": round(ttft, 2) if ttft else None,
            "prefill_tok_s": round(pt / ttft) if ttft else None, "decode_tok_s": round(dec, 1) if dec else None,
            "text": text, "reasoning_chars": len(reasoning), "tool_calls": list(calls.values())}


out = {}
r = stream([{"role": "user", "content": "What is 17 * 23? Answer with just the number."}], 64)
out["short"] = {k: r[k] for k in ("text", "reasoning_chars", "ttft_s", "decode_tok_s", "completion_tokens")}

tools = [{"type": "function", "function": {"name": "read_file", "description": "Read a text file from the workspace",
          "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}}]
r = stream([{"role": "user", "content": "Open the file notes/todo.txt and tell me what is in it."}], 256, tools=tools)
out["tool"] = {k: r[k] for k in ("tool_calls", "text", "ttft_s", "completion_tokens")}

filler = " ".join("Section %d: the river delta report notes sediment levels, rainfall totals and crop yields for the season." % i
                  for i in range(380))
r = stream([{"role": "user", "content": filler + "\n\nIn three sentences, what kind of document is this?"}], 300)
out["prefill_7k"] = {k: r[k] for k in ("prompt_tokens", "ttft_s", "prefill_tok_s", "decode_tok_s", "completion_tokens")}
out["prefill_7k"]["text_head"] = r["text"][:200]

r = stream([{"role": "user", "content": "Write a Python function that parses an ISO 8601 date string without using datetime, with docstring and tests."}], 600)
out["decode_600"] = {k: r[k] for k in ("completion_tokens", "ttft_s", "decode_tok_s")}
print(json.dumps(out, indent=1))
