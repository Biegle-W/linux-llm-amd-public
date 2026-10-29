# All-model benchmarks on actual 32 GB RAM — October 29, 2026

**Current availability — October 29:** Qwen27B/SGLang is qualified and enabled after the ROCm multicast/VRAM-guard correction; eight working profiles remain available. Ornith, both DeepSeek XS routes and Qwen Flash Next/Strata remain paused until the owner reports more RAM. Actual spill protection and all other guards remain. [Fix and verification](SGLANG-VRAM-GUARD-FIX-2026-10-29.md).

**Complete within the measured scopes below.** Host: i9-13900KS, 30.56 GiB OS-visible physical RAM, two RX 7900 XTX cards. No production profile was changed by this remaining-model series.

Snapshot: 2026-10-29T03:28:19.532436-04:00.

Configured swap capacity at this snapshot: 33.53 GiB. Swap is explicitly allowed under loading-swap-v3 and is not counted as physical RAM or dedicated VRAM.

| Stage | State |
|---|---|
| Original resident series | completed |
| Missing prefill/continuous recovery | completed |
| Bounded native placements | complete |
| Qwen-Image and FLUX | complete |
| SGLang graph-disabled candidate | completed |
| SGLang graph-disabled 1024-token buffer candidate | completed |
| Ornith client readiness-poll recovery | complete |
| Super balanced-cache non-mmap fallback | complete |
| Physical-RAM native placements | complete |
| Conditional Ornith paged placement | complete |

Stages are finished; qualification outcomes below include retained guard stops and loading timeouts.

Three timed code/prose trials follow an excluded warmup per task; prefill uses three fresh approximately 8K salted marker prompts. Values are medians. Prefill **N** is native engine timing; **E** is measured engine-phase timing. Fresh TTFT starts at request submission and ends at the first reasoning/content token; loading is excluded. Context is configured capacity, not a claim that every row exercised the full window. Storage is decimal allocated associated-file GB from the October 27 inventory.

## VRAM only models

| Model / engine | Date / status | Prefill t/s | Fresh TTFT s | Code / prose t/s | Context tokens | GB | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| Empero IQ4_XS · llama.cpp `19cce6919992` | Oct28 / measured selected runtime | 3,402.9 N | 2.416 | 132.46 / 83.76 | 262,144 | 19.63 | SATA1 `GGUF-Models/Empero-Qwen3.8-35B-A3B-Distill` |
| Flint UD-Q4_K_XL · llama.cpp `19cce6919992`, reasoning128 | Oct28 / measured selected runtime | 6,031.9 N | 1.398 | 46.89 / 46.94 | 32,768 | 25.06 | SATA1 `GGUF-Models/Flint-40B-A2.5B` |
| Sage-A1.5 W4A16 AutoRound · vLLM `0.32.1rc1.dev602+g5d35ce393.rocm72` | Oct28 / Oct29 / measured selected runtime | 5,075.2 E | 1.657 | 120.11 / 111.20 | 65,536 | 20.33 | SATA1 `vLLM-Models/Sage-A1.5-W4A16-AutoRound` |
| Qwen3.8-27B W4A16 · vLLM `0.32.1rc1.dev602+g5d35ce393.rocm72` | Oct28 / Oct29 / measured selected runtime | 1,403.6 E | 5.865 | 142.01 / 78.15 | 163,840 | 20.05 | System `models/Qwen3.8-27B-W4A16-AutoRound-GPTQ` |
| Nemotron3.5 Bolt74B-A9B W4A16 · vLLM `0.32.1rc1.dev435+gc50aca144.rocm72` held | Oct28 / Oct29 / measured selected runtime | 2,787.9 E | 2.906 | 38.04 / 37.88 | 262,144 | 43.65 | SATA1 `vLLM-Models/Nemotron-3.5-Bolt-74B-A9B-AutoRound-W4A16` |
| Qwen27B W4A16 · SGLang `f84475ccf593`, DFlash2 | Oct29 / low-buffer candidate did not qualify | — | — | — / — | 163,840 | 21.34 shared base + draft | System `models/Qwen3.8-27B-W4A16-AutoRound-GPTQ` + `models/drafts/Qwen3.8-27B-DFlash2-W4A16` |

