# Dual-Radeon retry after Unsloth shutdown — October 17, 2026

The user closed Unsloth before this batch. About 25 GiB host RAM was available
at the start. Both RX 7900 XTX cards remain enabled; weights stay GPU-resident.
No driver, BIOS, power limit, clock or P2P override was changed.

## What was tested

The existing GPTQ W4A16 target and W4A16 DFlash2 drafter were retained.
SGLang uses the Radeon fork `f84475ccf593087df3d1da13c9e675eadee12352` plus the
recorded local patches, BF16 KV, TP2 and GPU prefix caching. vLLM uses
`0.32.0rc1.dev190+g3f1bcfd82.rocm723`, INT4 KV and MTP3. Both use the isolated
ROCm 7.2.3 stack and no-hostcall RCCL 2.27.7 through host transport.

Short code/prose results use the same two saved NVIDIA prompts as the
[earlier trial](DUAL-TUNING-2026-10-17.md), temperature 0.6, top-p 0.95,
seed 42, thinking disabled, 256 output tokens, one excluded warm-up and three
measured runs per task. Report medians. Approximate external SSE decode is
`(completion_tokens - 1) / (stream_end - first_output)`; speculative bursts
limit precision. Quality tests are separate from throughput tasks.

The forum-style test uses pinned `llama-benchy` **0.4.0**, source
`446dd42fde2ebbaa1d68a0dfe9dc1e5b833f95ad`: PP 2,048, maximum TG 128,
concurrency one, three runs plus warm-up, `--no-cache`, generation latency mode,
temperature zero and thinking disabled. PP is the tool's latency-adjusted
estimate, not an isolated GPU kernel measurement. Context depth 16,384 adds
2,048 prompt tokens plus the template; it is not a 16,384-token total input.
The initial completed runs used the tool's randomized book offsets. Paired
repair comparisons use `hardware/benchy-seeded.py` to fix NumPy offsets and
cache-avoidance UUIDs to seed 42; no global application UUID behavior changes.
The author did not publish matching book offsets, so this is not an exact replay
of their requests. Different sampling, kernels, host platforms and text can
change speculative acceptance substantially.

## Measured results

| Configuration | Context | Code median t/s | Prose median t/s |
|---|---:|---:|---:|
| SGLang dflash8-Simple-verify0-clean2 | 65,536 | 178.85 | 62.71 |
| SGLang dflash8-auto-verify0-clean2 | 65,536 | 179.23 | 62.02 |
| SGLang mtp2-auto-verify0-clean2 | 40,960 | 88.36 | 65.28 |
| SGLang mtp3-auto-verify0-clean2 | 40,960 | 104.80 | 66.05 |
| vLLM mtp3-Simple-verify0-clean2 | 65,536 | 79.16 | 42.50 |
| vLLM mtp3-auto-verify0-clean2 | 65,536 | 76.45 | 41.34 |
| SGLang dflash8-auto-verify1-walkfix-fixed | 65,536 | 205.59 | 71.84 |
| SGLang mtp3-auto-verify1-walkfix-fixed | 40,960 | 114.57 | 66.05 |
| SGLang dflash8-auto-verify0-final | 65,536 | 165.63 | 57.10 |

Unmodified `verify1` failed ordering and has no usable throughput result.
The MTP3 `clean2` case passed model and near-window checks; its first bench-tool
attempt failed on SGLang's unsupported streaming `return_token_ids=true` option.
Later tool runs override it with `return_token_ids=false`, using stream usage and
the local tokenizer. This was an API/tool issue, not a failed MTP3 model check.

The selected MTP3 repair measured about 9% higher code throughput than standard
MTP3 and 30% above MTP2, with similar prose speed. Repaired DFlash2's code/prose
medians were about 15%/16% above its first standard run. The final standard repeat
was slower again (165.63/57.10), illustrating run-order/thermal/desktop variation;
these are measured workload results, not universal gains. vLLM Simple improved
both short medians by about 3.6%/2.8% versus auto; it is selected only for vLLM.
SGLang Simple did not improve the initial DFlash2 pair meaningfully.


