# Backup cleanup, model categories and all-VRAM trials — October 27, 2026

**Later October27 activation:** Empero/Sage VRAM-only defaults and selectable
Flint supersede the production-state statements below. The experiments and
measurements here retain their original scope.
[Current activation](VRAM-DEFAULTS-2026-10-27.md).

The user requested removal of the Super IQ3 SATA backup and old GLM Maya-S24
rollback, correction of Strata Qwen's category, and VRAM-only experiments for
Empero, Sage and Flint. **Both copies are removed; all three models pass the
isolated all-VRAM text probes on both AMD cards.** Production profiles and engine
pins remain unchanged; these experiments are not a deployment or a normal
DSH/gateway/full-context/vision/tools qualification.

## Storage removal and dependency protection

| Removed asset | Files | Logical GB | Allocated GB | Observed free-space gain GB |
|---|---:|---:|---:|---:|
| Super IQ3 SATA backup | 5 | 59.76 | 59.77 | 59.77 |
| GLM Maya-S24 rollback | 20 | 96.70 | 96.70 | 96.70 |

**25 files** removed; allocated payload **156.47 GB**.
Observed free space increased by **156,468,903,936 bytes
(156.47 GB / 145.72 GiB)** including directory overhead.
The active Super files under NVMe `LLM-Models/Nemotron-Super/`, active GLM
`Maya/Maya-S-v2-IQ2_XXS/`, shared DeepSeek Engram shards5/6 and all XS assets remain.
All **204 protected active files/configs** retained their identities, sizes and
modification times immediately after removal; small files retained SHA-256.
No full weight hash rerun is claimed, and Super/GLM inference was not restarted
on the reduced-RAM host. Their active dependencies/configuration were preserved.

The S24 checksum manifest is retained as **non-installable history**. Its files
list is empty and the downloader rejects the retired status. `maya/install.sh`
rejects the retired S24 quant before any checkout/build/install preparation.
The selected GLM v2 remains supported. Historical benchmark records are retained.

## Corrected three-category rule

**Strata Qwen3.8-Flash-Next IQ3_XXS is SSD stream.** Its bounded13.5GiB RAM expert
pool and GPU cache sit above an active SSD-backed cold/PLE path. Classifying it
as CPU RAM MoE merely because `--resident-cpu-experts` is set was too narrow.
Use the selected complete loading profile to classify future inventories.

Current production categories: VRAM only: Qwen27B (SGLang/vLLM), Bolt; CPU RAM MoE:
Empero, Super, Sage, Ornith; SSD stream: Strata Qwen, GLM Maya, DeepSeek XS in
Maya/Strata. The separately tested Empero/Sage candidates below are VRAM only;
Flint remains outside the enabled production catalog. The [current inventory](MODEL-STORAGE-INVENTORY.md)
counts shared assets once and now totals **776.24GB** of allocated model files
including the Flint download and small module cache.

## Isolated all-VRAM experiment

Hardware: i9-13900KS, **14.83GiB OS RAM**, **two RX7900XTX**, retained llama.cpp
`2280f0fd163b03d4331d49e08460f66502e35854` with ROCm7.2.3. These candidates remove
CPU expert tensor overrides/cache: `--device ROCm0,ROCm1 --split-mode layer
--tensor-split 1,1 --n-gpu-layers 99 --fit off --n-cpu-moe 0 --moe-cache-mib 0`
and GPU embedding placement; `--load-mode dio` is only the loading method, not
SSD expert streaming during inference. Q8 K/V and flash attention are retained.

Each task-owned worker read back **4GiB memory.high / 5GiB memory.max /
MemorySwapMax0** before native execution. Admission required at least7GiB
available host RAM and21GiB free per card. Existing VRAM3GiB floor /1.5GiB hard
stop, RAM3GiB headroom checks, zero sampled dedicated-VRAM spill, default bounded
low-churn host swap I/O and10% full-memory PSI gates remained. No guard was raised
to obtain a pass. GPU-LOCK serialized experiments, and only owned worker units
were stopped. Frontends/defaults and unrelated applications were preserved.

