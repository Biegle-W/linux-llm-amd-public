# Current dual-AMD benchmarks — October 29, 2026

## Nightly updater restored — October 29

The 03:00 daily engine updater is enabled; a manual guarded update run is in progress. This supersedes earlier updater-pause notes only. All existing manual runtime pins, other holds and qualification/safety gates remain. Do not duplicate `llm-daily-update.service` or its GPU reservation. [Current restoration/run status](ENGINE-UPDATER-RESTORED-2026-10-29.md); final promotion or rollback results are recorded in the daily ledger.

## Ornith maximum-VRAM 32 GB test / updater audit — October 29

Ornith has a scoped working isolated 32 GB placement; production remains held. [Measured attempts and limits](ORNITH-VRAM-32GB-2026-10-29.md). The overnight updater timer is absent/inactive; a read-only upstream check found five newer configured components and SGLang current on its AMD fork. [Version/coverage audit](ENGINE-UPDATE-AUDIT-2026-10-29.md). All owned experiment work is cleaned up; production hashes, guards and paused schedules remain.

## All models on 32 GB — measured October 29

The [all-model 32 GB benchmark](ALL-MODELS-32GB-2026-10-28.md) is complete within the recorded scopes, including Qwen-Image and FLUX. Fresh-server image request medians: qwen-image 190.720 s; flux-t2i 170.274 s; flux-edit 161.970 s. Current grouped tables distinguish measured selected runtimes, isolated native/SGLang candidates and retained profiles. All owned benchmark work is cleaned up; engine pins, contexts, guards, coordinators and paused schedules remain. No automatic promotion or restoration.

## Matched H3 on 32 GB — complete

The [matched newer H3 comparison](../graphics/H3-MATCHED-32GB-2026-10-28.md) is complete on real 32 GB RAM: three timed fresh-server trials per arm plus excluded warmups. Median request: **179.209 s single-GPU / 153.773 s actual fcys RCCL TP2** (14.2% shorter with TP2); both-ready sampler: **33.980 / 44.263 s**. Encoder costs are excluded. All eight AV/guard/cleanup checks passed; owned reservation released. Sampled visual limits remain; no production promotion.

## Temporary 32 GB SSD-streaming profiles — October 28

Activated temporary 32 GB profiles: **Qwen / Strata, GLM / Maya**. Held at the exact prior 64 GB profile: **DeepSeek XS / Maya, DeepSeek XS / Strata**. Each activation passed native safety/functional/performance/near-window/history checks and normal guarded authenticated JSON/SSE/tools/~8K/history checks. The exact 64 GB preimages are retained; restore only after at least 60 GiB physical RAM is visible and inference is idle. All other settings, guards, coordinator services and paused schedules remain. [Qualification, comparisons and limits](SSD-STREAMING-32GB-2026-10-28.md).

## Router validation — October 28

AMD router admission is implemented in source and validated: fair FIFO, bounded
pending count/bytes, consistent sanitized health and preserved backend HTTP/SSE
errors. **71 CPU regressions per checkout** and two 32-token Sage JSON/SSE smokes
pass. The user-authorized idle hub/gateway restart is complete; the new router
code is active and authenticated health passes. Profiles, guards, pins and paused
schedules remain unchanged.
No throughput or quality benchmark changed. [Transport smoke and CPU evidence](ROUTER-ADMISSION-2026-10-28.md).

[AMD H3 encoder-format comparison](../graphics/H3-AMD-ENCODER-FORMATS-2026-10-28.md): Tested W4A8 on the same H3 encoder against corrected NVFP4. Native HIP INT8 encoding was 5.91–8.11× faster across three prompts after warmup; separate cold-file load times, RAM/VRAM, nine paired TP2 clips and quality limits are recorded. Native W4A8 preserves the sampled main scenes, with design changes and shared prompt limitations; it remains an isolated tested candidate. Both host floors remain 1 GiB; other guards and production selection remain.

## Fresh H3 one-card versus two-card test — October28

Fresh tests completed on one physical 7900 XTX and on two 7900 XTX cards: one excluded warmup plus three timed 39-frame generations per arm, with a new isolated server for every generation. Full-request medians are 270.098 s on one card and 146.603 s on two (45.7% shorter on the two-card path). Sampler medians are 30.237/59.749 s. This establishes the measured fresh-server workflow result; loader/storage/noise/source differences limit attribution to GPU count alone. All independent guards and loading-swap-v3 remained. No production promotion or native Radiance run. [Fresh protocol, individual samples and limits](../graphics/H3-ONE-VS-TWO-2026-10-28.md).

