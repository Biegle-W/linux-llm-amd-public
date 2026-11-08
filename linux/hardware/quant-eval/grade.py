"""Grade quant-suite results. usage: grade.py results_dir model[,model...]  -> prints table, writes graded.json"""
import json, re, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from suite import MATH, CODE, KNOW

THINK = re.compile(r"(?s)^\s*<think>.*?</think>")


def text(row):
    return THINK.sub("", row.get("content") or "").strip()


def norm(v):
    v = v.strip().strip("*").strip()
    v = re.sub(r"\\boxed\{(.*)\}", r"\1", v)
    v = re.sub(r"\\d?frac\{([^}]*)\}\{([^}]*)\}", r"\1/\2", v)
    v = v.replace("$", "").replace("\\", "").replace(",", "").replace("%", "").replace("text{", "").replace("}", "").replace("{", "")
    v = re.sub(r"\s*(hours?|sides|students|ways|committees|dollars|zeros)\b.*$", "", v, flags=re.I)
    return v.strip().rstrip(".").strip()


def grade_math(row, keys):
    m = re.findall(r"ANSWER:\s*(.+)", text(row), re.I)
    if not m:
        return False, "no ANSWER line"
    got = norm(m[-1])
    for k in keys:
        if got == k:
            return True, got
        try:
            if abs(float(got) - float(k)) < 1e-9:
                return True, got
        except ValueError:
            pass
    return False, got


def grade_code(row, tests):
    t = text(row)
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", t, re.S)
    code = max(blocks, key=len) if blocks else t
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "case.py"
        f.write_text(code + "\n\n" + tests + "\nprint('ALLPASS')\n")
        try:
            p = subprocess.run([sys.executable, "-I", str(f)], cwd=d, capture_output=True, text=True, timeout=15)
        except subprocess.TimeoutExpired:
            return False, "timeout"
    ok = p.returncode == 0 and "ALLPASS" in p.stdout
    return ok, "pass" if ok else (p.stderr.strip().splitlines() or ["fail"])[-1][:120]


def grade_format(i, row):
    t = text(row)
    if i == "f01":
        s = re.sub(r"^```(?:json)?\s*|\s*```$", "", t.strip())
        try:
            o = json.loads(s)
        except ValueError:
            return False, "not JSON"
        ok = (set(o) == {"name", "age", "tags"} and isinstance(o["name"], str) and type(o["age"]) is int
              and isinstance(o["tags"], list) and len(o["tags"]) == 3
              and all(isinstance(x, str) and x == x.lower() for x in o["tags"]) and not t.startswith("```"))
        return ok, s[:80]
    if i == "f02":
        lines = [l for l in t.splitlines() if l.strip()]
        return len(lines) == 3 and all(l.startswith("- ") for l in lines), f"{len(lines)} lines"
    want = {"f03": "ANANAB", "f04": "2,3,5,7,11", "f05": "muchas gracias", "f06": "apple banana cherry mango pear"}[i]
    return t == want, t[:60]


def call(row):
    tc = row.get("tool_calls") or []
    if len(tc) != 1:
        return None, {}
    f = tc[0]["function"]
    try:
        return f["name"], json.loads(f["arguments"]) if isinstance(f["arguments"], str) else f["arguments"]
    except ValueError:
        return f["name"], {}


def grade_tool(i, row):
    name, a = call(row)
    low = {k: str(v).lower() for k, v in a.items()}
    if i == "t01":
        ok = name == "get_weather" and "tokyo" in low.get("city", "") and low.get("unit") == "celsius"
    elif i == "t02":
        ok = (name == "search_flights" and re.search(r"boston|bos", low.get("origin", "")) is not None
              and re.search(r"denver|den", low.get("destination", "")) is not None and low.get("date") == "2026-12-03")
    elif i == "t03":
        e = low.get("expression", "")
        ok = name == "calculator" and "1234" in e and "5678" in e and re.search(r"[*×x]", e) is not None
    else:
        ok = name is None and "187.42" in text(row)
    return ok, f"{name} {a}" if name else text(row)[:60]


def grade(results):
    keys = {i: k for i, _, k in MATH}
    tests = {i: t for i, _, t in CODE}
    pats = {i: p for i, _, p in KNOW}
    out = {}
    for i, row in results.items():
        if row.get("error"):
            out[i] = (row["cat"], False, row["error"][:80]); continue
        cat = row["cat"]
        if cat == "math":
            ok, d = grade_math(row, keys[i])
        elif cat == "code":
            ok, d = grade_code(row, tests[i])
        elif cat == "know":
            t = text(row); ok, d = re.search(pats[i], t, re.I) is not None, t[:60]
        elif cat == "format":
            ok, d = grade_format(i, row)
        else:
            ok, d = grade_tool(i, row)
        out[i] = (cat, ok, d)
    return out


if __name__ == "__main__":
    rdir = Path(sys.argv[1]); models = sys.argv[2].split(",")
    allg = {}
    for m in models:
        allg[m] = grade(json.loads((rdir / f"{m}.json").read_text()))
    cats = ["math", "code", "know", "format", "tool"]
    print("| model | " + " | ".join(cats) + " | total |")
    for m, g in allg.items():
        per = {c: [v[1] for v in g.values() if v[0] == c] for c in cats}
        print(f"| {m} | " + " | ".join(f"{sum(per[c])}/{len(per[c])}" for c in cats) + f" | {sum(v[1] for v in g.values())}/{len(g)} |")
    ids = sorted({i for g in allg.values() for i in g})
    print("\nItems that differ or fail:")
    for i in ids:
        r = [allg[m].get(i, ("", None, "missing")) for m in models]
        if not all(x[1] for x in r):
            print(i, " || ".join(f"{'PASS' if x[1] else 'FAIL'}: {str(x[2])[:70]}" for x in r))
    (rdir / "graded.json").write_text(json.dumps(allg, indent=1, ensure_ascii=False))
