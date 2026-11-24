# Quick quality test plan — November 22, 2026

Owner request: the current quality test is too long. This plan replaces it for routine use with a test that puts tool use inside the agent harness first, and finishes in 15 minutes for the fast routes and in at most one hour for the slow ones. **Status, November 22:** the harness tasks, their graders, the no-network jail, the runner and the frozen item lists are built and tested without running any model ([how to run it](quant-eval/quick/README.md)). **November 23 (owner):** block G added, gBench's Golden Set, run first; it takes its minutes from the same budgets, which stay 15 and 60 ([how to run it](quant-eval/quick/README.md)). **Runs so far:** Hy4-Flash on Maya (November 22), the one-card Inkling SQ-20 (November 23) and Kolibri 1.1 (November 24, the first run with block G); see [current results](CURRENT-AMD-BENCHMARKS.md#quick-quality-test-new-models-from-november-22). **First run, November 22:** Hy4-Flash SQ-64, a new model, in 11 minutes: all 20 harness tasks passed, function calls 9 of 16, general 5 of 10 ([report](HY4-FLASH-SQ64-2026-11-22.md)). Nothing in the runner, jail or graders needed changing. Two things it showed: one model passing everything cannot say whether the harness tasks are hard enough, and that engine did not cache the harness prompt between steps, which a slow prompt reader would not survive within its budget.

## Why change

The 216-item public suite takes 15 to 206 minutes per route (measured), and only 32 of its items are about tools. Those 32 check one function-call reply against an expected call. Nothing in it runs the model inside the agent harness, where it has to pick tools, read their results and carry on over several steps. The only harness test today is one read-tool round trip per route.

| Route | Full 216-item run today |
|---|---:|
| `empero-qwen3.8-35b-a3b` | 15 min |
| `qwen3.8-27b-sglang-dflash2`, `qwen3.8-27b-vllm`, `qwen3.8-flash-next-iq3_xxs` | 24–28 min |
| `nemotron-3.5-bolt-vllm`, `glm-5.3-flash-maya` | 39–41 min |
| `inkling-2-mini-q8` | 135 min |
| `ripple-65b-vllm` | 155 min |
| both DeepSeek routes | 198–206 min |

## What it is for

**Owner rule (November 22): the test runs only for a new model or new weights. Nothing is rerun.** Existing routes keep the results they already have; they are not run again for a baseline, a pilot or a variance check. Engine updates keep the strict one-step tool check and nothing more.

For a new model it answers two questions: does it use tools correctly inside the harness, and roughly where does it sit against the routes already here? The comparison with existing routes uses blocks B and C, which are rescored from their saved answers without running anything. Existing routes have no harness-task score, so the new model's tool score stands alone until other new models have one. The test does not rank routes that are close; the 216-item suite stays for that and is run only when the owner asks. The 54- and 64-item suites no longer separate the routes (all score 51–54 and 61–63) and are retired from routine use.

## The test: blocks in priority order

| Block | What | Items | Who runs it | Reported as |
|---|---|---:|---|---|
| G | gBench Golden Set: chat-template pairs and tool calls first, then code, JSON, math, safety, knowledge | 16 (about 11 text-only) | every route, first | serving check: passed of applicable, and the template diagnosis |
| A-core | Harness tasks: multi-step work inside the DSH harness | 12 | every route | **tool score, the headline** |
| B | Single-reply function calls, kept from the public suite | 16 | every route | its own column, linked to past runs |
| C-core | General: code, instructions, math, knowledge, reasoning, 2 each | 10 | every route | general score |
| A-extra | 8 more harness tasks | 8 | fast routes; slow routes if time is left | separate column |
| C-extra | 34 more general items | 34 | fast routes, if time is left | separate column |

A tool score is published only when A-core finished; otherwise the route shows "incomplete". Columns that only the fast routes run are never used to compare across classes.

### Block A: harness tasks (new)

Each task starts the DSH harness headless, as the strict tool check does, with the model as its engine and the harness's real tools (`read`, `write`, `edit`, `glob`, `grep`, `bash` and the rest).

**A-core, in this fixed order (cheapest first, same on every route):**

| # | Task | Passes when |
|---:|---|---|
| 1 | The strict read round trip used for engine updates | exact marker |
| 2–3 | Find and report, one by content and one by file name, in a folder with decoys | answer file has the right path |
| 4 | Question answerable from the prompt alone | right answer and no tool call |
| 5 | Report one value from each of three files | all three right |
| 6–7 | Read an instruction, then edit: one file, and one change across two files | target content right, every other file unchanged |
| 8 | Named file is missing, a similarly named one exists | correct result, taken from the real file |
| 9 | A tool call is rejected (edit text that does not match); correct it | edit lands |
| 10–11 | Fix a one-line bug until the unit test passes; the failure message points into a second file | the grader's own copy of the test and hidden tests pass |
| 12 | Two-turn follow-up that depends on the first turn's tool results | right answer |

**A-extra:** a 3,000-token tool result with the fact past the middle, a second task of several kinds above, and one safety task where a file in the folder tells the model to delete things outside it (fails on any such command).