Sage, Qwen vLLM and Bolt retain their valid original short trials; their missing prefill/continuous stages are measured in separate client sessions after repairing the client tokenizer dependency. Engine versions, quantization, contexts and pins remain. Flint retains its 128-token reasoning budget; visible-answer TTFT is separately recorded in the numeric evidence. SGLang’s original graph capture spilled dedicated VRAM and is excluded; a graph-disabled retry is an isolated candidate, with the same 163,840-token actual KV-capacity gate.

The LLM series measures text inference. Sage remains text-only; this series does not requalify vision support or change its retained capability limits.

A second isolated graph-disabled candidate reduces the temporary prefill chunk and maximum-prefill token caps from 2,048 to 1,024 after the first eager attempt spilled 121 MiB. Context, actual KV-capacity requirement, weights, quantization, DFlash settings, Mamba cache and all guards remain. Its result is reported separately; no production promotion.

Historical pre-fix Qwen27B/SGLang trial: **the low-buffer candidate did not qualify**. Dedicated-VRAM-spill guard stopped startup before a valid timing series. Owned cleanup and unchanged configuration fingerprints are verified.

**Earlier residency review, superseded by the qualified fix above — October 29:** The two graph-disabled attempts were terminated by the monitor's `vram_spill` rule after `drm-total-vram - drm-resident-vram` reached **121.273 MiB**. Both worker logs reported **6.00 GB available GPU memory** and completed application startup, before health/qualification finished. The graph-disabled and smaller-buffer attempts retained at least **17.07 / 17.61 GiB available host RAM**. These are guard stops; the saved evidence does not establish a physical-RAM admission failure or GPU out-of-memory failure. The [kernel counter definitions](https://docs.kernel.org/gpu/drm-usage-stats.html#memory) allow total buffers to include backing storage that is not yet instantiated, so this difference alone does not prove GPU-to-host eviction. Actual eviction versus transient/lazy-allocation accounting remains unresolved; the identical difference across both retries is a reason to audit the residency check, not proof of its cause. Additional system RAM is not an established fix. Original failure flags remain unchanged, no guard was relaxed, and no GPU trial was repeated. The owner pause remains in effect.

## MoE models with CPU RAM offload

| Model / engine | Date / status | Prefill t/s | Fresh TTFT s | Code / prose t/s | Context tokens | GB | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| Super120B UD-IQ3_XXS · llama.cpp `2280f0fd163b` | Oct29 / super-original-cache2; isolated | 371.2 N | 22.130 | 11.22 / 12.09 | 32,768 | 59.76 | NVMe `Nemotron-Super` |
| Super120B UD-IQ3_XXS · llama.cpp `2280f0fd163b` | Oct29 / super-original-physical; isolated | 434.6 N | 18.876 | 15.61 / 17.18 | 32,768 | 59.76 | NVMe `Nemotron-Super` |
| Ornith122B Q4_K_M · llama.cpp `2280f0fd163b` | Oct29 / retained CPU profile held; see file/paged attempts | — | — | — / — | 32,768 | 76.76 | SATA1 `GGUF-Models/Ornith-1.5-122B-GGUF` |

Native placements are isolated from the retained Super/Ornith production profiles. The bounded Super arm used experimental MemoryHigh/Max 20/22 GiB. The later physical-RAM series uses actual MemTotal for MemoryMax and no artificial MemoryHigh. RAM expert backing may page under the allowed swap policy; it is not a fully resident capacity claim. File-backed mmap candidates explicitly depend on SSD reads. Super’s passed near 31K/history checks and Ornith’s actual exercised scope are recorded per arm.

Metadata-only inventory finds 55.65 GiB of Super tensor weights and 70.62 GiB of Ornith weights. Both exceed the combined physical VRAM before KV, compute and reserve requirements. Increased GPU expert caches are tested within the existing floors; CPU or file/paged backing remains necessary at these fixed quantizations.

