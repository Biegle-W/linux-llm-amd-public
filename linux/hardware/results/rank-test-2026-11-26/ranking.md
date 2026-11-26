# Frozen rank-tier results

Supplied graded runs. Without run.json, coverage is inferred from grades; timing is unknown.

The core compares routes with a fully graded core. GPU holds exclude a run from every ranking. Extensions require at least three routes with a fully graded prefix. Capped, malformed and started errors are wrong; not-run and ungraded are not.

Wilson intervals are pointwise approximations for a fixed item mix. Each ranking and the longest-shared table uses its own exact two-sided McNemar/Holm family at α=0.05. No simultaneous guarantee across tables. Shared letters mean no detected difference, not equivalence. Minutes always refer to the whole run.

## Core ranking: first 30 items

### Complete routes (score order)

| Route | Group | Complete | Correct/scored | Scored/frozen | Score | Wilson 95% | Capped | Malformed | Not run | Ungraded | Used/budget (min) |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| qwen3.8-27b-sglang-dflash2 | A | yes | 26/30 | 30/30 | 86.7% | 70.3%–94.7% | 0 | 0 | 0 | 0 | 14.84/15 |
| qwen3.8-27b-vllm | A | yes | 25/30 | 30/30 | 83.3% | 66.4%–92.7% | 0 | 0 | 0 | 0 | 14.97/15 |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | A | yes | 24/30 | 30/30 | 80.0% | 62.7%–90.5% | 0 | 0 | 0 | 0 | 30.00/30 |
| qwen3.8-flash-next-iq3_xxs | A | yes | 24/30 | 30/30 | 80.0% | 62.7%–90.5% | 0 | 0 | 0 | 0 | 14.77/15 |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | A | yes | 23/30 | 30/30 | 76.7% | 59.1%–88.2% | 0 | 1 | 0 | 0 | 30.00/30 |
| kolibri-1.1-iq4_xs | A | yes | 23/30 | 30/30 | 76.7% | 59.1%–88.2% | 0 | 0 | 0 | 0 | 12.99/15 |
| ripple-65b-vllm | A | yes | 21/30 | 30/30 | 70.0% | 52.1%–83.3% | 5 | 0 | 0 | 0 | 29.41/30 |
| hy4-flash-sq-64-strata | A | yes | 18/30 | 30/30 | 60.0% | 42.3%–75.4% | 0 | 1 | 0 | 0 | 16.43/30 |
| glm-5.3-flash-maya | A | yes | 16/30 | 30/30 | 53.3% | 36.1%–69.8% | 0 | 0 | 0 | 0 | 30.00/30 |
| inkling-2-mini-sq-20-strata-2gpu | A | yes | 16/30 | 30/30 | 53.3% | 36.1%–69.8% | 0 | 4 | 0 | 0 | 13.94/15 |

### Incomplete routes (unranked)

None.

### Per category (correct/scored; frozen N in header)

| Route | code (N=4) | instruction (N=4) | knowledge (N=8) | math (N=5) | reasoning (N=4) | tools (N=5) |
|---|---:|---:|---:|---:|---:|---:|
| qwen3.8-27b-sglang-dflash2 | 3/4 | 4/4 | 8/8 | 5/5 | 3/4 | 3/5 |
| qwen3.8-27b-vllm | 2/4 | 3/4 | 8/8 | 5/5 | 3/4 | 4/5 |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | 4/4 | 3/4 | 8/8 | 5/5 | 1/4 | 3/5 |
| qwen3.8-flash-next-iq3_xxs | 3/4 | 2/4 | 8/8 | 5/5 | 3/4 | 3/5 |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | 4/4 | 3/4 | 8/8 | 5/5 | 0/4 | 3/5 |
| kolibri-1.1-iq4_xs | 4/4 | 2/4 | 8/8 | 5/5 | 1/4 | 3/5 |
| ripple-65b-vllm | 1/4 | 3/4 | 8/8 | 5/5 | 2/4 | 2/5 |
| hy4-flash-sq-64-strata | 1/4 | 4/4 | 7/8 | 3/5 | 1/4 | 2/5 |
| glm-5.3-flash-maya | 3/4 | 1/4 | 4/8 | 3/5 | 1/4 | 4/5 |
| inkling-2-mini-sq-20-strata-2gpu | 2/4 | 2/4 | 7/8 | 3/5 | 0/4 | 2/5 |

### Exact paired McNemar tests (Holm family: 45)

| A | B | Prefix N | A correct | B correct | A only | B only | Exact p | Holm p | Separated |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| qwen3.8-27b-sglang-dflash2 | qwen3.8-27b-vllm | 30 | 26 | 25 | 2 | 1 | 1 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | deepseek-v4.1-flash-1017-maya-unsloth-q1 | 30 | 26 | 24 | 4 | 2 | 0.6875 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | qwen3.8-flash-next-iq3_xxs | 30 | 26 | 24 | 4 | 2 | 0.6875 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | deepseek-v4.1-flash-1017-strata-unsloth-q1 | 30 | 26 | 23 | 5 | 2 | 0.45312 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | kolibri-1.1-iq4_xs | 30 | 26 | 23 | 6 | 3 | 0.50781 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | ripple-65b-vllm | 30 | 26 | 21 | 5 | 0 | 0.0625 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | hy4-flash-sq-64-strata | 30 | 26 | 18 | 9 | 1 | 0.021484 | 0.90234 | no |
| qwen3.8-27b-sglang-dflash2 | glm-5.3-flash-maya | 30 | 26 | 16 | 11 | 1 | 0.0063477 | 0.28564 | no |
| qwen3.8-27b-sglang-dflash2 | inkling-2-mini-sq-20-strata-2gpu | 30 | 26 | 16 | 11 | 1 | 0.0063477 | 0.28564 | no |
| qwen3.8-27b-vllm | deepseek-v4.1-flash-1017-maya-unsloth-q1 | 30 | 25 | 24 | 3 | 2 | 1 | 1 | no |
| qwen3.8-27b-vllm | qwen3.8-flash-next-iq3_xxs | 30 | 25 | 24 | 3 | 2 | 1 | 1 | no |
| qwen3.8-27b-vllm | deepseek-v4.1-flash-1017-strata-unsloth-q1 | 30 | 25 | 23 | 5 | 3 | 0.72656 | 1 | no |
| qwen3.8-27b-vllm | kolibri-1.1-iq4_xs | 30 | 25 | 23 | 5 | 3 | 0.72656 | 1 | no |
| qwen3.8-27b-vllm | ripple-65b-vllm | 30 | 25 | 21 | 5 | 1 | 0.21875 | 1 | no |
| qwen3.8-27b-vllm | hy4-flash-sq-64-strata | 30 | 25 | 18 | 9 | 2 | 0.06543 | 1 | no |
| qwen3.8-27b-vllm | glm-5.3-flash-maya | 30 | 25 | 16 | 10 | 1 | 0.011719 | 0.50391 | no |
| qwen3.8-27b-vllm | inkling-2-mini-sq-20-strata-2gpu | 30 | 25 | 16 | 11 | 2 | 0.022461 | 0.90234 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | qwen3.8-flash-next-iq3_xxs | 30 | 24 | 24 | 2 | 2 | 1 | 1 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | deepseek-v4.1-flash-1017-strata-unsloth-q1 | 30 | 24 | 23 | 2 | 1 | 1 | 1 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | kolibri-1.1-iq4_xs | 30 | 24 | 23 | 2 | 1 | 1 | 1 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | ripple-65b-vllm | 30 | 24 | 21 | 5 | 2 | 0.45312 | 1 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | hy4-flash-sq-64-strata | 30 | 24 | 18 | 7 | 1 | 0.070312 | 1 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | glm-5.3-flash-maya | 30 | 24 | 16 | 9 | 1 | 0.021484 | 0.90234 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | inkling-2-mini-sq-20-strata-2gpu | 30 | 24 | 16 | 9 | 1 | 0.021484 | 0.90234 | no |
| qwen3.8-flash-next-iq3_xxs | deepseek-v4.1-flash-1017-strata-unsloth-q1 | 30 | 24 | 23 | 4 | 3 | 1 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | kolibri-1.1-iq4_xs | 30 | 24 | 23 | 4 | 3 | 1 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | ripple-65b-vllm | 30 | 24 | 21 | 5 | 2 | 0.45312 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | hy4-flash-sq-64-strata | 30 | 24 | 18 | 8 | 2 | 0.10938 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | glm-5.3-flash-maya | 30 | 24 | 16 | 11 | 3 | 0.057373 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | inkling-2-mini-sq-20-strata-2gpu | 30 | 24 | 16 | 9 | 1 | 0.021484 | 0.90234 | no |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | kolibri-1.1-iq4_xs | 30 | 23 | 23 | 2 | 2 | 1 | 1 | no |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | ripple-65b-vllm | 30 | 23 | 21 | 5 | 3 | 0.72656 | 1 | no |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | hy4-flash-sq-64-strata | 30 | 23 | 18 | 7 | 2 | 0.17969 | 1 | no |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | glm-5.3-flash-maya | 30 | 23 | 16 | 9 | 2 | 0.06543 | 1 | no |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | inkling-2-mini-sq-20-strata-2gpu | 30 | 23 | 16 | 8 | 1 | 0.039062 | 1 | no |
| kolibri-1.1-iq4_xs | ripple-65b-vllm | 30 | 23 | 21 | 6 | 4 | 0.75391 | 1 | no |
| kolibri-1.1-iq4_xs | hy4-flash-sq-64-strata | 30 | 23 | 18 | 7 | 2 | 0.17969 | 1 | no |
| kolibri-1.1-iq4_xs | glm-5.3-flash-maya | 30 | 23 | 16 | 9 | 2 | 0.06543 | 1 | no |
| kolibri-1.1-iq4_xs | inkling-2-mini-sq-20-strata-2gpu | 30 | 23 | 16 | 9 | 2 | 0.06543 | 1 | no |
| ripple-65b-vllm | hy4-flash-sq-64-strata | 30 | 21 | 18 | 6 | 3 | 0.50781 | 1 | no |
| ripple-65b-vllm | glm-5.3-flash-maya | 30 | 21 | 16 | 9 | 4 | 0.26685 | 1 | no |
| ripple-65b-vllm | inkling-2-mini-sq-20-strata-2gpu | 30 | 21 | 16 | 7 | 2 | 0.17969 | 1 | no |
| hy4-flash-sq-64-strata | glm-5.3-flash-maya | 30 | 18 | 16 | 8 | 6 | 0.79053 | 1 | no |
| hy4-flash-sq-64-strata | inkling-2-mini-sq-20-strata-2gpu | 30 | 18 | 16 | 5 | 3 | 0.72656 | 1 | no |
| glm-5.3-flash-maya | inkling-2-mini-sq-20-strata-2gpu | 30 | 16 | 16 | 6 | 6 | 1 | 1 | no |

