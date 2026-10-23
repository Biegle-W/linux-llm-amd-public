# Current dual-AMD benchmarks — October 23, 2026

## Both DeepSeek quants are selectable — October23

Maya now offers **three profiles**: GLM-S v2, **DeepSeek Maya-XS + matching DSpark**
(`deepseek-v4.1-flash-1017-maya`, existing ID), and the larger **DeepSeek Maya-S**
(`deepseek-v4.1-flash-1017-maya-s`, new ID, no DSpark). All are32K, both7900XTX,
Maya1.1.24/ROCm7.2.3 with existing guards. The total active catalog is **11**.
Choose either DeepSeek quant in Maya's web selector, DSH, or the OpenAI-compatible
API; only one worker runs at a time. Strata remains the DSH default.
Normal S→XS→S→XS, authenticated API/tools/JSON/SSE and original UI passed.
No new throughput benchmark: saved S code/prose**6.42/6.78t/s**, PP**299.0**, fresh
TTFT**21.062s**; saved XS+DSpark**31.28/15.36t/s**, PP**445.5**, TTFT**14.156s**.
These are separate earlier same-day three-trial sessions, not an equal-quality A/B.
All six S shards passed fresh full-file SHA256; no download/deletion was needed.
[Deployment and validation](MAYA-DUAL-DEEPSEEK-2026-10-23.md).

### Maya-S DSpark retest — October23

**Current S selection: DSpark off.** Fresh Maya1.1.24/ROCm7.2.3 comparison uses
32K/24threads/both7900XTX, identical starting S routing seeds and unchanged guards.
Against the arithmetic mean of the two no-draft arm medians, DSpark changes code **-3.37%**, prose **-5.14%** and native prefill **-6.82%**; geometric mean **-5.12%**. Speed gate **fails**.

| Arm /32K | Code decode t/s | Prose decode t/s | Native fresh PP t/s | Fresh TTFT s |
|---|---:|---:|---:|---:|
| A1-none | 7.29 | 6.92 | 303.4 | 20.768 |
| B-dspark | 6.71 | 6.42 | 277.4 | 22.716 |
| A2-none | 6.59 | 6.61 | 292.0 | 21.577 |

Sequential A1(off)→B(on)→A2(off), three timed256-output trials per code/prose
workload and three fresh~6.3K actual DeepSeek input probes per arm. These are not
thermally equalized or a matched comparison to the older1.1.17/128-output test.
Retain S with DSpark disabled. XS keeps its own matching xs2 drafter; GLM and all other profiles are unchanged.
[All trials, functional/context checks and thermal coverage](MAYA-S-DSPARK-2026-10-23.md).


## Maya-XS + DSpark rollout history — October23 (before separate S selection)

DeepSeek now uses **Maya-XS + matching dspark-xs2** under the same model ID
`deepseek-v4.1-flash-1017-maya`:32K,both7900XTX,ROCm7.2.3/Maya1.1.24. GLM stays
Maya-S v2/MTP; all guards, ten-model catalog and Strata DSH default were preserved at that rollout; S is now separately selectable above.
Normal Desktop/Ptyxis/original UI/authenticated API and GLM→XS→GLM→XS passed;
XS is ready. [Production proof and rollback](MAYA-XS-PRODUCTION-2026-10-23.md).
Saved earlier XS benchmark: **31.28 code /15.36 prose t/s**, **445.5 native PP**,
**14.156s fresh TTFT**; single1024-output HTML**12.54t/s**. No throughput rerun
or new speed claim accompanies production integration. XS trades quality for size.

## Maya-XS + matching DSpark test — October23

The earlier isolated **Maya1.1.24/ROCm7.2.3, both7900XTX,32K** test below
preceded the user-authorized XS + DSpark production switch above. Ten profiles existed at that test stage. XS is the smaller, lower-quality IQ1_S quant;
its matching drafter is `dspark-xs2` (IQ2_XXS). Existing memory guards are unchanged.

| Maya1.1.24 /32K /ROCm7.2.3 | Code decode t/s | Prose decode t/s | Native fresh PP t/s | Fresh TTFT s |
|---|---:|---:|---:|---:|
| XS DSpark off | 20.45 | 15.56 | 428.7 | 14.714 |
| XS **matching DSpark on** | 31.28 | 15.36 | 445.5 | 14.156 |
| Saved same-day Maya-S, no DSpark | 6.42 | 6.78 | 299.0 | 21.062 |


Single1024-output HTML code probe: **10.95→12.54t/s** off→on;
short-code medians do not predict every workload.
Both arms passed; near-window/history/tools/JSON/SSE, exact counts, longer1024-output
probes, thermal coverage and draft/no-draft comparison are in the
[XS test report](MAYA-XS-DSPARK-2026-10-23.md). The saved S row is a separate
same-day session, not an equal-quality A/B. No NVIDIA community speed is claimed locally.

## Latest Maya 1.1.24 — October 23

Promoted exact tested development source **25deec5 /1.1.24** on retained ROCm7.2.3.
At source promotion, both quants were Maya-S, both GPUs/32K,GLM40GiB/MTP and DeepSeek24threads/noDSpark;
DeepSeek subsequently switched to XS + DSpark above. These S rates retain their original trial date; S is selectable again under a new alias;
all memory guards and the Strata DSH default remain. **GLM PREFILL_FUSED=0** retains
MMQ because the newly enabled gfx1100 fused path failed parity on both cards.
DeepSeek native fresh prefill185.1→299.0t/s and TTFT34.045→21.062s; decode remains similar.
GLM performance is approximately unchanged. These are sequential matched workloads,
not thermally equalised A/B trials; no universal source speedup is claimed.

