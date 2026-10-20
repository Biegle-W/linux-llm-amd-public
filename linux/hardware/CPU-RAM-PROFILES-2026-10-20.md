# i9 / 64 GB validation — October 20, 2026

> Subsequent October 20 retirement: Muse Q4 and Super Q4 are removed. This dated
> validation keeps its original tested catalog and measurements; use the
> [current report](CURRENT-AMD-BENCHMARKS.md) for active profiles.

Current hardware is Intel i9-13900KS (8P+16E, 24 cores/32 logical CPUs),
64 GB installed (61.51 GiB OS-visible), two RX 7900 XTX 24 GB, MSI MPG Z690
CARBON WIFI. Both GPUs use motherboard CPU PCIe4 x8/x8; the purchased PEX88096
switch remains pending installation and validation. Direct P2P remains disabled.
Layer splitting is used by llama.cpp/Strata; SGLang/vLLM use TP2 host transport.

## Runtime updates

llama.cpp HIP/Vulkan moved from 31288c9 to 4c3c5810 after all five original
profiles, both Super quants, the six-model Q4 catalog integration and production
HIP/Vulkan smoke tests passed. Profile throughput was performance-neutral within
noise; the retained benefits are upstream fixes including
[50/50 SLRU expert caching](https://github.com/ggml-org/llama.cpp/pull/30637),
[HIP attention race fix](https://github.com/ggml-org/llama.cpp/pull/30573),
[Stream-K cap](https://github.com/ggml-org/llama.cpp/pull/30553) and
[SWA checkpoints](https://github.com/ggml-org/llama.cpp/pull/30666).

vLLM is `0.32.1rc1.dev36+ge68efc685.rocm72`, replacing dev329. The wheel SHA-256
is `68cb33f115094f816077c193f8b51eac0ea01052254653b9b336e534d7a71f79`.
Its local fixes were retained; 64,033-token retrieval and prefix reuse passed.
It was first validated on the prior i5 hardware, then measured on the i9.
No speedup is claimed. SGLang f84475cc and Strata 477ac13c are unchanged.

## Production choices and precision trade-off

Super Q4 and IQ3 are both selectable by current configuration. Their files
remain on disk; neither quant was deleted. The current catalog has eleven profiles. Strata keeps IQ3_XXS and a
13.5 GiB expert budget. A higher RAM capacity does not require raising this cap.
Both configured model IDs retain their existing launchers; DSH is separate.

Super Q4 uses native HIP layer split 1:1, 32,768 total context, 47.424 GiB
CPU expert backing, 4,096 MiB total GPU hot-expert-cache ceiling, six decode/
prefill threads, batch/microbatch 512/128, Q8 K/V, `load-mode=none`,
`cache-ram=0`, checkpoints 0 and MTP off. CPU-backed experts are uploaded for
GPU execution on cache misses; this differs from Strata's CPU expert path.
The current source-revision measurements below used the isolated candidate at
`4c3c5810f87efe177949f1b85ae509d38a2a311f`, followed by a separate rebuild at the production paths.
The normal-launcher checks record the actual production binary fingerprint and
settings; they are functional checks, not newly timed benchmark trials.
Concurrent model copying, hashing and downloads overlapped these candidate runs
and ended at 2026-10-20T11:03:39.139290+00:00. RAM minima and timing differences
cannot be attributed solely to the engine build.

| Quant / workload, three-trial median | Input / output tokens | Native PP t/s | External TTFT s | External SSE decode t/s |
|---|---:|---:|---:|---:|
| Super Q4 code | 8,108 / 256 | 43.26 | 187.432 | 7.86 |
| Super Q4 prose | 8,111 / 256 | 44.17 | 183.653 | 8.19 |
| Super IQ3 code | 8,108 / 256 | 98.21 | 82.566 | 15.90 |
| Super IQ3 prose | 8,111 / 256 | 97.84 | 82.911 | 16.95 |

These are uncached fixed ~8K prompts, not short-prompt TTFT. Q4's heavier quant
and different placement use approximately twice the input-processing time and
half the decode rate here. They are complete-profile results, not a CPU-only
A/B or a general quality measurement. Both precision choices remain selectable; IQ3 is faster in these complete-profile trials.
No canonical short-prompt timing was saved for this selected Q4 configuration;
short numbers from rejected 64K experiments must not be substituted.

Super Q4 retrieved all markers at 28,546 input /
22 output, native PP
47.13, external TTFT
605.694 s. This validates that retrieval
workload, not full-window sustained generation or general long-document accuracy.
Minimum available RAM was 3.056 GiB;
peak whole-card VRAM was 21.222 /
19.193 GiB; owned swap/spill were zero. The sampled GPU0 peak left about 2.76 GiB free, a brief dip below 3 GiB that did not trip the unchanged three-sample guard. The later production normal-launcher proof passed with more whole-card headroom; no guard threshold was lowered.

## Rejected Q4 configurations

The 64K trials were stopped by the unchanged 3 GiB RAM/VRAM guards. One
3,072 MiB cache case reached about 56.8K of its 60K target before the GPU0
reserve failed. Moving another expert layer to RAM fixed GPU headroom but then
failed the RAM guard. No failed or interrupted case is an activated capacity or
completed benchmark. The selected configuration retains 32K; its 28,546-input retrieval pass does not
establish full-window sustained generation.
Additional CPU threads did not establish a speed benefit in one-trial controls.
These stops unloaded only owned inference workers; no model weights were removed.

## Shared-NVMe relocation and model integrity

Strata streaming assets use the new shared NVMe. Maya downloads are staged
there; its runtime is not yet installed or validated. Other active
llama.cpp MoEs use resident CPU expert buffers and GPU hot-expert caches, with
`load-mode=none`; header inspection found no disk-streamed PLE/Engram tables
in those models. Their SATA paths remain unchanged.

The standalone Strata app and managed backend use one shared asset set. The
main GGUF shards, MTP binary assets and dense pack matched across the old copies.
A generated expert-pack mismatch was checked against the exact reference packing
of every expert byte from the GGUF (48 layers,42,912,972,800 bytes). The app pack
matched the complete reference SHA-256
`e76956703f0cb960fa959cc0c33b0e38284ee98c8eb360417c74e7238c7bf005`;
the old managed pack did not. The canonical NVMe pack uses the reference-matching
copy, with a second destination hash verification. The root cause of the old
pack difference was not established. Unique vision/conversion assets are retained.
No re-quantization was performed. Old SATA-era timings retain their original
workload and cannot be presented as measurements of this corrected NVMe asset set.

## Strata pool comparison

| CPU pool | Load s | 8K PP t/s | Short decode, code / prose t/s | Minimum available RAM GiB | Near-window input / output |
|---|---:|---:|---:|---:|---:|
| 6 workers / all CPUs | 36.15 | 914.3 | 76.61 / 53.35 | 37.53 | 257,984 / 256 |
| 7 workers / p-cores | 36.14 | 909.5 | 82.50 / 53.80 | 37.61 | 257,984 / 256 |

Selected **6 workers / all CPUs**, retaining **13.5 GiB**, IQ3_XXS,
native 262,144, both GPUs and unchanged reserves/guards. Selection required
functional and near-window passes, prefill within 5% of the faster pool and
at least 5% geometric-mean decode gain to replace the baseline; three trials do
not establish statistical significance.

| Pool / fresh near-window input | Native PP t/s | Native decode t/s | Native prompt duration s | Total wall s | External TTFT |
|---|---:|---:|---:|---:|---|
| 6 workers / 257,984 input | 1000.1 | 67.1 | 257.963 | 263.613 | Not measured |
| 7 workers / 257,984 input | 997.1 | 71.8 | 258.728 | 263.000 | Not measured |

These probes returned a complete response rather than external SSE first-token timing; native prompt duration and total wall time are not TTFT. Both generated 256 tokens. The selected six-worker follow-up processed 258,266 total input, reused 257,977 tokens and completed in 1.732s total. The seven-worker follow-up reused 258,240 tokens and completed in 0.604s total; these different cache hits are not a fresh-prefill speed comparison.

Both pools passed fresh near-window retrieval/code plus a full-history follow-up.
The selected test used **257,984 input / 256 output**.
All markers were found in both requests. The follow-up reported
**257,977 cached input tokens**;
cache reuse is distinct from fresh prefill. Worker swap and VRAM spill were zero.
The exact timings, hashes, memory extrema, tests and all pool trials are in the
[current numeric record](results/dual-amd-i9-64gb-2026-10-20.json).

Normal visible-terminal launch subsequently passed arithmetic, tools/results,
JSON and SSE over authenticated loopback/LAN/Tailscale host self-access.
Eleven enabled profiles were listed, and unauthenticated catalog access was
rejected. This was not a separate remote Windows/phone test or a new speed run.


Each candidate uses the retained Strata HIP 0.1.45 revision
`477ac13cbe8e582c20484871ce459d20d82df09d`, both cards, layer split 26/overlap,
2,048-token prefill, MTP3, INT8 KV with 32K GPU residency and full host backing,
7/8 GiB startup reserves, worker-only no-swap scope and continuous latched guards.
The probe runs with `strata/.venv/bin/python` because its tokenizer imports
`regex`; the previous system-Python failure happened before an inference probe.
Native 262,144 allocation and actual near-window input are reported separately.
No RoPE extension is enabled. Earlier same-hardware 13.5/20 GiB controls used the OLD SATA pack, before the
asset-integrity correction. Their results were within noise and remain separate
from the corrected-NVMe pool tests;20 GiB is not a selected production optimization. Neither cap
forces that amount of allocation; inspect measured expert residency/file reads.

Selection is declared before testing: both pools must pass functional checks,
near-window marker/code plus cached-history follow-up, and guards. Candidate
prefill must remain within 5% of the faster pool, and a new CPU pool must improve
geometric-mean code/prose median decode by at least 5% to replace the baseline.
Three requests per task do not establish statistical significance.

## Sources and limits

This report's numbers are local saved measurements; forum reports are separate.
[Both-forum and upstream source ledger](FORUM-OPTIMIZATION-SOURCES.md) records
[lcz.me resident-expert discussion](https://lcz.me/topic/2027/13),
[older Strata HIP tuning](https://lcz.me/topic/2032/19),
and [Level1Techs CPU/memory discussion](https://forum.level1techs.com/t/9950x3d-reviewed-and-benchmarked-tokens/227386).
The latter concerns different CPU/model hardware and supplies no local speed.
[llama.cpp expert cache](https://github.com/ggml-org/llama.cpp/blob/4c3c5810f87efe177949f1b85ae509d38a2a311f/src/llama-moe-cache.cpp)
and [Strata affinity implementation](https://github.com/Niko1221/Strata/blob/477ac13cbe8e582c20484871ce459d20d82df09d/src/program/generate.cpp)
explain the tested mechanisms; core count alone does not establish the fastest setting.

[Current results index](results/README.md) · [Complete benchmark history](BENCHMARK-HISTORY.md)
· [Linux/Windows handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md).
Historical i5/32 GB and NVIDIA records retain their original dates/builds.

## Verified duplicate removal

Removed only 85 manifest-listed old Strata source files after the runtime gates passed:
119.336 GiB from the primary NVMe and
112.807 GiB from Shared SATA,
232.143 GiB logical total. Both launchers
point directly to the canonical shared-NVMe weights; all unique app assets and
all Super IQ3/Q4 weights remain. Observed free-space changes are retained in
[the storage record](results/streaming-storage-2026-10-20.json).

## Same-hardware selection evidence and historical results

The earlier 31288c9 i9/64 GB comparison measured Q4 PP 44.53/44.44 and decode 7.76/7.97,
versus IQ3 PP 97.18/96.41 and decode 15.26/16.22. These selection runs remain in
[the separate baseline record](results/dual-amd-i9-baseline-2026-10-20.json).
They are not substituted for the current 4c3c5810 table above. All baseline Strata
numbers there used the old SATA pack, before relocation/correction.

The [October 19 i5/32 GB report](AMD-BENCHMARKS-2026-10-19.md) is preserved unchanged.
Historical NVIDIA/Windows configurations and measurements are separate snapshots.
