# Selection and budget trade-off

Every route starts the same 30-item core, followed by a shared extension up to 144 items, using the standard caps throughout. Only the core must fit 85% of every conservative budget. The table compares candidate cores; validation scores did not enter the size/cap decision.

| Items | Caps | Feasible splits | Held-out Spearman | Held-out Kendall τ-b | DeepSeek Maya min, typical / slow | Inkling min, typical / slow | All budgets fit |
|---:|---|---:|---:|---:|---:|---:|---|
| 24 | standard | 128/128 | 0.7392 | 0.6259 | 13.31 / 18.95 | 4.47 / 5.75 | yes |
| 24 | moderate | 128/128 | 0.7238 | 0.6109 | 13.39 / 19.03 | 3.75 / 4.85 | yes |
| 24 | short | 128/128 | 0.63 | 0.5278 | 13.66 / 19.31 | 3.06 / 3.98 | yes |
| 26 | standard | 128/128 | 0.772 | 0.6596 | 14.65 / 20.93 | 5.29 / 6.82 | yes |
| 26 | moderate | 128/128 | 0.7252 | 0.613 | 14.65 / 20.93 | 4.37 / 5.64 | yes |
| 26 | short | 128/128 | 0.6423 | 0.5401 | 14.69 / 20.91 | 3.47 / 4.51 | yes |
| 28 | standard | 128/128 | 0.7769 | 0.6622 | 15.66 / 22.50 | 5.38 / 6.95 | yes |
| 28 | moderate | 128/128 | 0.7317 | 0.6185 | 15.66 / 22.50 | 4.46 / 5.77 | yes |
| 28 | short | 128/128 | 0.6411 | 0.5384 | 15.99 / 22.78 | 3.64 / 4.74 | yes |
| 30 | standard | 128/128 | 0.7885 | 0.6747 | 17.45 / 24.70 | 5.53 / 7.13 | yes |
| 30 | moderate | 128/128 | 0.7514 | 0.6397 | 17.45 / 24.70 | 4.60 / 5.96 | yes |
| 30 | short | 128/128 | 0.651 | 0.5491 | 17.40 / 24.61 | 3.74 / 4.87 | yes |
| 32 | standard | 128/128 | 0.8072 | 0.6964 | 18.59 / 26.23 | 6.59 / 8.48 | no |
| 32 | moderate | 128/128 | 0.7585 | 0.6496 | 18.08 / 25.69 | 5.07 / 6.56 | no |
| 32 | short | 128/128 | 0.6664 | 0.5597 | 18.03 / 25.59 | 4.17 / 5.41 | no |
| 34 | standard | 128/128 | 0.8089 | 0.7016 | 19.97 / 28.40 | 6.84 / 8.82 | no |
| 34 | moderate | 128/128 | 0.7585 | 0.6456 | 19.99 / 28.32 | 5.31 / 6.88 | no |
| 34 | short | 128/128 | 0.655 | 0.5409 | 19.54 / 27.90 | 4.43 / 5.76 | no |
| 36 | standard | 128/128 | 0.815 | 0.7093 | 21.29 / 30.13 | 7.00 / 9.03 | no |
| 36 | moderate | 128/128 | 0.7651 | 0.6547 | 21.31 / 30.05 | 5.47 / 7.09 | no |
| 36 | short | 128/128 | 0.6591 | 0.5498 | 21.16 / 29.97 | 4.67 / 6.08 | no |
| 40 | standard | 128/128 | 0.8296 | 0.7227 | 23.19 / 32.96 | 7.81 / 10.07 | no |
| 40 | moderate | 128/128 | 0.7808 | 0.6687 | 23.72 / 33.43 | 6.34 / 8.21 | no |
| 40 | short | 128/128 | 0.6781 | 0.5708 | 23.19 / 32.83 | 5.34 / 6.94 | no |
| 48 | standard | 127/128 | 0.8543 | 0.7502 | 29.82 / 42.00 | 9.26 / 11.95 | no |
| 48 | moderate | 127/128 | 0.8054 | 0.6951 | 30.13 / 42.19 | 7.99 / 10.34 | no |
| 48 | short | 127/128 | 0.6906 | 0.5806 | 28.20 / 40.09 | 6.53 / 8.50 | no |
| 56 | standard | 120/128 | 0.8595 | 0.7547 | 38.44 / 52.95 | 10.90 / 14.08 | no |
| 56 | moderate | 121/128 | 0.826 | 0.7189 | 36.70 / 50.96 | 9.09 / 11.77 | no |
| 56 | short | 123/128 | 0.7118 | 0.601 | 35.29 / 49.48 | 7.55 / 9.83 | no |

