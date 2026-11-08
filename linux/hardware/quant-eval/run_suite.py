import json, sys, time, urllib.request, urllib.error
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import importlib, os
requests = importlib.import_module(os.environ.get("SUITE", "suite")).requests
URL = "http://127.0.0.1:30100/v1/chat/completions"
out_dir = Path(sys.argv[1]); out_dir.mkdir(exist_ok=True)
only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
for model in sys.argv[2].split(","):
    path = out_dir / f"{model}.json"
    done = json.loads(path.read_text()) if path.exists() else {}
    for item, cat, body in requests():
        if item in done or (only and item not in only):
            continue
        body = dict(body, model=model, temperature=0, stream=False,
                    chat_template_kwargs={"enable_thinking": False, "thinking": False})
        t0 = time.time()
        try:
            req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
            r = json.load(urllib.request.urlopen(req, timeout=5400))
            m = r["choices"][0]["message"]
            row = {"cat": cat, "content": m.get("content"), "reasoning": m.get("reasoning_content") or m.get("reasoning"),
                   "tool_calls": m.get("tool_calls"), "finish": r["choices"][0].get("finish_reason"), "usage": r.get("usage")}
        except urllib.error.HTTPError as e:
            row = {"cat": cat, "error": f"HTTP {e.code}: {e.read()[:300]!r}"}
        except Exception as e:
            row = {"cat": cat, "error": f"{type(e).__name__}: {e}"}
        row["seconds"] = round(time.time() - t0, 2)
        done[item] = row
        path.write_text(json.dumps(done, indent=1))
        print(model, item, row["seconds"], (row.get("error") or (row.get("content") or "")[:60]).replace("\n", " "), flush=True)
