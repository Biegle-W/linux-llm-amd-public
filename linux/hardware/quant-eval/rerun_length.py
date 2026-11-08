"""Re-run items that hit max_tokens with a larger cap (greedy: same as a larger cap from the start)."""
import json, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from suite import requests
URL = "http://127.0.0.1:30100/v1/chat/completions"
CAP = 2048
bodies = {i: b for i, _, b in requests()}
for model in sys.argv[2].split(","):
    path = Path(sys.argv[1]) / f"{model}.json"; done = json.loads(path.read_text())
    for i, row in done.items():
        if row.get("finish") != "length" or row.get("rerun_cap"):
            continue
        body = dict(bodies[i], model=model, temperature=0, stream=False, max_tokens=CAP,
                    chat_template_kwargs={"enable_thinking": False, "thinking": False})
        t0 = time.time()
        r = json.load(urllib.request.urlopen(urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=5400))
        m = r["choices"][0]["message"]
        row.update(content=m.get("content"), tool_calls=m.get("tool_calls"), finish=r["choices"][0].get("finish_reason"),
                   usage=r.get("usage"), seconds=round(time.time() - t0, 2), rerun_cap=CAP)
        path.write_text(json.dumps(done, indent=1))
        print(model, i, row["finish"], row["usage"]["completion_tokens"], flush=True)
