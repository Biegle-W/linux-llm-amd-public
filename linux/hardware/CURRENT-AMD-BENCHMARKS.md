# Current dual-AMD benchmarks — October 19, 2026

Saved measurements of all ten active production profiles on **two RX 7900 XTX
24 GB cards**, i5-13600KF, MSI MPG Z690 CARBON WIFI, CPU PCIe4 x8/x8 and
**32 GB installed RAM**. Both GPUs participate in every row. Production contexts,
quantization, MTP/DFlash, expert placement, cache policies and memory guards
were retained. No engine update or model download was performed in this task.

## Measured builds

| Runtime | Measured build |
|---|---|
| llama.cpp Vulkan and HIP | `31288c9c66e59377f7788d920678a565bb89dd37`; both compiled build-info files identify `31288c9c` |
| SGLang ROCm | gfx1100 fork `f84475ccf593087df3d1da13c9e675eadee12352` plus retained local repairs |
| vLLM ROCm | `0.32.0rc1.dev329+g39983a5e7.rocm723` |
| Strata HIP | 0.1.45 / `477ac13cbe8e582c20484871ce459d20d82df09d` |

llama.cpp/Strata use layer splitting; SGLang/vLLM use TP2 with host transport,
without direct P2P. [Build dependencies and local fixes](RUNTIME-UPGRADE-2026-10-18.md).
Source/config hashes and every trial of the original nine-profile batch are in
[its curated numeric record](results/current-amd-2026-10-19.json). The tenth
profile has a [separate record](results/nemotron-super-2026-10-19.json).
Documentation was reconciled during maintenance; no timings were rerun or changed.

## Results

Three timed requests per workload; the tables show medians. These small samples
are not confidence intervals or guaranteed throughput. **Prefill** uses
a shared corpus sized near 8K Qwen tokens; actual per-model counts are shown. **Short TTFT** and **decode** use separate short code/prose
prompts, in that order. The corpus TTFT includes input processing and the first
visible token; no model loading time. Context is the configured total budget,
not the input length filled by these tests.

| Model / quant | Backend / strategy | Context tokens | Actual prefill input tokens | Prefill t/s | Prefill TTFT s | Short TTFT s, code / prose | Decode t/s, code / prose |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.8-27B Q4_K_M | llama.cpp Vulkan, MTP3 | 65,536 | 8,187–8,189 | 695.1 | 11.788 | 0.132 / 0.129 | 75.80 / 45.58 |
| Muse-Glimmer-30B UD-Q4_K_XL | llama.cpp Vulkan | 32,768 | 6,346–6,349 | 1375.5 | 4.725 | 0.258 / 0.259 | 37.85 / 37.92 |
| Qwen3.6-35B-A3B MXFP4_MOE | llama.cpp HIP, expert cache, MTP3 | 262,144 | 8,187–8,191 | 379.3 | 21.603 | 0.061 / 0.060 | 123.70 / 76.34 |
| Nemotron-3.5-Bolt-74B-A9B Q4_K_M | llama.cpp HIP, expert cache | 262,144 | 7,920–7,926 | 222.8 | 35.549 | 0.387 / 0.249 | 36.49 / 36.29 |
| Empero Qwen3.8-35B-A3B IQ4_XS | llama.cpp HIP, expert cache, MTP3 | 262,144 | 8,187–8,190 | 399.2 | 20.515 | 0.058 / 0.058 | 120.48 / 76.46 |
| Qwen3.8-27B GPTQ INT4 | SGLang TP2, MTP3 | 40,960 | 8,186–8,190 | 1397.7 | 5.871 | 0.084 / 0.080 | 115.22 / 68.85 |
| Qwen3.8-27B GPTQ INT4 | SGLang TP2, DFlash2 | 65,536 | 8,186–8,188 | 1491.5 | 5.510 | 0.086 / 0.083 | 210.42 / 70.88 |
| Qwen3.8-27B GPTQ INT4 | vLLM TP2, compiled MTP3 | 65,536 | 8,184–8,189 | 1488.2 | 5.513 | 0.067 / 0.081 | 131.05 / 73.31 |
| Qwen3.8-Flash-Next IQ3_XXS | Strata HIP, overlap/MTP3 | 262,144 | 8,186–8,189 | 900.9 | 9.126 | 0.238 / 0.245 | 71.50 / 48.46 |

