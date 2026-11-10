# All-models tool call and quality rerun — November 9, 2026

Owner request: "rerun all the test, using the same standard for tool call and also check for quality of work, drop the old memory guard". Same layout as the [November 7 working setup](AMD-WORKING-SETUP-2026-11-07.md), same boot `d81d1623`, patched kernel `7.0.14-42-vmpt1`. [Structured result](results/AMD-ALL-MODELS-TOOL-AND-QUALITY-2026-11-09.json).

**All 12 enabled routes passed** the [November 7 tool-call standard](AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.md), and every route finished both quality suites with no request errors.

The tool-call standard is one short DSH read-tool round trip per route (tool call, then an answer from the tool result). It runs under the guarded stage harness, one route at a time, and stops at the first fault. Four fresh two-card peer checks ran before each attempt: capability, local, direct/IPC integrity, and RCCL P2P/IPC.
- Every route made exactly one `read` call, and the call completed.
- Every guard passed: owned cgroups empty, no remaining KFD clients and no VRAM spill.
- No amdgpu kernel errors since the run started, and AER 0/0 on both GPUs.

The old memory guard was removed first (see the [changelog](CHANGELOG.md)). This run used only the owner policy: 1 GiB RAM and 128 MiB VRAM per card.

## Tool call and quality

| Route | Engine | Load s | Tool prompt tokens | Tool TTFT s | Prefill tok/s | Decode tok/s | Nov 7 decode | Tool step s | Answer step s | Max owned swap MiB | 54-item suite | 64-item suite | Suite time s | Capped answers |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `empero-qwen3.8-35b-a3b` | llama.cpp | 47.7 | 6,428 | 2.22 | 2,893 | 173.3 | 174.5 | 2.68 | 0.31 | 0 | 53/54 | 62/64 | 124 | 0 |
| `flint-40b-a2.5b` | llama.cpp | 50.7 | 5,895 | 1.27 | 4,653 | 64.0 | 64.8 | 3.94 | 1.86 | 0 | 43/54 | 36/64 | 263 | 36 |
| `ornith-1.5-122b` | llama.cpp | 167.9 | 6,419 | 10.66 | 602 | 11.6 | 11.3 | 18.01 | 4.40 | 1,302 | 53/54 | 62/64 | 970 | 0 |
| `qwen3.8-27b-vllm` | vLLM TP2 | 89.5 | 6,420 | 3.64 | 1,766 | 155.1 | 153.7 | 4.13 | 0.49 | 0 | 52/54 | 62/64 | 198 | 2 |
| `qwen3.8-27b-sglang-dflash2` | SGLang TP2 | 34.4 | 6,705 | 3.86 | 1,736 | 211.2 | 218.6 | 4.24 | 0.41 | 0 | 52/54 | 62/64 | 120 | 2 |
| `nemotron-3.5-bolt-vllm` | vLLM | 219.4 | 6,978 | 3.55 | 1,963 | 40.1 | 29.6 | 5.57 | 0.94 | 0 | 52/54 | 61/64 | 410 | 0 |
| `sage-a1.5` | vLLM | 88.5 | 6,395 | 1.14 | 5,619 | 140.0 | 136.5 | 1.65 | 0.32 | 0 | 51/54 | 61/64 | 169 | 2 |
| `ripple-65b-vllm` | vLLM TP2 | 117.6 | 6,244 | 8.18 | 764 | 28.0 | — | 10.89 | 0.87 | 0 | 50/54 | 56/64 | 451 | 12 |
| `qwen3.8-flash-next-iq3_xxs` | Strata | 69.5 | 6,193 | 8.73 | 710 | 66.3 | 66.5 | 9.89 | 8.09 | 0 | 51/54 | 62/64 | 348 | 2 |
| `deepseek-v4.1-flash-1017-strata-unsloth-q1` | Strata DeepSeek | 140.1 | 6,323 | 57.21 | 111 | 5.6 | 3.3 | 75.74 | 12.46 | 318 | 54/54 | 62/64 | 1,514 | 1 |
| `deepseek-v4.1-flash-1017-maya-unsloth-q1` | Maya | 72.7 | 6,323 | 182.22 | 35 | 6.8 | 1.2 | 197.54 | 6.76 | 0 | 54/54 | 63/64 | 1,226 | 0 |
| `glm-5.3-flash-maya` | Maya | 119.0 | 5,986 | 105.75 | 57 | 5.2 | 2.1 | 116.19 | 15.94 | 3,365 | 53/54 | 62/64 | 674 | 0 |

Columns are defined as on November 7:
- *Tool* is the first request: about 6.4K prompt tokens with 25 tool definitions. The model emits the read-tool call in 54–171 tokens.
- *Prefill tok/s* is prompt tokens divided by time to first token.
- *Decode tok/s* is output tokens divided by (step time − TTFT), measured on that short call.
- *Answer step* is the second request, which carries the tool result.
- *Nov 7 decode* comes from the [November 7 report](AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.md), which used the same formula.

The tool prompt is 600–700 tokens shorter than on November 7 (same 25 tools). This run did not establish why.

