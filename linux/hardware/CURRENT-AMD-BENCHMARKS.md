# Current dual-AMD benchmarks — October 21,2026

**Ten active profiles:** four llama.cpp, one SGLang, two vLLM, one Strata, two Maya. On October21 Bolt moved from llama.cpp to vLLM (13× faster prefill), and the llama.cpp Qwen3.8-27B Q4 profile was retired in favour of its faster SGLang/vLLM versions.
Hardware: i9-13900KS,64GB installed/61.51GiB OS-visible, two RX7900XTX24GB,
CPU PCIe4x8/x8; Intel desktop. Switch installation/P2P status is unchanged.
Super IQ3 is active; retired Muse Q4/Super Q4 and SGLang MTP remain historical.

All selected stacks remain unchanged; no ROCm 10.1 candidate passed every performance and validation gate.
[ROCm 10.1 comparison, decisions and exact build fingerprints](ROCM101-2026-10-21.md),
[all trials/thermals](results/rocm101-2026-10-21.json).
No driver/kernel update or global SDK replacement was performed.

## Sage-A1.5 — active since October21

Official **Q4_K_M + vision projector** are downloaded and checksum-verified on
sharedSATA1. **Active** as the llama.cpp profile `sage-a1.5` (64K/MTP3 +
projector), with a **Sage** Desktop shortcut that opens llama.cpp's built-in Chat.
DSH default is Strata Q3. llama.cpp4c3c5810/HIP7.2.3, both GPUs with
CPU expert backing/hot cache, **64K/MTP3** passes tools/JSON/SSE, fresh8K,
near61,999-input retrieval/full history and a separate vision smoke.

| Sage 64K arm (selected: ROCm7.2.3 MTP3) | Code decode t/s | Prose decode t/s | Native fresh PP t/s | Fresh TTFT s |
|---|---:|---:|---:|---:|
| ROCm7.2.3 noMTP | 53.58 | 53.16 | 393.18 | 20.832 |
| ROCm7.2.3 MTP3 | 83.42 | 66.75 | 387.02 | 21.160 |
| ROCm10.1.0 MTP3 | 84.03 | 66.33 | 386.65 | 21.182 |

10.1 is effectively tied for Sage; retain7.2.3. Latest official is10.1;
7.14.1 is a plausible next isolated candidate, **not locally validated**.
[Detailed test/limits](SAGE-A15-2026-10-21.md) ·
[all trials](results/sage-a15-2026-10-21.json) ·
[ROCm/driver distinction and both-forum research](ROCM-SELECTION-2026-10-21.md).

## Active profile results

### Installed and measured builds