## MoE models with SSD streaming

### Native file-backed or swap-paged candidates

No completed valid native file-backed measurement in this class.

These isolated candidates use mmap file reads or explicit swap-paged CPU buffers. They do not replace the normal streaming-engine profiles below and are not fully resident RAM capacity claims.

### Streaming engine profiles and compared tiers

| Model / engine | Date / status | Prefill t/s | Fresh TTFT s | Code / prose t/s | Context tokens | GB | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| Qwen / Strata `0.1.49.2/7dd5cf18e68c` | Oct28 / strata-iq3-profile-small; native candidate, held | 1,013.6 N | 8.098 | 36.42 / 37.35 | 262,144 | 128.14 | NVMe Strata/models, Strata/packs, Strata/mtp |
| Qwen / Strata `0.1.49.2/7dd5cf18e68c` | Oct28 / strata-iq3-profile-large; active temporary 32 GB | 1,155.8 N | 7.104 | 70.15 / 50.95 | 262,144 | 128.14 | NVMe Strata/models, Strata/packs, Strata/mtp |
| GLM / Maya `1.1.26/f26d8bab43f9` | Oct28 / maya-glm-profile-small; active temporary 32 GB | 440.9 N | 18.922 | 5.76 / 5.66 | 32,768 | 97.42 | NVMe Maya/Maya-S-v2-IQ2_XXS |
| GLM / Maya `1.1.26/f26d8bab43f9` | Oct28 / maya-glm-profile-large; native candidate, held | 464.6 N | 17.771 | 6.42 / 6.68 | 32,768 | 97.42 | NVMe Maya/Maya-S-v2-IQ2_XXS |
| DeepSeek XS / Maya `1.1.26/f26d8bab43f9` | Oct28 / maya-deepseek-profile-large; native candidate, held | 684.1 N | 11.993 | 2.76 / 2.12 | 32,768 | 281.87 shared | NVMe Maya/DeepSeek-V4.1-Flash-1017-GGUF |
| DeepSeek XS / Maya `1.1.26/f26d8bab43f9` | Oct28 / maya-deepseek-profile-small-retry1; native candidate, held | 691.1 N | 11.834 | 2.91 / 1.72 | 32,768 | 281.87 shared | NVMe Maya/DeepSeek-V4.1-Flash-1017-GGUF |
| DeepSeek XS / Strata `0.1.49.1/8183c6b67162` | Oct28 / strata-deepseek-xs-profile-small; native candidate, held | 185.6 N | 44.067 | 2.95 / 1.86 | 32,768 | 281.87 shared | Same XS weights; NVMe Strata/DeepSeek-V4.1-Flash-1017 metadata |
| DeepSeek XS / Strata `0.1.49.1/8183c6b67162` | Oct28 / strata-deepseek-xs-profile-large-retry1; native candidate, held | 185.2 N | 44.159 | 3.29 / 1.66 | 32,768 | 281.87 shared | Same XS weights; NVMe Strata/DeepSeek-V4.1-Flash-1017 metadata |

Qwen/Strata large and GLM/Maya small are the previously activated temporary 32 GB profiles. Both DeepSeek engines retain their prior production profiles: their native 32 GB rows are valid measurements, with mixed performance and incomplete activation qualification. GLM’s larger tier passed native tests but failed normal RAM admission; the smaller qualified tier remains selected. These completed October 28 tests were reused. The DeepSeek storage set is shared. [Qualification and exclusions](SSD-STREAMING-32GB-2026-10-28.md).

## Images and video

| Workflow | Timed trials | Fresh request median s | Range s | Encoder costs | Status |
|---|---:|---:|---:|---|---|
| qwen-image | 3 | 190.720 | 171.490–210.335 | included | passed; visual review complete |
| flux-t2i | 3 | 170.274 | 156.815–185.506 | included | passed; visual review complete |
| flux-edit | 3 | 161.970 | 161.705–196.266 | included | passed; visual review complete |
| H3 single GPU, reused Oct28 | 3 | 179.209 | 171.416–220.722 | excluded | passed within sampled scope |
| H3 actual RCCL TP2, reused Oct28 | 3 | 153.773 | 130.983–180.981 | excluded | passed within sampled scope |

