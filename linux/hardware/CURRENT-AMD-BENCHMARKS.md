# Current dual-AMD benchmarks — October 20, 2026

Measured on **Intel i9-13900KS, 64 GB RAM (61.51 GiB OS-visible), two RX 7900 XTX 24 GB**,
MSI MPG Z690 CARBON WIFI, CPU PCIe 4.0 x8/x8. Switch not installed; P2P disabled.
**Ten active profiles:** five llama.cpp, one SGLang, one vLLM, one Strata, two Maya.
Super IQ3 remains selectable at 32K. Muse Q4 and Super Q4 are retired at the user's request; their weights are removed and historical measurements are preserved.
Strata keeps Q3 and the 13.5 GiB budget, with 6 workers / all CPUs selected.
[CPU/RAM, storage, pool tests and limits](CPU-RAM-PROFILES-2026-10-20.md).


## Strata Linux app update and verified Intel desktop — October 20

Managed Strata **0.1.46.1 /9ae93f7b is active** after candidate and normal
Desktop/native-frontend/authenticated-API validation. The user-selected actual
startup minimum is5GiB/card; engine7/8GiB targets, continuous3GiB protection,
52G/no-swap worker, Q3/13.5GiB/256K and both cards remain. Intel UHD770/i915
renders the desktop. The separate App0.2.1/bundled0.1.46 remains installed.

Promotion-batch three-trial medians: native prefill**912.2t/s**, fresh8K TTFT**9.015s**,
code/prose decode**75.28/50.31t/s**. Actual257984-input/256-output retrieval/code
and258266-input cached full-history follow-up passed. Zero owned swap/spill.
Earlier0.1.45 rates retain their original build; no matched A/B speedup is claimed.
[Update, exact versions and validation limits](STRATA-STARTUP5-2026-10-20.md).

### Installed and measured builds

