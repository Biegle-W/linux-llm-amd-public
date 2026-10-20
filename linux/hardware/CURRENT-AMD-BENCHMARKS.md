# Current dual-AMD benchmarks — October 20, 2026

Measured on **Intel i9-13900KS, 64 GB RAM (61.51 GiB OS-visible), two RX 7900 XTX 24 GB**,
MSI MPG Z690 CARBON WIFI, CPU PCIe 4.0 x8/x8. Switch not installed; P2P disabled.
**Thirteen active profiles:** seven llama.cpp, two SGLang, one vLLM, one Strata, two Maya.
Super IQ3 and Q4 are both selectable at 32K; all their weights are retained.
Strata keeps Q3 and the 13.5 GiB budget, with 6 workers / all CPUs selected.
[CPU/RAM, storage, pool tests and limits](CPU-RAM-PROFILES-2026-10-20.md).

### Installed and measured builds

| Engine | Retained build | Validation scope |
|---|---|---|
| llama.cpp HIP/Vulkan | [`4c3c5810`](https://github.com/ggml-org/llama.cpp/commit/4c3c5810f87efe177949f1b85ae509d38a2a311f) | Five shared-method benchmarks plus both Super quants; candidate-source measurements, then production rebuild and functional proofs |
| SGLang ROCm | [gfx1100 fork `f84475cc`](https://github.com/StevenChenSE/sglang/commit/f84475ccf593087df3d1da13c9e675eadee12352) + local fixes | Both retained strategies on i9/64 GB |
| vLLM ROCm | `0.32.1rc1.dev36+ge68efc685.rocm72` | Retained local fixes; i9 timings, earlier 64K retrieval and prefix reuse |
| Strata HIP | [0.1.45 / `477ac13c`](https://github.com/Niko1221/Strata/commit/477ac13cbe8e582c20484871ce459d20d82df09d) | Corrected expert pack on shared NVMe, both CPU pools and actual near 256K probes |
| Maya HIP | [v1.1.17 / `8d9a9b5d`](https://github.com/mw00/project-maya/commit/8d9a9b5d705049a87da853717cdc59440252de30) | Selected S24/DeepSeek-S, 32K, both cards, near-30K probes and normal API/model switching |

The llama.cpp and vLLM updates were performance-neutral within noise; newer
source is not presented as a measured speedup. Older builds keep their original
results. [Profile validation and update report](CPU-RAM-PROFILES-2026-10-20.md).

### Eleven profiles using the shared benchmark method

Three timed requests per workload, median shown. Fresh prefill probes use ~8K
Qwen tokens; tokenizer counts differ. Short TTFT/decode use separate short
code/prose prompts and a 256-output cap. Native PP is used for llama.cpp/Strata/Maya;
SGLang/vLLM use their own measured engine-prefill phases. Context is the total
configured window, not proof of that entire window's quality or speed.

| Model / quant | Backend / strategy | Context tokens | Actual prefill input | Prefill t/s | Prefill TTFT s | Short TTFT s, code / prose | Decode t/s, code / prose |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.8-27B Q4_K_M | llama.cpp Vulkan, MTP3 | 65,536 | 8,187–8,190 | 670.4 | 12.222 | 0.132 / 0.131 | 77.10 / 45.86 |
| Muse-Glimmer-30B UD-Q4_K_XL | llama.cpp Vulkan | 32,768 | 6,348–6,353 | 1329.2 | 4.879 | 0.262 / 0.258 | 37.37 / 37.50 |
| Qwen3.6-35B-A3B MXFP4_MOE | llama.cpp HIP, expert cache, MTP3 | 262,144 | 8,187–8,189 | 373.5 | 21.933 | 0.059 / 0.059 | 126.73 / 78.36 |
| Nemotron-3.5-Bolt-74B-A9B Q4_K_M | llama.cpp HIP, expert cache | 262,144 | 7,923–7,926 | 220.3 | 35.989 | 0.400 / 0.243 | 37.21 / 36.87 |
| Empero Qwen3.8-35B-A3B IQ4_XS | llama.cpp HIP, expert cache, MTP3 | 262,144 | 8,185–8,188 | 388.4 | 21.083 | 0.057 / 0.057 | 125.85 / 77.07 |
| Qwen3.8-27B GPTQ INT4 | SGLang TP2, MTP3 | 40,960 | 8,185–8,189 | 1402.8 | 5.851 | 0.088 / 0.083 | 115.76 / 64.90 |
| Qwen3.8-27B GPTQ INT4 | SGLang TP2, DFlash2 | 65,536 | 8,186–8,188 | 1471.2 | 5.575 | 0.092 / 0.088 | 205.12 / 73.44 |
| Qwen3.8-27B GPTQ INT4 | vLLM TP2, compiled MTP3 | 65,536 | 8,184–8,186 | 1496.5 | 5.486 | 0.066 / 0.082 | 132.03 / 71.32 |
| Qwen3.8-Flash-Next IQ3_XXS | Strata HIP, overlap/MTP3 | 262,144 | 8,185–8,187 | 914.3 | 8.987 | 0.219 / 0.223 | 76.61 / 53.35 |
| GLM-5.3-Flash Maya-S24 | Maya HIP, layer split/MTP | 32,768 | 6,312–6,313 | 525.9 | 12.159 | 0.074 / 0.097 | 21.13 / 16.54 |
| DeepSeek-V4.1-Flash-1017 Maya-S | Maya HIP, layer split/no DSpark | 32,768 | 6,295–6,302 | 185.5 | 33.956 | 0.374 / 0.550 | 6.24 / 6.84 |

Muse retrieved all markers in 2/3 probes with a 1,024-output allowance; the failed
trial remains in the medians. All original counts, timing fields, hashes and memory
extrema are retained in the [numeric record](results/dual-amd-i9-64gb-2026-10-20.json).

Maya's two added rows retain every trial and actual tokenizer count in the
[Maya numeric record](results/maya-dual-amd-2026-10-20.json); [settings, selection and limits](MAYA-2026-10-20.md).

### Two Super profiles using fixed ~8K-input workloads

| Super quant / workload | Context | Actual input / output | Native PP t/s | External TTFT s | External decode t/s |
|---|---:|---:|---:|---:|---:|
| IQ3_XXS / code | 32,768 | 8,108 / 256 | 98.21 | 82.566 | 15.90 |
| IQ3_XXS / prose | 32,768 | 8,111 / 256 | 97.84 | 82.911 | 16.95 |
| Q4_K_XL / code | 32,768 | 8,108 / 256 | 43.26 | 187.432 | 7.86 |
| Q4_K_XL / prose | 32,768 | 8,111 / 256 | 44.17 | 183.653 | 8.19 |

These TTFT values include ~8K input processing and are **not short-prompt TTFT**.
MTP is off. IQ3 uses HIP 21:19, 19.124 GiB CPU experts and 2 GiB cache; Q4 uses HIP 1:1,
47.424 GiB CPU experts and 4 GiB cache. Both use six CPU threads and 32K total context.
Both retrieved markers at 28,546 input / 22 output. Candidate runs overlapped
user-authorized copy/hash/download IO ending 2026-10-20T11:03:39Z; timings and RAM
minima are not an isolated engine A/B. The actual production rebuild passed
separate normal-launcher tools/JSON/streaming/placement checks for both profiles.

### Long context and model storage

Strata's corrected-NVMe selected profile passed **257,984 actual input /
256 output**, then a cached full-history follow-up, at native 256K.
The selected fresh probe measured 1,000.1 native PP t/s and 67.1 native decode t/s; external TTFT was not measured. The full-history follow-up took 1.732s total, which is not TTFT. Both pool trials retained zero owned swap/spill. No RoPE extension is enabled.
The three smaller llama.cpp MoEs retain 256K allocation with ~64K retrieval on
older builds; their latest 8K probes do not prove full-window operation.
SGLang MTP/DFlash2 and vLLM retain 40K/64K/64K contexts, with earlier near-limit
retrieval under its original hardware/build attribution.

Strata's managed backend and standalone app share verified weights on the new
shared NVMe. The generated expert pack was checked against every source expert
byte before reuse. Maya's validated S24/DeepSeek-S weights and required generated
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