## Coverage and selection

The pool has 300 IDs. Eligibility requires observations on every complete route, leaving 216 core IDs. The extra 84 were measured only on eight faster routes. This restriction allows paired scoring and timing on the slow routes. The retained items span MATH-500 and AIME. The archived BFCL pool contains multiple, parallel_multiple and irrelevance. It has no simple items.

Category target shares are 25% knowledge, 15% math, 14% code, 15% instruction, 14% reasoning and 17% tools. Knowledge retains the largest share from the full suite. The other shares keep broad category coverage under the time limit. Largest-remainder rounding gives the counts in the manifest. Order rotates through categories until each quota is exhausted.

On each training panel, exclude items with unanimous simulated outcomes. For each remaining item, compare the mean original core score of passers and failers, removing the item itself from those totals. The association term rewards alignment with the full-suite ordering. Middle difficulty, fewer truncated answers and shorter prompts and completions also improve priority. The cost term uses a training-only DeepSeek-family median when available and a training-panel median otherwise. It weights prompt and answer lengths by 35 and 7.2 tokens/s. Within each category the best-scoring items fill the quota, reserving one per available tool subtype and one each for AIME and MATH-500. IDs break ties.

## Held-out check

The validation panel has 13 complete routes. One Inkling snapshot represents the family. Qwen-27B engines stay together, as do the two DeepSeek deployments. Seed 20261125 samples 128 distinct training sets of half the route families (rounded down). For each candidate, the selector re-estimates priorities and picks fresh IDs using only those training grades and lengths. It scores the remaining routes on those IDs against each route’s original 216-item total. Full-route token estimates used to forecast the final budget do not enter fold priorities.

A fold can be infeasible if too few mixed-outcome items remain for a quota. The table reports successful folds. Average ranks handle ties in Spearman, and Kendall uses τ-b. Fifth percentiles are nearest-rank. A separated pair passes the full-suite two-sided exact McNemar test after Holm adjustment across all pairs of complete routes. Agreement counts ties as disagreement and pools only comparisons where both routes were held out. Overlapping folds are correlated. These statistics describe historical deployments and selection of this size/profile, not a blind evaluation of the final frozen IDs.

## Timing and censoring

Per request, time equals fixed overhead plus prompt tokens divided by prefill speed plus capped completion tokens divided by decode speed. Typical and slow scenarios share lengths and use their respective speed parameters. Measured route-specific token counts take precedence, with the retired RDNA3 Inkling and partial Hy4 SQ-64 as family proxies. On missing items the model multiplies the median completion length from the eight-route calibration panel by the route verbosity. Prompt lengths fall back to the panel median. Time excludes loading, warm-up and grading. Engine changes, response lengths, retries outside the harness and contention can change wall time. The deadline guard remains necessary.

A saved correct answer loses credit only when its completion length exceeds the new cap. Previously capped answers stay wrong. The archive cannot predict changes in decoding caused by changing engines or max_tokens. Missing quick-run items are excluded from attempted totals.

Cap sensitivity holds the frozen IDs fixed while changing only the caps. The standard, moderate and short cap profiles use the following values.

| Profile | Knowledge | Math | Code | Instruction | Reasoning | Tools | AIME |
|---|---:|---:|---:|---:|---:|---:|---:|
| standard | 2048 | 3072 | 3072 | 2048 | 2048 | 2048 | 4096 |
| moderate | 1536 | 2048 | 2048 | 1536 | 1536 | 1024 | 2048 |
| short | 1024 | 1536 | 1536 | 1024 | 1024 | 768 | 1536 |

| Historical route | Cap profile | Correct at original caps | Simulated correct | Simulated capped |
|---|---|---:|---:|---:|
| ripple-65b-vllm | standard | 77 | 77 | 53 |
| ripple-65b-vllm | moderate | 77 | 67 | 66 |
| ripple-65b-vllm | short | 77 | 57 | 76 |
| inkling-2-mini-q8 | standard | 92 | 92 | 36 |
| inkling-2-mini-q8 | moderate | 92 | 80 | 50 |
| inkling-2-mini-q8 | short | 92 | 65 | 66 |
| inkling-2-mini-q8@inkling-q8-rdna3 | standard | 87 | 87 | 41 |
| inkling-2-mini-q8@inkling-q8-rdna3 | moderate | 87 | 80 | 49 |
| inkling-2-mini-q8@inkling-q8-rdna3 | short | 87 | 70 | 59 |