## Current policy and pending GPU compatibility — October 28

**Current swap policy: loading-swap-v3.** Loading, parked swap and reads are allowed. Rates/pressure are advisory; there is no default automatic swap-rate stop. An optional stop needs an explicit write budget plus matched measured inference slowdown. Old policy settings alone cannot restore historical stop rules. [Policy evidence](SWAP-TASK-CONTINUITY-2026-10-28.md). [Radiance H3](../graphics/RADIANCE-H3-PREFLIGHT-2026-10-28.md) has no compatible gfx1100 accelerated kernel target; no GPU video or speedup was measured. Existing benchmark values keep their original hardware, build and policy. Earlier v2 guard stops remain historical and do not prove SSD damage or a v3 failure.

## RAM configuration after reboot — October 28

Linux now exposes **30.56 GiB**. The LLM tables below retain their October27 14.83 GiB and earlier 64 GB measurements; the new 32 GB SSD-streaming section above supplies fresh October28 LLM results; the other historical rows keep their original RAM attribution. [H3 comparison and limitations](../graphics/H3-POST-UPGRADE-2026-10-28.md) are separate diffusion evidence.

## Current 32 GB results — October 28–29

Latest measurements on 30.56 GiB physical RAM; selected production profiles and isolated candidates are explicitly distinguished. N=native prefill; E=engine-phase prefill; fresh TTFT excludes model loading. See the [all-model report](ALL-MODELS-32GB-2026-10-28.md) and [numeric samples](results/all-models-32gb-2026-10-29.json) for memory, individual trials, exclusions and qualification limits. Historical 64 GB results remain in dated reports.

### VRAM only models

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

Qwen27B W4A16 · SGLang `f84475ccf593`, DFlash2: **low-buffer candidate did not qualify**. Dedicated-VRAM-spill guard stopped startup before a valid timing series. Owned cleanup and unchanged configuration fingerprints are verified.

### MoE models with CPU RAM offload

| Model / engine | Date / status | Prefill t/s | Fresh TTFT s | Code / prose t/s | Context tokens | GB | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| Super120B UD-IQ3_XXS · llama.cpp `2280f0fd163b` | Oct29 / super-original-cache2; isolated | 371.2 N | 22.130 | 11.22 / 12.09 | 32,768 | 59.76 | NVMe `Nemotron-Super` |
| Super120B UD-IQ3_XXS · llama.cpp `2280f0fd163b` | Oct29 / super-original-physical; isolated | 434.6 N | 18.876 | 15.61 / 17.18 | 32,768 | 59.76 | NVMe `Nemotron-Super` |
| Ornith122B Q4_K_M · llama.cpp `2280f0fd163b` | Oct29 / retained CPU profile held; see file/paged attempts | — | — | — / — | 32,768 | 76.76 | SATA1 `GGUF-Models/Ornith-1.5-122B-GGUF` |

Native placements are isolated from the retained Super/Ornith production profiles. The bounded Super arm used experimental MemoryHigh/Max 20/22 GiB. The later physical-RAM series uses actual MemTotal for MemoryMax and no artificial MemoryHigh. RAM expert backing may page under the allowed swap policy; it is not a fully resident capacity claim. File-backed mmap candidates explicitly depend on SSD reads. Super’s passed near 31K/history checks and Ornith’s actual exercised scope are recorded per arm.

Metadata-only inventory finds 55.65 GiB of Super tensor weights and 70.62 GiB of Ornith weights. Both exceed the combined physical VRAM before KV, compute and reserve requirements. Increased GPU expert caches are tested within the existing floors; CPU or file/paged backing remains necessary at these fixed quantizations.

### MoE models with SSD streaming

#### Native file-backed or swap-paged candidates

No completed valid native file-backed measurement in this class.

These isolated candidates use mmap file reads or explicit swap-paged CPU buffers. They do not replace the normal streaming-engine profiles below and are not fully resident RAM capacity claims.

#### Streaming engine profiles and compared tiers

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

### Images and video

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