| Engine | Source / selected stack | Scope |
|---|---|---|
| llama.cpp | [4c3c5810](https://github.com/ggml-org/llama.cpp/commit/4c3c5810f87efe177949f1b85ae509d38a2a311f); MoE HIP | Four MoE profiles (incl. Sage) on HIP 7.2.3; no Vulkan profile remains; both GPUs, unchanged expert backing/cache/MTP/contexts |
| SGLang | [f84475cc](https://github.com/StevenChenSE/sglang/commit/f84475ccf593087df3d1da13c9e675eadee12352), retained ROCm 7.2.3 stack | TP2 DFlash2/BF16 KV/163840; local RDNA repairs preserved |
| vLLM | 0.32.1rc1.dev36+ge68efc685.rocm72, retained ROCm 7.2.3 stack | Qwen: TP2/compiled MTP3/BF16 KV/163840. Bolt: TP2/AutoRound W4A16/BF16 KV/262144 |
| Strata | [9ae93f7b/0.1.46.1](https://github.com/Niko1221/Strata/commit/9ae93f7b1fe989d04a8e404d32cddaeeff10505f), ROCm 7.2.3 | Q3/13.5GiB/six workers/256K/INT8 KV32K resident; native frontend unchanged |
| Maya | [3384b5e/v1.1.19](https://github.com/mw00/project-maya/commit/3384b5e9366e696e5f23f51772fb94a8a7948e41), ROCm 7.2.3 | Both32K Maya-S profiles; original guards/source/quantization retained |
| ComfyUI | [8f04fd6e/0.42.0](https://github.com/Comfy-Org/ComfyUI/tree/8f04fd6ecf4a548937971e840af2a985529fab76), Torch2.15 nightly/packaged ROCm7.2.1 | Normal-RAM image/video controls; browser/native Desktop share this stack |

### Eight profiles using the shared benchmark method

Fresh October 21 controls: three timed requests/task and three fresh prefills,
except vLLM's six fixed-seed controls across two starts. Empero's row uses
six retained-control trials across two starts.
One excluded short warmup/task; max256 output, seed42, temperature0.6/top-p0.95,
thinking off. Different tokenizers count the same fresh record workload differently.
Native PP is used for llama.cpp/Strata/Maya; SGLang/vLLM use engine-phase measurements.
External SSE TTFT runs from submission to the first content/reasoning delta.
Decode is `(completion_tokens−1)/(stream_end−first_output)`; model cold-start is excluded.

| Model / quant | Backend / strategy | Context tokens | Actual fresh input | PP t/s | Fresh TTFT s | Short TTFT s, code / prose | Decode t/s, code / prose |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.6-35B-A3B MXFP4_MOE | llama.cpp HIP 7, cache/MTP3 | 262,144 | 8,183–8,188 | 379.6 | 21.579 | 0.059 / 0.059 | 124.95 / 76.72 |
| Nemotron-3.5-Bolt-74B-A9B AutoRound W4A16 | vLLM TP2, Triton int4 MoE | 262,144 | 7,922–7,925 | 2,958.7 | 2.692 | 0.077 / 0.071 | 37.32 / 37.21 |
| Empero Qwen3.8-35B-A3B IQ4_XS | llama.cpp HIP 7, cache/MTP3 | 262,144 | 8,185–8,190 | 395.1 | 20.727 | 0.058 / 0.057 | 122.11 / 74.32 |
| Qwen3.8-27B GPTQ INT4 | SGLang TP2, DFlash2 | 163,840 | 8,188–8,190 | 1449.7 | 5.657 | 0.086 / 0.083 | 211.58 / 72.57 |
| Qwen3.8-27B GPTQ INT4 | vLLM TP2, compiled MTP3 | 163,840 | 8,186–8,189 | 1475.2 | 5.562 | 0.068 / 0.075 | 133.92 / 70.91 |
| Qwen3.8-Flash-Next IQ3_XXS | Strata HIP 7, overlap/MTP3 | 262,144 | 8,187–8,189 | 908.5 | 9.047 | 0.223 / 0.229 | 77.33 / 53.25 |
| GLM-5.3-Flash Maya-S | Maya HIP 7, layer split/MTP | 32,768 | 6,311–6,312 | 532.5 | 12.041 | 0.086 / 0.097 | 17.96 / 16.09 |
| DeepSeek-V4.1-Flash-1017 Maya-S | Maya HIP 7, no DSpark | 32,768 | 6,297–6,301 | 187.3 | 33.666 | 0.380 / 0.553 | 6.92 / 7.08 |

These are selected-stack timings, not a universal SDK or source speedup claim.
Earlier October20/i5/NVIDIA measurements retain their original build/method/date.
The new record retains every actual short input/output count, fresh-input/cache metadata,
quality result, source/library fingerprint and thermal sample coverage.

### Super IQ3 using fixed ~8K-input workloads

| Super / workload | Context | Actual input / output | Native PP t/s | External TTFT s | External decode t/s |
|---|---:|---:|---:|---:|---:|
| IQ3_XXS / code | 32,768 | 8,108 / 256 | 98.64 | 82.213 | 15.94 |
| IQ3_XXS / prose | 32,768 | 8,111 / 256 | 98.31 | 82.517 | 16.94 |

Three trials/task, fixed8108/8111-token inputs,256 outputs, cache_prompt=false.
These TTFTs include8K processing and are **not short-prompt TTFT**. Retain HIP 7,
21:19 layer split,19.124GiB CPU experts/2GiB GPU cache, six threads, MTP off.

### Context, storage and validation limits

Empero's failed promotion gate is recorded in the new report; its allocated256K window is not a new full-window production proof.
Qwen3.6/Bolt retain256K allocation; latest shared-method probes are8K, with older
~64K retrieval evidence separately dated. Strata's retained selected build has
October20 near257984-input/256-output and full-history validation; its new SDK7
control timings above are fresh8K. The rejected10.1 Strata build was not tested
near256K. SGLang/vLLM retain their previously validated163840 settings; candidate
vLLM10.1 additionally passed160866-input retrieval/160913-input history, but failed
the diverse-seed speed gate and is not selected. No cache-token count or uncached
PP is inferred when the API omits cache usage. Maya retains its earlier near31.5K
history proof, while this batch adds fresh controls rather than new context sizes.

[Full numeric results](results/rocm101-2026-10-21.json) ·
[Results index](results/README.md) ·
[Benchmark ledger](BENCHMARK-HISTORY.md) ·
[Historical i5/32GB AMD](AMD-BENCHMARKS-2026-10-19.md).

All previous storage/guards/DSH default/PATH/frontend policies are retained.
No weights were downloaded or moved. Streaming Strata/Maya/Super assets stay on
shared NVMe; resident GGUFs on Shared SATA, SGLang/vLLM checkpoints on Linux NVMe.
[Storage evidence](results/streaming-storage-2026-10-20.json).

### Graphics controls

Normal allowance61.51GiB, same seeded full workflows, one excluded full warmup
and three timed runs/workflow/stack. QwenImage2.1 BF16:512×512/40steps;
MiniMaxH3 INT8:608×352/39frames/20steps/24fps/audio. Both GPUs stage components,
not TP. Server medians: retained/new image23.686/18.331s, video83.831/85.279s.
Video regressed, so retain current ComfyUI. All16 normal outputs pass technical
checks plus sampled visual review; the separate52GiB pilot's HIP fault remains
recorded and did not recur under normal RAM. [Full comparison](ROCM101-2026-10-21.md).
