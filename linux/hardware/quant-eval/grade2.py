"""Grade suite2 results. usage: grade2.py results_dir model[,model...]"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import suite2 as S
from grade import text, grade_code


def call(row):
    tc = row.get("tool_calls") or []
    if not tc:
        return None, {}
    f = tc[0]["function"]
    try:
        a = json.loads(f["arguments"]) if isinstance(f["arguments"], str) else f["arguments"]
    except ValueError:
        a = {}
    return f["name"], a


def grade_agent(i, row):
    n, a = call(row)
    low = {k: str(v).lower() for k, v in a.items()}
    if i == "a01":
        c = a.get("content", "")
        ok = n == "write_file" and low.get("path", "").endswith("calc.py") and re.search(r"return\s+a\s*\+\s*b", c) is not None and "def mul" in c
    elif i == "a02":
        ok = n == "get_weather" and "paris" in low.get("city", "")
    elif i == "a03":
        ok = n is None and "231.75" in text(row)
    elif i == "a04":
        ok = n == "book_hotel" and "lisbon" in low.get("city", "") and str(a.get("nights")) == "3"
    else:  # a05: must inspect before editing
        ok = n == "read_file" or (n == "search_docs" and "slug" in low.get("query", ""))
    return ok, f"{n} {json.dumps(a)[:90]}" if n else text(row)[:70]


def grade_format(i, row):
    t = text(row)
    kind, want = {x[0]: (x[2], x[3]) for x in S.FORMAT}[i]
    if kind == "json":
        try:
            return json.loads(t) == want, t[:60]
        except ValueError:
            return False, t[:60]
    if kind == "exact":
        return t == want, t[:60]
    rows = [l.strip() for l in t.splitlines() if l.strip()]
    ok = (len(rows) == 4 and all(r.startswith("|") and r.endswith("|") for r in rows)
          and re.search(r"\|\s*Ann\s*\|\s*30\s*\|", rows[2]) and re.search(r"\|\s*Bo\s*\|\s*25\s*\|", rows[3]))
    return bool(ok), f"{len(rows)} rows"


def grade(results):
    pat = {i: p for i, _, p in S.KNOW + S.REASON + S.LONG}
    tests = {i: t for i, _, t in S.CODE}
    out = {}
    for i, row in results.items():
        if row.get("error"):
            out[i] = (row["cat"], False, row["error"][:80]); continue
        c = row["cat"]
        if c in ("know", "reason", "long"):
            t = text(row); ok, d = re.search(pat[i], t, re.I | re.S) is not None, t[:60]
        elif c == "code":
            ok, d = grade_code(row, tests[i])
        elif c == "format":
            ok, d = grade_format(i, row)
        else:
            ok, d = grade_agent(i, row)
        out[i] = (c, ok, d)
    return out


if __name__ == "__main__":
    rdir = Path(sys.argv[1]); models = sys.argv[2].split(",")
    allg = {m: grade(json.loads((rdir / f"{m}.json").read_text())) for m in models}
    cats = ["know", "reason", "code", "format", "agent", "long"]
    print("| model | " + " | ".join(cats) + " | total |")
    for m, g in allg.items():
        per = {c: [v[1] for v in g.values() if v[0] == c] for c in cats}
        print(f"| {m} | " + " | ".join(f"{sum(per[c])}/{len(per[c])}" for c in cats) + f" | {sum(v[1] for v in g.values())}/{len(g)} |")
    print("\nItems that differ or fail:")
    for i in sorted({i for g in allg.values() for i in g}):
        r = [allg[m].get(i, ("", None, "missing")) for m in models]
        if not all(x[1] for x in r):
            print(i, " || ".join(f"{'PASS' if x[1] else 'FAIL'}: {str(x[2])[:70]}" for x in r))
    (rdir / "graded.json").write_text(json.dumps(allg, indent=1, ensure_ascii=False))
