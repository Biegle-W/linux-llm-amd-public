# LLM benchmark and context history

## October27 — VRAM-only defaults and selectable Flint

User-authorized Empero/Sage all-GPU default promotion and Flint catalog addition:
normal launcher/authenticated API, tools/JSON/SSE, near258K/62K/30K markers and
history, plus Sage vision pass with strict4/5GiB/no-swap workers and all guards.
Flint selects bounded reasoning128 after zero-reasoning history probes failed
both cached and uncached. Same retained llama2280f0fd/ROCm7.2.3, unchanged model
paths and saved Strata Q3 default. Twelve profiles/ten weight sets; no new model
copy/download or scheduled-update activation. Prior non-thinking timing trials
remain dated experiments. [Report](VRAM-DEFAULTS-2026-10-27.md),
[data](results/vram-defaults-2026-10-27.json).

## October27 — backup cleanup, corrected storage category and all-VRAM experiments

User-requested Super SATA backup/GLM S24 rollback retirement reclaimed156.47GB;
204 active files/configs were protected. Strata Qwen Q3 is SSD stream. All-VRAM
text candidates on both RX7900XTX pass: Empero256K/MTP3/batch512, Sage64K/MTP3/
projector/batch4096, Flint32K/reasoning-budget0. Code/prose/nativePP medians:
131.41/80.42/3397.2,91.26/74.31/4619.7,46.86/46.90/6027.1t/s respectively.
Zero worker swap/spill; current14.83GiB host, retained2280f0fd/ROCm7.2.3, strict
4GiB high/5GiB max/no-swap workers, original guards. No fresh CPU baseline or
production promotion; prior failures/harness corrections retained.
[Report](STORAGE-VRAM-2026-10-27.md), [data](results/storage-vram-2026-10-27.json).

## DeepSeek-S retired — October26

At the user's request, S is removed from Maya and Strata; **11 profiles** remain.
XS keeps the shared S Engram shards5/6, matching xs2 drafter and original pack
metadata. S-only shards1–4, old drafter, metadata and routing seeds were removed,
reclaiming **186.18 GB** on Shared NVMe. Config/pack seals and both XS dependency
maps are unchanged. This is storage/CPU/API verification only; no new inference
or speed measurement, and the reduced-RAM holds and paused updater remain.
[Removal, retained dependencies and limits](DEEPSEEK-S-RETIREMENT-2026-10-26.md).

## Reduced-RAM GPU-resident qualification — October26 (loading only)

At 14.83 GiB OS-visible RAM, normal-launcher Qwen/vLLM, Bolt/vLLM and
Qwen/SGLang DFlash2 trials used verified 7 GiB memory.high / 8 GiB memory.max /
4 GiB memory.swap.max worker units. All three exceeded the explicit experimental
4 GiB cumulative system swapout budget during loading and were guard-stopped.
No complete inference window, throughput, correctness or full-context result;
none qualified. Recorded worker swap and dedicated-VRAM spill are distinct from
system-wide swap I/O. Constraints do not invalidate earlier 64 GB results or prove
all configurations with the same physical RAM impossible. All owned workers were
cleaned up; settings/pins unchanged, updates held. Both trees pass 28 swap and
18 memory/updater CPU tests, with independent monitor re-review.
[Report](VRAM-QUALIFICATION-2026-10-26.md) and
[numeric record](results/vram-qualification-2026-10-26.json).

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

## Inference swap scope and idle timeout — October24 (functional only)