| Candidate | Context | MTP / vision | Prompt batch / ubatch | GPU layers | Code / prose decode t/s | Native prefill t/s | Fresh TTFT s |
|---|---:|---|---:|---|---:|---:|---:|
| Empero | 262,144 | MTP3 / none | 512 | 42/42 | 131.41 / 80.42 | 3397.2 | 2.413 |
| Sage | 65,536 | MTP3 / projector loaded | 4096 | 42/42 | 91.26 / 74.31 | 4619.7 | 1.778 |
| Flint | 32,768 | off / none | 4096 | 50/50 | 46.86 / 46.90 | 6027.1 | 1.415 |

Medians use three256-output code runs, three256-output prose runs and three
fresh approximately8K marker prompts, with native tokenization for each model,
plus an actual continuous request loop of at least35seconds. Arithmetic323,
JSON137, SSE and all three marker probes pass for each candidate. Complete
lifecycle telemetry has zero sampling/enforcement errors, zero worker swap,
zero sampled dedicated-VRAM spill and valid30second inference windows. Host
swapout totals are zero for the three selected runs; any background swapin is
retained in the numeric record. Every owned worker shuts down after testing.

Flint requires explicit `--reasoning-budget 0` for these non-thinking probes.
Its first32-token smoke test exhausted the cap before any final answer; that
attempt is retained and is not a successful correctness result. No stock model
chat template or weights were edited.

## Why file size alone is not a one-card fit

Every successful trial above uses both cards. VRAM-only means model/expert
weights reside on GPUs; host loading, tokenization and compute staging still
need RAM. Existing CPU placement was not evidence that these smaller models
intrinsically require CPU expert storage. The measured GPU-only candidates
show that CPU weight offload is unnecessary for these tested dual-card cases.

A single card exposes24560MiB. Empero's logged model buffers total18708MiB,
main+MTP KV2992MiB, and the existing3072MiB reserve already exceed one card before
compute buffers. Sage's model+KV+reserve leave only about43MiB, before its vision
projector and working buffers. Flint's23889MiB model buffers plus the reserve
already exceed one card before KV. These are allocation-budget observations,
not fresh single-card measurements; no one-card deployment is claimed and no
context/reserve was reduced to claim one.

## Failed attempts and practical limits

The initial Empero mmap attempt had repeated file rereads under the worker cap
and was stopped; its shutdown exposed a real process-exit accounting race.
The sampler now ignores a **confirmed zombie/dead status** encountered after
its process snapshot, while missing VmSwap on a live worker still fails closed.
The behavior has a CPU regression. No telemetry failure was waived on a pass.

Empero direct-I/O with4096-token prompt batches was stopped by the unchanged
host PSI gate (14.24%, three samples above10%), with zero worker swap/spill.
Reducing the candidate prompt batch to512 reduces staging/compute demand;
that distinct256K candidate passes. The first Sage run passed its short probes
but hit a harness-only missing tokenizer dependency before prefill. The corrected
run uses the native tokenizer and repeats the complete sequence. Initial port
TIME_WAIT and all failed attempts remain separate private/curated evidence.

No fresh CPU-offload baseline was run: its physical-RAM admission fails on this
14.83GiB host. Historical64GB numbers use their own source/hardware/method and
are not a controlled A/B proving a percentage speedup. No production preset,
MoE admission rule, model catalog/default, context or runtime pin is promoted by
these isolated tests. Full-window, fresh image/tool-roundtrip, normal browser UI
and authenticated gateway behavior have not been newly qualified for these
GPU-only candidates. Nightly updates remain paused.

All **45 relevant CPU regressions pass in each checkout** (worker-exit/live-counter
accounting, collector fail-closed behavior, S24 retirement/download prevention and
retained Super profile rules). Final recheck confirms all204 protected active
files/configs are unchanged; no inference worker or task-owned GPU-LOCK remains.

[Curated measurements and attempt history](results/storage-vram-2026-10-27.json).