## Tenth profile: Nemotron Super IQ3

`nemotron-3.5-super-iq3` uses llama.cpp HIP `31288c9c`, both GPUs with layer
split 21:19, UD-IQ3_XXS, 32,768 total context, 19.124 GiB CPU expert backing,
a 2 GiB total expert-cache ceiling and MTP off. Q4 remains an inactive 64 GB
candidate, with no measured speed.

| Workload, median of 3 | Actual input / output | Native prefill t/s | External TTFT s | External decode t/s |
|---|---:|---:|---:|---:|
| Code | 8,108 / 256 | 95.75 | 84.699 | 14.16 |
| Prose | 8,111 / 256 | 97.13 | 83.521 | 16.32 |

Unlike the original batch's short-prompt decode test, these code/prose requests
process approximately 8K uncached input tokens before generating 256 tokens.
Their TTFT is not short TTFT; do not place it in that column or rank these
workloads as a controlled model comparison. One separate three-marker retrieval
passed at 28,546 input / 22 output tokens (100.08 native PP, 285.249 s external
TTFT); this is not full-window sustained generation. Peak whole-card VRAM was
20.00 / 20.94 GiB, available RAM stayed above 5.84 GiB, with zero worker swap
and sampled VRAM spill. See [complete validation and failed splits](NEMOTRON-SUPER-2026-10-19.md)
and [all trials](results/nemotron-super-2026-10-19.json).

## Method and limits

- One managed backend/model at a time, launched in a visible terminal through
  the existing guarded launcher. DSH, gateway and unrelated applications were
  preserved. Normal desktop activity remained; this is not a controlled
  old/new-build or AMD-versus-NVIDIA A/B.
- An arithmetic request loads/checks each model before timing. Each short
  workload then has one excluded warm-up and three timed requests. The prompts
  are the saved merge-sorted-lists function and lighthouse-letter story,
  256 output-token cap, temperature 0.6, top-p 0.95, seed 42, thinking requested
  off. Actual completion counts are retained; models can stop before the cap.
- External SSE uses the managed loopback router, rather than the remote gateway.
  TTFT runs from request submission to the first content/reasoning
  delta. Decode is `(completion_tokens - 1) / (stream_end - first_output)`.
  Speculative bursts and stream completion overhead limit precision. Native
  timing fields are also retained for llama.cpp and Strata.
- Each prefill request uses a new leading salt and ~8K synthetic inventory
  records with three markers. All probes retain their marker outcome and
  report zero cached input tokens; native cache counts are checked too.
  Expert caches are warmed by preceding requests; fresh input does not mean
  cold weights. Short requests retain each engine's production prefix policy.
- llama.cpp/Strata PP is native engine prompt timing. SGLang PP divides actual
  input by its `prefill_forward` stage histogram delta (maximum TP-rank duration;
  one observation/rank). vLLM PP divides input by its request-prefill histogram
  delta (one request, scheduled-to-first-engine-token). These phase definitions
  differ from isolated kernels and from each other. Input/TTFT throughput is
  stored separately and is never labeled native PP.
- Muse's initial 64-output-token marker probe did not return all
  markers. The final complete three-trial batch allows 1,024 output tokens;
  it passed 2/3 marker checks. Every timed trial is retained, including
  failures; no unsuccessful trial is removed from the performance median.
  Its short code/prose timing still uses the same 256-token cap as the
  other models. Emitted reasoning can consume that cap; its throughput is not
  a guarantee of a final answer within 256 tokens. Preliminary retries and a
  successful diagnostic request did not
  establish consistent retrieval; their incomplete batches stay in ignored raw
  records and do not replace the complete three-trial result.
