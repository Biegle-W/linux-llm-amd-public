# SGLang context optimization — October 16, 2026

> Historical single-AMD measurements. Current dual-AMD settings and the blocked
> SGLang MTP profile are documented in the [migration report](UPGRADE-DUAL-7900XTX.md).

## Activated setting

`qwen3.8-27b-sglang`: **40,960 total tokens**, MTP2, BF16 KV/state,
static memory fraction 0.92, at least 23 GiB free AMD VRAM before model loading.
One RX 7900 XTX, GPTQ W4A16 target, Triton attention, standard verification,
one request, prefill chunk 512, four recurrent-state slots, prefix cache enabled.
The normal launcher and DSH/Turnstone/gateway catalog use the same model ID.
The separate DFlash2 production profile remains 16K BF16.

No weights, runtime source or CPU-offload policy changed. The larger MTP window
comes from a higher tested cache budget while retaining MTP2 and the corrected
verification path. It restores the former two-NVIDIA SGLang context size on one
AMD GPU. The earlier rejected 32K attempt used MTP3 and a different budget;
it was not proof of a 16K hardware limit.

## Measured comparison

Two trials per short workload, 512 output tokens, temperature zero, same prompts
and test harness. Prefix cache was flushed before timed requests. Decode is an
approximate streaming rate, excluding cold startup. The code workload measures
an output prefix, not full-file-edit correctness. These are small synthetic
checks, not a general model-quality evaluation or full-window decode benchmark.

| Strategy / KV | Context | Inventory t/s | Code output t/s | Prose t/s | Peak card VRAM GiB |
|---|---:|---:|---:|---:|---:|
| DFLASH FP8 | 32,768 | 56.62 | 111.34 | 46.90 | 22.68 |
| MTP BF16 | 16,384 | 53.74 | 62.18 | 44.66 | 20.99 |
| MTP BF16 | 32,768 | 53.37 | 61.92 | 43.52 | 22.06 |
| MTP BF16 | 40,960 | 53.50 | 61.93 | 42.78 | 22.60 |
| MTP FP8 | 32,768 | 38.79 | 50.20 | 40.79 | 20.99 |

The fresh 16K baseline and 40K BF16 runs are essentially tied on inventory/code;
40K prose is approximately 4% lower by these two-trial means. This is not a
promise of zero slowdown. FP8 MTP is materially slower on these workloads.

The identical **30,233-input-token** marker-retrieval request took **156.79 s**
at FP8/32K versus **37.92 s** at BF16/32K. At BF16/40K, **38,410 input tokens**
plus 22 output tokens took **51.94 s**, recovering all three markers.
These are total request times, not pure prefill rates. The 40K cache actually
allocated 40,960 tokens; peak whole-card VRAM was **22.60 GiB**, leaving about
1.4 GiB. No sampled nonresident VRAM was observed. All retained MTP candidates
passed arithmetic, ordered JSON, tool call/result round trip and marker retrieval.


DFlash2 FP8/32K passed the short functional suite and 13,048-token retrieval,
but was not tested near 32K. Its means were 56.62 / 111.34 / 46.90 t/s for
inventory/code/prose, versus the saved BF16/16K results of 83.0 / 147.9 / 45.9.
It was not activated: the inventory/code regressions outweigh its small prose
change. The DFlash comparison uses the earlier same-source BF16 results rather
than a fresh BF16 DFlash run, and is not a broad quality evaluation.

## FP8 and four-bit findings

The installed HIP code maps both requested `fp8_e5m2` and `fp8_e4m3` to
`torch.float8_e4m3fn`. We selected the explicit E4M3 spelling for comparisons.
The initial E5M2-named probe loaded and passed the initial functional checks,
but its oversized synthetic prompt was rejected by the test harness before
submission; that failed harness run is not an inference-capacity failure.
The corrected tests use appropriately sized prompts.

FP8 runs used the runtime's default 1.0 KV scales; no calibration file is present.
Passing these limited checks does not establish broad accuracy equivalence.
The installed four-bit KV compatibility gate rejects non-CUDA platforms, so
vLLM's Q4 settings cannot simply be copied into this SGLang ROCm build. No
untested kernel port or bypass of that gate was installed.

Relevant primary source: [Radeon SGLang fork](https://github.com/StevenChenSE/sglang/tree/f84475ccf593087df3d1da13c9e675eadee12352).
The [author's forum report](https://lcz.me/topic/1640) uses two AMD GPUs; its large
cache sizes and headline speeds are not single-card measurements for this PC.

## Reproduction and limits

Run:

```bash
sglang/.venv-rocm/bin/python hardware/test-sglang-context.py --mode mtp --kv bfloat16 --context 40960 --memory 0.92 --long
```
The harness refuses to start while configured inference is active. It monitors
whole-card VRAM, available host RAM and worker VRAM residency, stops only its
owned process group, and writes raw results under ignored `hardware/generated/`.
The previous launcher/profile is retained there for rollback and in Git history.

The existing DSH default remains llama.cpp Qwen Q4 at 64K. Select Local SGLang /
Qwen3.8-27B SGLang AMD (40K, MTP) to use this setting. Context includes both input
and reply; reserve output space. Larger than 40K BF16 was not validated, and this
is not a claim of the absolute hardware maximum. Long-context decode and broad
quantization-quality evaluations remain outside these measurements.