## Extended ranking: first 45 items

### Complete routes (score order)

| Route | Group | Complete | Correct/scored | Scored/frozen | Score | Wilson 95% | Capped | Malformed | Not run | Ungraded | Used/budget (min) |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| qwen3.8-flash-next-iq3_xxs | A B | yes | 37/45 | 45/45 | 82.2% | 68.7%–90.7% | 0 | 0 | 0 | 0 | 14.77/15 |
| qwen3.8-27b-sglang-dflash2 | A | yes | 36/45 | 45/45 | 80.0% | 66.2%–89.1% | 2 | 0 | 0 | 0 | 14.84/15 |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | A C | yes | 35/45 | 45/45 | 77.8% | 63.7%–87.5% | 0 | 0 | 0 | 0 | 30.00/30 |
| kolibri-1.1-iq4_xs | A B C D | yes | 34/45 | 45/45 | 75.6% | 61.3%–85.8% | 0 | 0 | 0 | 0 | 12.99/15 |
| qwen3.8-27b-vllm | A B C D | yes | 34/45 | 45/45 | 75.6% | 61.3%–85.8% | 2 | 1 | 0 | 0 | 14.97/15 |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | A B C D | yes | 33/45 | 45/45 | 73.3% | 59.0%–84.0% | 0 | 1 | 0 | 0 | 30.00/30 |
| ripple-65b-vllm | A B C D | yes | 29/45 | 45/45 | 64.4% | 49.8%–76.8% | 9 | 0 | 0 | 0 | 29.41/30 |
| hy4-flash-sq-64-strata | A B C D | yes | 28/45 | 45/45 | 62.2% | 47.6%–74.9% | 0 | 1 | 0 | 0 | 16.43/30 |
| inkling-2-mini-sq-20-strata-2gpu | C D | yes | 23/45 | 45/45 | 51.1% | 37.0%–65.0% | 1 | 5 | 0 | 0 | 13.94/15 |
| glm-5.3-flash-maya | B D | yes | 22/45 | 45/45 | 48.9% | 35.0%–63.0% | 0 | 0 | 0 | 0 | 30.00/30 |

### Incomplete routes (unranked)

None.

### Per category (correct/scored; frozen N in header)

| Route | code (N=6) | instruction (N=7) | knowledge (N=11) | math (N=7) | reasoning (N=6) | tools (N=8) |
|---|---:|---:|---:|---:|---:|---:|
| qwen3.8-flash-next-iq3_xxs | 4/6 | 5/7 | 11/11 | 7/7 | 5/6 | 5/8 |
| qwen3.8-27b-sglang-dflash2 | 4/6 | 7/7 | 10/11 | 7/7 | 3/6 | 5/8 |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | 5/6 | 6/7 | 11/11 | 7/7 | 1/6 | 5/8 |
| kolibri-1.1-iq4_xs | 5/6 | 4/7 | 11/11 | 7/7 | 1/6 | 6/8 |
| qwen3.8-27b-vllm | 3/6 | 6/7 | 10/11 | 7/7 | 3/6 | 5/8 |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | 5/6 | 5/7 | 11/11 | 7/7 | 0/6 | 5/8 |
| ripple-65b-vllm | 1/6 | 6/7 | 9/11 | 7/7 | 2/6 | 4/8 |
| hy4-flash-sq-64-strata | 2/6 | 7/7 | 8/11 | 5/7 | 1/6 | 5/8 |
| inkling-2-mini-sq-20-strata-2gpu | 3/6 | 3/7 | 9/11 | 4/7 | 0/6 | 4/8 |
| glm-5.3-flash-maya | 4/6 | 4/7 | 5/11 | 3/7 | 1/6 | 5/8 |

### Exact paired McNemar tests (Holm family: 45)