| Configuration | Depth | PP estimate mean t/s | Decode mean ± std t/s |
|---|---:|---:|---:|
| sglang-dflash8-auto-verify0-clean2 | 0 | 1614.20 | 85.13 ± 11.89 |
| sglang-dflash8-auto-verify0-clean2 | 16,384 | 1385.21 | 87.44 ± 32.73 |
| vllm-mtp3-auto-verify0-clean2 | 0 | 1102.58 | 38.54 ± 2.93 |
| sglang-dflash8-auto-verify1-walkfix-fixed | 0 | 1575.97 | 79.61 ± 7.71 |
| sglang-dflash8-auto-verify1-walkfix-fixed | 16,384 | 1310.23 | 93.67 ± 13.62 |
| sglang-mtp3-auto-verify1-walkfix-fixed | 0 | 1488.15 | 80.86 ± 0.89 |
| sglang-mtp3-auto-verify1-walkfix-fixed | 16,384 | 1281.71 | 78.73 ± 4.42 |
| sglang-dflash8-auto-verify0-final | 0 | 1572.44 | 77.34 ± 3.21 |
| sglang-dflash8-auto-verify0-final | 16,384 | 1345.02 | 91.45 ± 24.26 |

The paired final standard/repaired DFlash2 runs used identical seeded text.
Repair changed mean decode from 77.34 to 79.61 at depth 0 and 91.45 to 93.67
at depth 16K: only about 2–3%, within substantial sample variation. PP was nearly
unchanged at depth 0 and about 2.6% lower at 16K. Thus the repaired profile favors
the measured short code/prose gains while retaining context and correctness; it
is not established as faster for every prompt or prefill workload. The initial
unseeded DFlash2 85.13/87.44 and paired seeded rows use different passages.


## Why the forum headline differs

The original author's [220 t/s post](https://lcz.me/topic/1640) explicitly
limits its headline to short, favorable tasks. Its standardized DFlash2 depth
curve reports **128.3 t/s at depth 0 / 108.8 t/s at 16K**. MTP3 reports
93.6 / 78.2. These are not the same workload as a sampled original story.