Qwen/FLUX retain the saved staged component placement: transformer on GPU0, encoder/upsampler and VAE stages on GPU1. The H3 rows separately compare one-card execution with actual RCCL TP2.

Qwen-Image: 512×512, 40 steps. FLUX text-to-image: 1024×1024, 16 steps. FLUX reference edit: 1248×832. Each image workflow uses an excluded fresh-server warmup and three timed fresh servers; complete request times include encoder/upsampler/model reads, sample, decode and save. Server readiness is separate. Older warm-server Qwen timings are not comparable to these requests. H3 uses the completed matched 32 GB 608×352/39-frame test and excludes encoder cost; its sampler medians are 33.980/44.263 s single/TP2. [H3 scope and quality limits](../graphics/H3-MATCHED-32GB-2026-10-28.md).

| Image component set | Allocated GB | Storage |
|---|---:|---|
| qwen-image | 33.12 | SATA1 `Graphics-Models/diffusion_models`, `text_encoders`, `vae` |
| flux-t2i | 30.06 | SATA1 `Graphics-Models/diffusion_models`, `text_encoders`, `vae` |
| flux-edit | 30.06 | SATA1 `Graphics-Models/diffusion_models`, `text_encoders`, `vae` |

Image sizes include the workflow’s transformer, encoder(s), prompt upsampler where used, and VAE; metadata-only file stats measured October 29. FLUX text-to-image and edit share the same components and must not be added together. Video component storage remains in its dated report.

Reviewed qwen-image output, from the trial with the median request time:

![qwen-image reviewed sample](results/media/qwen-image.png)

Reviewed flux-t2i output, from the trial with the median request time:

![flux-t2i reviewed sample](results/media/flux-t2i.png)

Reviewed flux-edit output, from the trial with the median request time:

![flux-edit reviewed sample](results/media/flux-edit.png)

## Safety and measured limitations

All independent guards and loading-swap-v3 remained. LLM host floor: 3 GiB. Resident frameworks retain their profile-specific launcher/admission/runtime limits. The Super/Ornith placement harness retains the 3 GiB VRAM reserve and 1.5 GiB hard floor. Images retain the 3 GiB host floor and 2/1.5 GiB VRAM soft/hard floors with four soft samples. Dedicated VRAM spill allowed: zero. Image and physical native scopes use actual MemTotal. Completed H3 retains its separately qualified 1 GiB host floor. Swap occupancy, reads, rates and PSI alone do not stop a task; OS oomd is unchanged.

| Native arm | Load mode / GPU expert cache MiB | MemoryHigh / Max GiB | Result | Attribution |
|---|---|---:|---|---|
| super-original-cache2 | none / 2048 | 20.00 / 22.00 | passed | Passed checks within recorded scope |
| ornith-mmap-cache6 | mmap / 6144 | 18.00 / 20.00 | failed | TimeoutError: Native model loading |
| ornith-mmap-cache4 | mmap / 4096 | 18.00 / 20.00 | failed | TimeoutError: Native model loading |
| super-original-physical | none / 2048 | none / 30.56 | passed | Passed checks within recorded scope |
| super-balanced-mmap-cache4-physical | mmap / 4096 | none / 30.56 | failed | TimeoutError: Native model loading |
| super-balanced-mmap-cache3-physical | mmap / 3072 | none / 30.56 | failed | TimeoutError: Native model loading |
| ornith-mmap-cache4-physical | mmap / 4096 | none / 30.56 | failed | TimeoutError: Native model loading |
| ornith-paged-cache6-20 | none / 6144 | 18.00 / 20.00 | failed | TimeoutError: timed out |
| ornith-paged-cache4-20 | none / 4096 | 18.00 / 20.00 | failed | TimeoutError: timed out |
| super-balanced-direct-cache4-physical | none / 4096 | none / 30.56 | failed | RuntimeError: Desktop VRAM headroom low: minimum 2.74 GiB free |
| super-balanced-direct-cache3-physical | none / 3072 | none / 30.56 | failed | RuntimeError: Desktop VRAM headroom low: minimum 2.96 GiB free |
| ornith-poll-recovery-cache6-20 | none / 6144 | 18.00 / 20.00 | failed | TimeoutError: Native model loading |
| ornith-poll-recovery-cache4-20 | none / 4096 | 18.00 / 20.00 | failed | TimeoutError: Native model loading |

