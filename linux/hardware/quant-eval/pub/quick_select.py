#!/usr/bin/env python3
"""Freeze the quick-test item lists (blocks B, C-core, C-extra) from saved public-suite results. No model is run.
Usage: quick_select.py <graded.json> [<graded.json> ...] --out quick-items.json
Rule: choose on half of the routes (every second route by full-suite score), keep only items that the selection
half does not answer uniformly, prefer middle difficulty, then the cheapest items on the slowest selection route;
then check on the other half that the subset orders the routes as the full suite does."""
import json, sys, statistics
args = sys.argv[1:]; out = args[args.index('--out') + 1]; files = [a for a in args[:args.index('--out')]]
R = {}
for f in files: R.update({k: v for k, v in json.load(open(f))['routes'].items() if isinstance(v, dict) and len(v) == 216})
routes = sorted(R, key=lambda r: -sum(v['status'] == 'correct' for v in R[r].values()))
sel, val = routes[0::2], routes[1::2]
items = list(R[routes[0]])
ok = lambda r, i: R[r][i]['status'] == 'correct'
slowest = max(sel, key=lambda r: sum(v['seconds'] or 0 for v in R[r].values()))
def pick(cat, k, subs=None, exclude=()):
    c = [i for i in items if R[routes[0]][i]['category'] == cat and i not in exclude and (subs is None or i.split(':')[0] in subs)]
    n = len(sel); score = {i: sum(ok(r, i) for r in sel) for i in c}
    c.sort(key=lambda i: (not (1 <= score[i] <= n - 1), abs(score[i] - n * 0.6), R[slowest][i]['seconds'] or 0, i))
    return c[:k]
B = pick('tools', 4, {'tools_multiple'}) + pick('tools', 8, {'tools_parallel_multiple'}) + pick('tools', 4, {'tools_irrelevance'})
Cc, Ce = [], []
for cat, k1, k2 in [('code', 2, 6), ('instruction', 2, 6), ('math', 2, 6), ('knowledge', 2, 10), ('reasoning', 2, 6)]:
    p = pick(cat, k1 + k2); Cc += p[:k1]; Ce += p[k1:]
def rho(xs, ys):
    rk = lambda v: [sorted(v).index(x) + (v.count(x) - 1) / 2 for x in v]
    a, b = rk(xs), rk(ys); ma, mb = statistics.mean(a), statistics.mean(b)
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** .5
    return round(sum((x - ma) * (y - mb) for x, y in zip(a, b)) / den, 2) if den else None
sc = lambda r, S: sum(ok(r, i) for i in S); mins = lambda r, S: round(sum(R[r][i]['seconds'] or 0 for i in S) / 60, 1)
table = {r: {'half': 'selection' if r in sel else 'check', 'full_216': sc(r, items), 'B_16': sc(r, B), 'C_core_10': sc(r, Cc), 'C_extra_34': sc(r, Ce),
             'minutes': {'full_216': mins(r, items), 'B': mins(r, B), 'C_core': mins(r, Cc), 'C_extra': mins(r, Ce)}} for r in routes}
allq = B + Cc + Ce
check = {'spearman_quick60_vs_full_on_check_half': rho([sc(r, allq) for r in val], [sc(r, items) for r in val]),
         'spearman_quick60_vs_full_on_selection_half_in_sample': rho([sc(r, allq) for r in sel], [sc(r, items) for r in sel]),
         'spearman_core26_vs_full_on_check_half': rho([sc(r, B + Cc) for r in val], [sc(r, items) for r in val])}
json.dump({'schema': 1, 'frozen': '2026-11-22', 'rule': __doc__.split('Rule: ')[1], 'selection_routes': sel, 'check_routes': val,
           'slowest_selection_route': slowest, 'blocks': {'B': B, 'C_core': Cc, 'C_extra': Ce}, 'check': check, 'rescored_saved_runs': table,
           'note': 'Scores of selection-half routes on these items are in-sample. No route was run to produce this file.'}, open(out, 'w'), indent=1)
print(json.dumps(check)); print(f"{'route':44s} half       full  B/16 Cc/10 Ce/34 | min B  Cc   Ce")
for r in routes:
    t = table[r]; m = t['minutes']; print(f"{r:44s} {t['half']:9s} {t['full_216']:5d} {t['B_16']:5d} {t['C_core_10']:5d} {t['C_extra_34']:5d} | {m['B']:5.1f} {m['C_core']:4.1f} {m['C_extra']:4.1f}")
