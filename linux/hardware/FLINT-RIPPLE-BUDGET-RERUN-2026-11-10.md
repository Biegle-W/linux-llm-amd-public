# Flint and Ripple quality rerun with a larger answer budget — November 10, 2026

**Result:** with enough room to finish, both routes score like the rest of the fleet. Flint goes from 43/54 and 36/64 to **51/54 and 62/64**; Ripple from 50/54 and 56/64 to **53/54 and 63/64**. The low [November 9](AMD-ALL-MODELS-TOOL-AND-QUALITY-2026-11-09.md) scores were the 60-token limit, not wrong answers.

## What was run

- The same two suites (`quant-eval/suite.py`, 54 items; `quant-eval/suite2.py`, 64 items), through the hub, temperature 0, thinking off, graded by the unchanged `grade.py` and `grade2.py`.
- One change: every item's `max_tokens` was raised to at least 4,096 (it was 60 on short-answer items, 200–1,200 elsewhere).
- Routes: `flint-40b-a2.5b` then `ripple-65b-vllm`, serial, hub-started. All 236 requests returned; no errors, no GPU or kernel messages.

## Scores

| Route | Suite | November 9 | November 10 | Capped Nov 9 | Capped Nov 10 |
|---|---|---:|---:|---:|---:|
| `flint-40b-a2.5b` | 54-item | 43 | 51 | 8 | 0 |
| `flint-40b-a2.5b` | 64-item | 36 | 62 | 28 | 0 |
| `ripple-65b-vllm` | 54-item | 50 | 53 | 3 | 0 |
| `ripple-65b-vllm` | 64-item | 56 | 63 | 9 | 1 |

By category on November 10:

| Route | math | code | know | format | tool | — | know | reason | code | format | agent | long |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `flint-40b-a2.5b` | 17/18 | 12/12 | 14/14 | 4/6 | 4/4 | | 29/30 | 11/12 | 10/10 | 4/4 | 5/5 | 3/3 |
| `ripple-65b-vllm` | 18/18 | 12/12 | 14/14 | 5/6 | 4/4 | | 30/30 | 12/12 | 9/10 | 4/4 | 5/5 | 3/3 |

The first five columns are the 54-item suite, the last six the 64-item suite.

## Remaining misses

Flint (5):
- **m03:** answered 1448 instead of 2318. This item is a common miss across routes.
- **f01:** the answer contained the JSON twice with a stray `</think>` tag between the copies, so it is not valid JSON. This is a reasoning-tag leak into the answer.
- **f05:** "gracias muy mucho" instead of "muchas gracias".
- **k09 (64-item):** answered Mercury for atomic number 79 (gold).
- **r02 (64-item):** answered "47th day". The answer is right; the grader accepts only a bare "47".

Ripple (2):
- **f05:** "gracias" instead of "muchas gracias".
- **c03 (64-item):** reasoned through all 4,096 tokens and returned no code. It also ran out at 1,200 tokens on November 9.

## How much budget they need

Both still reason with thinking off, but briefly. The longest finished answer used 560 completion tokens on Flint and 721 on Ripple, so about a thousand tokens of headroom is enough for short answers. Ripple's c03 is the one runaway.

Wall time for all 118 items: Flint 284 s, Ripple 579 s (request time only, excluding model loads).

## What this does and does not show

- Flint (113/118) and Ripple (116/118) are inside the 112–117 band of the other ten routes. Differences inside that band are within run-to-run variation; the suites do not rank routes there.
- The other ten routes were not rerun. They had 0–2 capped answers each on November 9, so their scores could rise by at most that much with the larger budget.
- Callers that set a small `max_tokens` on these two routes will get empty answers. Allow about a thousand tokens.
- Not covered, as before: thinking mode, long multi-turn agent sessions, sustained throughput, full-context quality.

Machine-readable: [results/flint-ripple-budget-rerun-2026-11-10.json](results/flint-ripple-budget-rerun-2026-11-10.json).