| A | B | Prefix N | A correct | B correct | A only | B only | Exact p | Holm p | Separated |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| qwen3.8-flash-next-iq3_xxs | qwen3.8-27b-sglang-dflash2 | 45 | 37 | 36 | 5 | 4 | 1 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | deepseek-v4.1-flash-1017-maya-unsloth-q1 | 45 | 37 | 35 | 4 | 2 | 0.6875 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | kolibri-1.1-iq4_xs | 45 | 37 | 34 | 7 | 4 | 0.54883 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | qwen3.8-27b-vllm | 45 | 37 | 34 | 6 | 3 | 0.50781 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | deepseek-v4.1-flash-1017-strata-unsloth-q1 | 45 | 37 | 33 | 7 | 3 | 0.34375 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | ripple-65b-vllm | 45 | 37 | 29 | 10 | 2 | 0.038574 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | hy4-flash-sq-64-strata | 45 | 37 | 28 | 12 | 3 | 0.035156 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | inkling-2-mini-sq-20-strata-2gpu | 45 | 37 | 23 | 15 | 1 | 0.0005188 | 0.023346 | yes |
| qwen3.8-flash-next-iq3_xxs | glm-5.3-flash-maya | 45 | 37 | 22 | 18 | 3 | 0.0014896 | 0.061075 | no |
| qwen3.8-27b-sglang-dflash2 | deepseek-v4.1-flash-1017-maya-unsloth-q1 | 45 | 36 | 35 | 4 | 3 | 1 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | kolibri-1.1-iq4_xs | 45 | 36 | 34 | 7 | 5 | 0.77441 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | qwen3.8-27b-vllm | 45 | 36 | 34 | 3 | 1 | 0.625 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | deepseek-v4.1-flash-1017-strata-unsloth-q1 | 45 | 36 | 33 | 6 | 3 | 0.50781 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | ripple-65b-vllm | 45 | 36 | 29 | 7 | 0 | 0.015625 | 0.51563 | no |
| qwen3.8-27b-sglang-dflash2 | hy4-flash-sq-64-strata | 45 | 36 | 28 | 10 | 2 | 0.038574 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | inkling-2-mini-sq-20-strata-2gpu | 45 | 36 | 23 | 14 | 1 | 0.00097656 | 0.041992 | yes |
| qwen3.8-27b-sglang-dflash2 | glm-5.3-flash-maya | 45 | 36 | 22 | 15 | 1 | 0.0005188 | 0.023346 | yes |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | kolibri-1.1-iq4_xs | 45 | 35 | 34 | 3 | 2 | 1 | 1 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | qwen3.8-27b-vllm | 45 | 35 | 34 | 4 | 3 | 1 | 1 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | deepseek-v4.1-flash-1017-strata-unsloth-q1 | 45 | 35 | 33 | 3 | 1 | 0.625 | 1 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | ripple-65b-vllm | 45 | 35 | 29 | 8 | 2 | 0.10938 | 1 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | hy4-flash-sq-64-strata | 45 | 35 | 28 | 9 | 2 | 0.06543 | 1 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | inkling-2-mini-sq-20-strata-2gpu | 45 | 35 | 23 | 13 | 1 | 0.0018311 | 0.073242 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | glm-5.3-flash-maya | 45 | 35 | 22 | 14 | 1 | 0.00097656 | 0.041992 | yes |
| kolibri-1.1-iq4_xs | qwen3.8-27b-vllm | 45 | 34 | 34 | 6 | 6 | 1 | 1 | no |
| kolibri-1.1-iq4_xs | deepseek-v4.1-flash-1017-strata-unsloth-q1 | 45 | 34 | 33 | 3 | 2 | 1 | 1 | no |
| kolibri-1.1-iq4_xs | ripple-65b-vllm | 45 | 34 | 29 | 10 | 5 | 0.30176 | 1 | no |
| kolibri-1.1-iq4_xs | hy4-flash-sq-64-strata | 45 | 34 | 28 | 9 | 3 | 0.146 | 1 | no |
| kolibri-1.1-iq4_xs | inkling-2-mini-sq-20-strata-2gpu | 45 | 34 | 23 | 14 | 3 | 0.012726 | 0.47086 | no |
| kolibri-1.1-iq4_xs | glm-5.3-flash-maya | 45 | 34 | 22 | 15 | 3 | 0.0075378 | 0.28644 | no |
| qwen3.8-27b-vllm | deepseek-v4.1-flash-1017-strata-unsloth-q1 | 45 | 34 | 33 | 6 | 5 | 1 | 1 | no |
| qwen3.8-27b-vllm | ripple-65b-vllm | 45 | 34 | 29 | 7 | 2 | 0.17969 | 1 | no |
| qwen3.8-27b-vllm | hy4-flash-sq-64-strata | 45 | 34 | 28 | 10 | 4 | 0.17957 | 1 | no |
| qwen3.8-27b-vllm | inkling-2-mini-sq-20-strata-2gpu | 45 | 34 | 23 | 14 | 3 | 0.012726 | 0.47086 | no |
| qwen3.8-27b-vllm | glm-5.3-flash-maya | 45 | 34 | 22 | 13 | 1 | 0.0018311 | 0.073242 | no |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | ripple-65b-vllm | 45 | 33 | 29 | 8 | 4 | 0.3877 | 1 | no |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | hy4-flash-sq-64-strata | 45 | 33 | 28 | 9 | 4 | 0.26685 | 1 | no |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | inkling-2-mini-sq-20-strata-2gpu | 45 | 33 | 23 | 12 | 2 | 0.012939 | 0.47086 | no |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | glm-5.3-flash-maya | 45 | 33 | 22 | 14 | 3 | 0.012726 | 0.47086 | no |
| ripple-65b-vllm | hy4-flash-sq-64-strata | 45 | 29 | 28 | 7 | 6 | 1 | 1 | no |
| ripple-65b-vllm | inkling-2-mini-sq-20-strata-2gpu | 45 | 29 | 23 | 10 | 4 | 0.17957 | 1 | no |
| ripple-65b-vllm | glm-5.3-flash-maya | 45 | 29 | 22 | 13 | 6 | 0.16707 | 1 | no |
| hy4-flash-sq-64-strata | inkling-2-mini-sq-20-strata-2gpu | 45 | 28 | 23 | 9 | 4 | 0.26685 | 1 | no |
| hy4-flash-sq-64-strata | glm-5.3-flash-maya | 45 | 28 | 22 | 12 | 6 | 0.23788 | 1 | no |
| inkling-2-mini-sq-20-strata-2gpu | glm-5.3-flash-maya | 45 | 23 | 22 | 9 | 8 | 1 | 1 | no |

## Extended ranking: first 60 items

### Complete routes (score order)

| Route | Group | Complete | Correct/scored | Scored/frozen | Score | Wilson 95% | Capped | Malformed | Not run | Ungraded | Used/budget (min) |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| qwen3.8-flash-next-iq3_xxs | A | yes | 50/60 | 60/60 | 83.3% | 72.0%–90.7% | 0 | 0 | 0 | 0 | 14.77/15 |
| qwen3.8-27b-sglang-dflash2 | A | yes | 49/60 | 60/60 | 81.7% | 70.1%–89.4% | 2 | 0 | 0 | 0 | 14.84/15 |
| qwen3.8-27b-vllm | A | yes | 47/60 | 60/60 | 78.3% | 66.4%–86.9% | 3 | 1 | 0 | 0 | 14.97/15 |
| kolibri-1.1-iq4_xs | A B | yes | 45/60 | 60/60 | 75.0% | 62.8%–84.2% | 0 | 1 | 0 | 0 | 12.99/15 |
| hy4-flash-sq-64-strata | A B | yes | 43/60 | 60/60 | 71.7% | 59.2%–81.5% | 0 | 1 | 0 | 0 | 16.43/30 |
| glm-5.3-flash-maya | B | yes | 33/60 | 60/60 | 55.0% | 42.5%–66.9% | 0 | 0 | 0 | 0 | 30.00/30 |
| inkling-2-mini-sq-20-strata-2gpu | B | yes | 31/60 | 60/60 | 51.7% | 39.3%–63.8% | 1 | 6 | 0 | 0 | 13.94/15 |

### Incomplete routes (unranked)

None.

### Per category (correct/scored; frozen N in header)

| Route | code (N=9) | instruction (N=9) | knowledge (N=15) | math (N=9) | reasoning (N=8) | tools (N=10) |
|---|---:|---:|---:|---:|---:|---:|
| qwen3.8-flash-next-iq3_xxs | 6/9 | 7/9 | 15/15 | 9/9 | 6/8 | 7/10 |
| qwen3.8-27b-sglang-dflash2 | 6/9 | 9/9 | 13/15 | 9/9 | 5/8 | 7/10 |
| qwen3.8-27b-vllm | 6/9 | 8/9 | 13/15 | 9/9 | 5/8 | 6/10 |
| kolibri-1.1-iq4_xs | 7/9 | 5/9 | 14/15 | 9/9 | 2/8 | 8/10 |
| hy4-flash-sq-64-strata | 5/9 | 9/9 | 12/15 | 7/9 | 3/8 | 7/10 |
| glm-5.3-flash-maya | 7/9 | 6/9 | 8/15 | 3/9 | 2/8 | 7/10 |
| inkling-2-mini-sq-20-strata-2gpu | 5/9 | 4/9 | 11/15 | 5/9 | 1/8 | 5/10 |

### Exact paired McNemar tests (Holm family: 21)