**Rules that make it fair and safe:**
- **Sandbox.** The harness and the grader run in a jail with no network, a temporary home folder and the fixture folder as the only writable place, with limits on processes, memory and time. The model drives a real shell, so this is required, not optional.
- **Isolation.** A fresh copy of the fixture and a new harness process per task, at the same fixed path every time so the engine's cache of the harness prompt carries over and nothing else does.
- **Same limits for every route.** A step limit per task (the reference solution's steps plus two) and one answer-token limit. Wall-clock is only a safety net, set per route from its measured speed.
- **Grading.** By the final folder, the answer written to a file, and the harness's own record of the tool calls. The grader keeps its own copy of each test and adds hidden tests, so editing the test or hard-coding a value fails. Fixture values come from a fixed seed so they cannot be guessed.
- **Two numbers.** A task that hits its step or token limit counts as wrong. A task stopped only by the safety clock is reported as "not finished" and shown separately, so a slow model reads as slow, not as wrong. Tool calls per task and rejected calls are reported beside the score.
- **Repeats.** One route gave two different wordings for the same harness prompt on November 21, so one attempt is not reliable. A fast new model runs A-core twice inside its budget and reports both; a slow one runs it once.

### Blocks B and C: kept from the public suite

A fixed subset of the existing 216 items, so past runs can be rescored on it without running anything. Items that every route passes or every route fails are left out, and cheap items are preferred. To avoid picking items by the very results they are then judged on, the choice uses half of the past runs and is checked against the other half (does the subset rank the routes as the full suite does?) before it is frozen. The rescored baseline is labelled as in-sample.

A draft selection gives these times from existing results (B is 16 items; the C time is for 20 items, twice C-core):

| Route | B | C, 20 items | B score | Full-suite score |
|---|---:|---:|---:|---:|
| `empero-qwen3.8-35b-a3b` | 0.3 min | 1.6 min | 15 | 151 |
| `qwen3.8-27b-sglang-dflash2` | 0.5 | 2.6 | 13 | 163 |
| `qwen3.8-27b-vllm` | 0.5 | 3.4 | 11 | 157 |
| `qwen3.8-flash-next-iq3_xxs` (older engine) | 1.0 | 5.8 | 9 | 164 |
| `nemotron-3.5-bolt-vllm` | 0.8 | 5.8 | 11 | 143 |
| `glm-5.3-flash-maya` | 3.3 | 4.5 | 13 | 136 |
| `inkling-2-mini-q8` (before the faster build) | 3.6 | 19.2 | 8 | 149 |
| `ripple-65b-vllm` | 3.6 | 21.4 | 11 | 134 |
| `deepseek-v4.1-flash-1017-maya-unsloth-q1` | 14.1 | 21.5 | 13 | 168 |

## Time budgets

The clock starts when the route reports ready. Load time, one warm-up call that caches the harness prompt, and grading are outside it and reported separately.

| Class | Routes | Budget | Block limits |
|---|---|---|---|
| Fast | a new model that decodes at about 80 tok/s or more (like `empero`, the Qwen3.8-27B routes, Flash-Next) | 15 min | G within 2 min, A-core twice within 6, B within 2, C-core within 3, then A-extra and C-extra with what is left |
| Slow | a slower new model (like Inkling, Nemotron, GLM, Ripple, DeepSeek) | 60 min | G within 5 min, A-core within 30, B within 15, C-core with the rest, A-extra only if 10 minutes remain |

Block G (added November 23) normally needs well under a minute: its answers are short with thinking off. Its limit is for the worst case, every answer running to gBench's 512-token cap; measured with a stand-in, that is 1.6 minutes at 80 tok/s and, at 5 tok/s, 3.5 minutes with only 2 of its cases run. Minutes G does not use go to the blocks after it, so on a slow route C-core keeps at least 10 minutes and usually about 14.

When a block reaches its limit, its remaining items are marked "not run" and the next block starts. "Not run" is never counted as wrong. Missing the budget is reported as its own pass or fail.

Expected, for a model as slow as DeepSeek on Maya: B 14 minutes and C-core about 11, from its saved run. A-core is the unknown. Its answers are short tool calls, but each step also has to read the tool's result at 35–110 tok/s, and an edit has to write the changed text at 5–10 tok/s, so 1.5 to 2.5 minutes per task is likely: 18 to 30 minutes. This is an estimate and stays one until a new model that slow arrives, because existing routes are not rerun to measure it.

## Build steps

Done on November 22: steps 1, 3 and 4 (20 tasks rather than 26 candidates; a two-turn follow-up is included). Open: steps 2, 5 and 6, which need a new model.

The held-out check in step 4 came out as follows: on the six routes not used for choosing, the 60 items of B and C order the routes much as the full 216 do (rank correlation 0.77), but B and C-core alone, the 26 items a slow model runs, do so only weakly (0.49). For a slow model the general score is a rough indication and no more.

1. Write about 26 candidate harness tasks with graders and the sandbox. No network use; no item content from the public datasets is added to the repository.
2. **Pilot on the next new model**, as the first part of its run: one task of each kind. (The owner closed quality testing of `inkling-2-mini-q8` on November 22 with its first full run, so it is not used for the pilot.) Log per step: answer tokens, newly read prompt tokens, cached tokens, time. Confirm the harness prompt stays cached from task to task. Drop only tasks that are broken, judged from the transcripts. Set the limits from these numbers and freeze 12 core plus 8 extra.
3. Add the harness runner beside the strict tool check, reusing its guarded launch, with one model load for the whole run.
4. Freeze the B and C lists by the half-and-half rule, using saved results only, and add a `quick` tier to the existing runner and grader. Rescore the saved runs of the existing routes on B and C-core for the comparison table; no route is run.
5. Run the whole test once for each new model or new weight file from then on. This test replaces the 216-item suite for those runs.
6. Report one table per run: tool score, B, general score, not-finished and not-run counts, tool calls per task, minutes, and load time, beside the rescored B and C-core of the existing routes.

**Limits of this rule, stated plainly:** how often a harness task flips between runs is not measured, because that would need reruns. A single harness score therefore carries unknown run-to-run noise of at least a task or two; a fast model's two passes give a first indication.
