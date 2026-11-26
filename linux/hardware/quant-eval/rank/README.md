# Rank tier: quality under a time limit

Every route must answer the same first **30 items**. This is the core. After the core, the runner keeps going in the same frozen order, up to **144 items**, while the next request fits. Small routes get **15 minutes**; large routes get **30 minutes**. Use the core to compare all routes that finished it. Use extensions to compare routes that reached the same checkpoint. Do not rank routes by how far they got or by percentages on different items.

| Category | Source | Core | Full list (includes core) |
|---|---|---:|---:|
| Knowledge | MMLU-Pro | 8 | 38 |
| Math | MATH-500 and AIME | 5 | 31 |
| Code | BigCodeBench | 4 | 13 |
| Instruction following | IFEval | 4 | 21 |
| Reasoning | MuSR | 4 | 21 |
| Tools | BFCL, single turn | 5 | 20 |
| **Total** | | **30** | **144** |

Source: [frozen manifest](rank-items.json), fields `core_n`, `order`, `core_counts` and `counts`. The manifest refers to items by ID. Requests and grading material stay in the existing public suite.

## What should fit?

The two time columns are **minutes for the core alone**. The last two columns are **total items from the start**, using the whole budget. They are forecasts, not measurements, stopping rules or guarantees.

| Route | Class / budget (min) | Core typical | Core conservative | Items typical | Items conservative |
|---|---|---:|---:|---:|---:|
| `qwen3.8-27b-vllm` | small / 15 | 1.94 | 2.50 | 137 | 123 |
| `qwen3.8-27b-sglang-dflash2` | small / 15 | 1.48 | 2.15 | 144 | 135 |
| `qwen3.8-flash-next-iq3_xxs` | small / 15 | 2.45 | 3.73 | 134 | 106 |
| `kolibri-1.1-iq4_xs` | small / 15 | 1.24 | 1.29 | 144 | 144 |
| `inkling-2-mini-sq-20-strata-2gpu` | small / 15 | 5.53 | 7.13 | 73 | 58 |
| `ripple-65b-vllm` | large / 30 | 19.69 | 19.73 | 46 | 46 |
| `deepseek-v4.1-flash-1017-maya-unsloth-q1` | large / 30 | 17.45 | 24.70 | 48 | 35 |
| `deepseek-v4.1-flash-1017-strata-unsloth-q1` | large / 30 | 13.44 | 18.44 | 56 | 47 |
| `glm-5.3-flash-maya` | large / 30 | 5.00 | 9.92 | 117 | 71 |
| `hy4-flash-sq-64-strata` | large / 30 | 2.64 | 2.92 | 144 | 144 |

Source: [selection report, current-route time forecast](selection-report.md#current-route-time-forecast) and [speed model](speeds.md). Even in the conservative scenario, every core fits within 85% of its route budget. DeepSeek Maya leaves the least margin against that target. No such margin is required for the extension.

## Run one route, grade it, then compare routes

Run these commands **from `rank/`** with Python 3.14. Keep `../pub/` next to this directory. Use the original, validated `../pub/items.jsonl` and its adjacent `items.manifest.json`. Use a working Linux `bwrap` sandbox for grading code. See the [public harness instructions](../pub/README.md) if these prerequisites are missing. No benchmark download or reselection is needed for an ordinary run.

1. **Optional: reproduce the freeze offline.** This requires the original saved grade archive under `../data/`; live inference does not. Write to a separate directory and compare before using the shipped list.

   ```sh
   mkdir -p replay
   python3.14 rank_select.py --data ../data --pub ../pub --speeds speeds.json --out replay/rank-items.json --report replay/selection-report.md
   cmp replay/rank-items.json rank-items.json
   cmp replay/selection-report.md selection-report.md
   ```

2. **Check the sandbox, then run.** Use the matching class from the table and a fresh output directory per route. The example uses the public runner's default chat-completions endpoint. For another endpoint, append `--url "$CHAT_COMPLETIONS_URL"` with that variable set to the full request URL.

   ```sh
   ROUTE=qwen3.8-27b-vllm
   CLASS=small
   OUT="results/$ROUTE"
   python3.14 ../pub/check_sandbox.py --temp-root ../pub/.pub-sandbox &&
     python3.14 run_rank.py "$OUT" "$ROUTE" --class "$CLASS" --items ../pub/items.jsonl --rank-items rank-items.json --speeds speeds.json
   ```

   The clock starts after a successful warm-up. Loading, warm-up and grading do not use item time. Requests run one at a time, at temperature zero with thinking disabled. The runner adjusts its estimate to the observed pace. It stops before the next item if that estimate exceeds the remaining time. A client timeout cannot guarantee the backend has stopped generating; check or drain it before starting another run.

   Keep both `$OUT/$ROUTE.json` (responses) and `$OUT/run.json` (time and coverage). In `run.json`, `answered_prefix` counts consecutive attempted items. `core_complete` means the core was attempted; `complete` means the entire list was attempted. Exit **0** is normal once the core is covered, even if the extension stops between checkpoints. Exit **3** means the time guard left a core item unstarted. Exit **4** means a hold or failed warm-up. Inspect `stop_reason`; do not restart the clock to fill a missing suffix.

3. **Grade outside the clock.** Use the public grader unchanged. `--tier all` is the public pool, not the rank denominator. The scorer below selects only frozen rank IDs. If isolation fails or a grade is missing, fix grading before interpreting a ranking. Do not rerun inference to repair grading.

   ```sh
   python3.14 ../pub/grade_pub.py "$OUT" "$ROUTE" --items ../pub/items.jsonl --tier all --temp-root ../pub/.pub-sandbox
   python3.14 score_rank.py "$OUT/graded.json" --run "$OUT/run.json" --rank-items rank-items.json --output-prefix results/ranking
   ```

   For a fleet report, grade each route separately. Pass every `graded.json` together and repeat `--run` for its matching metadata. For example, after running the two Qwen 27B engines:

   ```sh
   A=results/qwen3.8-27b-vllm
   B=results/qwen3.8-27b-sglang-dflash2
   python3.14 score_rank.py "$A/graded.json" "$B/graded.json" --run "$A/run.json" --run "$B/run.json" --output-prefix results/ranking
   ```

Read `results/ranking.md` for the tables or `results/ranking.json` for the same comparisons in code. The core table includes only routes with every core item graded in its ranking; incomplete routes are listed separately. Each extension table requires at least three routes with the same fully graded prefix. The final pair table uses the longest checkpoint shared by each pair, even if nobody else reached it. A shared letter means the test did not detect a difference. It does not mean the routes are equal. See [DESIGN](DESIGN.md#how-to-read-the-rankings) before interpreting close scores.

## Verification and limits

```sh
python3.14 -m unittest
python3.14 score_rank.py --rescore ../data --output-prefix replay/historical
```

The first command runs offline tests for [selection](test_rank_select.py), [deadlines](test_run_rank.py) and [scoring](test_score_rank.py). The regeneration test needs the archive; without it that test can skip. With the archive, all 34 tests passed. The freeze and selection report reproduced byte for byte. Fake-clock tests covered stops before and after the core. Archive rescoring reproduced the selector counts for all 17 snapshots: 14 had all 144 grades, and three lacked a complete core. See `rescored_saved_runs` in the [manifest](rank-items.json); the second command writes the historical comparison, not a current leaderboard.

**Not verified here:** live route readiness, current answer lengths or quality, actual deadlines, backend cancellation, or sandbox operation on the deployment machine. No held-out selection fold supplied all 144 items. Current ranks and achieved prefixes require graded, timed runs. The [design and validation results](DESIGN.md) show what the shorter checkpoints can support.
