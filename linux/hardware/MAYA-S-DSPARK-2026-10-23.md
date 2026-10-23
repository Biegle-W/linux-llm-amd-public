# Maya-S DSpark retest — October23,2026

**Retain S with DSpark disabled. XS keeps its own matching xs2 drafter; GLM and all other profiles are unchanged.** Both DeepSeek API IDs remain selectable; the catalog stays at
three Maya/eleven total profiles. No weights were downloaded or deleted. Strata
remains the DSH default. Normal XS + matching DSpark worker intentionally left ready.

The user requested a fresh test on installed **Maya1.1.24 /25deec505b525212e05faa58697d9d2b7d17fdb3**,
exact native binary **4a3b77e997d88498f9fd140867af227553f9c651c4693c0a31b710620bdcd814**, ROCm7.2.3,
i9-13900KS/64GB (61.51GiB visible) and both RX7900XTX cards on motherboard
PCIe4x8/x8. The purchased switch remains uninstalled/unvalidated. DeepSeek uses
layer groups, **not true TP2**. No driver, source, binary, other engine or model
quantization was updated. [Pinned source](https://github.com/mw00/project-maya/tree/25deec505b525212e05faa58697d9d2b7d17fdb3).

## Method and selection rule

A1 no DSpark → B standard S DSpark → A2 no DSpark. Each arm uses the same copied
S expert-routing seed,32K/24CPUthreads/8GiB native reserves, at least6GiB actual
whole-card startup free,52G/no-swap scope and existing latched continuous guards.
`DS4_IQ_Q8K=0` and `DS4_STREAM=0` remain; CPU mapped experts and GPU hot caches
stay active. The candidate standard drafter is **dspark.bin,7,967,616,768bytes**,
not XS's IQ2_XXS dspark-xs2. Both S drafter files passed full published SHA256;
S's six shards had been fully checked in the preceding deployment task.
No source assertion/tolerance or admission/watchdog threshold was weakened.

The preregistered rule requires **>=5%** geometric mean improvement across
code decode, prose decode and native fresh prefill, with **no metric >5% slower**,
compared with the arithmetic mean of A1/A2 per-arm medians. All functional,
near-window and memory gates must pass. Three small deterministic answers are
compared as an extra consistency smoke; this is not broad quality/losslessness proof.

Maintained shared benchmark method: one excluded warmup/task, three timed
short-code/prose requests,256-output cap, temperature0.6/top_p0.95/seed42/thinking
off. Three fresh approximately8K Qwen-tokenizer record prompts become about6.3K
actual DeepSeek tokens,64-output cap, greedy, new salt and zero cached input.
All actual input/output counts, timings and seeds are retained in the numeric
record. External SSE decode is(completion_tokens−1)/(stream_end−first_output);
TTFT is monotonic submission→first content/reasoning. Native PP is the engine's
prompt phase, **not input divided by TTFT**. Cold load time is excluded from TTFT.
The order is sequential, not thermally equalized; three trials do not establish
statistical significance. Cache warming and control spread remain visible.

## Results

The first control benchmark completed successfully, then a missing import in the
follow-up test harness stopped the sequence. Its valid timings and full-arm
telemetry were preserved; a fresh guarded control load completed the missing
functional/greedy checks before the DSpark arm. No timing trial was overwritten
or selectively rerun. Original failed harness evidence remains private.

| Arm /32K | Code decode t/s | Prose decode t/s | Native fresh PP t/s | Fresh TTFT s |
|---|---:|---:|---:|---:|
| A1-none | 7.29 | 6.92 | 303.4 | 20.768 |
| B-dspark | 6.71 | 6.42 | 277.4 | 22.716 |
| A2-none | 6.59 | 6.61 | 292.0 | 21.577 |

Against the arithmetic mean of the two no-draft arm medians, DSpark changes code **-3.37%**, prose **-5.14%** and native prefill **-6.82%**; geometric mean **-5.12%**. Speed gate **fails**.

[All numeric trials and gates](results/maya-s-dspark-2026-10-23.json) preserve
partial or failed evidence. The older [1.1.17 DSpark rejection](DEEPSEEK-DSPARK-2026-10-20.md)
used128-output caps and different warmup/context probes. Do not attribute a
cross-version rate change solely to the new kernels. Upstream1.1.22 reports
improved S+DSpark verification on a Ryzen AI Max; that is different hardware,
not a locally reproduced universal gain. [Pinned changelog](https://github.com/mw00/project-maya/blob/25deec505b525212e05faa58697d9d2b7d17fdb3/CHANGELOG.md).
Existing forum/source background is in the [source ledger](FORUM-OPTIMIZATION-SOURCES.md);
no new forum-derived tuning change is deployed by this comparison.

## Functional and memory coverage

Arithmetic/SSE, JSON, synthetic tool round-trip, both GPU allocations and memory
telemetry are checked. Controls use~7K retrieval/history probes; the candidate
uses fresh near31.5K retrieval and cached full-history follow-up. Exact tested
counts/statuses remain in the numeric record;32K configured capacity alone is
not full-window/general-quality validation. No real internet tool or separate
remote peer was tested; vision remains unvalidated. Failed mixedQ4_K/IQ4_XS
kernels remain excluded. There is no approximate expert skipping.

All production files were frozen during the isolated comparison. Any S selection
change is made only after gates and normal visible terminal/nativeUI/authenticated
API integration; other profiles/defaults/guards stay unchanged. Only owned test
workers are stopped. DSH, hub, gateway and unrelated applications are preserved.

## Thermal coverage

| Arm | Recorded samples | GPU0/GPU1 peak junction °C | CPU package peak °C |
|---|---:|---|---:|
| A1-none | 450 | 87.0/74.0 | 98.0 |
| B-dspark | 652 | 94.0/77.0 | 98.0 |
| A2-none | 574 | 97.0/79.0 | 96.0 |
| A1 functional follow-up | 124 | 87.0/71.0 | 89.0 |

About1s sampling includes startup and available benchmark/functional probes.
A1 functional follow-up coverage is separate from its initial timed-arm coverage;
per-request timing has its own coverage. The numeric record preserves available
power/clocks/fans/SMU flag counts and missing sensors. Sampled peaks are not
continuous sensor maxima. Flags alone do not quantify a speed loss, and these
finite tests do not establish later production lifetime temperatures. Keep
historical thermal evidence attributed to its original workloads/builds.

[Both DeepSeek selections](MAYA-DUAL-DEEPSEEK-2026-10-23.md) ·
[Current handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md).
