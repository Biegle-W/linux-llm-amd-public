# Temporary 32 GB SSD-streaming qualification — October 28, 2026

**Current availability — October 29:** Qwen27B/SGLang is qualified and enabled after the ROCm multicast/VRAM-guard correction; eight working profiles remain available. Ornith, both DeepSeek XS routes and Qwen Flash Next/Strata remain paused until the owner reports more RAM. Actual spill protection and all other guards remain. [Fix and verification](SGLANG-VRAM-GUARD-FIX-2026-10-29.md).

Native status: **native_tests_complete**. Normal guarded API integration: **complete**.

Activated temporary 32 GB profiles: **Qwen / Strata, GLM / Maya**. Held at the exact prior 64 GB profile: **DeepSeek XS / Maya, DeepSeek XS / Strata**. Each activation passed native safety/functional/performance/near-window/history checks and normal guarded authenticated JSON/SSE/tools/~8K/history checks. The exact 64 GB preimages are retained; restore only after at least 60 GiB physical RAM is visible and inference is idle. All other settings, guards, coordinator services and paused schedules remain.

Current host: 32 GB nominal / 30.56 GiB OS-visible, two RX 7900 XTX cards. Only profiles that pass native qualification and authenticated normal API checks may be activated. The exact prior 64 GB profiles are retained for restoration when at least 60 GiB physical RAM is visible and inference is idle.

| Model | Candidate tier | Short native stage | Code t/s | Prose t/s | Fresh prefill t/s | Fresh TTFT s |
|---|---|---|---:|---:|---:|---:|
| Qwen / Strata | 8 GiB experts / 20 GiB cap | passed | 36.42 | 37.35 | 1013.6 | 8.098 |
| Qwen / Strata | 12 GiB experts / 22 GiB cap | passed | 70.15 | 50.95 | 1155.8 | 7.104 |
| GLM / Maya | 8 GiB experts / 20 GiB cap | passed | 5.76 | 5.66 | 440.9 | 18.922 |
| GLM / Maya | 12 GiB experts / 22 GiB cap | passed; normal admission blocked | 6.42 | 6.68 | 464.6 | 17.771 |
| DeepSeek XS / Maya | native auto / 20 GiB cap | preflight blocked | — | — | — | — |
| DeepSeek XS / Maya | native auto / 22 GiB cap | passed | 2.76 | 2.12 | 684.1 | 11.993 |
| DeepSeek XS / Maya | native auto / 20 GiB cap | passed | 2.91 | 1.72 | 691.1 | 11.834 |
| DeepSeek XS / Strata | native auto / 20 GiB cap | passed | 2.95 | 1.86 | 185.6 | 44.067 |
| DeepSeek XS / Strata | native auto / 22 GiB cap | preflight blocked | — | — | — | — |
| DeepSeek XS / Strata | native auto / 22 GiB cap | passed | 3.29 | 1.66 | 185.2 | 44.159 |

All candidate rows above are **MoE models with SSD streaming**, measured October 28. Configured context and associated storage remain:

| Model | Context tokens | Storage GB | Location |
|---|---:|---:|---|
| Qwen / Strata | 262,144 | 128.14 | NVMe Strata/models, Strata/packs, Strata/mtp |
| GLM / Maya | 32,768 | 97.42 | NVMe Maya/Maya-S-v2-IQ2_XXS |
| DeepSeek XS / Maya | 32,768 | 281.87 shared | NVMe Maya/DeepSeek-V4.1-Flash-1017-GGUF |
| DeepSeek XS / Strata | 32,768 | 281.87 shared | Same XS weights; NVMe Strata/DeepSeek-V4.1-Flash-1017 metadata |

Retained engine pins:

| Model / engine | Engine version | Source commit |
|---|---|---|
| Qwen / Strata | 0.1.49.2 | `7dd5cf18e68c639a8773e096c5c79f971ea2a9f5` |
| GLM / Maya | 1.1.26 | `f26d8bab43f9b10f0475986b541dc46ada45285e` |
| DeepSeek XS / Maya | 1.1.26 | `f26d8bab43f9b10f0475986b541dc46ada45285e` |
| DeepSeek XS / Strata | 0.1.49.1 | `8183c6b67162340c09b67360860177c577a65f2e` |

