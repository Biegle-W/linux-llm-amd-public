# What the rank tier measures

The primary result is a comparison on the same 30 items. It is meant to show large quality differences across tasks, not to order every nearby pair. The extension uses time that would otherwise go unused. It adds evidence only for routes that answer the same additional items. Speed affects who enters an extension table; it never earns correctness credit.

## Choosing the list

Start with the 300 public IDs. Use the 216 measured on every complete historical route. The other 84 were measured only on faster routes. On the full selection panel, 147 of the 216 have both passes and failures under standard caps. Unanimous items do not help order that panel. Apply this filter afresh within each training split, not once before validation.

For each remaining item, compare the passers’ and failers’ mean scores on the **rest** of the public core. Prefer items where passing goes with a stronger score elsewhere. Reward middle difficulty. Penalize truncated answers and long requests. Estimate that cost from training-only prompt and completion lengths. Use the DeepSeek family if present, otherwise the whole training panel. Sort within category; the item ID breaks ties. The exact weights are in `priority_lists` in [rank_select.py](rank_select.py).

The target mix is 25% knowledge, 15% math, 14% code, 15% instruction, 14% reasoning and 17% tools. Knowledge keeps the largest share from the public suite. The other shares leave room for all six skills. Round core quotas by largest remainder. Reserve both MATH-500 and AIME, and each available BFCL subtype: multiple, parallel_multiple and irrelevance. Rotate through categories until the core quotas are filled. Coverage is not exhaustive: the archive has no BFCL simple items, and the four non-AIME core math items are all prealgebra.

Choose the largest tested core that fits within 85% of **every** route’s conservative budget. At equal size choose the looser caps. Do not use held-out accuracy to choose the winner. The 30-item core fits with standard caps. At 32 items even the short-cap candidate put DeepSeek Maya at 25.59 minutes, above its 25.50-minute planning limit.

Keep that core intact. For each next position, take the highest-priority unused item in the available category furthest below its target share. Stop the list at the longest prefix any small route can fit in 15 minutes at conservative speed. That route is Kolibri; it sets the limit at 144, not 147. Category pools run out at different times: the last seven items are math. The final mix is **not** a fresh quota sample or a harder version of each category. [README](README.md) gives the actual counts at both ends.

