# Maya-XS and matching DSpark — October 23, 2026

**User-requested isolated test; production remains Maya-S with DSpark off.**
Maya **1.1.24 /25deec505b525212e05faa58697d9d2b7d17fdb3**, exact deployed
HIP binary SHA256 `4a3b77e997d88498f9fd140867af227553f9c651c4693c0a31b710620bdcd814`,
retained ROCm7.2.3, i9-13900KS,64GB installed/61.51GiB visible and **two RX7900XTX24GB**.
CPU PCIe4x8/x8; purchased switch is not installed, direct P2P unvalidated.
No engine/driver upgrade, production quant switch or new active profile occurred.

## Measured results

| Maya1.1.24 /32K /ROCm7.2.3 | Code decode t/s | Prose decode t/s | Native fresh PP t/s | Fresh TTFT s |
|---|---:|---:|---:|---:|
| XS DSpark off | 20.45 | 15.56 | 428.7 | 14.714 |
| XS **matching DSpark on** | 31.28 | 15.36 | 445.5 | 14.156 |
| Saved same-day Maya-S, no DSpark | 6.42 | 6.78 | 299.0 | 21.062 |

Draft on relative to XS off: code decode tps +52.9%, prose decode tps -1.3%, native prefill tps +3.9%, fresh ttft seconds -3.8%.
For the single1024-output HTML probe, decode is **10.95→12.54t/s**.
Longer-code behavior differs substantially from the short merge-function benchmark.
Draft acceptance: **585/621 (94.2%)** on timed code; **164/209 (78.5%)** on timed prose.
The S row is the [saved same-day source1.1.24 reference](MAYA-UPDATE-2026-10-23.md),
with the same short/fresh method but a different quant and separate session.
It is not an interleaved, equal-quality comparison. The NVIDIA screenshots are
other people's reports with different hardware/workloads. Their 70 t/s figures
are not used as local measurements or like-for-like controls.

## Quant and memory settings