| A | B | Prefix N | A correct | B correct | A only | B only | Exact p | Holm p | Separated |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| qwen3.8-flash-next-iq3_xxs | qwen3.8-27b-sglang-dflash2 | 60 | 50 | 49 | 7 | 6 | 1 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | qwen3.8-27b-vllm | 60 | 50 | 47 | 8 | 5 | 0.58105 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | kolibri-1.1-iq4_xs | 60 | 50 | 45 | 10 | 5 | 0.30176 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | hy4-flash-sq-64-strata | 60 | 50 | 43 | 12 | 5 | 0.14346 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | glm-5.3-flash-maya | 60 | 50 | 33 | 22 | 5 | 0.0015137 | 0.027247 | yes |
| qwen3.8-flash-next-iq3_xxs | inkling-2-mini-sq-20-strata-2gpu | 60 | 50 | 31 | 21 | 2 | 6.6042e-05 | 0.0013869 | yes |
| qwen3.8-27b-sglang-dflash2 | qwen3.8-27b-vllm | 60 | 49 | 47 | 4 | 2 | 0.6875 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | kolibri-1.1-iq4_xs | 60 | 49 | 45 | 11 | 7 | 0.48068 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | hy4-flash-sq-64-strata | 60 | 49 | 43 | 10 | 4 | 0.17957 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | glm-5.3-flash-maya | 60 | 49 | 33 | 19 | 3 | 0.00085545 | 0.016253 | yes |
| qwen3.8-27b-sglang-dflash2 | inkling-2-mini-sq-20-strata-2gpu | 60 | 49 | 31 | 20 | 2 | 0.00012112 | 0.0024223 | yes |
| qwen3.8-27b-vllm | kolibri-1.1-iq4_xs | 60 | 47 | 45 | 10 | 8 | 0.81453 | 1 | no |
| qwen3.8-27b-vllm | hy4-flash-sq-64-strata | 60 | 47 | 43 | 10 | 6 | 0.4545 | 1 | no |
| qwen3.8-27b-vllm | glm-5.3-flash-maya | 60 | 47 | 33 | 17 | 3 | 0.0025768 | 0.041229 | yes |
| qwen3.8-27b-vllm | inkling-2-mini-sq-20-strata-2gpu | 60 | 47 | 31 | 20 | 4 | 0.0015439 | 0.027247 | yes |
| kolibri-1.1-iq4_xs | hy4-flash-sq-64-strata | 60 | 45 | 43 | 9 | 7 | 0.80362 | 1 | no |
| kolibri-1.1-iq4_xs | glm-5.3-flash-maya | 60 | 45 | 33 | 18 | 6 | 0.022656 | 0.29453 | no |
| kolibri-1.1-iq4_xs | inkling-2-mini-sq-20-strata-2gpu | 60 | 45 | 31 | 18 | 4 | 0.0043435 | 0.065153 | no |
| hy4-flash-sq-64-strata | glm-5.3-flash-maya | 60 | 43 | 33 | 16 | 6 | 0.052479 | 0.62975 | no |
| hy4-flash-sq-64-strata | inkling-2-mini-sq-20-strata-2gpu | 60 | 43 | 31 | 16 | 4 | 0.011818 | 0.16545 | no |
| glm-5.3-flash-maya | inkling-2-mini-sq-20-strata-2gpu | 60 | 33 | 31 | 13 | 11 | 0.83882 | 1 | no |

## Extended ranking: first 75 items

### Complete routes (score order)

| Route | Group | Complete | Correct/scored | Scored/frozen | Score | Wilson 95% | Capped | Malformed | Not run | Ungraded | Used/budget (min) |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| qwen3.8-flash-next-iq3_xxs | A | yes | 64/75 | 75/75 | 85.3% | 75.6%–91.6% | 0 | 0 | 0 | 0 | 14.77/15 |
| qwen3.8-27b-sglang-dflash2 | A | yes | 59/75 | 75/75 | 78.7% | 68.1%–86.4% | 3 | 0 | 0 | 0 | 14.84/15 |
| qwen3.8-27b-vllm | A B | yes | 57/75 | 75/75 | 76.0% | 65.2%–84.2% | 5 | 1 | 0 | 0 | 14.97/15 |
| kolibri-1.1-iq4_xs | A B C | yes | 55/75 | 75/75 | 73.3% | 62.4%–82.0% | 0 | 1 | 0 | 0 | 12.99/15 |
| hy4-flash-sq-64-strata | A B C | yes | 53/75 | 75/75 | 70.7% | 59.6%–79.8% | 0 | 1 | 0 | 0 | 16.43/30 |
| glm-5.3-flash-maya | B C | yes | 43/75 | 75/75 | 57.3% | 46.1%–67.9% | 0 | 0 | 0 | 0 | 30.00/30 |
| inkling-2-mini-sq-20-strata-2gpu | C | yes | 39/75 | 75/75 | 52.0% | 40.9%–62.9% | 1 | 9 | 0 | 0 | 13.94/15 |

### Incomplete routes (unranked)

None.

### Per category (correct/scored; frozen N in header)

| Route | code (N=11) | instruction (N=11) | knowledge (N=19) | math (N=11) | reasoning (N=10) | tools (N=13) |
|---|---:|---:|---:|---:|---:|---:|
| qwen3.8-flash-next-iq3_xxs | 7/11 | 9/11 | 19/19 | 11/11 | 8/10 | 10/13 |
| qwen3.8-27b-sglang-dflash2 | 6/11 | 11/11 | 15/19 | 11/11 | 6/10 | 10/13 |
| qwen3.8-27b-vllm | 6/11 | 10/11 | 16/19 | 11/11 | 5/10 | 9/13 |
| kolibri-1.1-iq4_xs | 8/11 | 5/11 | 18/19 | 11/11 | 3/10 | 10/13 |
| hy4-flash-sq-64-strata | 5/11 | 11/11 | 15/19 | 9/11 | 4/10 | 9/13 |
| glm-5.3-flash-maya | 7/11 | 8/11 | 10/19 | 5/11 | 3/10 | 10/13 |
| inkling-2-mini-sq-20-strata-2gpu | 7/11 | 5/11 | 12/19 | 6/11 | 1/10 | 8/13 |

### Exact paired McNemar tests (Holm family: 21)

| A | B | Prefix N | A correct | B correct | A only | B only | Exact p | Holm p | Separated |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| qwen3.8-flash-next-iq3_xxs | qwen3.8-27b-sglang-dflash2 | 75 | 64 | 59 | 11 | 6 | 0.33231 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | qwen3.8-27b-vllm | 75 | 64 | 57 | 12 | 5 | 0.14346 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | kolibri-1.1-iq4_xs | 75 | 64 | 55 | 15 | 6 | 0.078354 | 0.83071 | no |
| qwen3.8-flash-next-iq3_xxs | hy4-flash-sq-64-strata | 75 | 64 | 53 | 16 | 5 | 0.026604 | 0.34585 | no |
| qwen3.8-flash-next-iq3_xxs | glm-5.3-flash-maya | 75 | 64 | 43 | 26 | 5 | 0.0001922 | 0.0038439 | yes |
| qwen3.8-flash-next-iq3_xxs | inkling-2-mini-sq-20-strata-2gpu | 75 | 64 | 39 | 28 | 3 | 4.6492e-06 | 9.7632e-05 | yes |
| qwen3.8-27b-sglang-dflash2 | qwen3.8-27b-vllm | 75 | 59 | 57 | 5 | 3 | 0.72656 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | kolibri-1.1-iq4_xs | 75 | 59 | 55 | 15 | 11 | 0.5572 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | hy4-flash-sq-64-strata | 75 | 59 | 53 | 12 | 6 | 0.23788 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | glm-5.3-flash-maya | 75 | 59 | 43 | 21 | 5 | 0.0024939 | 0.042397 | yes |
| qwen3.8-27b-sglang-dflash2 | inkling-2-mini-sq-20-strata-2gpu | 75 | 59 | 39 | 25 | 5 | 0.00032491 | 0.0061734 | yes |
| qwen3.8-27b-vllm | kolibri-1.1-iq4_xs | 75 | 57 | 55 | 13 | 11 | 0.83882 | 1 | no |
| qwen3.8-27b-vllm | hy4-flash-sq-64-strata | 75 | 57 | 53 | 12 | 8 | 0.50344 | 1 | no |
| qwen3.8-27b-vllm | glm-5.3-flash-maya | 75 | 57 | 43 | 18 | 4 | 0.0043435 | 0.069496 | no |
| qwen3.8-27b-vllm | inkling-2-mini-sq-20-strata-2gpu | 75 | 57 | 39 | 25 | 7 | 0.0021024 | 0.037843 | yes |
| kolibri-1.1-iq4_xs | hy4-flash-sq-64-strata | 75 | 55 | 53 | 12 | 10 | 0.83181 | 1 | no |
| kolibri-1.1-iq4_xs | glm-5.3-flash-maya | 75 | 55 | 43 | 21 | 9 | 0.042774 | 0.51329 | no |
| kolibri-1.1-iq4_xs | inkling-2-mini-sq-20-strata-2gpu | 75 | 55 | 39 | 23 | 7 | 0.0052229 | 0.078343 | no |
| hy4-flash-sq-64-strata | glm-5.3-flash-maya | 75 | 53 | 43 | 18 | 8 | 0.075519 | 0.83071 | no |
| hy4-flash-sq-64-strata | inkling-2-mini-sq-20-strata-2gpu | 75 | 53 | 39 | 21 | 7 | 0.012541 | 0.17557 | no |
| glm-5.3-flash-maya | inkling-2-mini-sq-20-strata-2gpu | 75 | 43 | 39 | 18 | 14 | 0.59661 | 1 | no |