The chosen configuration gave mean Spearman 0.7885 (5th percentile 0.4685) and mean Kendall τ-b 0.6747 (5th percentile 0.3504). Pair ordering agreed in 98.35% of 726 held-out comparisons. The full suite separated 20 distinct pairs.

## Nested checkpoints

The core above is unchanged. Each next ID is the highest-priority remaining ID in the category furthest below its target share at the next prefix length; exhausted categories are skipped and ties follow the fixed category order. The final length is the longest prefix any small route can fit at conservative speed in 15 minutes. The 84 incompletely observed extra IDs are never used.

| Category | Core | Whole list |
|---|---:|---:|
| knowledge | 8 | 38 |
| math | 5 | 31 |
| code | 4 | 13 |
| instruction | 4 | 21 |
| reasoning | 4 | 21 |
| tools | 5 | 20 |

The four non-AIME core math IDs are all prealgebra; category coverage does not imply broad math subdomain coverage. Cap sensitivity above uses the whole list. Below each family split reselects its own core and extension before scoring held-out routes. Agreement means matching direction, not replicating statistical significance.

| Prefix | Feasible folds | Spearman mean / p05 | Kendall τ-b mean / p05 | Separated-pair agreement | Comparisons |
|---:|---:|---:|---:|---:|---:|
| 30 | 128/128 | 0.7885 / 0.4685 | 0.6747 / 0.3504 | 0.9835 | 726 |
| 45 | 128/128 | 0.8448 / 0.6 | 0.736 / 0.4286 | 0.9972 | 726 |
| 60 | 128/128 | 0.8766 / 0.6429 | 0.7751 / 0.488 | 1 | 726 |
| 75 | 128/128 | 0.9069 / 0.7143 | 0.8154 / 0.5521 | 1 | 726 |
| 90 | 121/128 | 0.9224 / 0.7928 | 0.843 / 0.6831 | 1 | 672 |
| 105 | 94/128 | 0.9525 / 0.8729 | 0.8899 / 0.7333 | 1 | 501 |
| 120 | 24/128 | 0.966 / 0.9286 | 0.9092 / 0.7857 | 1 | 130 |
| 135 | 0/128 | None / None | None / None | None | 0 |
| 144 | 0/128 | None / None | None / None | None | 0 |

When no half-split can supply enough mixed-outcome IDs, its statistics are unavailable. As a separate sensitivity check for those checkpoints, hold out three whole families instead. This provides more selection data but fewer held-out routes; its statistics are not directly comparable to the half-splits.

| Prefix | Feasible folds | Spearman mean / p05 | Kendall τ-b mean / p05 | Separated-pair agreement | Comparisons |
|---:|---:|---:|---:|---:|---:|
| 135 | 63/128 | 0.9424 / 0.8 | 0.9042 / 0.6667 | 1 | 72 |
| 144 | 0/128 | None / None | None / None | None | 0 |

## Current-route time forecast

Minutes are core-only (`predicted_minutes`). Prefix counts use the entire route budget and stop before the first item that would exceed it. Neither scenario is a measured runtime or guarantee.

| Route | Budget min | Core typical min | Core conservative min | Typical prefix | Conservative prefix |
|---|---:|---:|---:|---:|---:|
| qwen3.8-27b-vllm | 15 | 1.94 | 2.50 | 137 | 123 |
| qwen3.8-27b-sglang-dflash2 | 15 | 1.48 | 2.15 | 144 | 135 |
| qwen3.8-flash-next-iq3_xxs | 15 | 2.45 | 3.73 | 134 | 106 |
| kolibri-1.1-iq4_xs | 15 | 1.24 | 1.29 | 144 | 144 |
| inkling-2-mini-sq-20-strata-2gpu | 15 | 5.53 | 7.13 | 73 | 58 |
| ripple-65b-vllm | 30 | 19.69 | 19.73 | 46 | 46 |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | 30 | 17.45 | 24.70 | 48 | 35 |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | 30 | 13.44 | 18.44 | 56 | 47 |
| glm-5.3-flash-maya | 30 | 5.00 | 9.92 | 117 | 71 |
| hy4-flash-sq-64-strata | 30 | 2.64 | 2.92 | 144 | 144 |