XS uses **IQ1_S** routed experts and Q8_0 dense weights; its own `dspark-xs2.bin/.json`
uses IQ2_XXS draft experts (4,251,725,568-byte binary), not S's older FP4 drafter.
[Official quant card](https://huggingface.co/peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF/blob/d1fc01009f21e26157acb6858c315d0365483b72/README.md)
and [pinned installer manifest](https://github.com/mw00/project-maya/blob/25deec505b525212e05faa58697d9d2b7d17fdb3/tools/ds4/download_gguf.json).
The publisher reports original top-token agreement87.5% for XS versus92.6% for S;
this measures agreement on its text set, **not downstream benchmark accuracy**.
XS is a quality tradeoff; these smoke tests do not establish equal quality.

Both arms use32,768 context,24CPU threads,mapped CPU experts plus GPU hot caches,
`DS4_IQ_Q8K=0`, `DS4_STREAM=0`, copied identical expert-routing seeds and both GPUs.
`--tp 2` falls back to width1/layer groups because the2304-wide expert cannot split
into two256-value block groups. Both GPUs serve the model; this is **not true TP2**.
Native reserve8192MiB/card, actual loaded startup minimum6GiB/card,52G/no-swap
worker scope, continuous3GiB/hard1.5GiB VRAM floors and latched owned-worker-only
shutdown are unchanged. No desktop apps, DSH, gateway or hub were stopped.

The native logs report87.2GB of routed experts on the mapped CPU lane without
drafting and91.3GB with drafting. These are logical mapped weights, not fully
resident RAM. Reserves leave roughly32GiB across the cards for weights/caches/
workspace;52GiB host scope also includes non-expert allocations/file cache.
This is not a fully GPU/RAM-resident XS configuration. Native CPU-lane expert
percentages are retained per request; they are not CPU utilization or measured
SSD miss rates. No isolated disk/PCIe bottleneck attribution is claimed.

## Validation and timing limits

Both arms passed: streaming arithmetic, JSON, synthetic tool round-trip, fresh-marker probes,
**31,497-input retrieval and 31,529-input full-history follow-up** in each arm. Exact input/output/cache counts,
actual placement, memory minima, effective flags and library SHA256 are in
[the numeric evidence](results/maya-xs-dspark-2026-10-23.json).
All three small greedy answers matched between drafting off and on.
This is a consistency smoke check, not broad losslessness or model-quality validation.
No external internet tool was invoked. XS was not added to the normal UI/API catalog;
normal production Maya-S's previous Desktop/frontend/API validation remains unchanged.

Three timed short requests/task,256-output cap,temp0.6/top_p0.95/seed42/thinking off;
one excluded warmup/task. The code-trial range was 18.30–23.89 t/s off and
28.87–35.22 t/s on; fresh PP ranged 234.1–453.6 off and 242.4–449.9 on. Three fresh common-record prompts,64-output cap,greedy,
zero cached tokens; the common records are ~8K under the Qwen tokenizer but ~6.3K
under DeepSeek. Cold model loading is excluded. Native PP is engine prompt-phase
throughput; external TTFT is API submission to first SSE output; decode is
`(completion_tokens-1)/(stream_end-first_output)`. Starts are sequential off→on,
not thermally equalized or interleaved. All trials remain in the numeric record.

- xs-none code: inputs 22, 22, 22; outputs 256, 256, 256.
- xs-none prose: inputs 16, 16, 16; outputs 256, 256, 256.
- xs-none fresh: inputs 6297, 6304, 6299; outputs 17, 17, 17.
- xs-draft code: inputs 22, 22, 22; outputs 256, 256, 256.
- xs-draft prose: inputs 16, 16, 16; outputs 256, 256, 256.
- xs-draft fresh: inputs 6299, 6300, 6301; outputs 17, 17, 17.

### Longer output probes

One request/task/arm,1024-output cap; these are individual observations, **not medians**.

| Arm/task | Input tokens | Output tokens | Decode t/s | TTFT s |
|---|---:|---:|---:|---:|
| xs-none code | 39 | 1024 | 10.95 | 2.768 |
| xs-none prose | 30 | 1024 | 13.60 | 2.375 |
| xs-draft code | 39 | 1024 | 12.54 | 2.968 |
| xs-draft prose | 30 | 1024 | 13.79 | 2.178 |

## Correctness and thermal evidence

Focused tests use the retained source/object dependencies with a separate test
translation unit; production source/binaries were untouched. IQ1_S/IQ1_S and
IQ2_XXS/IQ2_XXS token/prompt/CPU/streamed-lane checks, including actual5120/2304
expert dimensions, passed on **each physical card**. Existing mixedQ4_K/IQ4_XS
exclusions remain; this does not admit those formats or weaken production checks.

| Full arm lifecycle | Samples (~1s) | GPU0 /GPU1 peak junction °C | CPU package peak °C | Minimum free VRAM GiB/card |
|---|---:|---:|---:|---:|
| xs-none | 518 | 97.0 / 86.0 | 100.0 | 7.56 / 7.55 |
| xs-draft | 486 | 99.0 / 86.0 | 100.0 | 7.56 / 7.44 |

Lifecycle coverage includes loading, benchmark, long probes and cleanup. Nested
per-request/benchmark logs overlap; do not add their sample counts. All available
edge/VRAM temperatures,power,clocks,fans and SMU flag counts are retained numerically.
Sampled peaks can miss transients; flags do not measure time throttled or establish
speed lost to heat. Missing sensors are not inferred. Zero owned swap/VRAM spill
is required for the passing arms.

Existing CPU admission/ownership and web-security regressions passed **14 tests
in each repository**; syntax/JSON/relative-link and staged privacy checks accompany
publication. A sandbox-only HTTP attempt could not open local sockets; host reruns
passed. This was a test-environment restriction, not a model failure.

## Storage and reproducibility

Three XS GGUF shards and matching xs2 drafter: **119,593,334,090 new bytes** on shared
NVMe. Reuse the existing161,284,798,884-byte pair of S Engram shards and existing vision
pack. [Pinned assets/reuse map](../maya/deepseek-xs-models.json). Weights stay outside Git.

The initial assumption of identical **whole GGUF files** failed checksum and stopped
before any inference. Both shards have different192-byte split headers. For each,
full local S SHA matches the published S object, and **official XS header + entire
local S payload hashes to the published XS SHA**. Tensor names/types/shapes/offsets
match. This verifies unchanged payload identity without downloading another161GB.
The upstream `pack_gguf.py --shards` accepts the three XS files plus two original S
files; only the pack's two file references are made relative to `../Maya-S/`.
Tensor records and weight bytes remain unchanged. No hardlinks/symlinks or fake XS
weight files are created on exFAT. Linux/Windows must generate their own pack paths;
do not run an unattended stock setup that redownloads the absent XS-named Engram copies.

For a reproduction, download `maya/deepseek-xs-models.json`'s pinned files using
`maya/download-models.py --root <shared-nvme>/LLM-Models/Maya --manifest maya/deepseek-xs-models.json`.
Verify shared asset checksums/payload mapping, then build the metadata with the
pinned converter and explicit `--drafter ../dspark/dspark-xs2.json`. Copy the S
profile to an isolated config, change only pack/tokenizer/log/copied routing seed
and DSpark off/on; retain all dual-GPU,context,CPU and guard values. The experimental
IQ1_S format remains outside the production admission list. Never bypass guards
by directly starting an unmonitored engine. Private test helpers/raw outputs are
retained under ignored `hardware/generated/`; only curated evidence is published.

Forum review: [LCZ historical Maya discussion](https://lcz.me/topic/2195/9) concerns
older1.0.11/NVIDIA/64K and changed sampling; the current fetch was unavailable.
[Level1Techs speculative-decoding discussion,October13](https://forum.level1techs.com/t/ultimate-2x-r9700-guide-for-qwen-3-8-27b-mxfp4-200t-s-c-1-500t-s-at-c-8/257789?page=3)
concerns RDNA4/Radiance, not a matched XS/gfx1100 recipe. Neither supplies local
measurements or settings adopted here. Primary implementation is the pinned Maya
source and quant manifest above; [source ledger](FORUM-OPTIMIZATION-SOURCES.md).