**NVIDIA-agent notes delivered — October27:** the user requested a
[NVIDIA-server handoff](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/main/docs/AMD-PARITY-HANDOFF-20261027.md) for agents there to address the gap queue.
It is published in both NVIDIA repositories and linked from their README/AGENTS;
their public export allowlist includes those notes. This delivery changes only
documentation/discovery/export metadata, with no runtime, benchmark, guard or
schedule change. G3's agent entry point is added; the GLM table repair and runtime
items remain for NVIDIA-host work. AMD-owned G5/G7 remain separate. Optional new
models and schedules still require the specific choices in the handoff.

## Handoff and cross-repository review — October 27

Read-only AMD/native Linux NVIDIA [gap audit](AMD-NVIDIA-GAP-AUDIT-2026-10-27.md):
no new inference measurements or selected settings in this review. The latest
Sage INT4 selection/retirement below remains current. Root README/AGENTS and the
canonical handoff now record the standing takeover-ready documentation requirement.
Proposed parity changes await the user's choice; no NVIDIA source/runtime changed.

## Earlier Sage INT4 activation on dev435 — October27

Sage now uses native W4A16 INT4 on the installed vLLMdev435 runtime under the
same `sage-a1.5` ID,64K/TP2/MTP3. Normal API/tools/JSON/SSE/history and
62,009-token markers pass. Selected benchmark: engine-phase prefill
4142.6t/s, fresh TTFT2.001s, code/prose148.04/138.33t/s,
20.33GB SATA1. Native image checks failed on both tested vLLM builds; the replacement is text-only. The slower Sage GGUF and
exclusive projector are removed (22.61GB reclaimed); all other GGUFs remain.
Twelve profiles remain; DSH default, remaining engine pins, current swap policy,
independent guards and paused updater remain. Earlier same-day snapshots below
retain their original status; this selection supersedes their Sage GGUF state.
[Comparison, compatibility results and removal](SAGE-INT4-REPLACEMENT-2026-10-27.md).

## Loading-swap framework/INT4 retry — October27

Recorded 13 model/kernel attempts on 14.83 GiB RAM with loading swap allowed;
6 completed benchmark/memory checks, including a no-thinking Flint diagnostic.
Qwen/Bolt vLLM and Sage native INT4 text tests completed; the original Qwen
paging stop and its successful unchanged-setting confirmation are both retained.
SGLang hit VRAM/telemetry/kernel blockers; matched reasoning128 Flint remained
partial at the inference swap-write guard. Three earlier systemd-syntax setup
failures are separate. Selected versions/profiles and the paused updater remain;
no models were retired and H3 was not retried.
[All attempts, benchmark fields and thermals](LOADING-SWAP-RETRY-2026-10-27.md).


## Current-RAM retest — October27

After verified inactive compiler temps were retained on disk, both H3 and blocked
vLLM/SGLang/native INT4 profiles were retried with more free RAM and unchanged
guards. H3 advanced to text-encoder loading, then hit its RAM floor; LLM loading
still hit the swapout budget, with an additional Sage auto-Marlin HIP compile
failure. No new model/engine promotion or retirement; no new inference medians.
[All attempts, memory counters and thermals](CURRENT-RAM-RETEST-2026-10-27.md).


## VRAM engine refresh — October27

Qualified llama.cpp19cce691 for Empero/Sage/Flint with profile-specific source
pins; CPU profiles retain2280f0fd. New vLLM dev602 and Sage/Flint native INT4
trials remain held by current-host loading guards; production staysdev435.
Required SGLang f84475cc is already latest. All current guards/settings and the
paused updater remain. [Full fields, paired medians, source pins and failed attempts](VRAM-ENGINE-UPDATE-2026-10-27.md).


## Earlier October27 Flint reasoning-budget128 benchmark (2280f0fd)

Fresh normal-launcher/authenticated API medians on both RX 7900 XTX and 14.83 GiB
host RAM: native prefill **6034.8 tokens/s**, fresh ~8K first-token TTFT
**1.396 s**, code/prose decode **46.63/46.57 tokens/s**.
First visible-answer TTFT is **4.436 s**; decode includes reasoning.
Context 32,768, storage 25.06 GB on SATA1, retained 2280f0fd/ROCm 7.2.3, VRAM-only,
reasoning 128 and all guards remain. Three runs/task, all fresh markers pass;
zero worker swap/spill, full lifecycle thermals and owned cleanup pass.
Earlier reasoning-off timings stay separate.
[Report](FLINT-REASONING128-2026-10-27.md) and
[all trials](results/flint-reasoning128-2026-10-27.json).