| Engine | Retained build | Validation scope |
|---|---|---|
| llama.cpp HIP/Vulkan | [`4c3c5810`](https://github.com/ggml-org/llama.cpp/commit/4c3c5810f87efe177949f1b85ae509d38a2a311f) | Four retained shared-method models plus Super IQ3; exact production HIP control timings; dense Vulkan retains its earlier candidate/rebuild proof. Retired models stay historical. |
| SGLang ROCm | [gfx1100 fork `f84475cc`](https://github.com/StevenChenSE/sglang/commit/f84475ccf593087df3d1da13c9e675eadee12352) + local fixes | DFlash2 at 160K, actual 160,861-input retrieval; separate MTP profile retired |
| vLLM ROCm | `0.32.1rc1.dev36+ge68efc685.rocm72` | Retained local fixes; 160K BF16, actual 160,868-input retrieval and full-history follow-up |
| Strata HIP | [0.1.46.1 / `9ae93f7b`](https://github.com/Niko1221/Strata/commit/9ae93f7b1fe989d04a8e404d32cddaeeff10505f) | Exact tested binary, 5 GiB/card startup, six-worker13.5GiB pool, near256K/history and actual Desktop/UI/API proof |
| Maya HIP | [v1.1.19 / `3384b5e`](https://github.com/mw00/project-maya/commit/3384b5e9366e696e5f23f51772fb94a8a7948e41) | ROCm7.2.3 retained; exact tested binaries, Maya-S32K/both GPUs, near31.5K/history and actual Desktop/UI/API/switchback |

The llama.cpp and vLLM updates were performance-neutral within noise; newer
source is not presented as a measured speedup. Older builds keep their original
results. [Profile validation and update report](CPU-RAM-PROFILES-2026-10-20.md).

Fresh retained-SDK7 controls for Strata and four HIP llama models now use the exact production binaries, measured after this task’s compilation and bulk transfers completed. [SDK/table comparison, candidate rates, full trials and thermal coverage](ROCM10-OTHER-ENGINES-2026-10-20.md). Other engines remain on their retained stacks; candidate SDK10 is not promoted.

### Nine profiles using the shared benchmark method

Medians shown: six timed requests per workload across two GLM starts; three for the other shared-method rows. Fresh prefill probes use ~8K
Qwen tokens; tokenizer counts differ. Short TTFT/decode use separate short
code/prose prompts and a 256-output cap. Native PP is used for llama.cpp/Strata/Maya;
SGLang/vLLM use their own measured engine-prefill phases. Context is the total
configured window, not proof of that entire window's quality or speed.

| Model / quant | Backend / strategy | Context tokens | Actual prefill input | Prefill t/s | Prefill TTFT s | Short TTFT s, code / prose | Decode t/s, code / prose |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.8-27B Q4_K_M | llama.cpp Vulkan, MTP3 | 65,536 | 8,187–8,190 | 670.4 | 12.222 | 0.132 / 0.131 | 77.10 / 45.86 |
| Qwen3.6-35B-A3B MXFP4_MOE | llama.cpp HIP, expert cache, MTP3 | 262,144 | 8,186–8,191 | 380.1 | 21.552 | 0.059 / 0.058 | 124.36 / 77.11 |
| Nemotron-3.5-Bolt-74B-A9B Q4_K_M | llama.cpp HIP, expert cache | 262,144 | 7,923–7,927 | 224.8 | 35.246 | 0.388 / 0.249 | 37.01 / 36.79 |
| Empero Qwen3.8-35B-A3B IQ4_XS | llama.cpp HIP, expert cache, MTP3 | 262,144 | 8,186–8,191 | 395.2 | 20.722 | 0.058 / 0.057 | 119.23 / 73.35 |
| Qwen3.8-27B GPTQ INT4 | SGLang TP2, DFlash2 | 163,840 | 8,185–8,191 | 1314.8 | 6.235 | 0.102 / 0.097 | 178.82 / 63.40 |
| Qwen3.8-27B GPTQ INT4 | vLLM TP2, compiled MTP3 | 163,840 | 8,187–8,188 | 1413.8 | 5.806 | 0.066 / 0.092 | 130.31 / 68.96 |
| Qwen3.8-Flash-Next IQ3_XXS | Strata HIP, overlap/MTP3 | 262,144 | 8,186–8,190 | 918.0 | 8.956 | 0.226 / 0.225 | 75.81 / 54.21 |
| GLM-5.3-Flash Maya-S | Maya v1.1.19 HIP, layer split/MTP | 32,768 | 6,308–6,314 | 518.0 | 12.363 | 0.087 / 0.102 | 18.44 / 16.10 |
| DeepSeek-V4.1-Flash-1017 Maya-S | Maya v1.1.19 HIP, layer split/no DSpark | 32,768 | 6,295–6,299 | 188.6 | 33.418 | 0.429 / 0.525 | 6.89 / 7.08 |

GLM now uses six source19/SDK7 trials across two starts; DeepSeek uses three selected `DS4_STREAM=0` trials. Earlier quant ABBA remains historical. [Maya update, SDK decision and complete trials](MAYA-ROCM10-2026-10-20.md).

The retired Muse/Q4 Super measurements remain in the [original numeric batch](results/dual-amd-i9-64gb-2026-10-20.json). They are historical, not active profiles.

Maya's current rows use the [v1.1.19 numeric record](results/maya-rocm10-2026-10-20.json). Initial17 and quant-selection trials remain historical with their exact builds.

### Super IQ3 using fixed ~8K-input workloads

| Super quant / workload | Context | Actual input / output | Native PP t/s | External TTFT s | External decode t/s |
|---|---:|---:|---:|---:|---:|
| IQ3_XXS / code | 32,768 | 8,108 / 256 | 98.55 | 82.287 | 15.92 |
| IQ3_XXS / prose | 32,768 | 8,111 / 256 | 98.12 | 82.672 | 16.90 |

These TTFT values include ~8K input processing and are **not short-prompt TTFT**.
MTP is off. IQ3 uses HIP 21:19, 19.124 GiB CPU experts and a 2 GiB cache,
six CPU threads and 32K total context. The earlier 28,546-input/22-output marker
proof remains historical; these fixed-8K controls do not repeat near-window validation.
Current rows use fresh SDK7 production controls after the task’s builds completed.
Earlier transfer-overlapped candidate timings remain historical. Normal launcher
checks were previously passed; this comparison adds functional tools/JSON/streaming.
The retired Q4 profile's results
remain in the dated ledger and original numeric batch.

### Long context and model storage

Strata's corrected-NVMe selected profile passed **257,984 actual input /
256 output**, then a cached full-history follow-up, at native 256K.
The selected fresh probe measured 1,000.1 native PP t/s and 67.1 native decode t/s; external TTFT was not measured. The full-history follow-up took 1.732s total, which is not TTFT. Both pool trials retained zero owned swap/spill. No RoPE extension is enabled.
The three smaller llama.cpp MoEs retain 256K allocation with ~64K retrieval on
older builds; their latest 8K probes do not prove full-window operation.
SGLang retains only TP2 DFlash2 at **163,840 tokens**, BF16 KV. vLLM
retains compiled MTP3 at **163,840 tokens**, `bfloat16` KV.
The separate SGLang MTP profile is retired. Both new profiles passed fresh
near-window markers and full-history follow-ups, with zero owned swap/spill.
[Context selection, actual counts and limits](QWEN-INT4-CONTEXT-2026-10-20.md).

Strata's managed backend and standalone app share verified weights on the new
shared NVMe. The generated expert pack was checked against every source expert
byte before reuse. Maya's validated Maya-S/DeepSeek-S weights and required generated
assets also use that NVMe. Other resident GGUF models stay
on Shared SATA; SGLang/vLLM target/draft checkpoints stay on Linux NVMe.
[Storage inventory](results/streaming-storage-2026-10-20.json).

[Current results index](results/README.md) · [Dated benchmark ledger](BENCHMARK-HISTORY.md)
· [Historical i5/32 GB AMD report](AMD-BENCHMARKS-2026-10-19.md).


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
- Muse's complete current three-trial batch allows 1,024 output tokens and passed
  2/3 marker checks. All failures remain in the medians. Its short code/prose
  timing uses the same 256-token cap; reasoning can consume that cap and leave
  no final answer. This is a measured limitation, not universal retrieval success.
- All rows retain their production context allocations. The shared-method prefill
  probes reach only ~8K input. Separate Strata pool tests reached near 256K;
  these do not extend validation to other models or workloads. Earlier
  [near-window context checks](BENCHMARK-HISTORY.md) retain their original build,
  date and workload; no older speed is silently promoted into this batch.


[Full post-upgrade report](CPU-RAM-PROFILES-2026-10-20.md).

October21 [Maya browser switching/DSH reuse validation](MAYA-WEB-SWITCHING-2026-10-21.md)
changes frontend control only. All rates and their measured builds above remain unchanged;
no new throughput benchmark or context extension was run.
