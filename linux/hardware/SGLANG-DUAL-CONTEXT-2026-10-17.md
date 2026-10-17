# Dual-Radeon SGLang context and prefix-cache validation — October 17, 2026

## Selected DFlash2 configuration

`qwen3.8-27b-sglang-dflash2` now uses a **65,536-token total context budget**,
GPU prefix caching, **2,048-token prefill chunks** and eight Mamba cache slots.
The checkpoint, W4A16 DFlash2 drafter, draft length 8, draft window 2,048,
BF16 KV, ROCm TP2, memory fraction 0.85 and one simultaneous request are retained.
The context budget includes both input and output; it is not a 65,536-token
input allowance plus a separate output budget. DFlash2 remains the SGLang default.

Hardware: two RX 7900 XTX 24 GB cards, MSI MPG Z690 CARBON WIFI, CPU PCIe 4 x8/x8,
32 GB system RAM. ROCm peer access remains unavailable. Both cards are required;
all weights remain GPU-resident. Host HiCache and Strata remain deferred until
the pending RAM upgrade and separate validation.

## Measured comparison

Two fresh, streamed 256-output-token samples per workload, temperature 0 and
thinking disabled. Cache was flushed before each throughput sample. Input lengths
were 3,273 inventory / 1,321 code / 39 prose tokens. Values below are arithmetic
means of the two samples, not statistically established performance guarantees.

| DFlash2 configuration | Inventory decode t/s | Code decode t/s | Prose decode t/s | Peak VRAM GPU0 / GPU1 GiB |
|---|---:|---:|---:|---:|
| Previous 16K, no cache, chunk 512, 2 Mamba slots | 98.57 | 200.65 | 61.83 | 14.35 / 13.06 |
| **Selected 64K, cache, chunk 2,048, 8 Mamba slots** | **104.23** | **200.57** | **60.12** | **17.01 / 15.78** |
| 64K, cache, chunk 8,192, 8 Mamba slots | 97.32 | 199.67 | 62.32 | 19.20 / 17.87 |

The selected setup increased inventory throughput about 5.7%, left code throughput
almost unchanged, and reduced prose throughput about 2.8% in this small comparison.
Several settings changed together versus the 16K baseline; these measurements do
not isolate the effect of context alone. The two 64K candidates differ only in
prefill chunk/max-prefill size. Selecting 2,048 favors lower cold-prompt latency
and lower peak VRAM, rather than claiming it wins every output workload.

| DFlash2 configuration | Cold 8,005-token input TTFT | Identical repeat TTFT | Follow-up TTFT | 64,033-token input TTFT |
|---|---:|---:|---:|---:|
| 16K, no cache, chunk 512 | 5.740 s | 5.778 s | 5.802 s | Not applicable |
| **64K, cache, chunk 2,048** | **5.564 s** | **0.292 s** | **0.165 s** | **66.551 s** |
| 64K, cache, chunk 8,192 | 6.189 s | 0.120 s | 0.167 s | 69.392 s |

Each cached repeat and follow-up reported **8,000 cached prompt tokens**. All
three-marker retrievals passed, including both near-64K inputs. These timings are
single retrieval probes. Prefix reuse helps matching conversation history; new
prompts still require prefill. Caches are lost when the worker unloads or switches
profiles, and a small Mamba state pool does not promise every conversation survives
eviction. No host or disk cache is enabled.

## MTP prefix cache restored

`qwen3.8-27b-sglang` retains its **40,960-token** context, MTP2, BF16 KV and
512-token prefill chunks. GPU prefix caching is now enabled with eight Mamba
cache slots. It passed arithmetic, ordered JSON and tool round-trip checks,
8K repeated-prefix/continuation checks, and a **39,440-token** three-marker input
(22 output tokens; **36.983 s** TTFT). The old motherboard's cache failure was not
reproduced in this test. Broader workload stability is not guaranteed by this suite.

| MTP40K measurement | Result |
|---|---:|
| Inventory / code / prose mean decode | 74.46 / 89.32 / 66.18 t/s |
| Cold / repeated / follow-up 8K TTFT | 5.977 / 0.111 / 0.161 s |
| Confirmed cached tokens on repeat and follow-up | 8,000 |
| Sampled peak VRAM GPU0 / GPU1 | 14.08 / 12.80 GiB |
| Minimum available host RAM | 18.01 GiB |
| Sampled nonresident VRAM | 0 bytes |

These use two samples of each short throughput workload above, not
an MTP cache-off/cache-on decode comparison. No MTP prefill-chunk sweep was run.

## Correctness, memory and measurement limits

All three DFlash2 configurations passed three arithmetic checks, ordered JSON and
a tool-call/result round trip. Both larger-context candidates passed marker
retrieval from a 64,033-token input plus 22 output tokens. This validates the
context setting, not every long-context task or sustained long-context decode.

No nonresident VRAM was observed in the once-per-second process-residency samples.
The selected DFlash2 run had at least 18.92 GiB host RAM available; sampled peak
VRAM includes desktop/runtime allocations and may miss brief peaks. Both GPUs
held model allocations. Test workers are stopped after validation.

Decode is approximately `(completion_tokens - 1) / (stream_end - first_output)`;
speculative streaming may deliver multiple tokens together. TTFT measures request
to first output and includes prefill, first decode and request overhead. The JSON
field `input_tokens_per_ttft` is an end-to-end proxy, **not a pure prefill benchmark**.
The short 256-token code output is a throughput workload, not a complete code-edit
correctness test. Functional checks are separate.

Runtime: SGLang Radeon fork `f84475ccf593087df3d1da13c9e675eadee12352`, isolated
ROCm 7.2.3 and local no-hostcall RCCL 2.27.7. Existing BF16/TRITON settings,
P2P/SDMA restrictions, KV bounds-trap patch and conservative speculative verifier
are retained. `SGLANG_RDNA_VLLM_VERIFY=0` stays unchanged because its earlier local
correctness failure was not resolved by this tuning exercise.

Reproduce with `sglang/.venv-rocm/bin/python hardware/test-sglang-dual-context.py`
and the context, chunk, cache and Mamba-slot arguments in
[the sanitized results](sglang-dual-context-2026-10-17.json). Raw prompts, outputs,
logs and workstation paths remain in ignored `hardware/generated/` files.

## Integration validation

The saved DFlash2 profile was loaded through the existing production router.
Its live server configuration confirmed radix caching enabled, 2,048-token
prefill chunks, eight Mamba slots and 65,536 available KV tokens. Arithmetic,
JSON and tool round trips passed again. DSH, Turnstone and the authenticated
API catalog all advertise 65,536 DFlash2 / 40,960 MTP tokens, with eight total
profiles. Validation workers were shut down; existing frontends and gateway
were preserved. No model download, move or deletion was needed.

## Sources that motivated the tests

- [lcz.me dual-7900-XTX setup, 8K chunks and caching](https://lcz.me/topic/1814).
- [lcz.me DFlash2, 2K chunks and cold versus cached latency](https://lcz.me/topic/1893).
- [lcz.me MTP and prefix/host caching](https://lcz.me/topic/1714).
- [Radeon SGLang fork](https://github.com/StevenChenSE/sglang/tree/gfx1100-support).

Forum results are not measurements of this PC. Higher-memory HiCache recipes,
128K/196K contexts and stock-RCCL transport changes were not adopted without
local validation. No new model download or runtime upgrade was required.