## Earlier VRAM-default activation and Flint — October27 (Sage since replaced above)

Empero256K/MTP3/batch512 and Sage64K/MTP3/projector/batch4096 now default to
VRAM-only on both GPUs. Flint is selectable at32K with a128-token reasoning
budget. Normal launcher/authenticated API, tools/JSON/SSE, long markers/history
(Empero257,996 input, Sage62,009, Flint29,986) and Sage vision pass; verified
4GiB high/5GiB max/no-swap workers retain all existing guards. The zero-reasoning
Flint history failure is recorded; the selected bounded setting passes the same
question. Earlier isolated timing medians are not a new production A/B speedup
claim. [Activation report](VRAM-DEFAULTS-2026-10-27.md) and
[numeric evidence](results/vram-defaults-2026-10-27.json).

## Backup cleanup and all-VRAM candidates — October27

Super's SATA backup and the old GLM S24 rollback are removed (156.47GB reclaimed);
active model dependencies remain. Strata Qwen Q3 is **SSD stream**, with bounded
RAM/GPU tiers. Isolated dual-GPU all-VRAM text probes pass for Empero256K/MTP3
(batch512), Sage64K/MTP3/projector (batch4096) and Flint32K/reasoning-budget0.
Three-trial median code/prose/nativePP: Empero131.41/80.42/3397.2; Sage91.26/74.31/4619.7;
Flint46.86/46.90/6027.1t/s. All selected runs have zero worker swap/spill and valid
continuous-inference windows. These are candidate experiments, not a fresh CPU
A/B, normal-launcher qualification or production placement change. Earlier failed
attempts and thermal evidence remain. [Report](STORAGE-VRAM-2026-10-27.md) and
[numeric record](results/storage-vram-2026-10-27.json).

## DeepSeek-S retired — October26

At the user's request, S is removed from Maya and Strata; **11 profiles** remain.
XS keeps the shared S Engram shards5/6, matching xs2 drafter and original pack
metadata. S-only shards1–4, old drafter, metadata and routing seeds were removed,
reclaiming **186.18 GB** on Shared NVMe. Config/pack seals and both XS dependency
maps are unchanged. This is storage/CPU/API verification only; no new inference
or speed measurement, and the reduced-RAM holds and paused updater remain.
[Removal, retained dependencies and limits](DEEPSEEK-S-RETIREMENT-2026-10-26.md).

## Fresh engine tests — October25

Fresh normal-launcher gates promoted llama.cpp `2280f0fd` on all four profiles.
Maya 1.1.28 failed DeepSeek XS code/prose and S prose decode gates, then rolled back
to 1.1.26 with the restored GLM launcher answering. Strata DeepSeek 0.1.51 failed
selected IQ3_XXS kernel parity on both cards before installation; 0.1.49.1 stays.
All completed memory records met the new 64 MiB cap/zero spill. Actual counts,
full trials, lifecycle memory and sampled thermals are retained; no full-window
or general speedup claim. [Report](FRESH-ENGINE-TESTS-2026-10-25.md) and
[numeric record](results/fresh-engine-tests-2026-10-25.json).

## Minor worker swap allowance — October25 (validation only)