| Model /1.1.24 | Context | Code / prose decode t/s | Native PP t/s | Fresh TTFT s |
|---|---:|---:|---:|---:|
| GLM-5.3-Flash Maya-S | 32,768 | 19.72 / 15.69 | 535.6 | 11.928 |
| DeepSeek-V4.1-Flash-1017 Maya-S | 32,768 | 6.42 / 6.78 | 299.0 | 21.062 |

Both candidates passed near31.5K retrieval/history,JSON/tools/SSE, dual-GPU/no-swap
and normal Desktop/Ptyxis/original browser UI/selector/authenticated API/switchback.
Actual counts, timings, sampled high temperatures and failed/excluded kernels:
[update report](MAYA-UPDATE-2026-10-23.md) · [numeric evidence](results/maya-update-2026-10-23.json).

Other latest llama.cpp sizes and rates are in the [October22 batch sweep](LLAMA-BATCH-SWEEP-2026-10-22.md); its new-size full-window tests were not repeated. All earlier rates below retain their original workload/build/date.

**Eleven active profiles:** four llama.cpp (Ornith-1.5-122B added October22), one SGLang, two vLLM, one Strata, three Maya. On October21 Bolt moved from llama.cpp to vLLM (13× faster prefill), and the llama.cpp Qwen3.8-27B Q4 profile was retired in favour of its faster SGLang/vLLM versions.
Hardware: i9-13900KS,64GB installed/61.51GiB OS-visible, two RX7900XTX24GB,
CPU PCIe4x8/x8; Intel desktop. Switch installation/P2P status is unchanged.
Super IQ3 is active; retired Muse Q4/Super Q4 and SGLang MTP remain historical.

All production ROCm stacks remain on 7.2.3; no ROCm 10.1 candidate passed every performance and validation gate.
[ROCm 10.1 comparison, decisions and exact build fingerprints](ROCM101-2026-10-21.md),
[all trials/thermals](results/rocm101-2026-10-21.json).
No driver/kernel update or global SDK replacement was performed.

## Sage-A1.5 — active since October21

Official **Q4_K_M + vision projector** are downloaded and checksum-verified on
sharedSATA1. **Active** as the llama.cpp profile `sage-a1.5` (64K/MTP3 +
projector), usable through DSH, the model hub and the API (Desktop Chat shortcut removed October22).
DSH default is Strata Q3. llama.cpp4c3c5810/HIP7.2.3, both GPUs with
CPU expert backing/hot cache, **64K/MTP3** passes tools/JSON/SSE, fresh8K,
near61,999-input retrieval/full history and a separate vision smoke.

| Sage 64K arm (selected: ROCm7.2.3 MTP3) | Code decode t/s | Prose decode t/s | Native fresh PP t/s | Fresh TTFT s |
|---|---:|---:|---:|---:|
| ROCm7.2.3 noMTP | 53.58 | 53.16 | 393.18 | 20.832 |
| ROCm7.2.3 MTP3 | 83.42 | 66.75 | 387.02 | 21.160 |
| ROCm10.1.0 MTP3 | 84.03 | 66.33 | 386.65 | 21.182 |

10.1 is effectively tied for Sage; retain7.2.3. Latest official is10.1;
7.2.4/7.14.1 were subsequently tested and rejected; see [October22 comparison](ROCM-724-7141-2026-10-22.md).
[Detailed test/limits](SAGE-A15-2026-10-21.md) ·
[all trials](results/sage-a15-2026-10-21.json) ·
[ROCm/driver distinction and both-forum research](ROCM-SELECTION-2026-10-21.md).

## Active profile results

### Installed and measured builds

| Engine | Source / selected stack | Scope |
|---|---|---|
| llama.cpp | [4c3c5810](https://github.com/ggml-org/llama.cpp/commit/4c3c5810f87efe177949f1b85ae509d38a2a311f); MoE HIP | Four MoE profiles (Empero, Super, Sage, Ornith) on HIP 7.2.3; no Vulkan profile remains; both GPUs, unchanged expert backing/cache/MTP/contexts |
| SGLang | [f84475cc](https://github.com/StevenChenSE/sglang/commit/f84475ccf593087df3d1da13c9e675eadee12352), retained ROCm 7.2.3 stack | TP2 DFlash2/BF16 KV/163840; local RDNA repairs preserved |
| vLLM | 0.32.1rc1.dev36+ge68efc685.rocm72, retained ROCm 7.2.3 stack | Qwen: TP2/compiled MTP3/BF16 KV/163840. Bolt: TP2/AutoRound W4A16/BF16 KV/262144 |
| Strata | [9ae93f7b/0.1.46.1](https://github.com/Niko1221/Strata/commit/9ae93f7b1fe989d04a8e404d32cddaeeff10505f), ROCm 7.2.3 | Q3/13.5GiB/six workers/256K/INT8 KV32K resident; native frontend unchanged |
| Maya | [25deec5/v1.1.24](https://github.com/mw00/project-maya/commit/25deec505b525212e05faa58697d9d2b7d17fdb3), ROCm 7.2.3 | Both 32K Maya-S profiles; guards/quants retained; GLM MMQ with failed fused path disabled |
| ComfyUI | [8f04fd6e/0.42.0](https://github.com/Comfy-Org/ComfyUI/tree/8f04fd6ecf4a548937971e840af2a985529fab76), Torch2.15 nightly/packaged ROCm7.2.1 | Normal-RAM image/video controls; browser/native Desktop share this stack |

### October 21 shared-method baseline (historical)

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
| Qwen3.6-35B-A3B MXFP4_MOE (retired Oct23) | llama.cpp HIP 7, cache/MTP3 | 262,144 | 8,183–8,188 | 379.6 | 21.579 | 0.059 / 0.059 | 124.95 / 76.72 |
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
