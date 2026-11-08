import json, re, sys, urllib.request

URL = "http://127.0.0.1:%s/v1/chat/completions" % sys.argv[1]
MODEL = sys.argv[2]
QS = [
    ("Is 391 a prime number? Answer only yes or no.", r"\bno\b"),
    ("What is 17 * 23? Answer with just the number.", r"\b391\b"),
    ("What is the capital of Australia? One word.", r"canberra"),
    ("What is the derivative of x^3? Answer briefly.", r"3\s*\*?\s*x\s*(\^|\*\*)\s*2|3x²"),
    ("In what year did World War II end? Just the year.", r"\b1945\b"),
    ("Reverse the word 'stressed'. Just the word.", r"desserts"),
    ("How many times does the letter r appear in 'strawberry'? Just the number.", r"\b3\b|three"),
    ("In Python, what does len([1, [2, 3]]) return? Just the value.", r"\b2\b"),
    ("What is 2 to the power of 10? Just the number.", r"\b1024\b"),
    ("Which is the largest planet in the solar system? One word.", r"jupiter"),
    ("Is 97 a prime number? Answer only yes or no.", r"\byes\b"),
    ("What is 144 divided by 12? Just the number.", r"\b12\b"),
]
score = 0
rows = []
for q, pat in QS:
    body = {"model": MODEL, "messages": [{"role": "user", "content": q}], "max_tokens": 1024, "temperature": 0}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    m = json.load(urllib.request.urlopen(req, timeout=600))["choices"][0]["message"]
    content = m.get("content") or ""
    final = re.sub(r"(?s)^\s*<think>.*?</think>", "", content).strip()
    ok = bool(re.search(pat, final, re.I))
    score += ok
    rows.append({"q": q, "answer": final[:80], "ok": ok})
print(json.dumps({"model": MODEL, "score": f"{score}/{len(QS)}", "rows": rows}, indent=1))