## Extended ranking: first 90 items

### Complete routes (score order)

| Route | Group | Complete | Correct/scored | Scored/frozen | Score | Wilson 95% | Capped | Malformed | Not run | Ungraded | Used/budget (min) |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| qwen3.8-flash-next-iq3_xxs | A | yes | 76/90 | 90/90 | 84.4% | 75.6%–90.5% | 1 | 0 | 0 | 0 | 14.77/15 |
| qwen3.8-27b-sglang-dflash2 | A | yes | 70/90 | 90/90 | 77.8% | 68.2%–85.1% | 5 | 0 | 0 | 0 | 14.84/15 |
| qwen3.8-27b-vllm | A B | yes | 69/90 | 90/90 | 76.7% | 66.9%–84.2% | 6 | 1 | 0 | 0 | 14.97/15 |
| kolibri-1.1-iq4_xs | A B C | yes | 63/90 | 90/90 | 70.0% | 59.9%–78.5% | 0 | 2 | 0 | 0 | 12.99/15 |
| hy4-flash-sq-64-strata | A B C | yes | 62/90 | 90/90 | 68.9% | 58.7%–77.5% | 0 | 1 | 0 | 0 | 16.43/30 |
| glm-5.3-flash-maya | C | yes | 51/90 | 90/90 | 56.7% | 46.4%–66.4% | 0 | 0 | 0 | 0 | 30.00/30 |
| inkling-2-mini-sq-20-strata-2gpu | B C | yes | 51/90 | 90/90 | 56.7% | 46.4%–66.4% | 2 | 9 | 0 | 0 | 13.94/15 |

### Incomplete routes (unranked)

None.

### Per category (correct/scored; frozen N in header)

| Route | code (N=13) | instruction (N=13) | knowledge (N=23) | math (N=13) | reasoning (N=13) | tools (N=15) |
|---|---:|---:|---:|---:|---:|---:|
| qwen3.8-flash-next-iq3_xxs | 8/13 | 11/13 | 23/23 | 13/13 | 9/13 | 12/15 |
| qwen3.8-27b-sglang-dflash2 | 6/13 | 13/13 | 18/23 | 13/13 | 8/13 | 12/15 |
| qwen3.8-27b-vllm | 7/13 | 12/13 | 20/23 | 13/13 | 7/13 | 10/15 |
| kolibri-1.1-iq4_xs | 9/13 | 5/13 | 21/23 | 13/13 | 4/13 | 11/15 |
| hy4-flash-sq-64-strata | 6/13 | 12/13 | 19/23 | 10/13 | 5/13 | 10/15 |
| glm-5.3-flash-maya | 8/13 | 10/13 | 12/23 | 5/13 | 5/13 | 11/15 |
| inkling-2-mini-sq-20-strata-2gpu | 9/13 | 7/13 | 15/23 | 8/13 | 2/13 | 10/15 |

### Exact paired McNemar tests (Holm family: 21)

| A | B | Prefix N | A correct | B correct | A only | B only | Exact p | Holm p | Separated |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| qwen3.8-flash-next-iq3_xxs | qwen3.8-27b-sglang-dflash2 | 90 | 76 | 70 | 13 | 7 | 0.26318 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | qwen3.8-27b-vllm | 90 | 76 | 69 | 13 | 6 | 0.16707 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | kolibri-1.1-iq4_xs | 90 | 76 | 63 | 20 | 7 | 0.019157 | 0.2682 | no |
| qwen3.8-flash-next-iq3_xxs | hy4-flash-sq-64-strata | 90 | 76 | 62 | 20 | 6 | 0.0093553 | 0.14033 | no |
| qwen3.8-flash-next-iq3_xxs | glm-5.3-flash-maya | 90 | 76 | 51 | 31 | 6 | 4.1258e-05 | 0.00082515 | yes |
| qwen3.8-flash-next-iq3_xxs | inkling-2-mini-sq-20-strata-2gpu | 90 | 76 | 51 | 29 | 4 | 1.0929e-05 | 0.0002295 | yes |
| qwen3.8-27b-sglang-dflash2 | qwen3.8-27b-vllm | 90 | 70 | 69 | 6 | 5 | 1 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | kolibri-1.1-iq4_xs | 90 | 70 | 63 | 21 | 14 | 0.3105 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | hy4-flash-sq-64-strata | 90 | 70 | 62 | 17 | 9 | 0.16864 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | glm-5.3-flash-maya | 90 | 70 | 51 | 26 | 7 | 0.0013187 | 0.023737 | yes |
| qwen3.8-27b-sglang-dflash2 | inkling-2-mini-sq-20-strata-2gpu | 90 | 70 | 51 | 26 | 7 | 0.0013187 | 0.023737 | yes |
| qwen3.8-27b-vllm | kolibri-1.1-iq4_xs | 90 | 69 | 63 | 18 | 12 | 0.36159 | 1 | no |
| qwen3.8-27b-vllm | hy4-flash-sq-64-strata | 90 | 69 | 62 | 16 | 9 | 0.22952 | 1 | no |
| qwen3.8-27b-vllm | glm-5.3-flash-maya | 90 | 69 | 51 | 23 | 5 | 0.00091223 | 0.017332 | yes |
| qwen3.8-27b-vllm | inkling-2-mini-sq-20-strata-2gpu | 90 | 69 | 51 | 27 | 9 | 0.0039332 | 0.062931 | no |
| kolibri-1.1-iq4_xs | hy4-flash-sq-64-strata | 90 | 63 | 62 | 13 | 12 | 1 | 1 | no |
| kolibri-1.1-iq4_xs | glm-5.3-flash-maya | 90 | 63 | 51 | 25 | 13 | 0.072951 | 0.91982 | no |
| kolibri-1.1-iq4_xs | inkling-2-mini-sq-20-strata-2gpu | 90 | 63 | 51 | 25 | 13 | 0.072951 | 0.91982 | no |
| hy4-flash-sq-64-strata | glm-5.3-flash-maya | 90 | 62 | 51 | 21 | 10 | 0.070756 | 0.91982 | no |
| hy4-flash-sq-64-strata | inkling-2-mini-sq-20-strata-2gpu | 90 | 62 | 51 | 23 | 12 | 0.089531 | 0.91982 | no |
| glm-5.3-flash-maya | inkling-2-mini-sq-20-strata-2gpu | 90 | 51 | 51 | 19 | 19 | 1 | 1 | no |

## Extended ranking: first 105 items

### Complete routes (score order)

| Route | Group | Complete | Correct/scored | Scored/frozen | Score | Wilson 95% | Capped | Malformed | Not run | Ungraded | Used/budget (min) |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| qwen3.8-flash-next-iq3_xxs | A | yes | 89/105 | 105/105 | 84.8% | 76.7%–90.4% | 2 | 0 | 0 | 0 | 14.77/15 |
| qwen3.8-27b-sglang-dflash2 | A B | yes | 80/105 | 105/105 | 76.2% | 67.2%–83.3% | 6 | 0 | 0 | 0 | 14.84/15 |
| qwen3.8-27b-vllm | A B C | yes | 77/105 | 105/105 | 73.3% | 64.2%–80.9% | 10 | 1 | 0 | 0 | 14.97/15 |
| hy4-flash-sq-64-strata | B C | yes | 71/105 | 105/105 | 67.6% | 58.2%–75.8% | 0 | 2 | 0 | 0 | 16.43/30 |
| kolibri-1.1-iq4_xs | B C | yes | 70/105 | 105/105 | 66.7% | 57.2%–75.0% | 1 | 3 | 0 | 0 | 12.99/15 |
| glm-5.3-flash-maya | B C | yes | 61/105 | 105/105 | 58.1% | 48.5%–67.1% | 0 | 0 | 0 | 0 | 30.00/30 |
| inkling-2-mini-sq-20-strata-2gpu | C | yes | 60/105 | 105/105 | 57.1% | 47.6%–66.2% | 3 | 10 | 0 | 0 | 13.94/15 |