- All rows retain their production context allocations. New capacity/throughput
  probes reach only ~8K input, not a filled 32K/40K/64K/256K window. Earlier
  [near-window context checks](BENCHMARK-HISTORY.md) retain their original build,
  date and workload; no older speed is silently promoted into this batch.

## Actual lengths and memory telemetry

| API model ID | Actual prefill input tokens, three trials | Prefill source | Minimum available RAM GiB | Peak VRAM0 / 1 GiB | Aggregate managed VmSwap MiB | Marker checks |
|---|---|---|---:|---|---:|---:|
| `qwen3.8-27b-q4` | 8187, 8189, 8189 | Native prompt | 23.284 | 9.773 / 11.438 | 0.00 | 3/3 |
| `muse-glimmer-30b` | 6349, 6346, 6349 | Native prompt | 23.562 | 7.515 / 10.228 | 0.53 | 2/3 |
| `qwen3.6-35b-a3b` | 8191, 8190, 8187 | Native prompt | 15.299 | 13.374 / 15.869 | 0.55 | 3/3 |
| `nemotron-3.5-bolt` | 7926, 7920, 7925 | Native prompt | 11.927 | 22.730 / 23.031 | 0.54 | 3/3 |
| `empero-qwen3.8-35b-a3b` | 8190, 8187, 8190 | Native prompt | 14.706 | 11.936 / 15.732 | 0.54 | 3/3 |
| `qwen3.8-27b-sglang` | 8187, 8190, 8186 | Engine prefill phase | 18.128 | 12.921 / 15.121 | 5417.84 | 3/3 |
| `qwen3.8-27b-sglang-dflash2` | 8188, 8186, 8187 | Engine prefill phase | 19.518 | 15.604 / 17.410 | 8521.77 | 3/3 |
| `qwen3.8-27b-vllm` | 8189, 8184, 8188 | Engine prefill phase | 18.231 | 14.230 / 15.983 | 0.00 | 3/3 |
| `qwen3.8-flash-next-iq3_xxs` | 8189, 8188, 8186 | Native prompt | 6.018 | 18.706 / 19.838 | 12.01 | 3/3 |

Memory is sampled once per second after model loading, including warm-up and
measurements. Whole-card VRAM includes desktop allocations and can miss brief
peaks. Aggregate managed VmSwap includes routers and descendants, including
pre-existing swapped router pages; it is not a claim of active model-weight
paging or zero startup swap. Existing worker/cgroup guards stay in force.
Every measured profile sampled both GPU allocations and zero dedicated-VRAM spill.
SGLang MTP3/DFlash2 retained about **5.29/8.32 GiB aggregate VmSwap** in their
managed process trees. Swap I/O during the timed requests was not recorded,
so these runs must not be described as zero-paging or zero-swap measurements.

## Reproduce and preserve evidence

Use [the benchmark helper](benchmark-current-amd.py) and
[results index](results/README.md). The helper benchmarks an already-running
backend; it does not change profiles, start engines or disable safety guards.
Raw per-backend numeric records are under ignored
`hardware/generated/current-amd-2026-10-19/`. The published numeric record keeps
counts, timings and output hashes, with no generated answers, credentials,
private addresses or model binaries. The previous private README was archived
privately; the public NVIDIA and Windows snapshots were preserved.

Timing implementation sources:
[llama.cpp](https://github.com/ggml-org/llama.cpp/blob/31288c9c66e59377f7788d920678a565bb89dd37/tools/server/server-context.cpp),
[Strata](https://github.com/Niko1221/Strata/blob/477ac13cbe8e582c20484871ce459d20d82df09d/serve/server.py),
[SGLang request stages](https://github.com/StevenChenSE/sglang/blob/f84475ccf593087df3d1da13c9e675eadee12352/python/sglang/srt/observability/req_time_stats.py),
[vLLM request stats](https://github.com/vllm-project/vllm/blob/39983a5e7/vllm/v1/metrics/stats.py).
This task measures installed settings; it adds no new forum-derived optimization.
Existing tuning/source records remain in [the source ledger](FORUM-OPTIMIZATION-SOURCES.md).