Sources: [selector](rank_select.py), [selection report](selection-report.md#coverage-and-selection), and [frozen order and counts](rank-items.json). The cutoff, like Kolibri’s forecast, depends on estimated lengths for items absent from its short saved run.

## Why keep the public answer caps?

A lower limit can save time by cutting off a model before it gives the answer. Ripple and Inkling often reason even with thinking disabled. Keep the public caps throughout: 2,048 tokens for knowledge, instruction, reasoning and tools; 3,072 for MATH-500 and code; 4,096 for AIME.

To test other caps, keep the **same 144 IDs**. Treat a saved completion as truncated if its length is **greater than** the proposed cap. A previously capped answer stays wrong. Reaching the cap exactly is not by itself evidence of truncation. The table shows correct / capped, not accuracy at the route’s predicted stopping point.

| Historical route or proxy | Standard | Moderate | Short |
|---|---:|---:|---:|
| Ripple | 77 / 53 | 67 / 66 | 57 / 76 |
| Inkling Q8 | 92 / 36 | 80 / 50 | 65 / 66 |
| Inkling Q8, other saved engine | 87 / 41 | 80 / 49 | 70 / 59 |

The lower caps change the quality comparison, not just its duration. This simulation assumes the saved greedy completion would have the same beginning under the lower cap. It cannot recover what a truncated answer would have become or how new engines will behave. Source: [cap profiles and fixed-ID sensitivity](selection-report.md#timing-and-censoring).

## Predicting and enforcing time

For each route, estimate warm request seconds as:

`fixed overhead + prompt tokens / prefill rate + min(expected answer tokens, cap) / decode rate`.

Use that route’s lengths for that item when available, including failed or capped outputs with recorded lengths. Otherwise use the item’s panel-median prompt length and its panel-median answer length scaled by the route’s historical verbosity. Do not scale an observed route-specific length twice. Typical and conservative scenarios use the same lengths but different speeds and overheads. Sum over the core for minutes. For the prefix forecast, sum in frozen order until the next item exceeds the whole class budget.

The rates combine historical fits with current throughput checks. The fixed cost comes from residual time on short requests, not a direct time-to-first-token measurement. DeepSeek’s historical request times vary substantially around its fitted model. A conservative forecast has no assigned probability. It is not a worst case. The [calibration and route-specific evidence](speeds.md) and [parameters](speeds.json) document each input.

The [runner](run_rank.py) reuses the public HTTP client. After warm-up it measures elapsed time on a monotonic clock. It adjusts the typical estimate by the ratio of observed to predicted time on completed non-error requests, anchored by one modeled average request. It never skips ahead to a cheaper item. A started request that expires counts as an attempted error; an unstarted suffix does not count wrong. Checkpoints do not stop the runner. The live deadline limits the client, not necessarily backend compute after disconnect.

## Held-out validation by checkpoint

The target is the ordering by the **original 216-item score**, not a general intelligence score. The selection panel used 13 complete historical routes from 11 families. Use only one Inkling snapshot. Keep the two Qwen 27B engines together and the two DeepSeek deployments together. Seed 20261125 selects 128 distinct family splits. Each trains on five families. Rebuild priorities, the core and its extension using only the training families’ grades and lengths. Compare the held-out routes’ new prefix totals with their original public totals. Final-route timing forecasts do not supply fold priorities.

Spearman uses average ranks for ties; Kendall uses τ-b. `p05` is the fifth percentile of feasible folds, not a confidence bound. The last column gives direction agreement on held-out comparisons of pairs the original full test separated. There were 20 distinct separated pairs on that panel. A tied prefix score counts as disagreement. Repeated comparisons across overlapping folds are **not** independent observations.

| Items | Feasible folds | Spearman mean / p05 | Kendall τ-b mean / p05 | Direction agreement (comparisons) |
|---:|---:|---:|---:|---:|
| 30 | 128/128 | 0.7885 / 0.4685 | 0.6747 / 0.3504 | 0.9835 (726) |
| 45 | 128/128 | 0.8448 / 0.6000 | 0.7360 / 0.4286 | 0.9972 (726) |
| 60 | 128/128 | 0.8766 / 0.6429 | 0.7751 / 0.4880 | 1 (726) |
| 75 | 128/128 | 0.9069 / 0.7143 | 0.8154 / 0.5521 | 1 (726) |
| 90 | 121/128 | 0.9224 / 0.7928 | 0.8430 / 0.6831 | 1 (672) |
| 105 | 94/128 | 0.9525 / 0.8729 | 0.8899 / 0.7333 | 1 (501) |
| 120 | 24/128 | 0.9660 / 0.9286 | 0.9092 / 0.7857 | 1 (130) |
| 135 | 0/128 | — | — | — (0) |
| 144 | 0/128 | — | — | — (0) |

Fewer training panels have enough mixed-outcome items at longer prefixes. Do not read the higher means as gains measured on all the same folds. A separate check held out three families at a time, leaving more training data. At 135 items, 63/128 such folds worked: Spearman 0.9424 / 0.8000, Kendall 0.9042 / 0.6667, agreement 1 over 72 comparisons. At 144, none worked. **There is no held-out accuracy estimate for the full list.** The split results evaluate the selection procedure on historical deployments. They are not a blind test of the published IDs, present engines or the subset of routes fast enough to reach each checkpoint.

Sources: [checkpoint validation tables](selection-report.md#nested-checkpoints) and `prefix_validation` / `prefix_validation_hold_three_families_out` in [rank-items.json](rank-items.json).

## How to read the rankings

- **Core:** rank every route with a grade on every core item. Count one point per correct answer. Capped, malformed and started errors earn zero. Not-run items and ungraded attempts are both unscored, but reported separately. A missing grade breaks the scored prefix even if the runner attempted the item. Partial totals are diagnostics, not ranked percentages.
- **Extension:** at each frozen checkpoint, compare only routes with the whole prefix graded. Publish a ranking only if at least three qualify. Include the core items in that prefix. A higher percentage in a different table is not a win against a route absent from that table.
- **Pair:** for every core-eligible pair, compare the longest listed checkpoint both graded, even if only those two reached it. That can be the core. Do not combine these rows into a fleet ranking; pairs may have faced different items.

The report gives total and per-category correct/scored counts and whole-run minutes against budget. For each ranked total it gives a pointwise Wilson 95% interval. The items were selected, not drawn at random. The interval describes uncertainty approximately for this mix, not accuracy on all future tasks. Category counts in the core are too small for fine distinctions.

Use the **paired test**, not overlap of Wilson intervals, to read a difference. Exact two-sided McNemar uses the items on which only one route was correct. Holm adjusts across all eligible pairs within each ranking at 0.05. The longest-shared table gets its own Holm adjustment across all eligible pairs. There is no simultaneous error guarantee across tables. A shared letter means **no difference detected**; no shared letter means the adjusted test separated the pair. A route can share one letter with a stronger route and another with a weaker one. Letters are not equivalence classes.

**How coarse is the core?** In the historical rescore, GLM’s 16/30 gave a Wilson interval of 36.1%–69.8%, about 34 percentage points wide. DeepSeek Strata (28/30) separated from Flint (4/30). It did **not** separate from Ripple (17/30; Holm-adjusted p = 0.078125), or from DeepSeek Maya (27/30). The two Qwen 27B engines both scored 25/30. Of 91 historical core pairs, only ten separated; every one involved Flint. There is no fixed score gap that assures separation. The pattern of disagreements and the other pairs matter. Getting the direction right in a held-out fold is **not** the same as proving a difference in a run.

Source: [score_rank.py](score_rank.py) and the historical `core.routes` / `core.pairs` tables. Reproduce those tables with the `--rescore` command in [README](README.md#verification-and-limits). They use all available historical snapshots, not just the validation panel.

## Where evidence is missing

The archived score replay has 17 snapshots. Fourteen cover all 144 IDs because the old public runs covered them, **not** because those routes finished in time. The Kolibri and two Hy4 quick snapshots each cover only nine scattered core IDs. None can be ranked even on the core. The current Inkling SQ-20 has no saved full run; the two Q8 snapshots are older family proxies, not scores for SQ-20. Hy4’s current deployment also lacks a saved complete run. Kolibri and Hy4 timing estimates rely on 26-item quick samples. Flash-Next changed engines. Even reused route IDs are not evidence of unchanged behavior.

Sources: the [speed calibration](speeds.md#length-reference-and-audit-inputs), `rescored_saved_runs` in the [manifest](rank-items.json), and the historical replay. Live timed runs with a verified sandbox are still needed for current quality, prefix lengths and elapsed minutes. A missing core means the fleet comparison is missing a route; an extension table cannot repair that.