The two early Ornith mmap arms reached the 15-minute loading deadline without a host-floor, OOM or dedicated-VRAM-spill fault. That is a bounded loading timeout, not proof the model cannot run on 32 GB. Harness setup and preflight failures are retained separately from measured inference failures.

Loading-deadline arms: `ornith-mmap-cache6`, `ornith-mmap-cache4`, `super-balanced-mmap-cache4-physical`, `super-balanced-mmap-cache3-physical`, `ornith-mmap-cache4-physical`, `ornith-poll-recovery-cache6-20`, `ornith-poll-recovery-cache4-20`. They have no inference speed result; use the completed arms separately.

The original paged-loader client could abort on a single 30-second readiness-poll timeout before its model-loading deadline. Those attempts are retained as client/harness failures. A separate recovery retries transient readiness polls within the original 900-second deadline and reuses the same RAM caps, placement and guards; only its completed valid timings are eligible.

Sequential small samples and natural file caching leave storage, execution-order, desktop and thermal/power variation. Synthetic functional/marker checks and sampled visual review do not establish general quality, maximum resolution/context capacity or equivalence. Historical 64 GB results remain in dated reports and are not a matched causal RAM comparison. No benchmark candidate is automatically promoted.

Sampled headroom and lifecycle swap/spill for passed arms:

| Arm | Min available host GiB | Min free VRAM GiB/card | Peak worker swap GiB | Spill bytes |
|---|---:|---:|---:|---:|
| empero-qwen3.8-35b-a3b | 22.87 | 11.96 / 10.64 | 0.00 | 0 |
| flint-40b-a2.5b | 23.90 | 9.61 / 11.19 | 0.00 | 0 |
| sage-a1.5 | 18.54 | 6.95 / 6.98 | 3.48 | 0 |
| qwen3.8-27b-vllm | 18.57 | 7.19 / 7.22 | 4.82 | 0 |
| nemotron-3.5-bolt-vllm | 18.79 | 1.17 / 1.20 | 4.72 | 0 |
| super-original-cache2 | 5.54 | 3.59 / 4.70 | 5.56 | 0 |
| super-original-physical | 4.81 | 3.59 / 4.70 | 6.95 | 0 |
| qwen-image | 9.15 | 10.08 / 6.72 | 3.05 | 0 |
| flux-t2i | 13.55 | 12.60 / 13.81 | 3.47 | 0 |
| flux-edit | 13.47 | 12.12 / 12.79 | 2.90 | 0 |

Resident free-VRAM minima cover the benchmark/continuous headroom observer after arithmetic; its separate lifecycle guard also covers loading. Native/image headroom minima cover their sampled lifecycle. Host availability and peak swap/spill use lifecycle telemetry. Sampled minima/maxima do not guarantee unsampled transients. Individual timings, lifecycle thermal summaries, checks and failures are retained in the numeric evidence; no thermal throttling absence is inferred solely from temperatures.

The exact 64 GB restoration preimages are retained. Restoration requires a new explicit user instruction plus the documented physical-RAM and idle prerequisites; RAM detection alone does not authorize it. No restoration automation is enabled. Coordinators, engine pins, contexts, guards and paused schedules remain.

[Numeric results and individual timing samples](results/all-models-32gb-2026-10-29.json), [current benchmark listing](CURRENT-AMD-BENCHMARKS.md), [prior SSD qualification](SSD-STREAMING-32GB-2026-10-28.md).