### Incomplete routes (unranked)

None.

### Per category (correct/scored; frozen N in header)

| Route | code (N=13) | instruction (N=16) | knowledge (N=27) | math (N=16) | reasoning (N=15) | tools (N=18) |
|---|---:|---:|---:|---:|---:|---:|
| qwen3.8-flash-next-iq3_xxs | 8/13 | 13/16 | 26/27 | 16/16 | 11/15 | 15/18 |
| qwen3.8-27b-sglang-dflash2 | 6/13 | 15/16 | 20/27 | 16/16 | 8/15 | 15/18 |
| qwen3.8-27b-vllm | 7/13 | 14/16 | 22/27 | 15/16 | 7/15 | 12/18 |
| hy4-flash-sq-64-strata | 6/13 | 15/16 | 21/27 | 12/16 | 6/15 | 11/18 |
| kolibri-1.1-iq4_xs | 9/13 | 5/16 | 23/27 | 15/16 | 5/15 | 13/18 |
| glm-5.3-flash-maya | 8/13 | 13/16 | 15/27 | 5/16 | 7/15 | 13/18 |
| inkling-2-mini-sq-20-strata-2gpu | 9/13 | 8/16 | 17/27 | 10/16 | 3/15 | 13/18 |

### Exact paired McNemar tests (Holm family: 21)

| A | B | Prefix N | A correct | B correct | A only | B only | Exact p | Holm p | Separated |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| qwen3.8-flash-next-iq3_xxs | qwen3.8-27b-sglang-dflash2 | 105 | 89 | 80 | 16 | 7 | 0.09314 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | qwen3.8-27b-vllm | 105 | 89 | 77 | 18 | 6 | 0.022656 | 0.29453 | no |
| qwen3.8-flash-next-iq3_xxs | hy4-flash-sq-64-strata | 105 | 89 | 71 | 25 | 7 | 0.0021024 | 0.035741 | yes |
| qwen3.8-flash-next-iq3_xxs | kolibri-1.1-iq4_xs | 105 | 89 | 70 | 26 | 7 | 0.0013187 | 0.025056 | yes |
| qwen3.8-flash-next-iq3_xxs | glm-5.3-flash-maya | 105 | 89 | 61 | 36 | 8 | 2.5449e-05 | 0.00050897 | yes |
| qwen3.8-flash-next-iq3_xxs | inkling-2-mini-sq-20-strata-2gpu | 105 | 89 | 60 | 34 | 5 | 2.4299e-06 | 5.1028e-05 | yes |
| qwen3.8-27b-sglang-dflash2 | qwen3.8-27b-vllm | 105 | 80 | 77 | 8 | 5 | 0.58105 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | hy4-flash-sq-64-strata | 105 | 80 | 71 | 20 | 11 | 0.14961 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | kolibri-1.1-iq4_xs | 105 | 80 | 70 | 25 | 15 | 0.15386 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | glm-5.3-flash-maya | 105 | 80 | 61 | 30 | 11 | 0.004324 | 0.069184 | no |
| qwen3.8-27b-sglang-dflash2 | inkling-2-mini-sq-20-strata-2gpu | 105 | 80 | 60 | 29 | 9 | 0.0016581 | 0.029845 | yes |
| qwen3.8-27b-vllm | hy4-flash-sq-64-strata | 105 | 77 | 71 | 18 | 12 | 0.36159 | 1 | no |
| qwen3.8-27b-vllm | kolibri-1.1-iq4_xs | 105 | 77 | 70 | 22 | 15 | 0.32401 | 1 | no |
| qwen3.8-27b-vllm | glm-5.3-flash-maya | 105 | 77 | 61 | 25 | 9 | 0.0090412 | 0.13562 | no |
| qwen3.8-27b-vllm | inkling-2-mini-sq-20-strata-2gpu | 105 | 77 | 60 | 30 | 13 | 0.013718 | 0.19205 | no |
| hy4-flash-sq-64-strata | kolibri-1.1-iq4_xs | 105 | 71 | 70 | 16 | 15 | 1 | 1 | no |
| hy4-flash-sq-64-strata | glm-5.3-flash-maya | 105 | 71 | 61 | 24 | 14 | 0.14331 | 1 | no |
| hy4-flash-sq-64-strata | inkling-2-mini-sq-20-strata-2gpu | 105 | 71 | 60 | 26 | 15 | 0.11728 | 1 | no |
| kolibri-1.1-iq4_xs | glm-5.3-flash-maya | 105 | 70 | 61 | 28 | 19 | 0.24296 | 1 | no |
| kolibri-1.1-iq4_xs | inkling-2-mini-sq-20-strata-2gpu | 105 | 70 | 60 | 26 | 16 | 0.16415 | 1 | no |
| glm-5.3-flash-maya | inkling-2-mini-sq-20-strata-2gpu | 105 | 61 | 60 | 23 | 22 | 1 | 1 | no |

## Extended ranking: first 120 items

### Complete routes (score order)

| Route | Group | Complete | Correct/scored | Scored/frozen | Score | Wilson 95% | Capped | Malformed | Not run | Ungraded | Used/budget (min) |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| qwen3.8-flash-next-iq3_xxs | A | yes | 100/120 | 120/120 | 83.3% | 75.7%–88.9% | 3 | 0 | 0 | 0 | 14.77/15 |
| qwen3.8-27b-sglang-dflash2 | A B | yes | 88/120 | 120/120 | 73.3% | 64.8%–80.4% | 10 | 0 | 0 | 0 | 14.84/15 |
| qwen3.8-27b-vllm | A B C | yes | 86/120 | 120/120 | 71.7% | 63.0%–79.0% | 13 | 1 | 0 | 0 | 14.97/15 |
| kolibri-1.1-iq4_xs | B C | yes | 80/120 | 120/120 | 66.7% | 57.8%–74.5% | 1 | 3 | 0 | 0 | 12.99/15 |
| hy4-flash-sq-64-strata | B C | yes | 78/120 | 120/120 | 65.0% | 56.1%–72.9% | 0 | 4 | 0 | 0 | 16.43/30 |
| inkling-2-mini-sq-20-strata-2gpu | C | yes | 67/120 | 120/120 | 55.8% | 46.9%–64.4% | 3 | 12 | 0 | 0 | 13.94/15 |

### Incomplete routes (unranked)

None.

### Per category (correct/scored; frozen N in header)

| Route | code (N=13) | instruction (N=19) | knowledge (N=31) | math (N=19) | reasoning (N=18) | tools (N=20) |
|---|---:|---:|---:|---:|---:|---:|
| qwen3.8-flash-next-iq3_xxs | 8/13 | 16/19 | 27/31 | 19/19 | 13/18 | 17/20 |
| qwen3.8-27b-sglang-dflash2 | 6/13 | 17/19 | 21/31 | 18/19 | 9/18 | 17/20 |
| qwen3.8-27b-vllm | 7/13 | 16/19 | 23/31 | 18/19 | 8/18 | 14/20 |
| kolibri-1.1-iq4_xs | 9/13 | 7/19 | 25/31 | 18/19 | 7/18 | 14/20 |
| hy4-flash-sq-64-strata | 6/13 | 17/19 | 22/31 | 13/19 | 8/18 | 12/20 |
| inkling-2-mini-sq-20-strata-2gpu | 9/13 | 10/19 | 17/31 | 12/19 | 5/18 | 14/20 |

### Exact paired McNemar tests (Holm family: 15)