The quality suites are the 54-item suite and the harder 64-item suite from the [quant comparison](QUANT-QUALITY-COMPARISON-2026-11-08.md). Both ran through the hub at temperature 0 with thinking off, and answers were graded automatically.
- *Suite time* is the total time for both suites, cold load included.
- *Capped answers* counts answers that hit the item's token limit.

## What the numbers say

**Speed.** The nine GPU-resident routes are within about 3% of November 7, except two:
- Nemotron decode is up from 29.6 to 40.1 tok/s.
- Ornith's load is 16 s slower.

The three expert-streaming routes (both DeepSeek routes and GLM) decode 1.7–5.7 times faster than on November 7. That comes from the November 8 RAM-tier and reserve tuning ([report](GLM-DEEPSEEK-RAM-RESERVE-TUNING-2026-11-08.md)). The first request is still cold, though: 1–3 minutes before the first token on about 6K prompt tokens.

On 400-token hub answers these three routes reach 7.5–22 tok/s (November 8). The 5–7 tok/s here is measured on a 54–104-token tool call.

**Quality.** All routes except Flint and Ripple score 51–54 on the 54-item suite and 61–63 on the 64-item suite.
- The DeepSeek pair is strongest: 54/54 on both routes, and 62/64 and 63/64 on the harder suite.
- Both DeepSeek routes refused the same long-document question ("can't determine that from the register"). Strata DeepSeek also wrapped a raw-JSON answer in a code fence.
- On November 8 both DeepSeek routes scored 64/64. The one or two misses here are run-to-run variation at temperature 0, not a regression in the files.
- GLM scored 62/64, the same as on November 8.
- Common misses across many routes were the same hard items: m03 (a multi-step arithmetic answer), r10 (spelling a word backwards) and c07 (one coding task).

**Flint and Ripple scores are mostly a token-budget effect, not wrong answers.** Both keep reasoning even though the suite asks for thinking off.
- On short-answer items (60-token limit), they use the whole budget reasoning and return an empty answer.
- This hit 36 Flint answers and 12 Ripple answers. Flint's reasoning text often already contains the right answer, for example "Fyodor Dostoe…" for Crime and Punishment.
- Where the budget is larger, they do well. Flint: 12/12 and 10/10 code, all tool and agent items. Ripple: 18/18 math, 12/12 code, 5/5 agent.
- Their scores here are not comparable with the other routes. The fair comparison was run on November 10 with a larger answer budget: Flint 51/54 and 62/64, Ripple 53/54 and 63/64 ([report](FLINT-RIPPLE-BUDGET-RERUN-2026-11-10.md)).

## Stops during the campaign (none were GPU faults)

| Attempt | Stop | Cause | Resolution |
|---|---|---|---|
| 1 | Route 10 (Strata DeepSeek) | The short-trial check still required 6 GiB free VRAM per card at startup, a leftover of the old guard. The route only needs the owner's 128 MiB, so the check refused a correct start. The controller had also left out the stage's `active-terminal` pointer. | `hardware/daily-update/short_trial.py` now checks `resource_policy.VRAM_RESERVE_BYTES`; controller fixed. The owner released the hold; route 10 passed. |
| 2 | Route 11 (Maya DeepSeek) | Maya refused to start: card 0 was below its 1 GiB startup floor. The owner's desktop session and a game held about 1 GiB of card 0. | The owner closed the game and released the hold; route 11 passed. |
| 3 | Route 12 (GLM) | Watchdog "supervisor heartbeat missing" 110 s into loading. GLM warms about 80 GB of expert tiers from `models/streaming` on the system drive (I/O stall about 42% over 5 minutes). The supervisor's sample and heartbeat writes go to the same drive and stalled for more than 6 s. No kernel faults, no spill, cleanup clean. | Owner choice: GLM reran with a **30 s heartbeat instead of 6 s**, with all other limits unchanged. This is the one deviation from the standard. GLM passed with a 119 s load. |

Each stopped attempt's files are kept next to the stage as `*.attempt1`–`*.attempt3`, with the hold records. The hold was released with a new owner approval each time.

ComfyUI was stopped for the run and restarted automatically afterwards. No GPU hold remains.

## Operational notes

- **Desktop GPU apps and Maya DeepSeek.** With about 1 GiB of card 0 used by the desktop or a game, Maya DeepSeek (2 GiB reserve, 1 GiB startup floor) refuses to start. That is safe, but close GPU-heavy desktop apps before using it.
- **GLM warm-up I/O.** The GLM warm-up saturates the system drive for about 2 minutes. Anything else that writes and syncs to that drive during warm-up, including the guarded harness, will stall. Moving `models/streaming` to another drive would remove the contention. Not done.
- **Owned swap.** Peak owned swap was 3.3 GB (GLM), 1.3 GB (Ornith) and 318 MB (Strata DeepSeek), all within policy. The lowest free VRAM was 0.5 GiB, on card 0 during Strata DeepSeek.

Not covered: thinking mode, long multi-turn agent sessions, sustained throughput and full-context quality.