Zero-swap gating excludes unrelated/background tasks; no global swap change.
Managed inference now unloads after 600 seconds idle, preserving DSH/gateway and
normal guarded reload on the next request. CPU safety/reload tests and a full
production idle cycle validate behavior; no new throughput or per-model power
benchmark is implied. [Idle policy and evidence](MODEL-HUB-2026-10-22.md#ten-minute-idle-power-saving--october24).
The live Qwen27B/vLLM idle shutdown was observed at 607.0 seconds, with zero
remaining owned inference processes and sampled card usage 16.871→0.026 GiB each;
DSH/gateway/all 13 catalog IDs remained. Both repositories pass 86 CPU regressions.
[Functional record and limits](results/model-idle-2026-10-24.json).

## Daily updater zero-swap gate — October24 (validation only)

Fixed promotion to require zero recorded worker swap and VRAM spill, valid
per-model and launch-through-shutdown memory evidence, and complete model coverage.
The collector counts PIDs/shared DRM clients once. CPU-only regression tests prove
rejection and the updater's rollback/smoke path; saved October24 vLLM records now
reject for their reported swap. Old counts may include duplicate descendants;
old results remain dated under their original gate. No new performance measurement,
hardware/profile change or installed runtime rollback occurred. [Method and limits](daily-update/README.md#zero-swap-gate-correction--october-24).



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

Strata now reuses the existing Maya-S and Maya-XS weights with independent metadata, both GPUs and 32K. **13 active profiles**; all Maya choices and the Strata Q3 DSH default remain. Separate gfx1100 / HIP 7.2.3 DeepSeek engine 0.1.49.1 at 8183c6b6; the Qwen engine remains 7ddc17a3. No weight download/duplication, no new ports.

| Model ID | RAM-store GB | Code / prose t/s | Native PP t/s | TTFT s |
|---|---:|---:|---:|---:|
| `deepseek-v4.1-flash-1017-strata-s` | 0 | 7.00 / 7.16 | 168.0 | 37.491 |
| `deepseek-v4.1-flash-1017-strata-xs` | 0 | 18.25 / 12.77 | 183.7 | 34.289 |

Exact-binary isolated timings, three code/prose trials with a 256-token output cap and three fresh prompts with ~6.3K actual input tokens; native prefill and external SSE TTFT/decode are distinct. Selected profiles pass the normal Ptyxis launcher, original UI, authenticated host-self API, near-31.5K/history checks and Q3 switchback with zero owned swap/spill. These are not a matched Maya speed comparison. [Setup, gates and thermals](STRATA-DEEPSEEK-2026-10-24.md) · [numeric record](results/strata-deepseek-2026-10-24.json).


## First daily engine update — October23

The new daily update (`hardware/daily-update/`) promoted llama.cpp edc35384, vLLM dev361, Strata 7ddc17a3
and Maya 1.1.26 after each passed every gate against a same-night production run (shared method, normal
launchers). Notable changes against that night's production: Maya DeepSeek XS prefill +42.9% (448.5→640.9
t/s) and DeepSeek S +28.2% (293.4→376.0); vLLM Qwen 27B decode +5.2% code / +8.8% prose (135.0→142.0,
71.9→78.3); Strata code decode −4.1% (within the 5% gate); llama.cpp within ±2.2%. Full tables:
[DAILY-UPDATES.md](DAILY-UPDATES.md). The October23 table below predates these versions.

## All eleven profiles re-measured — October23 (current rates)

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


## Maya-S DSpark retest — October23

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


## Both DeepSeek quants are selectable — October23

Maya now offers **three profiles**: GLM-S v2, **DeepSeek Maya-XS + matching DSpark**
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


## Maya-XS + DSpark is production — October23

DeepSeek now uses **Maya-XS + matching dspark-xs2** under the same model ID
`deepseek-v4.1-flash-1017-maya`:32K,both7900XTX,ROCm7.2.3/Maya1.1.24. GLM stays
Maya-S v2/MTP; all guards, ten-model catalog and Strata DSH default were preserved at that rollout; S is now separately selectable above.
Normal Desktop/Ptyxis/original UI/authenticated API and GLM→XS→GLM→XS passed;
XS is ready. [Production proof and rollback](MAYA-XS-PRODUCTION-2026-10-23.md).
Saved earlier XS benchmark: **31.28 code /15.36 prose t/s**, **445.5 native PP**,
**14.156s fresh TTFT**; single1024-output HTML**12.54t/s**. No throughput rerun
or new speed claim accompanies production integration. XS trades quality for size.


## Maya-XS + matching DSpark test — October23

Isolated **Maya1.1.24/ROCm7.2.3, both7900XTX,32K** test; production remains
Maya-S/noDSpark and ten profiles. XS is the smaller, lower-quality IQ1_S quant;
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


## October23 — Maya1.1.24, retained SDK7

Exact25deec5 development source promoted with tested binaries after selected-format kernel,near31.5K/history,normalDesktop/browser selector/API/switchback gates. GLM19.72/15.69 decode/535.6PP/11.928s freshTTFT; DeepSeek6.42/6.78/299.0/21.062s. NewGLM fused parity fails, explicitlyoff; knownDS4mixed exclusions retained. Samequants/32K/bothAMD/guards; full thermal peaks and all three-trial counts preserved. [Report](MAYA-UPDATE-2026-10-23.md), [numeric evidence](results/maya-update-2026-10-23.json).

## October 22 — llama.cpp prompt batch sweep 2 (Super, Qwen3.6, Empero, Sage)

Same build/method, production contexts (256K Qwen3.6/Empero, 64K Sage, 32K Super). Native ~8K
prefill at 4096/4096: Qwen3.6 381.7 → 2,881.8, Empero 397.2 → 2,944.7, Sage 385.1 → 2,793.7 tok/s
(TTFT ~21 → 2.8–2.9 s); decode within 2% (Qwen3.6 122.33/75.34 → 121.33/73.88). Super 2048/1024:
93.9 → 431.4, 3.61/4.68 GiB free; 2048/512 261.6. All **activated**; actual inputs 8,185–8,191
(7,922–7,927 Super); zero swap/spill; GPU0 junction ≤88 °C, CPU ≤82 °C. Hub proofs: 11,129-token
prompts at 2,043–2,138 tok/s (Super 439), guard clear (validation only).
[Report](LLAMA-BATCH-SWEEP-2026-10-22.md).

## October 22 — llama.cpp prompt batch sweep (Ornith, Super)

llama.cpp 4c3c5810/HIP 7.2.3, i9-13900KS/64 GB, both 7900 XTX, production 32K presets with only
batch/ubatch/threads changed; shared method (three short code/prose runs, three fresh ~8K prompts:
actual 8,185–8,189 Ornith / 7,922–7,927 Super input tokens). Ornith native prefill 52.7 → 714.9
tok/s at 4096/4096 (TTFT 155.2 → 11.5 s), decode 11.44/13.36 → 11.44/13.34; **activated**. 8192
reached 986.9 but left 2.31 GiB on card 0, below the 3 GiB guard. Super 93.9 → 847.0 at 4096
but ≤2.93 GiB free; not activated. Threads 6/8/16 within ±1%. Controls repeated within 0.3%; zero
swap/spill; GPU0 junction peak 98 °C (Super 2048), CPU ≤89 °C. Production hub proof: 11,129-token
prompt at 673.1 tok/s, 4.05/5.03 GiB free (validation only).
[Report](LLAMA-BATCH-SWEEP-2026-10-22.md), [all runs](results/llama-batch-sweep-2026-10-22.json).

## October 21 — Sage-A1.5 download, MTP and ROCm comparison

Official Q4_K_M plus projector verified on Shared SATA; test-only, outside the ten
active profiles. Both GPUs, CPU expert backing and hot cache, 64K, same llama.cpp
4c3 source. Three trials/task/arm: SDK7 noMTP53.58/53.16 decode/393.18 nativePP;
MTP3 83.42/66.75/387.02; SDK10.1 MTP3 84.03/66.33/386.65. Fresh8K TTFT
20.832/21.160/21.182s respectively. SDK10.1 effectively tied; retain7.2.3.
Actual61999-input/22-output retrieval and62047-input history/cached62020 pass;
separate vision smoke passes. All owned swap/spill zero;609 outer-lifecycle
thermal samples, hotspot84/60C,VRAM80/70C,CPU74C. Native256K not quality-tested.
Existing active profiles/defaults/versions unchanged. [Report](SAGE-A15-2026-10-21.md),
[all trials](results/sage-a15-2026-10-21.json),
[ROCm/driver and forum research](ROCM-SELECTION-2026-10-21.md).

## October21 — six-engine ROCm10.1 comparison

All selected stacks remain unchanged; no ROCm10.1 candidate passed every performance and validation gate. Empero: Matched seeds 42/43/44 improved aggregate speed by only 0.30%, below the >3% gate; keep HIP 7.2.3. The candidate's near-256K functional tests passed. Fresh controls update all ten profile rows,
with six fixed-seed vLLM controls and separate three-seed confirmation; Super
retains its fixed8K method. All trials/counts/native-vs-phase timing/thermal coverage
and failed pilot/preparation evidence are preserved. No NVIDIA/Windows history,
weights, contexts or memory guards changed. [Report](ROCM101-2026-10-21.md),
[full numeric record](results/rocm101-2026-10-21.json).

## October 21 — Maya web switching and DSH frontend reuse

[Functional validation](MAYA-WEB-SWITCHING-2026-10-21.md) adds guarded GLM/DeepSeek
selection to the persistent local web page and fixes duplicate DSH startup.
No throughput benchmark, context extension, engine update or memory-setting
change was made; October20 rates retain their original methods/builds.


## October 20 — isolated ROCm10 native-engine comparison

Strata source9ae and four HIP llama.cpp4c3 profiles compared SDK7/10 on the same i9/64GB/dualXTX. Production remains SDK7. Strata also has a matching-table7 arm; its prefill gain trades against prose decode. All Strata arms pass30070-input retrieval/tools/SSE; this is not SDK10 full256K/normal-launcher proof. Three llama MoEs retain shared short/fresh8K; Super IQ3 retains fixed~8K/256 output. Fresh SDK7 controls replace those active overview rows, with no claimed source speedup. Earlier rates stay dated. Full server/per-request thermal coverage, actual tokens, binary/library hashes and memory checks are retained. Failed tokenizer-harness partials remain separate.
[Comparison, sources and limits](ROCM10-OTHER-ENGINES-2026-10-20.md), [all trials](results/rocm10-other-engines-2026-10-20.json).



## October 20 — Maya v1.1.19, retained SDK7 and NVMe Maya-S

Exact tested3384b5e binaries and matching source are promoted after normal Desktop/Ptyxis/nativeUI/authenticated gateway/switchback proof. ROCm10 is rejected: GLM code/prose/PP−2.3/−8.5/−4.2% vs same-source7; automatic-stream DeepSeek decode−34.9/−36.6%;10nostream stalled first timed request (no timed throughput). Selected DeepSeek0/0 retains CPUexperts/GPUhotcache,32K/24threads/noDSpark/reserves. GLM uses40GiB/MTP/32K. Both packs stay on shared NVMe. GLM six-sample19 medians18.44/16.10decode,518.0PP,12.363s freshTTFT; DeepSeek three-sample6.89/7.08,188.6,33.418s. Actual fresh inputs6308–6314/6295–6299; near31496/31482 plus full-history passed. Zero owned swap/spill; temperatures have full per-start coverage, not invented historical peaks. Other engines remain unchanged.
[Report, failed arms and limitations](MAYA-ROCM10-2026-10-20.md), [full numeric trials](results/maya-rocm10-2026-10-20.json).



## October 20 — Strata0.1.46.1 promoted with5GiB startup admission

Exact tested9ae93f7b/c6706bc engine is deployed after candidate and normal
Desktop/Ptyxis/nativeUI/authenticatedgateway gates. Q3/13.5GiB/sixworkers/256K,
INT8KV32K residency/MTP3/layer26/bothAMD remain. User-authorized actual startup
minimum5GiB; engine7/8GiBtargets,continuous3GiB,52G/noswap remain. New three-trial
code/prose decode75.28/50.31t/s, nativePP912.2t/s, fresh8K TTFT9.015s; input8185–8188,
output20–22 for fresh markers, short29/25-input and256-output. Near257984/256 and
full-history258266/22 (cached258239) markers pass; zero swap/spill. No matched A/B
speedup claim; old0.1.45/NVIDIA/SATA rates retain their original attribution.
[Full method/results](STRATA-STARTUP5-2026-10-20.md) and
[all numeric trials](results/strata-startup5-2026-10-20.json).

## October 20 — Strata Linux app update; managed candidate blocked

App0.2.1/bundled HIP0.1.46 passes12 packaged checks, with unchanged shared
weights/menu names. Development source9ae93f7b/engine0.1.46.1 compiles and passes
small device tests, but the original Q3/13.5GiB/256K candidate fails actual6GiB/card
startup admission. Both cards allocated; owned swap/spill remain zero and the
owned worker stopped. No throughput or near-window test completed. Production
477ac13c/0.1.45 and all its original measurements remain unchanged. Intel desktop
preference is active: after user logout/login GNOME explicitly selects Intel.
Two post-login starts still fail the same gate; the confirmation exact loaded
free VRAM is5.388/6.269GiB, requiring6GiB on each card. Zero owned swap/spill;
only the candidate stops. No new generation or throughput measurement is added.
[Detailed state](STRATA-LINUX-UPDATE-2026-10-20.md) and
[numeric evidence](results/strata-linux-update-2026-10-20.json).



## October 20 — GLM Maya-S versus S24

Maya-S passed the declared speed, functional/memory and normal-launcher checks; it is now selected. The fixed ABBA test uses six samples per workload per quant,32K, both GPUs, RAM40/native8GiB reserves, identical seeds/tokenizers/prompts, functional near30K checks and zero owned swap/spill. DeepSeek and every other engine/profile are unchanged.

| Quant | Native prefill t/s | Fresh prefill TTFT s | Short TTFT s, code / prose | Decode t/s, code / prose |
|---|---:|---:|---:|---:|
| Maya-S24 | 501.1 | 12.676 | 0.082 / 0.112 | 18.38 / 15.18 |
| Maya-S | 487.9 | 13.031 | 0.095 / 0.112 | 16.83 / 14.44 |

[Full comparison](MAYA-S-VS-S24-2026-10-20.md) and [numeric evidence](results/maya-s-vs-s24-2026-10-20.json). Maya-S is the selected GLM quant; the S24 files are retained as rollback evidence, without adding another active profile. DeepSeek is unchanged.


## October 20 — Qwen INT4 contexts and requested retirements

Ten active profiles remain. Muse Q4, Super Q4_K_XL and SGLang MTP are retired;
four GGUF files (95.726 GiB) were removed, shared GPTQ/DFLASH and Super IQ3 kept.
The original dated benchmark batches remain unchanged. No engine update.

SGLang retains only TP2 DFlash2 at **163,840 tokens**, BF16 KV. vLLM
retains compiled MTP3 at **163,840 tokens**, `bfloat16` KV.
The separate SGLang MTP profile is retired. Both new profiles passed fresh
near-window markers and full-history follow-ups, with zero owned swap/spill.
[Context selection, actual counts and limits](QWEN-INT4-CONTEXT-2026-10-20.md).

| Model / quant | Backend / strategy | Context tokens | Actual prefill input | Prefill t/s | Prefill TTFT s | Short TTFT s, code / prose | Decode t/s, code / prose |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.8-27B GPTQ INT4 | SGLang TP2, DFlash2 | 163,840 | 8,185–8,191 | 1314.8 | 6.235 | 0.102 / 0.097 | 178.82 / 63.40 |
| Qwen3.8-27B GPTQ INT4 | vLLM TP2, compiled MTP3 | 163,840 | 8,187–8,188 | 1413.8 | 5.806 | 0.066 / 0.092 | 130.31 / 68.96 |

Rows use the same column order as the current report: model, engine, total window,
actual fresh input, engine-phase PP, external fresh TTFT, short code/prose TTFT
and short code/prose SSE decode. Three timed trials per task; all raw numerical
trials and actual long counts are in the [new numeric record](results/qwen-int4-context-2026-10-20.json).
Larger SGLang 192K failed desktop headroom and stayed inactive. The selected
vLLM cache follows the declared threshold, not an assumed compression speedup.
Earlier rates remain attached to their original 64K/40K contexts and workloads.


Maintained October 20, 2026. The original compilation used saved results;
the October 19 Strata optimization adds fresh measurements and validation. Dates below are local dates in 2026.
This is the index of measured updates, including older hardware and retired
profiles; it does not imply that every historical configuration remains installed.



## October 20: Maya on dual AMD, shared NVMe and 32K

Maya v1.1.17 / 8d9a9b5d705049a87da853717cdc59440252de30 adds two profiles on the
same i9-13900KS / 64 GB / two 7900XTX / motherboard x8/x8 system. The switch remains
uninstalled. [Full report](MAYA-2026-10-20.md) and [numeric evidence](results/maya-dual-amd-2026-10-20.json)
retain exact source/binary/settings, every trial, input/output and memory proof.

GLM-5.3-Flash Maya-S24: 32,768 configured, 29,989-input retrieval/history passed;
MTP and 40 GiB bounded RAM tier. Three-trial medians: native PP 525.9 t/s on
6,312–6,313 actual input, external prefill TTFT 12.159 s; short code/prose TTFT
0.074/0.097 s and SSE decode 21.13/16.54 t/s (256-output cap).
DeepSeek-V4.1-Flash-1017 Maya-S: 32,768 configured, 29,989-input retrieval/history;
CPU-mapped experts + GPU cache/NVMe, 24 CPU threads, DSpark not loaded after the
bounded comparison. PP 185.5 on 6,295–6,302 input, prefill TTFT 33.956 s; short TTFT
0.374/0.550 s and SSE decode 6.24/6.84 t/s. These windows are not general full-window
quality guarantees. No other engine or older benchmark was rerun for this addition.

Native reserves are 8 GiB/card and actual startup free >= 6 GiB/card; continuous
latched RAM/VRAM guards, no-swap 52G worker scope and dual-card placement retained.
GLM RAM 40 improved its declared composite 22.91% over the same-reserve RAM 36
case, with >=10 GiB available acceptance floor; this is a 3-trial selection with stateful
caches, not a universal speed guarantee. Both normal authenticated host-self routes,
JSON/tools/SSE and GLM→DeepSeek→GLM switching passed; remote peer untested.

Both 14-check GLM/kernel suites passed. DeepSeek's broader suite retains two mixed
Q4_K/IQ4_XS bit-exact failures per card; selected Maya-S contains neither and other
types are blocked. Both use layer groups, not true TP2; DeepSeek's 256-value blocks
do not divide its 2,304-wide experts into two parts. GGUF assets are shared; Windows
needs a separate path-specific index. [Both forums and pinned sources](FORUM-OPTIMIZATION-SOURCES.md#project-maya-october-20).

## October 20: i9/64 GB, both Super quants, development runtime promotions and shared-NVMe Strata

Hardware: i9-13900KS,64 GB installed,61.51 GiB OS-visible, two RX 7900 XTX 24 GB,
MSI MPG Z690 CARBON WIFI, CPU PCIe 4.0 x8/x8. Purchased switch remains uninstalled;
P2P disabled. Historical i5/32 GB and NVIDIA measurements retain their hardware.

Current source revisions: llama.cpp HIP/Vulkan 4c3c5810f87efe177949f1b85ae509d38a2a311f;
SGLang f84475ccf593087df3d1da13c9e675eadee12352; vLLM 0.32.1rc1.dev36+ge68efc685.rocm72;
Strata 0.1.45/477ac13cbe8e582c20484871ce459d20d82df09d. Both engine updates were
performance-neutral within noise, with exact promotion/rollback provenance in
[the profile report](CPU-RAM-PROFILES-2026-10-20.md). Source-candidate timings and
later production-rebuild functional proofs are distinguished.

[Current eleven-profile record](results/dual-amd-i9-64gb-2026-10-20.json) retains
EVERY trial, actual token count, method, source/build, memory and output hash:
nine shared-method short code/prose +fresh ~8K prefill profiles and BOTH fixed ~8K
Super quants. Qwen dense64K, Muse32K, three llama MoEs256K, SGLang MTP40,960,
SGLang DFlash2/vLLM65,536, Super IQ3/Q4 each 32,768, Strata262,144 are allocated
budgets, not equivalent actual lengths. Muse retained 2/3 marker success.
[README overview](../../README.md) and [current report](CURRENT-AMD-BENCHMARKS.md)
show each model's PP, TTFT and decode with matching methods.

Super Q4: fixed 8,108/8,111 inputs with 256 output; native PP 43.26/44.17,
external TTFT 187.432/183.653s, decode 7.86/8.19 t/s. IQ3: same inputs/cap,
PP 98.21/97.84, TTFT 82.566/82.911s, decode 15.90/16.95 t/s. Both separate marker
probes passed 28,546 input/22 output. Their candidate batch overlapped copy/hash/
download IO ending 2026-10-20T11:03:39Z; no isolated engine effect is claimed.
Candidate Q4 had a brief whole-card reserve dip under 3 GiB without triggering the
unchanged sample-debounced guard. Both normal production rebuild proofs passed
actual settings, both GPUs, JSON, tools, SSE and zero owned swap/spill. Both quants
are selectable; all weights remain. Rejected64K Q4 trials are not active capacity.
[Earlier 31288c9 selection/baseline evidence](results/dual-amd-i9-baseline-2026-10-20.json)
is preserved separately, including OLD SATA-pack Strata results.

Corrected-NVMe Strata compares six all-CPU versus seven P-core workers at the
retained 13.5 GiB expert cap, INT8 KV/32K GPU residency, split 26/overlap, MTP3, prefill 2048,
7/8 GiB startup reserves. Both passed functional/30K tools/streaming and fresh
**257,984 input/256 output** near-window checks, all markers,
then full cached-history follow-up. Selected **6 workers/all CPUs**
under the predeclared5% aggregate-decode gain and prefill eligibility rule.
All timings, including both pool cases, remain saved. No RoPE extension or20 GiB
budget activation. Normal launcher and three authenticated host-self routes passed;
no separate remote-peer or reboot test is implied.

Strata's standalone App and managed backend now share one verified NVMe asset
set. GGUF/MTP matched; a generated expert-pack mismatch was resolved with a full
48-layer source-reference hash. Unique app assets were retained. Maya's 13 files/
443,117,880,880 bytes are downloaded/checksummed on that NVMe; its runtime is staged,
not yet installed/validated. [Storage inventory](results/streaming-storage-2026-10-20.json).
No private model files, binaries, credentials or raw logs are published.

## October 19 publication: two hardware result sets

The public README now groups results into the current dual-AMD setup and the
archived dual-NVIDIA setup, with per-model/backend context, prefill, TTFT and
decode. This is a saved-evidence reorganization, not a runtime update or a new
benchmark. At that earlier publication, the newest llama.cpp build had only
functional checks; the later October 19 batches below add its timings. Missing
metrics stay unmeasured.

Additional short TTFT medians below are extracted from existing curated timing
records, not inferred from native prompt durations. Values are seconds, code /
prose; their decode rates and methods remain in the dated sections below.

| Hardware / measured profile | Short TTFT s | Saved source |
|---|---|---|
| Dual AMD, llama.cpp Vulkan Qwen Q4/MTP3, old `f12aaa3` | 0.127 / 0.124 | [Level1 result record](level1-tests-2026-10-17.json), `llama-current-vulkan-q8-mtp3` medians |
| Dual AMD, SGLang repaired DFlash2 `f84475c` | 0.100 / 0.098 | [Clean-tuning record](dual-tuning-clean-2026-10-17.json), `sglang-dflash8-auto-verify1-walkfix-fixed` medians |
| Dual AMD, SGLang repaired MTP3 `f84475c` | 0.101 / 0.090 | Same record, `sglang-mtp3-auto-verify1-walkfix-fixed` medians |
| Dual AMD, vLLM dev329 MTP3 | 0.069 / 0.091 | [Upgrade record](runtime-upgrade-2026-10-18.json), median of three timed trials/task |

Strata's saved native prompt durations and full-request wall times are not
relabeled as TTFT. The previous public README is retained as a historical
publication snapshot in the public tree, with relative source links adjusted.

## How to read the results

- Context is the configured **total token budget**, including instructions,
  tools, history, input and output. 32K = 32,768; 40K = 40,960; 48K = 49,152;
  64K = 65,536; 128K = 131,072; 256K = 262,144; 1M = 1,048,576.
- Allocating a window is different from testing an input near its limit. The
  actual input column records retrieval/capacity probes, not sustained decode.
- PP = prefill tokens/s. **Native PP** is engine-reported prompt timing.
  **Book PP** is llama-benchy 0.4.0's latency-adjusted estimate with PP2048/TG128,
  concurrency one, three runs plus warm-up. Book depth 16K adds 16,384 tokens
  before the prompt/template; it is not the total input length.
- Code/prose are separate decode workloads, in that order when shown as a pair.
  Repeated short SSE tests report warm medians; older inventory trials, native
  timing and single smoke probes are labeled separately. `—` means unmeasured,
  not zero. TTFT includes scheduling, prefill and first output; it is **not PP**.
- Hardware, quantization, sampling, prompt/output lengths and speculative
  acceptance differ between batches. Cross-date values are a history of complete
  profiles, not a controlled GPU or version speed comparison. A three-token
  smoke response is not a useful sustained speed benchmark.

## Current profiles: fresh October 19 evidence

All ten current profiles have saved prefill, external TTFT and code/prose decode
measurements on their installed builds: the original nine-profile batch below
and the [later Nemotron Super IQ3 batch](NEMOTRON-SUPER-2026-10-19.md). Their
input lengths and timing methods differ. This maintenance did not rerun them. See
[the current benchmark report](CURRENT-AMD-BENCHMARKS.md) and
[all numeric trials](results/current-amd-2026-10-19.json). Three fresh ~8K marker
probes and three warm short runs/task; production context allocations retained.
Muse's complete final 1,024-output-allowance batch retains all three marker
outcomes, including failures, beside its timing data.
This update changes result publication, not runtime versions or model settings.

### Superseded summary before the fresh nine-profile batch

Hardware at this historical summary: i5-13600KF, MSI MPG Z690 CARBON WIFI, **two RX 7900 XTX 24 GB**,
CPU PCIe4 x8/x8, **32 GB RAM**. All nine profiles use both GPUs. llama.cpp and
Strata split layers; SGLang/vLLM use TP2 with host transport, without direct P2P.
Only one configured inference backend/model is active at a time.

| Model / quant | Engine / strategy | Allocated context | Actual retrieval input tested | Latest saved prefill | Latest saved decode t/s | Speed evidence |
|---|---|---:|---:|---|---|---|
| Qwen3.8-27B Q4_K_M | llama.cpp Vulkan, MTP3 | 65,536 | 59,984 on earlier single-AMD profile; no fresh dual near-limit probe in latest upgrade | Book PP 1,171.05 at depth 0 | Code 79.38 / prose 45.53 | Oct 17–18, old `f12aaa3` build [L1] |
| Muse-Glimmer-30B UD-Q4_K_XL | llama.cpp Vulkan, no speculation | 32,768 | 32,245 on earlier single-AMD profile | — on dual AMD | 34.89, one guide smoke | Oct 16, old `f12aaa3` build [D16] |
| Qwen3.6-35B-A3B MXFP4_MOE | llama.cpp HIP, CPU experts/cache, MTP3 | 262,144 | 63,911 | Native PP 417.9 at 63,911 input | 96.7, one 48-token code probe | Oct 18, old `f12aaa3` build [MOE] |
| Nemotron-3.5-Bolt-74B-A9B Q4_K_M | llama.cpp HIP, CPU experts/cache, no speculation | 262,144 | 63,911 | Native PP 424.0 at 63,911 input | 35.7, one 101-token code probe | Oct 18, old `f12aaa3` build [Q4] |
| Empero Qwen3.8-35B-A3B IQ4_XS | llama.cpp HIP, CPU experts/cache, MTP3 | 262,144 | 63,911 | Native PP 457.8 at 63,911 input | 104.9, one 128-token code probe | Oct 18, old `f12aaa3` build [MOE] |
| Qwen3.8-27B GPTQ INT4/group64 | SGLang ROCm TP2, MTP3 | 40,960 | 39,440 | Book PP 1,488.15 at depth 0 | Code 114.57 / prose 66.05 | Oct 17, repaired `f84475c` fork [C17] |
| Qwen3.8-27B GPTQ INT4/group64 | SGLang ROCm TP2, DFlash2 | 65,536 | 64,033 | Book PP 1,575.97 at depth 0 | Code 205.59 / prose 71.84 | Oct 17, repaired `f84475c` fork [C17] |
| Qwen3.8-27B GPTQ INT4/group64 | vLLM ROCm TP2, compiled MTP3 | 65,536 | 64,033; latest TTFT 54.56 s | No fresh PP on dev329; previous dev190 Book PP 1,556.04 at depth 0 | Code 130.61 / prose 72.69 | Oct 18, dev329, three warm samples/task [U18] |
| Qwen3.8-Flash-Next IQ3_XXS | Strata HIP, overlapped layer split, CPU experts/MTP3/streamed INT8 KV | 262,144 | 258,044 | Native PP 775.1 at 258,044 input | Short code 72.2 / prose 48.0; long code 39.9 | Oct 19, 0.1.45; three warm short runs, one long sample [CTX19] |

**Latest-build limits:** llama.cpp is now `31288c9c66e5`, but its five profiles
received allocation, math, streaming and tool validation only; the table's
throughput remains dated to the older build. SGLang retained `f84475ccf593`
plus repairs and received functional/cache-capacity revalidation, without fresh
timed workloads. vLLM is `0.32.0rc1.dev329+g39983a5e7.rocm723`; Strata HIP is
0.1.45 / `477ac13cbe8e`. Exact pins: [runtime upgrade][U18].

The three llama.cpp 256K MoE allocations passed approximately 64K retrieval, **not full
256K filling or sustained decode there**. The current dense-model retrieval
figures above predate dual-card migration and are explicitly not fresh dual-card
capacity measurements. Strata's 64 GB candidate retains native 256K and remains inactive/unmeasured. October 18 Strata 0.1.45 timings had background C++ compilation; October 19
Strata timing runs did not. vLLM's new
short benchmark did not. Do not infer a controlled old/new speedup.

## Update history: NVIDIA pair, 64 GB RAM

RTX 4070 12 GB + RTX 3060 12 GB. SGLang/vLLM/HyperQwen use TP2 without P2P;
llama.cpp/Strata use layer splitting and CPU backing where configured.
The retired hardware is a reference, not an active AMD profile.

### October 1–5: original retained measurements

| Date | Model / engine | Allocated context | Native PP t/s | Decode t/s | Sample |
|---|---|---:|---:|---:|---|
| Oct 5 | Flash-Next IQ2_XS, Strata 0.1.39, MTP; retired | 131,072 | 71.7 / 75.8 | 68.9 / 60.3 | Code/prose, 29/25 input, 192 output each |
| Oct 5 | Flash-Next IQ3_XXS, Strata 0.1.39, MTP | 131,072 | 55.4 / 56.2 | 48.8 / 43.9 | Same code/prose method |
| Oct 5 | Qwen27B Q4 MTP, llama.cpp v0.5.0 | 65,536 | 49.2 / 123.7 | 53.5 / 32.0 | Same code/prose method |
| Oct 1 | Muse Glimmer, llama.cpp v0.5.0 | 131,072 | 291.1 | 23.6 | Smoke: 70 input / 93 output |
| Oct 1 | Qwen35B-A3B MXFP4 MTP, llama.cpp v0.5.0 | 262,144 | 72.7 | 26.2 | Smoke: 26 input / 3 output |
| Oct 1 | Nemotron Lightning MXFP4 MTP, llama.cpp v0.5.0; retired | 1,048,576 | 55.0 | 22.1 | Smoke: 30 input / 3 output; not 1M input validation |
| Oct 1 | Empero35B-A3B IQ4 MTP, llama.cpp v0.5.0 | 262,144 | 105.7 | 32.6 | Smoke: 26 input / 3 output |
| Oct 1 | GPT-OSS-20B, llama.cpp v0.5.0; retired | 131,072 | 307.6 | 83.9 | Smoke: 81 input / 57 output |
| Before Oct 1 | GPT-OSS-120B, older llama.cpp; retired | 131,072 | 5.6 | 6.8 | Smoke: 81 input / 32 output |
| Oct 5 | Qwen27B INT4/group128 MTP, SGLang 0.5.21 | 32,768 | — | 81.0 / 52.8 | SSE code/prose, 192 output |
| Oct 1 | Qwen27B INT4/group128 MTP, vLLM 0.30.0 | 32,768 | — | 73.6 / 56.4 | SSE code/prose, 192 output |

Native long probes: Strata Q2 **126,462 input / 49 output**, PP **2,415.5**;
Strata Q3 **126,462 / 31**, PP **2,375.0**; llama Qwen Q4 **60,042 / 14**,
PP **687.9**. SGLang used **32,055 input**, TTFT **60.95 s**; vLLM used
**32,042 input**, total request **70.47 s**. These short retrieval answers are
not sustained full-window decode. Source: original saved benchmark summary
`dsh/research/saved-benchmarks-2026-10-05.json`; published historical values also
appear in the [public README][PUB]. Earlier retired Q5/Bonsai profiles are not
given invented measurements; the retained summary excluded them.

### October 5: HyperQwen comparison

Qwen27B AWQ, HyperQwen `10bb48841806` on isolated vLLM 0.30.0, INT4 KV,
three warm timed runs, 256 output, temperature 0.6/top-p 0.95/seed 42,
thinking off. Baseline was directly retested. No isolated PP saved.

| Profile | Context | Code / prose decode t/s | Code / prose TTFT ms |
|---|---:|---:|---:|
| Baseline vLLM MTP3 | 32,768 | 86.1 / 53.6 | 70 / 67 |
| HyperQwen MTP3 | 65,536 | 108.3 / 66.8 | 94 / 91 |
| HyperQwen DFlash2, 7 draft tokens | 65,536 | 170.1 / 67.3 | 66 / 99 |

DFlash2 at **59,244 input / 256 output**: **159.01 s TTFT**, **19.2 decode t/s**,
zero prefix hits. These results predate later INT8-MLP and 1 GiB KV changes.
Sources: [published historical benchmark tables][PUB] and archived
`BENCHMARKS-HYPERQWEN.md`.

### October 7: context and Strata placement tuning

Three warm 256-token short runs per task; SGLang/vLLM greedy SSE medians.

| Profile | Before → after context | Before code / prose t/s | After code / prose t/s | Actual retrieval input after update / TTFT |
|---|---|---:|---:|---|
| SGLang 0.5.21 MTP | 32,768 → 40,960 | 84.18 / 51.94 | 83.56 / 51.59 | 39,484 / 78.79 s |
| vLLM 0.30.0 MTP3 | 32,768 → 49,152 | 86.09 / 54.98 | 86.04 / 58.01 | 47,666 / 120.28 s |

At 30,049 input, selected SGLang/vLLM code decode medians were **33.11 / 36.99**;
first-request TTFT **55.20 / 63.54 s**. Repeats could reuse prefixes.

Strata Q3 changed from 0.1.39/128K/40:8 layers to **0.1.40.3/256K/32:16**,
trimmed stage weights, MTP4, INT8 KV and 8,192-token prefill chunks. Its same-batch
previous/selected code medians were **48.6 → 68.8**, prose **50.1 → 64.6**.
At **14,195 input**, native PP **1,529.3 → 1,538.5**; 1,024-token long-code
decode **56.4 → 71.9**. Three short runs/task, greedy, up to 512 output.
Fuller retrieval used **257,850 input / 22 output**, PP **2,266.2**; not sustained
256K decode. This is the strongest saved NVIDIA Strata capacity test.
Sources: dated context/Strata October 7 reports; [preserved Strata comparison][NVA]
and [published historical results][PUB].

### October 14–15: development update and prefix/MLP tuning

| Engine update | Context retained | What was newly measured |
|---|---:|---|
| llama.cpp v0.5.0 → `a0e6dc7384ed` CUDA | Per-model budgets above | Functional validation, no new throughput |
| Strata 0.1.40.3 → 0.1.44.1 / `296b59d2f73c` CUDA | 262,144 | Functional validation, no new throughput |
| SGLang 0.5.21 → `0.5.22.dev20261015+ga12814c158` | 40,960 | Cache capacity/tools/retrieval; no new throughput |
| vLLM 0.30.0 → `0.32.0rc1.dev182+g429a3da66` CUDA | 49,152 | Cache capacity/tools/retrieval; no new throughput |
| HyperQwen → `95ee3b64b0df` on vLLM 0.31.0 | 65,536 | Switching/retrieval/tools; Oct 15 TTFT tests below |

HyperQwen DFlash2 INT8-MLP versus W4A16 with explicit dense prefix retention:
fresh **5,237 input** mean TTFT **8.04 → 5.93 s**, immediate repeat
**3.02 → 2.51 s**; **21,077 input** with no cached prefix **39.40 → 30.81 s**.
These are TTFT tests with 128 output, not PP/decode rates. Selected policy later
kept boundary-only retention; the dense-retention trial is not its exact default.
Source: October 14 upgrade and October 15 optimization reports, preserved in the
[NVIDIA build snapshot][NVB] and [published historical result tables][PUB].

## Update history: AMD migration, 32 GB RAM

### October 16: single RX 7900 XTX (historical)

RTX 4070 was present but unused in these selected tests. These are **historical
single-card measurements**, not permission to run current profiles on one card.

| Model / engine | Context | Prefill t/s | Decode t/s | Method |
|---|---:|---:|---:|---|
| Qwen27B Q4 MTP3, llama.cpp Vulkan `f12aaa3` | 65,536 | 802–804 | 82.4–82.5 | Two 3,424-input / 256-output inventory trials |
| Muse Glimmer, same Vulkan | 32,768 | 786–790 | 44.0 | Two 2,878-input / 256-output trials |
| Qwen35B-A3B MXFP4 MTP3, same Vulkan | 32,768 | 1,888–1,891 | 163.3–163.6 | Two 3,424-input / 256-output trials |
| Empero35B-A3B IQ4 MTP3, same Vulkan | 32,768 | 1,837–1,840 | 203.3–203.6 | Same inventory method |
| Nemotron Bolt IQ2, same Vulkan | 65,536 | 804–807 | 75.2–75.4 | Two 3,428-input / 256-output trials |
| Qwen27B GPTQ MTP3, vLLM ROCm dev190 | 65,536 | — | 29.68–34.68 | Two 3,424-input / 256-output trials; CPU compilation in background |
| Qwen27B GPTQ DFlash2, SGLang `f84475c` | 16,384 | — | Code 147.9 / prose 45.9 | Two 512-output samples/task, standard verifier |
| Qwen27B GPTQ MTP2, SGLang `f84475c`, early corrected verifier | 16,384 | — | Code 62.22 / prose 46.39 | Two 512-output samples/task |
| Qwen27B GPTQ MTP2 BF16, later SGLang context tuning | 40,960 | — | Code 61.93 / prose 42.78 | Two 512-output samples/task |

Near-window inputs: llama Qwen **59,984**, Muse **32,245**, Qwen MoE and Empero
**32,242** each; Bolt **59,990** at native PP **855.0**. SGLang MTP40K
retrieved **38,410 input** in **51.94 s total**. vLLM retrieved **59,995 input**
in **529.54 s total**. None establishes sustained full-window decode.

The preceding `a0e6dc7384ed` Vulkan build also tested now-retired GPT-OSS-20B:
32K, native PP **2,299.3–2,726.1**, decode **158.2–158.3** at 2,749 input;
Nemotron Lightning: 32K, PP **2,297.5–2,308.4**, decode **158.4–159.7** at
3,428 input, no MTP, two 256-output trials each. These are different models from
current Bolt Q4. GPT-OSS-120B was excluded from that GPU-resident test.

Sources: original October 16 GPU-resident, llama migration and Bolt reports;
[published AMD tables][PUB], [speculative comparison][S16] and
[SGLang context comparison][SC16]. SGLang FP8/32K was tested but not selected:
DFlash code/prose **111.34/46.90**, MTP **50.20/40.79**. More allocation did
not establish faster performance; both retain their measured candidate status.

### October 16: second RX 7900 XTX, older motherboard

Previous topology: CPU PCIe4 x16 plus chipset x4. Both cards, 32 GB RAM,
llama `f12aaa3`, SGLang `f84475c`, vLLM dev190. **One short guide smoke each**,
256-token cap, reasoning counted; no new PP. These are not comparable to the
later thinking-off code/prose medians.

| Model / engine | Context | Decode t/s |
|---|---:|---:|
| Qwen27B Q4 MTP3, llama Vulkan | 65,536 | 56.27 |
| Muse Glimmer, llama Vulkan | 32,768 | 34.89 |
| Qwen35B-A3B MXFP4 MTP3, llama Vulkan | 32,768 | 101.11 |
| Empero35B-A3B IQ4 MTP3, llama Vulkan | 32,768 | 111.16 |
| Nemotron Bolt IQ2, llama Vulkan | 65,536 | 47.82 |
| Qwen27B GPTQ DFlash2, SGLang TP2 | 16,384 | 77.70 |
| Qwen27B GPTQ MTP3, vLLM TP2 | 65,536 | 53.67 |

SGLang MTP was blocked on this topology, so has no usable benchmark here. Muse's
timed guide used its cap in reasoning; separate correctness checks passed.
Source: [dual-AMD migration][D16].

### October 17: Z690 x8/x8, SGLang context/cache and verifier updates

The motherboard changed to CPU-connected x8/x8; RAM remained 32 GB. Direct
ROCm peer access remained unavailable. First restored SGLang MTP2 sample:
**40,960 context, 75.82 decode t/s**, one guide smoke, no new PP. Source: [Z690][Z17].

Subsequent tests on that board:

| Update / SGLang profile | Context | Code / prose decode t/s | Actual retrieval input | Method / source |
|---|---:|---:|---:|---|
| DFlash2 control, no prefix cache | 16,384 | 200.65 / 61.83 | Within 16K | Two 256-output samples/task [SC17] |
| DFlash2, prefix cache + chunk2048 | 65,536 | 200.57 / 60.12 | 64,033; TTFT 66.551 s | Same prompts and two-sample method [SC17] |
| MTP2, prefix cache restored | 40,960 | 89.32 / 66.18 | 39,440; TTFT 36.983 s | Two 256-output samples/task [SC17] |
| DFlash2, repaired unified verifier selected | 65,536 | 205.59 / 71.84 | 64,033 | Three warm 256-output medians/task [C17] |
| MTP3, repaired unified verifier selected | 40,960 | 114.57 / 66.05 | 39,440 | Same three-run method [C17] |

Context tuning's code prompt differs from the later clean-retry code prompt;
do not interpret 200.57 versus 205.59 as an isolated verifier improvement.
Same-batch standard-verifier controls in the clean retry were DFlash2
**179.23/62.02** and MTP3 **104.80/66.05**; a later standard DFlash repeat
was **165.63/57.10**, demonstrating variation. Unmodified optimized verification
failed ordering and is excluded from usable results.

Repaired Book PP/decode estimates: DFlash2 depth0 **1,575.97/79.61**, depth16K
**1,310.23/93.67**; MTP3 depth0 **1,488.15/80.86**, depth16K
**1,281.71/78.73**. The much higher code rates do not describe these book tasks.

### October 17: vLLM cache/compiler/prefill update

Same dev190 source, Qwen27B GPTQ target, TP2, **65,536 context throughout**.
Three warm short-task medians per profile. Source: [vLLM tuning][V17].

| Update | Code / prose decode t/s | Book depth0 PP / decode t/s |
|---|---:|---:|
| Original INT4 KV, no compile, chunk512 | 79.06 / 42.27 | 1,114.44 / 38.97 |
| INT8 KV, no compile | 107.59 / 54.88 | — |
| INT8 KV + compilation, chunk512 | 130.98 / 71.33 | — |
| Selected BF16 KV + compile + tuned prefill, chunk2048 | 131.34 / 77.46 | 1,585.23 / 88.93 |

Selected depth16K Book PP/decode: **1,431.67/65.13**. Fresh **64,033 input**
retrieval TTFT **53.73 s**, versus **130.38 s** for tuned INT8 KV. These
22-token retrieval answers are not sustained decode. MTP4 was slower in these
short tests (**124.13/57.81**) and was not selected.

### October 17–18: HIP/rocWMMA/Radiance/queue candidates

All Qwen27B on both AMD cards, **65,536 context**, same three-run code/prose
method. Book PP/decode below is depth0; depth16K results remain in the report.
These are candidates/control repetitions, not additional active model options.
Source: [Level1Techs candidate tests][L1], including its primary/forum citations.

| Profile | Code / prose decode t/s | Book depth0 PP / decode t/s | Decision |
|---|---:|---:|---|
| vLLM dev190 selected-profile control | 133.06 / 78.50 | 1,556.04 / 92.62 | Retained |
| llama Vulkan Q8 KV/MTP3 control | 79.38 / 45.53 | 1,171.05 / 50.38 | Retained |
| llama HIP native FP16 KV/MTP3 | 67.04 / 40.85 | 1,150.06 / 38.80 | Not selected |
| llama HIP restored rocWMMA | 65.81 / 35.31 | 979.69 / 44.38 | Not selected |
| Radiance ROCM_ATTN+AITER/native MTP3 full | 95.27 / 60.35 | 1,606.63 / 59.96 | Not selected |
| vLLM queue cap1 | 124.65 / 73.57 | 1,577.41 / 88.86 | Not selected |

### October 18: MoE expert offload and Q4 replacement

llama HIP `f12aaa3`, both GPUs, Q8 KV, CPU expert backing plus actual GPU
hot-expert caching. Each **allocated 262,144** and retrieved **63,911 input**.
Single native code probes with different output lengths; no matched ranking.

| Model / update | Code decode t/s (output tokens) | Native PP at 63,911 input | Source |
|---|---:|---:|---|
| Qwen35B-A3B MXFP4, MTP3 | 96.7 (48) | 417.9 | [MoE offload][MOE] |
| Empero35B-A3B IQ4, MTP3 | 104.9 (128) | 457.8 | [MoE offload][MOE] |
| Bolt IQ2, no MTP; later retired | 40.7 (87) | 526.4 | [MoE offload][MOE] |
| Bolt Q4_K_M, no MTP, 12 CPU layers/7 GiB cache | 35.7 (101) | 424.0 | [Q4 replacement][Q4] |

Qwen/Empero increased allocation from 32K to 256K, Bolt from 64K to 256K;
these changes added CPU expert backing/cache and changed engine/placement.
They did not establish speed at a filled 256K window. Full 256K remains untested.

### October 18: Strata AMD activation and latest runtime update

Strata IQ3_XXS uses both GPUs, **32,768 context**, INT8 KV, MTP3, 512-token
prefill, bounded 8 GiB CPU expert budget. One native timing sample/task.

| Build | Code / prose decode t/s | Code / prose native PP t/s | Native PP at 30,070 input | Retrieval output tokens |
|---|---:|---:|---:|---:|
| HIP 0.1.44.1 / `296b59d2f73c` | 59.8 / 47.8 | 85.5 / 80.1 | 763.1 | 19 |
| HIP 0.1.45 / `477ac13cbe8e` | 66.7 / 48.5 | 87.7 / 82.1 | 801.4 | 19 |

The newer samples had background compilation and different available cache
headroom; this is **not a controlled version comparison**. Sources:
[AMD activation][ST18] and [runtime upgrade][U18].

| Latest runtime update | Context retained | Fresh evidence after update |
|---|---|---|
| llama `f12aaa3` → `31288c9c66e5`, HIP/Vulkan | Qwen64K; Muse32K; three MoEs256K | All five allocated context, math/tools/SSE passed, worker-only no-swap scope; **no fresh throughput** |
| SGLang `f84475ccf593` + retained repairs | MTP40K / DFlash64K | Both cache capacities, math/tools passed; **no fresh throughput** |
| vLLM ROCm dev190 → dev329 | 64K | Code/prose **130.61/72.69**, three warm 256-output medians/task; **64,033 input**, TTFT **54.56 s**; no fresh Book PP |
| Strata HIP 0.1.44.1 → 0.1.45 | 32K | Native timing table above; **30,070 input**, PP **801.4**, tools/SSE passed |

No speed numbers were inferred for a build or context that was only validated.
FreeToken is retired and outside the active nine-profile catalog; its distinct
test results/limitations remain in the [retirement record][FT], not mixed into
these dual-GPU production comparisons. Image/video generation has step/time
metrics rather than LLM context/decode; see [graphics validation](../graphics/VALIDATION-2026-10-18.md).

## October 19: Strata protected overlap and prefill tuning

Both RX7900XTX cards, 32 GB RAM, HIP0.1.45 at unchanged source `477ac13cbe8e`.
Retained **32,768 context**; explicit split26/stage trimming and continuous
desktop protection. Controls reserve 6 GiB/card; the selected profile reserves 7 GiB/card. A matched serial/overlap/serial sequence used 512 prefill, 10 GiB expert
budget, three timed greedy code/prose samples per arm plus warm-up. Subsequent
prefill candidates are complete-profile comparisons, not isolated overlap gains.

| Arm | Overlap | Prefill chunk / expert RAM budget / VRAM reserve per card | Code / prose median decode t/s | Native PP at 8,022 input t/s | Minimum free VRAM GPU0 / GPU1 GiB |
|---|---:|---|---:|---:|---|
| serial-1 | 0 | 512 / 10 GiB / 6 GiB reserve | 65.9 / 46.2 | 774.8 | 5.249 / 3.708 |
| overlap-1 | 1 | 512 / 10 GiB / 6 GiB reserve | 79.4 / 53.4 | 772.7 | 5.249 / 3.845 |
| serial-2 | 0 | 512 / 10 GiB / 6 GiB reserve | 66.3 / 46.8 | 780.8 | 5.249 / 3.81 |
| prefill-2048 | 1 | 2048 / 12 GiB / 6 GiB reserve | 81.0 / 53.7 | 984.2 | 4.568 / 3.125 |
| prefill-2048-reserve7 | 1 | 2048 / 14 GiB / 7 GiB reserve | 77.6 / 52.3 | 938.1 | 5.568 / 4.115 |

Selected: **overlap enabled, 2048-token prefill, 14 GiB CPU expert budget**,
explicit split26 and stage trimming, 7 GiB reserve/card, unchanged 32K context,
INT8 KV and MTP3/minimum probability 0.7. Cold expert loading is excluded.
The matched overlap arm improved code/prose medians by **20.5%/15.6%**
versus the first serial control; repeating serial returned close to the original
speeds. The 6 GiB/2K candidate was faster (81.0/53.7 t/s, PP984.2), but left
only 3.125 GiB free on the display card, close to the 3 GiB guard threshold.
The selected 7 GiB candidate left **4.115 GiB free** there, trading about
4.2% code /2.6% prose /4.7% prefill speed for one more GiB of margin.
Compared with the first protected serial control, the retained complete profile
improved code/prose by **17.8%/13.2%** and the same 8,022-input prefill by **21.1%**.
These are small sequential samples; they do not isolate each later setting.

The selected startup reported **11.79 GiB pinned CPU expert backing** and
**14.65/13.53 GiB GPU expert caches**. Dense/head/MTP weights, KV, prompt/graph
buffers and unrelated desktop allocations occupy additional memory. The 14 GiB
value is a CPU expert budget, not a claim that exactly 14 GiB is consumed.

The matched serial→overlap comparison is separate from later complete-profile
prefill/RAM changes. Compare actual output counts/hashes in the data; identical
outputs occurred in several runs, but not every greedy output was identical.

Production validation passed arithmetic, a complete tool-call/result round trip,
authenticated gateway access (recorded separately), SSE and **30,070 input**
three-marker retrieval: native PP **1063.6 t/s**, **28.53 s total**.
Its 19-token answer is not sustained full-context decode. Latest
short-task medians are **77.6/52.3 t/s**. Full validation minimum
available RAM: **13.24 GiB**; maximum
worker swap and sampled dedicated-VRAM spill were zero. Monitoring cannot prove
long-duration stability or prevent every burst. The selected model remains in its
visible terminal; DSH stays separate and API IDs/endpoints/context are unchanged.

[Curated settings, individual timings, output hashes and memory checks](strata-optimization-2026-10-19.json).
Guard/admission/ownership regression tests passed in both repositories. Tests use
synthetic memory pressure; no GPU-exhaustion or deliberate desktop-crash test was run.

## October 20: Super IQ3 NVMe load and SSD-streaming trial

i9-13900KS / 64 GB, llama.cpp `4c3c5810`, 32K, HIP 21:19, three ~8.1K-input / 256-output trials per task.

| Arm | Load s | PP code / prose | Decode code / prose |
|---|---:|---:|---:|
| SATA, normal load (A1) | 112.1 | 98.58 / 98.06 | 15.90 / 16.94 |
| NVMe, normal load (C) | 42.2 | 98.42 / 97.96 | 15.87 / 16.93 |
| SATA, normal load (A2) | 112.1 | 98.66 / 98.09 | 15.90 / 16.92 |

Moving the files to the NVMe changes only load time (inference −0.12%). The user chose NVMe for faster loading.
mmap streaming failed forced tool calls (llama.cpp grammar exception) and was rejected.
[Report](SUPER-NVME-LOAD-2026-10-20.md) · [numbers](results/super-nvme-load-2026-10-20.json).

## October 20: DeepSeek DSpark production retest

Maya 8d9a9b5d, 32K, 24 threads, 8 GiB reserve, 3 timed 128-output runs per task.

| Arm | Code / prose decode | ~7K PP |
|---|---:|---:|
| A1 DSpark off | 11.73 / 6.94 | 155.2 |
| B DSpark on | 6.66 / 5.66 | 149.3 |
| A2 DSpark off | 8.23 / 7.65 | 150.9 |

DSpark was −20.4% overall and is rejected; production stays `--dspark none`.
[Report](DEEPSEEK-DSPARK-2026-10-20.md) · [numbers](results/deepseek-dspark-production-2026-10-20.json).

## Recording future updates

After a runtime, hardware, quantization, context or placement change, append a
dated row with exact source/version, GPU/RAM configuration, allocated context,
actual input/output lengths, sampling/cache state, measured PP/decode or TTFT,
method and evidence link. If no benchmark was run, write **validation only**;
keep the previous speed's original date/build. Do not rerun benchmarks merely
to fill gaps without a request. Refresh the current table, both repository
READMEs and the consolidated Shared handoff when relevant.

[U18]: RUNTIME-UPGRADE-2026-10-18.md
[L1]: LEVEL1-TESTS-2026-10-17.md
[D16]: UPGRADE-DUAL-7900XTX.md
[MOE]: MOE-OFFLOAD-2026-10-18.md
[Q4]: NEMOTRON-Q4-2026-10-18.md
[C17]: CLEAN-TUNING-2026-10-17.md
[SC17]: SGLANG-DUAL-CONTEXT-2026-10-17.md
[V17]: VLLM-TUNING-2026-10-17.md
[S16]: SPECULATIVE-2026-10-16.md
[SC16]: SGLANG-CONTEXT-2026-10-16.md
[Z17]: Z690-2026-10-17.md
[NVA]: NVIDIA-COMPARISON-RUNTIME-AUDIT-2026-10-18.md
[ST18]: STRATA-DUAL-AMD-2026-10-18.md
[FT]: FREETOKEN-RETIRED-2026-10-18.md
[PUB]: https://github.com/Biegle-W/linux-llm-amd-public#saved-benchmark-results
[NVB]: https://github.com/Biegle-W/linux-llm-amd-public/blob/main/archives/ubuntu-nvidia/BUILD.md

[OPT19]: STRATA-OPTIMIZATION-2026-10-19.md


## October 19: native 256K Strata on 32 GB RAM

The context sweep passed 64K,128K and 256K with 32K resident INT8 KV, RAM backing,
both GPUs and unchanged HIP 0.1.45 source. Actual near-limit input/output:
**258,044/256**, native PP **775.1**, native decode **39.9 t/s**.
Short code/prose medians: **72.2/48.0**, three warm 512-token-cap samples/task.
Expert budget 13.5 GiB, reserve7/8 GiB, split 26/trim/overlap. No worker swap/spill
was sampled; tools and SSE passed. No model/runtime update or RoPE extension.
These are complete-profile comparisons, not a context-only speedup claim.
[CTX19]: STRATA-CONTEXT-2026-10-19.md

[Report and all samples][CTX19]. Earlier 32K/64 GB candidate references in the
dated history describe that earlier state; the current table is authoritative.

## October 19: Nemotron Super IQ3 added after the nine-profile batch

New 120B-total/12B-active model, UD-IQ3_XXS, llama.cpp HIP `31288c9c66e5`,
both XTX cards, 32 GB RAM, CPU experts + GPU cache, 32K/non-MTP.
Three fixed ~8K-input/256-output runs per workload: native prefill **95.75 /
97.13 t/s**, external TTFT **84.699 / 83.521 s**, external decode **14.16 /
16.32 t/s** (code/prose). A separate **28,546-input/22-output** marker probe
passed, with native prefill **100.08 t/s** and TTFT **285.249 s**.
These fixed-input TTFT/decode trials differ from the earlier batch's short
prompts; do not combine them into an unqualified hardware speed comparison.
[Settings and validation](NEMOTRON-SUPER-2026-10-19.md),
[numeric trials and rejected splits](results/nemotron-super-2026-10-19.json).
Q4 is prepared but inactive, with no local performance result.

## October 19 documentation reconciliation

At that maintenance,no performance run or engine update was performed. The [dated report](AMD-BENCHMARKS-2026-10-19.md)
covered ten enabled profiles, retaining the original nine-profile record and
the separate approximately-8K Nemotron Super timing batch. Previous results and
measured builds remain unchanged. See [maintenance](WORKSPACE-MAINTENANCE-2026-10-19.md).