| A | B | Prefix N | A correct | B correct | A only | B only | Exact p | Holm p | Separated |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| qwen3.8-flash-next-iq3_xxs | qwen3.8-27b-sglang-dflash2 | 120 | 100 | 88 | 19 | 7 | 0.028959 | 0.26063 | no |
| qwen3.8-flash-next-iq3_xxs | qwen3.8-27b-vllm | 120 | 100 | 86 | 21 | 7 | 0.012541 | 0.12541 | no |
| qwen3.8-flash-next-iq3_xxs | kolibri-1.1-iq4_xs | 120 | 100 | 80 | 28 | 8 | 0.0011932 | 0.015512 | yes |
| qwen3.8-flash-next-iq3_xxs | hy4-flash-sq-64-strata | 120 | 100 | 78 | 29 | 7 | 0.00031255 | 0.0043757 | yes |
| qwen3.8-flash-next-iq3_xxs | inkling-2-mini-sq-20-strata-2gpu | 120 | 100 | 67 | 39 | 6 | 5.4178e-07 | 8.1267e-06 | yes |
| qwen3.8-27b-sglang-dflash2 | qwen3.8-27b-vllm | 120 | 88 | 86 | 9 | 7 | 0.80362 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | kolibri-1.1-iq4_xs | 120 | 88 | 80 | 27 | 19 | 0.302 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | hy4-flash-sq-64-strata | 120 | 88 | 78 | 23 | 13 | 0.1325 | 0.92749 | no |
| qwen3.8-27b-sglang-dflash2 | inkling-2-mini-sq-20-strata-2gpu | 120 | 88 | 67 | 32 | 11 | 0.001914 | 0.022968 | yes |
| qwen3.8-27b-vllm | kolibri-1.1-iq4_xs | 120 | 86 | 80 | 24 | 18 | 0.4408 | 1 | no |
| qwen3.8-27b-vllm | hy4-flash-sq-64-strata | 120 | 86 | 78 | 23 | 15 | 0.25588 | 1 | no |
| qwen3.8-27b-vllm | inkling-2-mini-sq-20-strata-2gpu | 120 | 86 | 67 | 33 | 14 | 0.0079427 | 0.08737 | no |
| kolibri-1.1-iq4_xs | hy4-flash-sq-64-strata | 120 | 80 | 78 | 18 | 16 | 0.86417 | 1 | no |
| kolibri-1.1-iq4_xs | inkling-2-mini-sq-20-strata-2gpu | 120 | 80 | 67 | 32 | 19 | 0.091915 | 0.73532 | no |
| hy4-flash-sq-64-strata | inkling-2-mini-sq-20-strata-2gpu | 120 | 78 | 67 | 30 | 19 | 0.15241 | 0.92749 | no |

## Extended ranking: first 135 items

### Complete routes (score order)

| Route | Group | Complete | Correct/scored | Scored/frozen | Score | Wilson 95% | Capped | Malformed | Not run | Ungraded | Used/budget (min) |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| qwen3.8-flash-next-iq3_xxs | A | yes | 107/135 | 135/135 | 79.3% | 71.7%–85.2% | 8 | 0 | 0 | 0 | 14.77/15 |
| kolibri-1.1-iq4_xs | B | yes | 89/135 | 135/135 | 65.9% | 57.6%–73.4% | 2 | 4 | 0 | 0 | 12.99/15 |
| hy4-flash-sq-64-strata | B | yes | 88/135 | 135/135 | 65.2% | 56.8%–72.7% | 0 | 6 | 0 | 0 | 16.43/30 |
| inkling-2-mini-sq-20-strata-2gpu | B | yes | 73/135 | 135/135 | 54.1% | 45.7%–62.3% | 5 | 15 | 0 | 0 | 13.94/15 |

### Incomplete routes (unranked)

None.

### Per category (correct/scored; frozen N in header)

| Route | code (N=13) | instruction (N=21) | knowledge (N=37) | math (N=23) | reasoning (N=21) | tools (N=20) |
|---|---:|---:|---:|---:|---:|---:|
| qwen3.8-flash-next-iq3_xxs | 8/13 | 17/21 | 28/37 | 23/23 | 14/21 | 17/20 |
| kolibri-1.1-iq4_xs | 9/13 | 8/21 | 28/37 | 22/23 | 8/21 | 14/20 |
| hy4-flash-sq-64-strata | 6/13 | 18/21 | 27/37 | 15/23 | 10/21 | 12/20 |
| inkling-2-mini-sq-20-strata-2gpu | 9/13 | 10/21 | 20/37 | 13/23 | 7/21 | 14/20 |

### Exact paired McNemar tests (Holm family: 6)

| A | B | Prefix N | A correct | B correct | A only | B only | Exact p | Holm p | Separated |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| qwen3.8-flash-next-iq3_xxs | kolibri-1.1-iq4_xs | 135 | 107 | 89 | 28 | 10 | 0.0050976 | 0.025488 | yes |
| qwen3.8-flash-next-iq3_xxs | hy4-flash-sq-64-strata | 135 | 107 | 88 | 31 | 12 | 0.0054016 | 0.025488 | yes |
| qwen3.8-flash-next-iq3_xxs | inkling-2-mini-sq-20-strata-2gpu | 135 | 107 | 73 | 43 | 9 | 2.0378e-06 | 1.2227e-05 | yes |
| kolibri-1.1-iq4_xs | hy4-flash-sq-64-strata | 135 | 89 | 88 | 20 | 19 | 1 | 1 | no |
| kolibri-1.1-iq4_xs | inkling-2-mini-sq-20-strata-2gpu | 135 | 89 | 73 | 36 | 20 | 0.044047 | 0.13214 | no |
| hy4-flash-sq-64-strata | inkling-2-mini-sq-20-strata-2gpu | 135 | 88 | 73 | 35 | 20 | 0.058064 | 0.13214 | no |

## Extended ranking: first 144 items

### Complete routes (score order)

| Route | Group | Complete | Correct/scored | Scored/frozen | Score | Wilson 95% | Capped | Malformed | Not run | Ungraded | Used/budget (min) |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| kolibri-1.1-iq4_xs | A | yes | 96/144 | 144/144 | 66.7% | 58.6%–73.8% | 3 | 5 | 0 | 0 | 12.99/15 |
| hy4-flash-sq-64-strata | A | yes | 91/144 | 144/144 | 63.2% | 55.1%–70.6% | 0 | 9 | 0 | 0 | 16.43/30 |
| inkling-2-mini-sq-20-strata-2gpu | B | yes | 73/144 | 144/144 | 50.7% | 42.6%–58.7% | 6 | 20 | 0 | 0 | 13.94/15 |

### Incomplete routes (unranked)

None.

### Per category (correct/scored; frozen N in header)

| Route | code (N=13) | instruction (N=21) | knowledge (N=38) | math (N=31) | reasoning (N=21) | tools (N=20) |
|---|---:|---:|---:|---:|---:|---:|
| kolibri-1.1-iq4_xs | 9/13 | 8/21 | 28/38 | 29/31 | 8/21 | 14/20 |
| hy4-flash-sq-64-strata | 6/13 | 18/21 | 28/38 | 17/31 | 10/21 | 12/20 |
| inkling-2-mini-sq-20-strata-2gpu | 9/13 | 10/21 | 20/38 | 13/31 | 7/21 | 14/20 |

### Exact paired McNemar tests (Holm family: 3)

| A | B | Prefix N | A correct | B correct | A only | B only | Exact p | Holm p | Separated |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| kolibri-1.1-iq4_xs | hy4-flash-sq-64-strata | 144 | 96 | 91 | 25 | 20 | 0.55148 | 0.55148 | no |
| kolibri-1.1-iq4_xs | inkling-2-mini-sq-20-strata-2gpu | 144 | 96 | 73 | 43 | 20 | 0.0051524 | 0.015457 | yes |
| hy4-flash-sq-64-strata | inkling-2-mini-sq-20-strata-2gpu | 144 | 91 | 73 | 38 | 20 | 0.024746 | 0.049492 | yes |

## Whole-run coverage (not a ranking)

