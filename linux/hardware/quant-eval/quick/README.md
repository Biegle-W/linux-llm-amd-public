# Quick quality test

The routine quality test for **new models and new weights only** (owner rule, November 22, 2026: existing routes are not rerun). Plan and reasoning: [QUICK-QUALITY-PLAN-2026-11-22.md](../../QUICK-QUALITY-PLAN-2026-11-22.md).

| Block | What | Run with |
|---|---|---|
| G, first | gBench's Golden Set (pinned 0.5.0.post1): 16 fixed serving checks, about 11 on a text-only route; two chat-template pairs tell a broken template or tool parser from a weak model | `run_golden.py` |
| A | 12 core + 8 extra tasks inside the DSH harness, in a no-network jail | `run_quick.py` |
| B, C | 16 function-call items, 10 core + 34 extra general items from the public suite | `../pub/run_pub.py --only`, then `../pub/grade_pub.py` |

## Running it for a new route

The route must already load through the hub. Check first that no GPU hold is present and that nothing the owner is using is loaded. `fast` is for a model that decodes at about 80 tok/s or more.

```bash
# Once per server: gBench in its own venv (not committed).
uv venv --python 3.13 ../gbench/.venv && uv pip install --python ../gbench/.venv/bin/python gbench==0.5.0.post1 transformers

# Block G first: 2 minutes for a fast model, 5 for a slow one. --tokenizer is the model's Hugging Face tokenizer
# (its repo id, or a local folder that has tokenizer files and the chat template).
python3 run_golden.py <out>/golden <route> --class slow --tokenizer <tokenizer> --abort-file <hold file>

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
- `python3 -m unittest test_golden.py` and `./golden_smoke.sh <tokenizer folder>`: block G against a scripted stand-in (`golden_stub.py`, which answers each case from the installed gBench package; no case text is kept here). Measured on November 23 with the stand-in: a fast route 0.04 min, a slow one at 7 tok/s 0.3 min, and the worst cases, every answer running to gBench's 512-token cap, 1.6 of 2 min at 80 tok/s and 3.5 of 5 min at 5 tok/s (2 cases run, the rest "not run"). A GPU hold stops it before the next case. The code case runs in bubblewrap. First real run: Kolibri 1.1 on November 24, 14 of 14 in 0.2 minutes.
- **Block G, what to know.** gBench sends no thinking switch and caps every answer at 512 tokens, so `run_golden.py` adds the same thinking-off switch as the other blocks and raises gBench's 30 s request timeout to 60 s (fast) or 150 s (slow); a warm-up request loads the route before the clock starts. A case starts only if the slowest case so far still fits, so the block ends inside its limit, and the time it does not use goes to the next blocks. Tool cases need the route to return OpenAI `tool_calls`; a tool call written as text fails. gBench 0.5.0 marks a refusal written with a curly apostrophe as a failure (open fix, google-deepmind/gbench pull 13); the summary flags it. A template pair that fails only on its structured half points at the template or parser, not the model.
- **Runs so far.** Blocks A to C: Hy4-Flash on Strata and on Maya (November 22) and the one-card Inkling SQ-20 (November 23). All blocks, G included: Kolibri 1.1 (November 24, 3 minutes; G 14 of 14). Results: [current results](../../CURRENT-AMD-BENCHMARKS.md#quick-quality-test-new-models-from-november-22).

## Item lists

`../pub/quick_select.py` froze blocks B and C from saved public-suite results, choosing on half of the routes and checking on the other half. On the check half the 60 items order the routes much as the full 216 do (rank correlation 0.77); blocks B and C-core alone (26 items) do so only weakly (0.49). The quick test therefore shows large differences, not close rankings.