User-authorized update acceptance now permits up to 64 MiB (67,108,864 bytes) of
aggregate inference worker swap per model and full lifecycle, including loading;
larger swap fails. Zero VRAM spill, valid telemetry, model coverage and all
performance/quality gates remain. All 18 CPU memory/promotion/rollback tests pass.
Saved October25 llama.cpp/Maya/Strata DeepSeek baselines pass the new memory gate;
vLLM dev466 still fails large swap and Qwen prose regression. Historical nightly
outcomes remain unchanged. No fresh GPU/throughput test or runtime promotion;
worker cgroup limits and live guards remain. [Policy and replay limits](daily-update/README.md#minor-worker-swap-allowance--october-25).


## Strata Qwen table selection — October24

The matching gfx1100/hipBLASLt100202 table is now selected on source8183c6b6/HIP7.2.3;
Linux model `qwen3.8-flash-next-iq3_xxs` retains262144 context, prefill2048 and every
existing dual-GPU/memory guard. Windows CUDA profiles and connection settings are unchanged. Pooled repeated
controls→table: native fresh~8K PP **916.1→1208.85t/s (+32.0%)**,
external fresh TTFT **8.973→6.807s**. Normal-production
three-trial medians: code/prose **77.38/50.61t/s**, PP**1208.2**,
fresh TTFT**6.810s**. This is an exact-build settings comparison,
not a universal decode/quality speedup.4096 failed unchanged5GiB/card startup
admission (4.655/5.510GiB);8192 was not attempted. Near257990-input markers,
full-history follow-up, JSON/tools/SSE/originalUI/authenticated host-self API pass;
zero owned swap/spill. [Gates, failures and full-run thermals](STRATA-TUNING-2026-10-24.md)
and [all trials](results/strata-tuning-2026-10-24.json).

## Strata 0.2.4 DeepSeek — October 24

The October24 integration reused the existing Maya-S and Maya-XS weights with independent metadata, both GPUs and 32K. **13 active profiles**; all Maya choices and the Strata Q3 DSH default remain. Separate gfx1100 / HIP 7.2.3 DeepSeek engine 0.1.49.1 at 8183c6b6; the current Qwen engine is8183c6b6 (October24 daily promotion). No weight download/duplication, no new ports.

| Model ID | RAM-store GB | Code / prose t/s | Native PP t/s | TTFT s |
|---|---:|---:|---:|---:|
| `deepseek-v4.1-flash-1017-strata-s` | 0 | 7.00 / 7.16 | 168.0 | 37.491 |
| `deepseek-v4.1-flash-1017-strata-xs` | 0 | 18.25 / 12.77 | 183.7 | 34.289 |

Exact-binary isolated timings, three code/prose trials with a 256-token output cap and three fresh prompts with ~6.3K actual input tokens; native prefill and external SSE TTFT/decode are distinct. Selected profiles pass the normal Ptyxis launcher, original UI, authenticated host-self API, near-31.5K/history checks and Q3 switchback with zero owned swap/spill. These are not a matched Maya speed comparison. [Setup, gates and thermals](STRATA-DEEPSEEK-2026-10-24.md) · [numeric record](results/strata-deepseek-2026-10-24.json).


## Eleven profiles measured — October23 (pre-daily-update builds)

Every active profile was re-run with its production launcher and unchanged settings, using the shared
method (three 256-output code/prose runs, three fresh ~8K marker prompts, medians), one backend at a time,
after enabling GPU fan control (OverDrive `amdgpu.ppfeaturemask=0xfff7ffff`, CoolerControl max-cooling
curves on every fan) and BIOS OS-controlled ASPM. **All eleven passed** (all markers, no cache reuse, both
GPUs, zero VRAM spill).

| Model · engine | Context | Code / prose decode t/s | Fresh PP t/s | Fresh TTFT s | Actual fresh input | vs previous: code / prose / PP |
|---|---:|---:|---:|---:|---:|---|
| Empero Qwen3.8-35B-A3B IQ4_XS · llama.cpp | 262,144 | 119.89 / 72.61 | 2,988.5 | 2.748 | 8,185–8,188 | -1.3% / -1.2% / +1.5% |
| Sage-A1.5 Q4_K_M · llama.cpp MTP3 | 65,536 | 80.42 / 64.93 | 2,839.2 | 2.892 | 8,186–8,188 | -0.5% / -0.4% / +1.6% |
| Nemotron Super IQ3_XXS · llama.cpp | 32,768 | 15.63 / 17.14 | 433.4 | 18.300 | 7,924–7,925 | -0.1% / -0.5% / +0.5% |
| Ornith-1.5-122B Q4_K_M · llama.cpp | 32,768 | 11.43 / 13.32 | 717.2 | 11.425 | 8,187–8,189 | -0.1% / -0.1% / +0.3% |
| Qwen3.8-27B INT4 · SGLang TP2 DFlash2 | 163,840 | 206.18 / 71.08 | 1,468.8ᵉ | 5.585 | 8,187–8,189 | -2.6% / -2.1% / +1.3% |
| Qwen3.8-27B INT4 · vLLM TP2 MTP3 | 163,840 | 134.82 / 71.73 | 1,511.0ᵉ | 5.435 | 8,186–8,191 | +0.7% / +1.2% / +2.4% |
| Nemotron Bolt W4A16 · vLLM TP2 | 262,144 | 38.12 / 38.08 | 2,950.4ᵉ | 2.699 | 7,923–7,927 | +2.1% / +2.3% / -0.3% |
| Qwen3.8-Flash-Next IQ3_XXS · Strata | 262,144 | 78.05 / 47.63 | 916.0 | 8.974 | 8,185–8,187 | +0.9% / -10.6% / +0.8% |
| GLM-5.3-Flash Maya-S · Maya | 32,768 | 18.64 / 16.28 | 539.1 | 13.289 | 6,310–6,312 | -5.5% / +3.8% / +0.7% |
| DeepSeek-V4.1 Maya-XS + DSpark · Maya | 32,768 | 27.60 / 13.67 | 448.1 | 14.074 | 6,299–6,300 | -11.8% / -11.0% / +0.6% |
| DeepSeek-V4.1 Maya-S · Maya | 32,768 | 6.73 / 6.78 | 301.2 | 20.919 | 6,296–6,300 | +4.8% / +0.0% / +0.7% |

ᵉ engine-phase prefill (SGLang/vLLM); others native. Previous values: llama.cpp from the October22 batch sweep; SGLang/vLLM Qwen and Strata from the October21 shared baseline; Bolt from its October21 production benchmark; GLM and DeepSeek-S from the October23 Maya1.1.24 update; DeepSeek-XS from the October23 isolated XS+DSpark test.

Nine profiles are within ±5.5% of their previous rates. **Strata prose −10.6%** (consistent 47.5–47.7 t/s;
different generated text than every earlier run, so not an isolated cause) and **DeepSeek-XS −11.8% / −11.0%**
decode against its earlier isolated test harness (first production-launcher XS rate; prefill unchanged).
Under load both GPUs' fans now reach 3,600 / 3,100 RPM; sampled GPU hotspot peaks were 84 / 73 °C,
CPU package 100 °C. GLM recorded 25.8 MiB swap across its process tree at 12.45 GiB available RAM; the
other ten recorded zero. [Report, thermals and fan setup](ALL-MODELS-2026-10-23.md) ·
[numeric record](results/all-models-2026-10-23.json).


## Both DeepSeek quants are selectable — October23

The October23 deployment offered **three profiles**: GLM-S v2, **DeepSeek Maya-XS + matching DSpark**
(`deepseek-v4.1-flash-1017-maya`, existing ID), and the larger **DeepSeek Maya-S**
(`deepseek-v4.1-flash-1017-maya-s`, new ID, no DSpark). All are32K, both7900XTX,
Maya1.1.26 / f26d8ba / ROCm7.2.3 with existing guards. The total active catalog is **13**.
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

## llama.cpp profiles after the prompt batch sweep — October22

Every active llama.cpp profile now overrides the inherited `batch-size = 512` /
`ubatch-size = 128`. These are the current llama.cpp rates: the shared method (three short
code/prose runs, three fresh ~8K prompts; medians), llama.cpp4c3c5810/HIP7.2.3, both 7900XTX,
production settings with only batch/ubatch changed, 6 threads.

| Profile | Context | batch / ubatch | Code / prose decode t/s | Native fresh ~8K PP t/s (before) | Fresh TTFT s (before) | Min free VRAM GiB |
|---|---:|---|---:|---:|---:|---:|
| `ornith-1.5-122b` | 32,768 | 4096 / 4096 | 11.44 / 13.34 | **714.9** (52.7) | **11.5** (155.2) | 4.03 / 5.02 |
| `nemotron-3.5-super-iq3` | 32,768 | 2048 / 1024 | 15.65 / 17.23 | **431.4** (93.9) | **18.4** (84.4) | 3.61 / 4.68 |
| `empero-qwen3.8-35b-a3b` | 262,144 | 4096 / 4096 | 121.45 / 73.52 | **2,944.7** (397.2) | **2.8** (20.6) | 9.65 / 6.24 |
| `sage-a1.5` | 65,536 | 4096 / 4096 | 80.81 / 65.16 | **2,793.7** (385.1) | **2.9** (21.3) | 9.91 / 10.11 |

- "Before" is each profile's same-session 512/128 control. Decode stayed within 2% of it.
- Actual fresh inputs: 8,185–8,191 tokens (Qwen-family tokenizers), 7,922–7,927 (Super).
- Ornith and Super keep their production 3 GiB/card VRAM guard. The larger sizes that measured
  faster (Ornith 8192: 986.9 t/s; Super 4096: 847.0) fall below it; Ornith 8192 was stopped
  by the guard in production.
- Thread count (6/8/16) and P-core pinning changed nothing beyond ±1%.
- Every selected size then passed one fresh ~11.1K-token prompt through the model hub with the
  guard active.
- Near-full-window prompts were not repeated at the new sizes.
- The Qwen3.6-35B-A3B profile was measured too (381.7 → 2,881.8 t/s) but was retired on October23.

[Sweep report, all arms and thermals](LLAMA-BATCH-SWEEP-2026-10-22.md) ·
[numeric record](results/llama-batch-sweep-2026-10-22.json).

## Catalog and platform

All earlier rates below retain their original workload/build/date. The llama.cpp rows in the
sections below were measured at the old 512/128 batch.

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

These Sage rows used the old 512/128 batch; current Sage prefill is in the October22 batch table above.
10.1 is effectively tied for Sage; retain7.2.3. Latest official is10.1;
7.2.4/7.14.1 were subsequently tested and rejected; see [October22 comparison](ROCM-724-7141-2026-10-22.md).
[Detailed test/limits](SAGE-A15-2026-10-21.md) ·
[all trials](results/sage-a15-2026-10-21.json) ·
[ROCm/driver distinction and both-forum research](ROCM-SELECTION-2026-10-21.md).

## Active profile results

### October23 installed-build snapshot (historical)

Engines now update daily when a newer upstream version passes every promotion gate against the same night's production run; see [DAILY-UPDATES.md](DAILY-UPDATES.md). The rates in the tables above predate the October 23 update unless marked.

| Engine | Source / selected stack | Scope |
|---|---|---|
| llama.cpp | [edc35384](https://github.com/ggml-org/llama.cpp/commit/edc353842c1be9b4ebc27460a1da4526a026d3a9) (daily update Oct 23; was 4c3c5810); MoE HIP | Four MoE profiles (Empero, Super, Sage, Ornith) on HIP 7.2.3; no Vulkan profile remains; both GPUs, unchanged expert backing/cache/MTP/contexts; batch/ubatch 4096/4096 (Super 2048/1024) since October22 |
| SGLang | [f84475cc](https://github.com/StevenChenSE/sglang/commit/f84475ccf593087df3d1da13c9e675eadee12352), retained ROCm 7.2.3 stack | TP2 DFlash2/BF16 KV/163840; local RDNA repairs preserved |
| vLLM | 0.32.1rc1.dev361+g83c078d95.rocm72 (daily update Oct 23; was dev36), amd-aiter 0.1.26, retained ROCm 7.2.3 Torch stack | Qwen: TP2/compiled MTP3/BF16 KV/163840. Bolt: TP2/AutoRound W4A16/BF16 KV/262144 |
| Strata | [7ddc17a3](https://github.com/Niko1221/Strata/commit/7ddc17a38fe7f31637e895ecfba58c2cd43d65ec) (daily update Oct 23; was 9ae93f7b/0.1.46.1), ROCm 7.2.3 | Q3/13.5GiB/six workers/256K/INT8 KV32K resident; native frontend unchanged |
| Maya | [f26d8ba/v1.1.26](https://github.com/mw00/project-maya/commit/f26d8bab43f9b10f0475986b541dc46ada45285e) (daily update Oct 23; was 25deec5/v1.1.24), ROCm 7.2.3 | Three 32K profiles: GLM Maya-S v2/MTP (MMQ; failed fused path disabled), DeepSeek Maya-XS + matching DSpark xs2, DeepSeek Maya-S without DSpark; guards retained |
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
The llama.cpp rows used the old 512/128 batch; current llama.cpp prefill is in the October22 batch table.
Earlier October20/i5/NVIDIA measurements retain their original build/method/date.
The new record retains every actual short input/output count, fresh-input/cache metadata,
quality result, source/library fingerprint and thermal sample coverage.

### Super IQ3 using fixed ~8K-input workloads (historical, 512/128 batch)

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