There are also real configuration differences. The
[author's launch recipe](https://github.com/StevenChenSE/sglang/blob/gfx1100-support/README.zh-CN.md)
enables RDNA custom all-reduce and the optimized unified verifier. This PC uses
RCCL host transport because peer access is unavailable; the custom reducer reads
peer GPU buffers. The Intel CPU/root-port limitation was independently documented
in [the P2P investigation](PCIE-P2P-2026-10-17.md). The missing fast collective
path is a plausible cost, but this batch does not isolate or quantify that cost.
Having the same GPUs does not establish the same complete platform or runtime.

The saved DSH default at inspection was **vllm-local / qwen3.8-27b-vllm**,
not the faster SGLang DFlash2 profile. On these two prompts, switching engines
therefore changes the result substantially. The saved selection is preserved;
to use the faster measured profile choose Local SGLang and
`qwen3.8-27b-sglang-dflash2` in DSH. The SGLang backend's own default remains
DFlash2. DSH's provider catalog was refreshed without changing chats or unrelated
settings.

Closing Unsloth fixed the competing-memory problem, but MTP2 measured essentially
the same throughput (88.36/65.28 versus 88.29/66.30 previously). It was not a
large steady-state decode improvement. No VRAM spill or runtime swap growth was
sampled in the successful repaired runs. The remaining forum gap cannot be
assigned entirely to RAM, PCIe or cooling from these tests. The custom collective,
verified kernel path, exact text/sampling and host platform all differ.

On the saved NVIDIA code/prose prompts, this new repaired DFlash2 profile measured
205.59/71.84 versus historical HyperQwen's 170.1/67.3. Those complete profiles
use different checkpoints/head quantization, KV/Mamba precision and runtime
revisions; this does not isolate a GPU-only hardware gain.

## Verifier investigation

The unmodified optimized verifier duplicated ordered JSON values under both MTP
and DFlash2. Its arithmetic and inventory tool round trip passed, demonstrating
why throughput and a few arithmetic replies alone are insufficient validation.
Those incorrect cases were stopped before timed workloads.

The pinned adapter had a proven metadata mismatch and a defensive masking opportunity:

1. Ordinary Triton TARGET_VERIFY metadata describes the prefix separately from
   current draft-token K/V. The unified adapter treated it as a complete causal
   walk. The candidate rebuilds prefix + current scatter slots and full lengths.
2. Qwen TP2 has 12 query heads / 2 KV heads (GQA ratio 6). A 16-row tile contains
   two complete query groups and four partial lanes. The candidate masks those
   extra query rows to avoid overlapping writes with the next query block.

The repair is gated by `SGLANG_LOCAL_RDNA_VERIFY_WALK_FIX` and requires linear
verification, DCP size one, untranslated KV pools and the configured fixed verify
window. Other configurations fall back to standard verification. The patch is
reproduced by `sglang/apply-rocm-fixes.py`, pinned to the source commit above.

Six numerical/graph cases on both cards passed, with maximum absolute error
**0.00712** against the FP32 oracle. Reproducing the old prefix-only metadata
produced maximum error **1.93035** on both cards. Corrected metadata without
the extra GQA mask also passed these numerical cases, so the walk mismatch is
the demonstrated correctness defect; the masking change is defensive.

Both repaired model profiles passed arithmetic, ordered JSON 1–12 and 1–100,
descending JSON, irregular reversal, and an inventory tool-call/result round trip.
MTP3 retrieved all markers from 39,440 input tokens; DFlash2 did so from 64,033.
The near-limit probes produced 22 output tokens each. This is not a sustained
near-limit decode benchmark or a broad accuracy evaluation.

The initial standalone numerical test used an unsuitable graph warm-up stream
and failed graph capture; the test was corrected to warm/capture on an explicit
side stream. The corrected numerical and graph-replay checks then passed. This
harness issue was separate from the model's demonstrated metadata failure.

## Memory and measurement limits

The first retry was stopped by an overly strict **startup swap-growth** guard,
even with 18.18 GiB available RAM. This was a harness false positive, not a model
fit failure. Swap growth is now checked after loading; the 12 GiB preflight,
2 GiB available-memory and 256 MiB nonresident-GPU guards remain. The harness
records per-request host swap I/O separately; small swap-ins may belong to other
applications. Test workers run alone among the configured inference backends,
but ordinary desktop applications remain open. No unrelated application is killed.

VRAM peaks include display and unrelated allocations. Memory and telemetry are
sampled every 0.5 seconds and can miss brief events. Peak clocks do not establish
sustained clocks or exclude thermal throttling. GPU0 runs warmer than GPU1. A separate 120-sample SMU observation recorded
108°C peak hotspot / 102°C memory on GPU0, versus 94°C / 86°C on GPU1. Both
reported hotspot and power-limit activity in the SMU masks. The high-level AMD
SMI binding collapses the masks to booleans, so the sampler reads the raw fields.
[Linux's independent throttle definitions](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/amd/pm/swsmu/inc/amdgpu_smu.h)
map bit 36 to hotspot limiting. These flags reflect the SMU reporting window;
120 flagged samples do not establish 120 seconds of continuous throttling.
No cooling A/B test was performed, so the associated speed loss is unquantified.
No fan curve, voltage, temperature limit or power cap was changed.
The batch does not establish a universal performance ranking or broad model
accuracy score. Host HiCache and Strata remain deferred until RAM expansion.

## Reproduction and integration

Selected production settings are SGLang MTP3/40K and DFlash2/64K with
`rdna_verify=true` and `rdna_verify_walk_fix=true` in the saved profile JSON.
The router sets the two process environment flags explicitly per profile and
rejects optimized verification without the repair before stopping a working
worker. Standalone SGLang starts still default to standard verification unless
the caller supplies flags. SGLang retains automatic RCCL selection; vLLM now
defaults to Simple, with `LOCAL_LLM_NCCL_PROTO=auto` available for comparisons.

The live production-router check loads each saved SGLang profile, verifies actual
context/steps/environment, repeats arithmetic/JSON/tool probes and samples both
cards' residency. Both saved profiles passed; their actual MTP3/DFLASH settings, full
context capacities, paired repair flags and zero sampled nonresident VRAM were
confirmed. Results are included in the sanitized JSON. DSH provider names were refreshed while preserving its saved
vLLM default. Client model IDs, context budgets, endpoints and credentials are
unchanged; no frontend or gateway was terminated. Historical Windows/NVIDIA
snapshots are preserved.

Reproduce the retained SGLang profiles with:

```bash
sglang/.venv-rocm/bin/python hardware/bench-dual-tuning.py --mode mtp --steps 3 --verify 1 --verify-walk-fix --long --benchy-depth 0 16384 --tag repeat
sglang/.venv-rocm/bin/python hardware/bench-dual-tuning.py --mode dflash --verify 1 --verify-walk-fix --long --benchy-depth 0 16384 --tag repeat
```

Run `hardware/bench-dual-tuning.py --help` using the SGLang ROCm Python. Use
`--tag` to preserve earlier batches, `--benchy-depth 0 16384` for the pinned
benchmark and `--verify 1 --verify-walk-fix` only for the candidate repair.
`hardware/test-rdna-verify-walk.py` checks scattered attention and graph replay
against a dense FP32 oracle on each GPU. The pinned benchmark checkout and venv,
models, generated outputs and raw logs are ignored.

[Sanitized per-run measurements](dual-tuning-clean-2026-10-17.json) retain quality
booleans, timing, cache/speculation gauges and sampled memory/telemetry. Prompts
and generated responses are not included in the published results.
