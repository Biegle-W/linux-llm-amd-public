# Quick quality test

The routine quality test for **new models and new weights only** (owner rule, November 22, 2026: existing routes are not rerun). Plan and reasoning: [QUICK-QUALITY-PLAN-2026-11-22.md](../../QUICK-QUALITY-PLAN-2026-11-22.md).

| Block | What | Run with |
|---|---|---|
| A | 12 core + 8 extra tasks inside the DSH harness, in a no-network jail | `run_quick.py` |
| B, C | 16 function-call items, 10 core + 34 extra general items from the public suite | `../pub/run_pub.py --only`, then `../pub/grade_pub.py` |

## Running it for a new route

The route must already load through the hub. Check first that no GPU hold is present and that nothing the owner is using is loaded. `fast` is for a model that decodes at about 80 tok/s or more.

```bash
# Block A: 6 minutes for a fast model (core tasks twice), 30 for a slow one.
python3 run_quick.py <out>/harness <route> --class slow --context <route context> --abort-file <hold file>

# Blocks B and C-core (every model), then C-extra (fast models, if time is left).
IDS=$(python3 -c "import json;b=json.load(open('../pub/quick-items.json'))['blocks'];print(','.join(b['B']+b['C_core']))")
python3 ../pub/run_pub.py <out>/items <route> --url http://127.0.0.1:30100/v1/chat/completions --tier core --only "$IDS" --budget-hours 0.4 --stop-new-hours 0.35
python3 ../pub/grade_pub.py <out>/items <route> --items <items.jsonl> --tier core
```

`run_quick.py` writes `rows.json` (one row per task: pass, steps, tool calls, rejected calls, tokens, seconds) and `summary.json`. The tool score is the number of core tasks passed in the first pass, out of 12, and reads `incomplete` if the block ran out of time. Compare blocks B and C-core with the saved scores of the existing routes in `../pub/quick-items.json` (`rescored_saved_runs`); those were rescored from saved answers, not run.

## What is and is not verified

- `python3 -m unittest test_quick.py`: every grader passes its reference solution and fails an untouched folder, a decoy answer, an edit to the wrong file, an edited test and a hard-coded value.
- `./smoke.sh`: the runner, the jail and the harness work end to end against a scripted stand-in (`stub_model.py`); the jail has no network and a throwaway home.
- **Not yet run against any model.** The first new model is also the pilot: read its transcripts, drop tasks that turn out broken, and set the time limits from its measured steps before trusting the score.

## Item lists

`../pub/quick_select.py` froze blocks B and C from saved public-suite results, choosing on half of the routes and checking on the other half. On the check half the 60 items order the routes much as the full 216 do (rank correlation 0.77); blocks B and C-core alone (26 items) do so only weakly (0.49). The quick test therefore shows large differences, not close rankings.