The two DeepSeek rows share one weight set; do not add their storage twice. **VRAM only models** and **MoE models with CPU RAM offload** retain their existing settings and dated measurements in the current benchmark report; this trial does not remeasure them.

Three timed samples per task follow one excluded warmup; three fresh ~8K marker requests check prefill. Decode is measured over SSE after the first token; prefill uses engine timing. Individual measurements and native timings are retained in the aggregate JSON.

Each eligible winner also needs independent near-window marker recall and a history follow-up. Functional checks cover arithmetic, logic, records, JSON, tools and generated merge code. Saved merge functions receive 64 deterministic extra input cases. These are limited synthetic quality checks.

| Model | Selected candidate | Near-window input/history tokens | Normal API outcome |
|---|---|---:|---|
| Qwen / Strata | strata-iq3-profile-large | 257986 / 258033 | activated |
| GLM / Maya | maya-glm-profile-small | 30982 / 31016 | activated |
| DeepSeek XS / Maya | none | not run; selection held | not run; native selection held |
| DeepSeek XS / Strata | none | 30993 / 31025 (retained prior proof) | not run; native selection held |

A retained prior near-window proof does not authorize activation after an expanded comparison produces a performance hold. Both DeepSeek engine variants passed short functional checks at both memory tiers; a mixed performance hold is separate from a quality failure or a claim that 32 GB cannot run the model.

GLM / Maya: the faster larger cache tier passed native tests but failed unchanged normal-launcher RAM admission before worker startup. Its exact prior profile was restored. The smaller already-benchmarked tier passed separate near-window/history and normal API checks and was activated; no short timing samples were repeated.

Sampled native safety evidence for eligible selected arms plus their independent confirmations:

| Model | Min host available GiB | Min free VRAM GiB/card | Peak scope RAM GiB | Peak worker swap GiB | Peak VRAM spill bytes |
|---|---:|---:|---:|---:|---:|
| Qwen / Strata | 6.47 | 5.24 / 6.17 | 19.44 | 0.52 | 0 |
| GLM / Maya | 13.19 | 7.59 / 7.63 | 18.00 | 1.84 | 0 |

These are sampled minima/maxima, not guarantees about unsampled transients. Worker swap is allowed under loading-swap-v3; rates/pressure alone do not stop work. Enforced scope limits and normal API verification are recorded separately.

Historical 64 GB references (October 25, original hardware; retained production builds):

| Model | Code t/s | Prose t/s | Fresh prefill t/s |
|---|---:|---:|---:|
| glm-5.3-flash-maya | 19.04 | 15.52 | 539.3 |
| deepseek-v4.1-flash-1017-maya | 22.59 | 13.31 | 634.1 |
| deepseek-v4.1-flash-1017-strata-xs | 18.67 | 13.59 | 184.9 |
| qwen3.8-flash-next-iq3_xxs | 75.52 | 47.44 | 1206.2 |

Sequential small sample; cache, execution order, desktop activity, thermal/power and storage effects remain. Synthetic checks establish sampled functional/recall behavior, not general quality equivalence. Historical 64 GB results are informational, not a matched causal RAM comparison.

All pinned engines, weights, precision, configured contexts, single-request execution, thermal logging, coordinator services and paused schedules are preserved. The smaller tiers enforce actual MemoryHigh 18/20 GiB and MemoryMax 20/22 GiB with at least 3 GiB admission headroom above the cap; the legacy 64 GB admission remains for untagged profiles. Swap rates and pressure are advisory under loading-swap-v3.

A preflight block before launch is an unavailable resource measurement. A tier unable to complete independent qualification is excluded from full eligibility; an already benchmarked smaller tier must complete those gates before activation. Failed normal API canaries restore their exact prior profile.

[Individual aggregate measurements](results/ssd-streaming-32gb-2026-10-28.json).