| Route | Core complete | Full complete | Answered prefix | Scored prefix | Correct/scored | Capped | Malformed | Not run | Ungraded |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | yes | no | 51 | 51 | 40/51 | 0 | 0 | 93 | 0 |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | yes | no | 50 | 50 | 37/50 | 0 | 1 | 94 | 0 |
| glm-5.3-flash-maya | yes | no | 111 | 111 | 65/111 | 0 | 0 | 33 | 0 |
| hy4-flash-sq-64-strata | yes | yes | 144 | 144 | 91/144 | 0 | 9 | 0 | 0 |
| inkling-2-mini-sq-20-strata-2gpu | yes | yes | 144 | 144 | 73/144 | 6 | 20 | 0 | 0 |
| kolibri-1.1-iq4_xs | yes | yes | 144 | 144 | 96/144 | 3 | 5 | 0 | 0 |
| qwen3.8-27b-sglang-dflash2 | yes | no | 134 | 134 | 95/134 | 16 | 0 | 10 | 0 |
| qwen3.8-27b-vllm | yes | no | 123 | 123 | 88/123 | 14 | 1 | 21 | 0 |
| qwen3.8-flash-next-iq3_xxs | yes | no | 137 | 137 | 108/137 | 9 | 0 | 7 | 0 |
| ripple-65b-vllm | yes | no | 47 | 47 | 30/47 | 10 | 0 | 97 | 0 |

## Longest shared checkpoint per core-eligible pair (Holm family: 45)

Prefix lengths can differ between rows. These comparisons do not define a fleet ranking.

| A | B | Prefix N | A correct | B correct | A only | B only | Exact p | Holm p | Separated |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | deepseek-v4.1-flash-1017-strata-unsloth-q1 | 45 | 35 | 33 | 3 | 1 | 0.625 | 1 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | glm-5.3-flash-maya | 45 | 35 | 22 | 14 | 1 | 0.00097656 | 0.041992 | yes |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | hy4-flash-sq-64-strata | 45 | 35 | 28 | 9 | 2 | 0.06543 | 1 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | inkling-2-mini-sq-20-strata-2gpu | 45 | 35 | 23 | 13 | 1 | 0.0018311 | 0.076904 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | kolibri-1.1-iq4_xs | 45 | 35 | 34 | 3 | 2 | 1 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | deepseek-v4.1-flash-1017-maya-unsloth-q1 | 45 | 36 | 35 | 4 | 3 | 1 | 1 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | qwen3.8-27b-vllm | 45 | 35 | 34 | 4 | 3 | 1 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | deepseek-v4.1-flash-1017-maya-unsloth-q1 | 45 | 37 | 35 | 4 | 2 | 0.6875 | 1 | no |
| deepseek-v4.1-flash-1017-maya-unsloth-q1 | ripple-65b-vllm | 45 | 35 | 29 | 8 | 2 | 0.10938 | 1 | no |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | glm-5.3-flash-maya | 45 | 33 | 22 | 14 | 3 | 0.012726 | 0.42639 | no |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | hy4-flash-sq-64-strata | 45 | 33 | 28 | 9 | 4 | 0.26685 | 1 | no |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | inkling-2-mini-sq-20-strata-2gpu | 45 | 33 | 23 | 12 | 2 | 0.012939 | 0.42639 | no |
| kolibri-1.1-iq4_xs | deepseek-v4.1-flash-1017-strata-unsloth-q1 | 45 | 34 | 33 | 3 | 2 | 1 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | deepseek-v4.1-flash-1017-strata-unsloth-q1 | 45 | 36 | 33 | 6 | 3 | 0.50781 | 1 | no |
| qwen3.8-27b-vllm | deepseek-v4.1-flash-1017-strata-unsloth-q1 | 45 | 34 | 33 | 6 | 5 | 1 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | deepseek-v4.1-flash-1017-strata-unsloth-q1 | 45 | 37 | 33 | 7 | 3 | 0.34375 | 1 | no |
| deepseek-v4.1-flash-1017-strata-unsloth-q1 | ripple-65b-vllm | 45 | 33 | 29 | 8 | 4 | 0.3877 | 1 | no |
| hy4-flash-sq-64-strata | glm-5.3-flash-maya | 105 | 71 | 61 | 24 | 14 | 0.14331 | 1 | no |
| glm-5.3-flash-maya | inkling-2-mini-sq-20-strata-2gpu | 105 | 61 | 60 | 23 | 22 | 1 | 1 | no |
| kolibri-1.1-iq4_xs | glm-5.3-flash-maya | 105 | 70 | 61 | 28 | 19 | 0.24296 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | glm-5.3-flash-maya | 105 | 80 | 61 | 30 | 11 | 0.004324 | 0.17296 | no |
| qwen3.8-27b-vllm | glm-5.3-flash-maya | 105 | 77 | 61 | 25 | 9 | 0.0090412 | 0.31644 | no |
| qwen3.8-flash-next-iq3_xxs | glm-5.3-flash-maya | 105 | 89 | 61 | 36 | 8 | 2.5449e-05 | 0.0011197 | yes |
| ripple-65b-vllm | glm-5.3-flash-maya | 45 | 29 | 22 | 13 | 6 | 0.16707 | 1 | no |
| hy4-flash-sq-64-strata | inkling-2-mini-sq-20-strata-2gpu | 144 | 91 | 73 | 38 | 20 | 0.024746 | 0.74238 | no |
| kolibri-1.1-iq4_xs | hy4-flash-sq-64-strata | 144 | 96 | 91 | 25 | 20 | 0.55148 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | hy4-flash-sq-64-strata | 120 | 88 | 78 | 23 | 13 | 0.1325 | 1 | no |
| qwen3.8-27b-vllm | hy4-flash-sq-64-strata | 120 | 86 | 78 | 23 | 15 | 0.25588 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | hy4-flash-sq-64-strata | 135 | 107 | 88 | 31 | 12 | 0.0054016 | 0.19986 | no |
| ripple-65b-vllm | hy4-flash-sq-64-strata | 45 | 29 | 28 | 7 | 6 | 1 | 1 | no |
| kolibri-1.1-iq4_xs | inkling-2-mini-sq-20-strata-2gpu | 144 | 96 | 73 | 43 | 20 | 0.0051524 | 0.19881 | no |
| qwen3.8-27b-sglang-dflash2 | inkling-2-mini-sq-20-strata-2gpu | 120 | 88 | 67 | 32 | 11 | 0.001914 | 0.078472 | no |
| qwen3.8-27b-vllm | inkling-2-mini-sq-20-strata-2gpu | 120 | 86 | 67 | 33 | 14 | 0.0079427 | 0.28594 | no |
| qwen3.8-flash-next-iq3_xxs | inkling-2-mini-sq-20-strata-2gpu | 135 | 107 | 73 | 43 | 9 | 2.0378e-06 | 9.17e-05 | yes |
| ripple-65b-vllm | inkling-2-mini-sq-20-strata-2gpu | 45 | 29 | 23 | 10 | 4 | 0.17957 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | kolibri-1.1-iq4_xs | 120 | 88 | 80 | 27 | 19 | 0.302 | 1 | no |
| qwen3.8-27b-vllm | kolibri-1.1-iq4_xs | 120 | 86 | 80 | 24 | 18 | 0.4408 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | kolibri-1.1-iq4_xs | 135 | 107 | 89 | 28 | 10 | 0.0050976 | 0.19881 | no |
| kolibri-1.1-iq4_xs | ripple-65b-vllm | 45 | 34 | 29 | 10 | 5 | 0.30176 | 1 | no |
| qwen3.8-27b-sglang-dflash2 | qwen3.8-27b-vllm | 120 | 88 | 86 | 9 | 7 | 0.80362 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | qwen3.8-27b-sglang-dflash2 | 120 | 100 | 88 | 19 | 7 | 0.028959 | 0.83982 | no |
| qwen3.8-27b-sglang-dflash2 | ripple-65b-vllm | 45 | 36 | 29 | 7 | 0 | 0.015625 | 0.48438 | no |
| qwen3.8-flash-next-iq3_xxs | qwen3.8-27b-vllm | 120 | 100 | 86 | 21 | 7 | 0.012541 | 0.42639 | no |
| qwen3.8-27b-vllm | ripple-65b-vllm | 45 | 34 | 29 | 7 | 2 | 0.17969 | 1 | no |
| qwen3.8-flash-next-iq3_xxs | ripple-65b-vllm | 45 | 37 | 29 | 10 | 2 | 0.038574 | 1 | no |
