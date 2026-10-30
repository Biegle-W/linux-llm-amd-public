# Linux LLM AMD — public reference

**October 30 Strata RDNA3/32 GB trial:** The fork loads and short replies work; conservative 8K recall passes, but its history follow-up stalls. This tested 32 GB configuration is not qualified. The isolated candidate and all three attempts are preserved; production selection and other RAM holds remain. [Measured scope and cleanup](linux/hardware/STRATA-RDNA3-32GB-TRIAL-2026-10-30.md).

**October 30 OpenCat iPhone API repair:** native `POST /v1/responses` is exposed through the authenticated, guarded API. Responses JSON/stream/history and Chat Completions pass on SGLang; 67 CPU routing checks pass per checkout. iPhone retry remains unverified. [Repair and supported scope](linux/network/OPENCAT-RESPONSES-ROUTING-2026-10-30.md).

**October 30 SGLang stream repair:** a reproduced child-exit telemetry race is fixed; five authenticated API streams and 179 CPU/ownership checks per checkout pass. Live missing counters and actual memory/eviction limits still fail closed. [Repair and limits](linux/hardware/SGLANG-TELEMETRY-EXIT-FIX-2026-10-30.md).

**October 30 DSH stream repair:** The DSH pi-ai HTTP adapter now counts incoming SSE activity, including loading comments, before SDK parsing. Delayed-stream, silence/cancellation/error regressions and authenticated frontend readiness pass. Timeout values and inference guards are unchanged; the original failing provider/model request still needs confirmation. [Repair and validation limits](linux/network/API-STREAM-ACTIVITY-FIX-2026-10-30.md).

**October 29 Super INT4 preflight:** Super INT4 small-kernel/UVA checks pass; a temporary nonessential-service pause still fails full-model RAM admission (26.9 GiB required / 23.5 GiB available, before cache/workspace overhead). All three services are restored. No full-model benchmark or promotion; working Super IQ3 remains selected. [Evidence and limits](linux/hardware/SUPER-INT4-VLLM-PREFLIGHT-2026-10-29.md).

**Current availability — October 29:** Qwen27B/SGLang is qualified and enabled after the ROCm multicast/VRAM-guard correction; eight working profiles remain available. Ornith, both DeepSeek XS routes and Qwen Flash Next/Strata remain paused until the owner reports more RAM. Actual spill protection and all other guards remain. [Fix and verification](linux/hardware/SGLANG-VRAM-GUARD-FIX-2026-10-29.md).

**October 29 Strata retry / current swap policy:** Diagnostics and `loading-swap-v4` are deployed: 128 MiB/s writes / 160 MiB/s combined over complete 30-second inference windows; loading/parked swap remains allowed. All 218 CPU checks per checkout pass, including the unchanged 95% performance boundary. The Strata build and production baseline passed with zero sampler errors. Candidate launch and the restored-build load smoke hit the unchanged 25 GiB available-RAM guard; no candidate performance verdict exists. Source 7dd5cf18e68c and all three restored build files match the rollback copies. Fresh rollback loading remains unverified. The approved temporary service pause has been restored and verified; the updater is inactive with no provisional state or task GPU reservation. [Policy, diagnostics, SSD evidence and retry status](linux/hardware/STRATA-RETRY-SAMPLER-2026-10-29.md).

**October 29 split llama.cpp update:** Empero, Super and Flint now use `eb4e244be77a` after standard gates. Ornith alone retains the independent old `2280f0fd163b` source/build pin; normal RAM admission remains. [Results, durable pin and validation](linux/hardware/LLAMA-SPLIT-UPDATE-2026-10-29.md).

**October 29 updater restoration:** The 03:00 nightly engine updater is enabled; the current update is complete. Qwen/Sage now use vLLM `0.33.0rc1.dev229+g3966924d5.rocm72`; Bolt retains dev435. The llama.cpp split is recorded above; Strata rollback and remaining RAM-held engine selections remain. Earlier updater-pause notes are superseded; manual runtime pins, other holds and safety gates remain. [Restoration status and repairs](linux/hardware/ENGINE-UPDATER-RESTORED-2026-10-29.md).

**October 29 Ornith / updater audit:** Ornith has a scoped working isolated 32 GB placement; production remains held. [Placement results and limits](linux/hardware/ORNITH-VRAM-32GB-2026-10-29.md). The pre-restoration audit found five newer configured components and SGLang current; the timer is now restored and final outcomes are recorded above. [Read-only version audit](linux/hardware/ENGINE-UPDATE-AUDIT-2026-10-29.md). Other production selections, guards and unrelated paused schedules remain.

## All models on 32 GB — measured October 29

The [all-model 32 GB benchmark](linux/hardware/ALL-MODELS-32GB-2026-10-28.md) is complete within the recorded scopes, including Qwen-Image and FLUX. Fresh-server image request medians: qwen-image 190.720 s; flux-t2i 170.274 s; flux-edit 161.970 s. Current grouped tables distinguish measured selected runtimes, isolated native/SGLang candidates and retained profiles. All owned benchmark work is cleaned up; engine pins, contexts, guards, coordinators and paused schedules remain. No automatic promotion or restoration.

## Matched H3 on 32 GB — complete

The [matched newer H3 comparison](linux/graphics/H3-MATCHED-32GB-2026-10-28.md) is complete on real 32 GB RAM: three timed fresh-server trials per arm plus excluded warmups. Median request: **179.209 s single-GPU / 153.773 s actual fcys RCCL TP2** (14.2% shorter with TP2); both-ready sampler: **33.980 / 44.263 s**. Encoder costs are excluded. All eight AV/guard/cleanup checks passed; owned reservation released. Sampled visual limits remain; no production promotion.

## Temporary 32 GB SSD-streaming profiles — October 28

Activated temporary 32 GB profiles: **Qwen / Strata, GLM / Maya**. Held at the exact prior 64 GB profile: **DeepSeek XS / Maya, DeepSeek XS / Strata**. Each activation passed native safety/functional/performance/near-window/history checks and normal guarded authenticated JSON/SSE/tools/~8K/history checks. The exact 64 GB preimages are retained; restore only after at least 60 GiB physical RAM is visible and inference is idle. All other settings, guards, coordinator services and paused schedules remain. [Qualification, comparisons and limits](linux/hardware/SSD-STREAMING-32GB-2026-10-28.md).

## AMD router admission — October 28

AMD router admission is implemented in source and validated: fair FIFO, bounded
pending count/bytes, consistent sanitized health and preserved backend HTTP/SSE
errors. **71 CPU regressions per checkout** and two 32-token Sage JSON/SSE smokes
pass. The user-authorized idle hub/gateway restart is complete; the new router
code is active and authenticated health passes. Profiles, guards, pins and paused
schedules remain unchanged.
[Validation, numeric evidence and next action](linux/hardware/ROUTER-ADMISSION-2026-10-28.md).

[AMD H3 encoder-format comparison](linux/graphics/H3-AMD-ENCODER-FORMATS-2026-10-28.md): Tested W4A8 on the same H3 encoder against corrected NVFP4. Native HIP INT8 encoding was 5.91–8.11× faster across three prompts after warmup; separate cold-file load times, RAM/VRAM, nine paired TP2 clips and quality limits are recorded. Native W4A8 preserves the sampled main scenes, with design changes and shared prompt limitations; it remains an isolated tested candidate. Both host floors remain 1 GiB; other guards and production selection remain.

## Fresh H3 one-card versus two-card test — October28

Fresh tests completed on one physical 7900 XTX and on two 7900 XTX cards: one excluded warmup plus three timed 39-frame generations per arm, with a new isolated server for every generation. Full-request medians are 270.098 s on one card and 146.603 s on two (45.7% shorter on the two-card path). Sampler medians are 30.237/59.749 s. This establishes the measured fresh-server workflow result; loader/storage/noise/source differences limit attribution to GPU count alone. All independent guards and loading-swap-v3 remained. No production promotion or native Radiance run. [Fresh protocol, individual samples and limits](linux/graphics/H3-ONE-VS-TWO-2026-10-28.md).

## User swap correction and Radiance preflight — October 28

**Historical October28 swap policy: loading-swap-v3, superseded by the October29 v4 ceilings above.** Loading, parked swap and reads are allowed. Rates/pressure are advisory; there is no default automatic swap-rate stop. An optional stop needs an explicit write budget plus matched measured inference slowdown. Old policy settings alone cannot restore historical stop rules. [Implementation and verification](linux/hardware/SWAP-TASK-CONTINUITY-2026-10-28.md). Radiance H3 preflight is blocked by the missing gfx1100 accelerated kernel plugin before any GPU run or memory guard; [source/build evidence](linux/graphics/RADIANCE-H3-PREFLIGHT-2026-10-28.md). Existing pins, independent physical/VRAM protections and paused schedules remain.

## Post-upgrade H3 comparison — October 28

Linux now exposes **30.56 GiB RAM**, up from **14.83 GiB** before the reboot. This is a physical MemTotal increase; the prior measurements retain their original hardware attribution. The full matched comparison did not complete. Keep the saved production workflow. Partial successful generations and failed attempts are retained; no SP2 speedup or production qualification is claimed. [Results and limitations](linux/graphics/H3-POST-UPGRADE-2026-10-28.md). LLM pins and the paused updater remain; previous LLM timings retain their measured RAM configuration.

## October27 vLLM qualification history

Historical selection below; the October29 updater result above supersedes the Qwen/Sage wheel and nightly pause. Bolt retains its explicit dev435 pin.

**Qwen and Sage use `0.32.1rc1.dev602+g5d35ce393.rocm72`; Bolt remains on
`0.32.1rc1.dev435+gc50aca144.rocm72`.** Qwen/Sage pass performance gates and new
installed API/tools/JSON/SSE, near-window/history and sustained-compute validation.
Bolt dev602 passed its earlier8K speed gates but hit the unchanged swap-churn guards
twice during near255K prefill; it is not promoted. Its launcher has an explicit
stable-runtime default and `manual_runtime_pin` excludes it from global updater
promotions. Actual mixed routing is verified. No guard/context is lowered, Sage
remains text-only, other engines/default Strata remain, and the updater stays paused.
[Qualification, selected benchmarks, failures and recovery](linux/hardware/VLLM-DEV602-PROMOTION-2026-10-27.md).
Earlier dev435/candidate-only snapshots below retain dated evidence; this section
supersedes them as current runtime state.

**NVIDIA-agent notes delivered — October27:** the user requested a
[NVIDIA-server handoff](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/main/docs/AMD-PARITY-HANDOFF-20261027.md) for agents there to address the gap queue.
It is published in both NVIDIA repositories and linked from their README/AGENTS;
their public export allowlist includes those notes. This delivery changes only
documentation/discovery/export metadata, with no runtime, benchmark, guard or
schedule change. G3's agent entry point is added; the GLM table repair and runtime
items remain for NVIDIA-host work. AMD-owned G5/G7 remain separate. Optional new
models and schedules still require the specific choices in the handoff.

## Standing handoff upkeep — October 27

After relevant work, keep both AMD repositories, `README.md`, `AGENTS.md`,
[current benchmark Markdown](linux/hardware/CURRENT-AMD-BENCHMARKS.md), numeric results
and the [canonical handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md) current in the same task.
Keep `AGENTS.md` as a thin entry point; change its instructions when needed,
rather than copying benchmark numbers or runtime settings into it. Before yielding,
record selected versus candidate settings, completed checks, actual failures,
active jobs/locks, unfinished work and the next concrete step. Preserve historical
measurements and private evidence; do not rerun completed GPU tests merely to refresh docs.
Review sanitized public changes, commit/push both maintained repositories and verify
publication, or record the exact outstanding sync step. The private canonical
handoff and Shared copy must match after relevant changes.

A read-only [AMD/native Linux NVIDIA gap audit](linux/hardware/AMD-NVIDIA-GAP-AUDIT-2026-10-27.md)
records actionable proposals and hardware/method differences. NVIDIA now records
six deployed profiles; the earlier prepared-only map is superseded. Ask the user
which gaps to fill before changing NVIDIA or applying parity candidates.
No inference test, engine/profile setting or schedule changed in this documentation review.

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
[Comparison, compatibility results and removal](linux/hardware/SAGE-INT4-REPLACEMENT-2026-10-27.md).

**Standing user instruction — October 27: loading swap is allowed.**
Allow swap while loading models, and allow parked swap pages afterward. Do not
reject loading because swap is nonzero, resident swap exceeds 4 GiB, or cumulative
loading swapout exceeds 4 GiB. Prohibit sustained aggressive swap churn during
inference that risks excessive SSD writes or slows inference. The default is
`loading-swap-v2`; older zero-swap, 64/256 MiB and 4 GiB rules are historical or
explicit legacy validation modes, and must not silently override this instruction.
Keep physical-RAM admission, RAM caps, GPU reserves, zero dedicated-VRAM spill,
ownership containment, thermal monitoring and quality/performance gates.
[Current policy, implementation and validation](linux/hardware/LOADING-SWAP-POLICY-2026-10-27.md).

## Loading-swap framework/INT4 retry — October27

Recorded 13 model/kernel attempts on 14.83 GiB RAM with loading swap allowed;
6 completed benchmark/memory checks, including a no-thinking Flint diagnostic.
Qwen/Bolt vLLM and Sage native INT4 text tests completed; the original Qwen
paging stop and its successful unchanged-setting confirmation are both retained.
SGLang hit VRAM/telemetry/kernel blockers; matched reasoning128 Flint remained
partial at the inference swap-write guard. Three earlier systemd-syntax setup
failures are separate. Selected versions/profiles and the paused updater remain;
no models were retired and H3 was not retried.
[All attempts, benchmark fields and thermals](linux/hardware/LOADING-SWAP-RETRY-2026-10-27.md).


October27: [Current-RAM H3 and LLM retries after compiler-temp cleanup](linux/hardware/CURRENT-RAM-RETEST-2026-10-27.md). Nothing was retired or promoted; all memory/VRAM guards remain.


October27: [VRAM engine refresh and native INT4 attempts](linux/hardware/VRAM-ENGINE-UPDATE-2026-10-27.md): llama.cpp qualified for three VRAM profiles; newer vLLM/INT4 loading remains held by current RAM/swap guards; required SGLang fork already current.


**Repository split — October 25:** this is the existing AMD Linux build, now
`linux-llm-amd` / `linux-llm-amd-public`. The new NVIDIA Linux build has separate
repositories and validation. Retired source/settings moved to private
[retired-llm-setting](https://github.com/Biegle-W/retired-llm-setting).
Active runtime paths, model profiles, guards and schedules are unchanged.
This README is the canonical maintenance policy; `AGENTS.md` is its thin agent
entry point. Previous root instructions remain consolidated below. [Seven-repository map](linux/hardware/REPOSITORY-MAP.md).

Benchmark-reference workstation: **2 × RX 7900 XTX 24 GB, Intel i9-13900KS, 64 GB RAM**,
MSI MPG Z690 CARBON WIFI, CPU PCIe 4.0 x8/x8. Every active model uses both AMD
cards. This repository covers the Ubuntu HIP/ROCm system. The independent
Windows NVIDIA / i5-13600KF / 64 GB fallback has its own
[Windows NVIDIA repository](https://github.com/Biegle-W/windows-llm-nvidia-public).

| Repository | Visibility | Ownership |
|---|---|---|
| [windows-llm-nvidia](https://github.com/Biegle-W/windows-llm-nvidia) | Private | Windows NVIDIA operational source |
| [windows-llm-nvidia-public](https://github.com/Biegle-W/windows-llm-nvidia-public) | Public | Reviewed Windows examples and measurements |
| [linux-llm-nvidia](https://github.com/Biegle-W/linux-llm-nvidia) | Private | Native Linux NVIDIA operational source and migration |
| [linux-llm-nvidia-public](https://github.com/Biegle-W/linux-llm-nvidia-public) | Public | Reviewed native Linux NVIDIA reference |
| [linux-llm-amd](https://github.com/Biegle-W/linux-llm-amd) | Private | Existing dual-RX-7900-XTX Linux operation |
| [linux-llm-amd-public](https://github.com/Biegle-W/linux-llm-amd-public) | Public | Reviewed AMD Linux source and measurements |
| [retired-llm-setting](https://github.com/Biegle-W/retired-llm-setting) | Private | Central retired source/settings and provenance |

Private repositories remain private. Public files exclude credentials, personal
settings, model weights, installed runtimes, raw private logs and private history.
The local Ubuntu checkout names remain unchanged for installed launcher and daily
publisher compatibility. GitHub repository names identify the system and hardware.

**October 26 qualification history:** the live OS currently exposes **14.83 GiB RAM**;
the 64 GB measurements below retain their original hardware attribution. Nightly
engine updates are paused. That qualification scope covered Qwen27B/vLLM,
Bolt/vLLM and Qwen27B/SGLang DFlash2; CPU/SSD RAM-offloaded profiles stay held.
The newer October27 Empero/Sage/Flint VRAM-only defaults are documented below.

The three October26 loading trials were guard-stopped at the 4 GiB cumulative
system swapout budget under a 7 GiB soft / 8 GiB hard worker RAM cap; none qualified.
Production pins and contexts are unchanged. Those early trials used opt-in low-churn;
the later October26 user instruction makes low-churn the default (see below).
AMD changes go only to `linux-llm-amd` / `linux-llm-amd-public`; Windows and native
Linux NVIDIA remain separate. [Outcomes and limits](linux/hardware/VRAM-QUALIFICATION-2026-10-26.md).

## Note for Claude Code and Codex — this server's maintenance scope

Standing user instruction after the repository restructure: **this server
maintains only `Biegle-W/linux-llm-amd` (private) and
`Biegle-W/linux-llm-amd-public` (sanitized public reference).**

- Exclude all Windows and native Linux NVIDIA repositories from this server's
  edits, testing, synchronization and publication unless the user explicitly
  changes scope. Links to those repositories and retained historical snapshots
  are reference material, not maintenance assignments. Do not merge their
  histories, copy their active trees here or delete their historical records.
- Keep the existing AMD checkout, installed engine/environment and model-storage
  paths unchanged. Repository renaming is not permission to relocate live assets.
- Reaffirmed October 29: automatically keep both maintained AMD repositories updated after relevant authorized work. Routine reviewed commits and normal non-force pushes to both repositories have standing user authorization; do not request repeated per-change approval. Preserve sanitization, unrelated work, runtime guards and existing holds.
- Keep both AMD repositories current after authorized AMD changes. Publish only
  reviewed, sanitized files to the public repository; never copy private history,
  credentials, personal settings, raw logs or model weights.
  Reaffirmed October27: always keep both repositories updated. This standing
  publication authorization includes model names, measured disk sizes, the three
  model categories and sanitized example storage paths in the public inventory.
- Read the AMD repository's root `README.md` first. It remains the canonical
  maintenance policy; root `AGENTS.md` points incoming agents to it and current
  handoff/benchmark records. Keep both current; do not duplicate volatile settings
  or introduce competing policy copies.
- Preserve concurrent agent/user work and all existing runtime safety guards and
  maintenance holds. This scope note does not authorize GPU trials, engine
  updates, service restarts or resuming paused nightly updates.

This scope takes precedence over legacy cross-platform maintenance wording.
Work on other repositories requires a new explicit user instruction.

## Start and connect

This public tree is a hardware-specific reference. Adapt example paths, install the pinned runtimes and validate your own hardware before launching. Active source is under `linux/`; install that tree in the example `/opt/local-llm` workspace.

| Command | Purpose | Loopback port |
|---|---|---:|
| `llm-llama` | Empero, Sage, Flint, Super IQ3 and Ornith | 8080 |
| `llm-sglang` | Qwen27B DFlash2 / TP2 | 30000 |
| `llm-vllm` | Qwen27B MTP3 / TP2 and Bolt | 30010 |
| `llm-strata` | Strata Qwen Q3 and DeepSeek XS | 30020 |
| `llm-maya` | Maya GLM and DeepSeek XS | 30030 |
| `dsh` | Separate client frontend | 3080 |

The model hub loads a selected backend on demand. The authenticated client API
uses port 10000 and `/v1`; use the [canonical handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md)
for access, storage, startup and per-engine limits. **DSH defaults to Strata Q3.**
Managed inference unloads after 600 seconds without inference activity. Active
requests/loading/jobs and GPU-LOCK defer unloading; DSH, gateway and unrelated
apps are preserved. Update acceptance uses the bounded low-churn swap policy below;
system-wide swap I/O is conservatively monitored. Existing RAM/VRAM admission, worker
cgroup limits and latched guards remain.

## DeepSeek-S retirement — October 26

DeepSeek-S and its unused drafter were removed from Maya and Strata at the user's
request, freeing **186.18 GB** on Shared NVMe. The two XS profiles retain shared S
Engram shards5/6, matching xs2 drafter and all original XS metadata. At that retirement, the catalog
had 11 profiles. GLM Maya-S is unchanged; the current reduced-RAM holds,
paused updater, runtime pins and inference guards remain.
[Retirement details and verification](linux/hardware/DEEPSEEK-S-RETIREMENT-2026-10-26.md).

**Earlier October27 VRAM-default activation (Sage GGUF since replaced above):** Empero256K/MTP3/batch512 and Sage64K/MTP3/projector/
batch4096 now use all-GPU weights by default. Flint is selectable as
`flint-40b-a2.5b` at32K, MTP off/reasoning-budget128. All three use both AMD cards,
DIO loading and a verified4GiB high/5GiB max RAM scope; loading swap is allowed by the current policy above. Physical
loading/staging admission remains12GiB total/7GiB available, with existing
continuous guards. CPU-backed Super/Ornith and SSD profiles retain their RAM
requirements. Twelve profiles are catalogued; DSH default remains Strata Q3.
[Activation evidence](linux/hardware/VRAM-DEFAULTS-2026-10-27.md).

**October27 storage and VRAM tests:** the Super SATA backup and old GLM S24
rollback are removed; active Super/GLM v2 and shared XS dependencies remain.
Strata Qwen Q3 is corrected to SSD stream because of its SSD cold/PLE path.
The user authorized isolated Empero/Sage/Flint all-VRAM trials under the existing
RAM/VRAM/swap/pressure guards; no broader update hold is lifted.
[Cleanup and trial evidence](linux/hardware/STORAGE-VRAM-2026-10-27.md).

## Model categories and disk inventory — October 27

Standing benchmark listing format (October 27): every future benchmark listing,
inventory with performance, and model comparison must group all model/engine
profiles into **VRAM only models**, **MoE models with CPU RAM offload**, and
**MoE models with SSD streaming**, according to the selected loading profile.
For each profile include **prefill (tokens/s)**, **time to first token (seconds)**,
**decode (tokens/s, code/prose separately when measured)**, **context limit
(tokens)**, **storage size (GB)**, and **storage location (drive and path)**.
Keep the model/engine identity and measurement date visible; distinguish native
prefill from engine-phase timing and configured context from actual tested length.
Use "not measured" when a metric is unavailable; never estimate or omit TTFT
because only throughput was recorded. Count shared files once in storage totals
and identify sharing in individual rows. Public paths use sanitized examples.

Standing user preference: from now on, group model inventories and comparisons
into **VRAM only models**, **MoE models with CPU RAM offload**, and **MoE models with SSD streaming**,
according to the selected loading profile. VRAM only: Empero, Sage, Flint,
Qwen27B (SGLang/vLLM) and Bolt. MoE models with CPU RAM offload: Super IQ3 and Ornith. MoE models with SSD streaming: Strata Qwen Q3,
GLM Maya and DeepSeek XS (Maya/Strata). Strata Qwen uses an SSD cold tier with
bounded RAM/GPU caches; its RAM expert pool does not make it a RAM-only profile;
these categories do not change runtime flags or memory guards. Shared weights
count once; backups/rollback/download-only assets are listed separately.
[Measured per-model disk space and locations](linux/hardware/MODEL-STORAGE-INVENTORY.md).

## Active profiles

| Model API ID | Engine | Configured context |
|---|---|---:|
| `empero-qwen3.8-35b-a3b` | llama | 262,144 |
| `nemotron-3.5-super-iq3` | llama | 32,768 |
| `sage-a1.5` | llama | 65,536 |
| `ornith-1.5-122b` | llama | 32,768 |
| `flint-40b-a2.5b` | llama | 32,768 |
| `qwen3.8-27b-sglang-dflash2` | sglang | 163,840 |
| `qwen3.8-27b-vllm` | vllm | 163,840 |
| `nemotron-3.5-bolt-vllm` | vllm | 262,144 |
| `qwen3.8-flash-next-iq3_xxs` | strata | 262,144 |
| `deepseek-v4.1-flash-1017-strata-xs` | strata | 32,768 |
| `glm-5.3-flash-maya` | maya | 32,768 |
| `deepseek-v4.1-flash-1017-maya` | maya | 32,768 |

Configured context is allocation capacity. It does not establish full-window
quality or throughput; reports state actual tested prompt and output lengths.
No model, quantization, context, hardware setting or measured speed changed in
this repository organization.

<a id="amd-latest-setup-and-results"></a>
<a id="saved-benchmark-results"></a>

## Current measurements and engine pins

**Flint current reasoning budget 128 — October 27:**

Fresh normal-launcher/authenticated API medians on both RX 7900 XTX and 14.83 GiB
host RAM: native prefill **6034.8 tokens/s**, fresh ~8K first-token TTFT
**1.396 s**, code/prose decode **46.63/46.57 tokens/s**.
First visible-answer TTFT is **4.436 s**; decode includes reasoning.
Context 32,768, storage 25.06 GB on SATA1, retained 2280f0fd/ROCm 7.2.3, VRAM-only,
reasoning 128 and all guards remain. Three runs/task, all fresh markers pass;
zero worker swap/spill, full lifecycle thermals and owned cleanup pass.
Earlier reasoning-off timings stay separate.
[Report](linux/hardware/FLINT-REASONING128-2026-10-27.md) and
[all trials](linux/hardware/results/flint-reasoning128-2026-10-27.json).

[October25 fresh tests](linux/hardware/FRESH-ENGINE-TESTS-2026-10-25.md) promoted llama.cpp
`2280f0fd`; Maya 1.1.28 failed DeepSeek decode gates and rolled back, while Strata
DeepSeek 0.1.51 failed selected kernel parity before installation. The 64 MiB swap
allowance passed the fresh baselines; current contexts/guards/dual-GPU settings remain.

The [current AMD report](linux/hardware/CURRENT-AMD-BENCHMARKS.md),
[numeric-results index](linux/hardware/results/README.md) and
[benchmark ledger](linux/hardware/BENCHMARK-HISTORY.md) retain exact builds,
hardware/RAM, tested lengths, thermals and timing methods. Native prefill,
external SSE TTFT/decode and functional-only checks remain distinct. Follow the
[Strata table selection](linux/hardware/STRATA-TUNING-2026-10-24.md) and
[DeepSeek integration](linux/hardware/STRATA-DEEPSEEK-2026-10-24.md) for their newer,
separately dated evidence. Historical speeds are not attributed to later builds.

Current validated engine pins live in the [daily ledger](linux/hardware/DAILY-UPDATES.md)
and the handoff. The 03:00 updater tests newer sources in isolation and promotes
only after all gates pass, including bounded low-churn swap and zero VRAM spill
with valid launch-through-shutdown telemetry. Updates remain paused. ROCm 7.2.3 is retained. See the
[updater method](linux/hardware/daily-update/README.md).

## Inference swap policy — current October 27 instruction

Loading swap and parked swap pages are allowed. Use the prominent standing
instruction above and `loading-swap-v2`; the October26 fixed byte caps and
blanket engine no-swap precedence are superseded. Legacy trial results retain
their original guard settings and do not prove a model fails the new policy.
[Policy and operational limits](linux/hardware/LOADING-SWAP-POLICY-2026-10-27.md).

## Model storage — October 26

Nemotron Bolt's AutoRound W4A16 checkpoint was moved from sharedSATA2 to
**sharedSATA1/vLLM-Models**. All 33 files (43,645,320,930 bytes) matched SHA-256
before the source model directory was removed. The Bolt profile, launcher and
reasoning-parser path now use SATA1. New static checkpoints also use SATA1;
new streaming packs remain on the system NVMe and the Shared NVMe stays closed
to new models. The 90% drive-use ceiling is unchanged.

The retired SATA2 volume is no longer required by model-volume discovery. After
user unmount/shutdown/removal and the October26 reboot it is no longer detected;
only its obsolete `/etc/fstab` entry remains for administrator cleanup. This is storage-only verification,
not another reduced-RAM inference test. NAS sharing has not been installed.
[Migration evidence and removal steps](linux/hardware/BOLT-STORAGE-MOVE-2026-10-26.md).

## Directory map

| Location | Scope |
|---|---|
| `linux/dsh/`, `linux/bin/`, `linux/launchers/`, `linux/network/` | Active catalog, guarded launchers, client/network helpers |
| `linux/sglang/`, `linux/vllm/`, `linux/maya/`, `linux/strata-dsv41/` | Current engine setup, source pins and patches |
| `linux/hardware/` | Current validation, dated research and numeric records |
| `linux/graphics/` | Current ComfyUI / native Comfy Desktop setup |
| [archives/](archives/README.md) | Retired system configurations and previous overview |

Models, environments and generated state stay outside tracked source. New static
weights use the configured SATA destination and new streaming packs use system
NVMe; the storage admission helper enforces the 90% limit. Existing model assets
and shared build dependencies stay in their validated locations.

<a id="nvidia-archived-setup-and-results"></a>

## Retired setups

The [archive index](archives/README.md) distinguishes the former Ubuntu
RTX 4070 + RTX 3060 system, retired models/backends, historical measurements and
recovery requirements. NVIDIA results retain their original CPU/RAM, hardware,
source version and workload; they do not describe current AMD performance.

The [complete previous overview](https://github.com/Biegle-W/retired-llm-setting/blob/main/linux-amd-public/archives/documentation/ubuntu-readme-before-organization-2026-10-24.md)
retains all earlier tables and detailed narratives. Windows retired setups are
maintained in the [Windows archive](https://github.com/Biegle-W/windows-llm-nvidia-public/tree/main/archives).


## Public repository maintenance

Standing language policy: all GitHub-facing documentation, comments, CLI messages,
commit messages, issues and pull requests must be in English. Chat may remain
Chinese. Preserve historical multilingual benchmark/test payload values using
Unicode escapes rather than translating measured inputs or outputs. Explain
fixtures in English and retain attribution links for Latin-script author names.

This is a sanitized reference distribution. Never copy private workstation paths,
IP addresses, hostnames, credentials, chat sessions, raw logs, or private Git
history here. Use example paths and addresses in documentation. Keep models and
runtime binaries ignored. Preserve third-party notices in included source patches.
Validate syntax and scan staged files and history for secrets before publishing.
Use a non-personal commit identity. Do not publish private source audit reports.

Standing user instruction: after relevant local-LLM changes, keep both the
private operational repository and this sanitized public repository current,
including applicable README/benchmark documentation and the shared Windows
handoff Markdown. Commit and push validated changes to each `origin/main`
without another reminder. Synchronize only reviewed, sanitized changes here;
never copy private history, settings or personal details. Preserve historical
NVIDIA snapshots here and Windows snapshots in the separate Windows repository.
The private Linux repository's README.md identifies its workspace and exact handoff
locations; Windows instructions are in its README. Keep the Linux repository handoff and its Shared-drive copy identical.
Report any blocked commit, push or handoff synchronization explicitly.

### Hardware-specific repositories — October 24

This is `Biegle-W/linux-llm-amd-public`. Maintain Linux AMD and the historical
`archives/ubuntu-nvidia/` tree here. Windows setup, reports and retired configurations now
live at the root of `Biegle-W/windows-llm-nvidia-public`; that work is handled
separately and is outside this AMD server's maintenance scope.
The pre-split public Windows snapshot remains in this repository's history.
Do not recreate `windows/` here or copy private repository history. Linux clients
running on Windows are still covered by the Linux network handoff. The existing
local checkout name may remain `local-llm-public` for updater compatibility.

Current Linux hardware policy: use BOTH RX 7900 XTX cards for every active model.
This supersedes the previous single-card preference. Validate per-engine dual-card
settings and report unsupported profiles rather than silently using one card.
Preserve historical NVIDIA/Windows snapshots. See
`linux/hardware/UPGRADE-DUAL-7900XTX.md` for validation status.

October 17 hardware: MSI MPG Z690 CARBON WIFI, CPU PCIe4 x8/x8. SGLang MTP
passed and is enabled again; 64 GB RAM is installed; current validation is described below.
See `linux/hardware/Z690-2026-10-17.md`. Dense-model weights remain GPU-resident; follow the newer MoE policy below.

### Current CPU/RAM and profiles — October 20

The benchmark-reference hardware used i9-13900KS and64GB RAM (61.51GiB visible);
the live OS currently exposes14.83GiB RAM. Both RX 7900 XTX cards
remain on CPU PCIe 4.0 x8/x8; the purchased switch is not installed/validated.
Twelve profiles remain after October27 Flint activation: five llama.cpp (Empero, Sage-A1.5, Flint, Super IQ3 and Ornith-1.5-122B), one SGLang, two vLLM, two Strata and two Maya. Qwen3.6-35B-A3B was retired October 23. User instruction (October 21): Bolt runs on vLLM (`nemotron-3.5-bolt-vllm`, AutoRound W4A16) and the slower llama.cpp `nemotron-3.5-bolt` and `qwen3.8-27b-q4` profiles are retired; Qwen3.8-27B uses SGLang/vLLM. llama.cpp defaults to HIP with no Vulkan profile. Their GGUF files were deleted at the user's request (October 22).
Super IQ3 remains selectable at 32K and loads from its verified shared-NVMe copy; the SATA backup was removed at the user's request October27. mmap SSD streaming was rejected (`linux/hardware/SUPER-NVME-LOAD-2026-10-20.md`). Muse Q4 and Super Q4_K_XL are retired at the user's request, with active setup and four weights removed; keep their dated results and non-installable regression fixture. SGLang retains only TP2 DFlash2. The user's saved
DSH default remains unchanged. Strata keeps IQ3_XXS, 13.5 GiB expert budget,
native 256K with INT8 KV /32K GPU residency, both GPUs and latched guards.
The 20 GiB candidate is not selected and remains inactive. Do not regenerate the
obsolete 32K/128K Strata presets or remove IQ3 on the basis of superseded plans.

Current engine versions are kept by the daily update (`linux/hardware/daily-update/`,
`linux/hardware/DAILY-UPDATES.md`); on October 23 it promoted llama.cpp edc35384, vLLM dev361,
Strata 7ddc17a3 and Maya f26d8ba/1.1.26. SGLang f84475cc (gfx1100 fork head) is retained. Current results preserve
candidate-source timings versus production rebuild functional proofs; no speedup
is claimed for these performance-neutral updates. See
`linux/hardware/CPU-RAM-PROFILES-2026-10-20.md`. Earlier i5/32 GB and NVIDIA results
must retain their original hardware/build/workload. Strata's corrected expert pack
and shared-NVMe pool measurements are distinct from old SATA-pack results.
Strata and standalone App share one new shared-NVMe asset set; engine settings
and watchdogs are independent. Maya selected profiles are validated there, with their guards described below. Keep engines/environments Linux ext4 and all model weights
excluded from Git.

### Project Maya — October 20

Maya v1.1.24 / 25deec5 is active on retained ROCm7.2.3 for GLM-5.3-Flash Maya-S v2 and
DeepSeek-V4.1-Flash-1017 Maya-XS + matching DSpark xs2 and separate Maya-S/noDSpark, each 32K, both 7900XTX cards through layer groups.
GLM retains 40 GiB bounded pinned RAM/MTP; DeepSeek 24 CPU threads/mapped experts,
GPU hot caching, with matching DSpark for XS only. Shared NVMe holds all weights/generated packs.
The native 8 GiB/card reserve must leave >=6 GiB actual whole-card free at startup;
keep continuous latched guards, zero worker swap/spill and 52G worker scope.
Physical 60 GiB / available 52 GiB before load remains required. The 64 GB Strata 13.5 GiB
profile and Super IQ3 are retained; DSH default is preserved.
Maya's source/binary/config and DeepSeek descriptor/index/Engram fingerprints
must match validation. Its broader DS4 suite retains two mixed Q4_K/IQ4_XS
bit-exact failures per card; do not enable those or other untested types.
Maya is a Strata fork: backend switching may stop only its configured native
binaries/server/router and owned workers, never arbitrary Python or other apps.
Windows must create separate Maya pack metadata, keeping shared weights intact.
See `linux/hardware/MAYA-2026-10-20.md` and
`linux/hardware/results/maya-dual-amd-2026-10-20.json`. No speed claim is inferred
from forum reports or other hardware; all trials/contexts/methods remain dated.

### Forum and reference-site research and source citations

Standing user instruction: consult [lcz.me](https://lcz.me/),
[Level1Techs Forums](https://forum.level1techs.com/) and
[Digital Spaceport](https://digitalspaceport.com/) when researching local
inference optimizations, including HIP kernels, ROCm and C++ runtimes. In BOTH
GitHub repositories, cite direct article/topic/post URLs beside source-derived claims,
recommendations and changes. Record author/date when available, relevant hardware,
model, quantization, context and workload. Link the primary upstream GitHub
commit/PR or official documentation supporting implementation details; pin
reviewed source revisions when practical. Mark forum reports, proposed candidates
and locally validated results separately. Never present another system's speed
as a local measurement or assume newer posts apply to gfx1100. Maintain the
source trail in hardware/FORUM-OPTIMIZATION-SOURCES.md (under linux/ in the public
repository) and link it from applicable reports/handoffs. This is a research and
citation rule, not authorization to deploy unvalidated changes or schedule checks.

### Consolidated Shared handoff

Keep `linux/network/LINUX-LLM-RUNTIME-HANDOFF.md` as the single current Shared
handoff. Update its current sections in place after relevant changes rather
than prepending incompatible chronological snapshots. It covers client access
and Windows differences as well as runtime state. Preserve the nine original
Shared files in `LLM-ARCHIVE/LLM-HANDOFF-ARCHIVE/2026-10-18/`; do not recreate the superseded
root client/upgrade/Windows handoffs. The private maintained source and Shared
copy must match exactly. Public exports use example addresses/paths and exclude
private archives and staging files. Preserve historical NVIDIA/Windows source
snapshots; historical evidence is not a current validated profile.

### MoE expert offload and caching — October 18

The user requests CPU expert offload plus GPU hot-expert caching for all MoE
models, with both RX 7900 XTX cards active. Size profiles for the actual64 GB using
bounded RAM/VRAM, swap and residency checks. Preserve dense Qwen27B GPU
placement. Identify MoEs by expert metadata; KV/prompt caching and static CPU
placement are not hot-expert caching. Validate each backend's implementation and
MTP behavior before activation. Preserve the validated13.5 GiB Strata expert cap,
streamed host KV admission, desktop headroom and continuous latched watchdog.
More installed RAM does not automatically select20 GiB or extend native context.

### FreeToken retired — October 18

The user explicitly requested complete FreeToken removal due to poor performance.
Its software, isolated environments, Desktop app state, launchers and caches are
removed. Shared model weights remain for other engines. The former single-GPU
exception is obsolete. Keep all active engines on both GPUs, and do not reinstall
FreeToken unless requested. Historical results remain in the hardware reports.

### Public documentation scope

The public repository demonstrates hardware configurations, inference-engine
setup, reproducible tuning and measured performance. Keep personal workstation
fault investigations, repair narratives and warranty disputes in private records.
Publish the measured RAM capacity needed to interpret results, without exporting
personal hardware-failure reports or troubleshooting histories. Apply this scope
when synchronizing future documentation; private and public content need not be
identical.

### Benchmark/context update ledger

Keep `hardware/BENCHMARK-HISTORY.md` (under `linux/` in the public copy) and
the README overview current after relevant updates. Record the exact measured
build, hardware/RAM, configured context, actual tested input/output lengths,
workload/method and saved evidence. Label functional-only checks as validation
only; preserve earlier speeds with their original dates/builds. Distinguish
native prefill, benchmark estimates and TTFT. Do not imply that an allocated
window was fully tested or invent throughput for an unmeasured update.

Strata desktop protection (October 19): preserve at least a 6 GiB per-card startup
reserve, continuous whole-card VRAM/owned-memory watchdog and latched guard
failure. Unload only its owned worker; never reclaim space by killing unrelated
GPU apps. The current measured profile and rollback limits are maintained in
`linux/hardware/STRATA-CONTEXT-2026-10-19.md`; overlap is layer splitting, not TP.

Native 256K Strata was previously checked on 32 GB; October 20 adds both CPU pools
and fresh near-window/follow-up tests on 64 GB with the corrected NVMe pack. Keep
INT8 KV, 32K GPU residency/full host backing, 13.5 GiB expert cap and desktop reserves.
The 20 GiB candidate is inactive. Beyond 256K needs experimental RoPE/quality validation,
not successful allocation alone. Overlap is layer splitting, not TP.

### Current benchmark publication

Use `linux/hardware/results/README.md` and
`linux/hardware/results/dual-amd-i9-64gb-2026-10-20.json` for the original eleven profiles; `linux/hardware/results/maya-dual-amd-2026-10-20.json` adds the two Maya profiles.
Nine use the shared short-prompt/fresh ~8K method; two Super quants use fixed ~8K
input/256-output trials. All trials, actual counts, build attribution, memory and
both Strata pool cases are retained. `dual-amd-i9-baseline-2026-10-20.json` preserves
31288c9 same-hardware selection evidence and OLD SATA Strata measurements.
The October 19 numeric/report records remain i5/32 GB history; never substitute
older speed into a current-build table. Update README, ledger, current report and
canonical handoff together. Distinguish native/engine-phase PP, external SSE TTFT/
decode, input/TTFT proxies and functional-only proofs. An ~8K probe is not full-window
validation. Muse marker failures stay visible. Candidate Q4 peak includes a brief
whole-card reserve dip; passing debounced guards does not mean reserves never
dipped below their threshold. Host self-access is not a remote-peer test.

### Qwen INT4 context follow-up — October 20

SGLang retains only TP2 DFlash2 at **163,840 tokens**, BF16 KV. vLLM
retains compiled MTP3 at **163,840 tokens**, `bfloat16` KV.
The separate SGLang MTP profile is retired. Both new profiles passed fresh
near-window markers and full-history follow-ups, with zero owned swap/spill.
[Context selection, actual counts and limits](linux/hardware/QWEN-INT4-CONTEXT-2026-10-20.md).
Keep the existing RDNA verification repair, both GPUs and startup admission.
No HiCache/FP8/CPU dense-weight offload is enabled. Current measurements live in
`hardware/results/qwen-int4-context-2026-10-20.json`; earlier contexts/rates remain historical.

### Native frontends — October 20

The user's newer request makes managed Strata Q3 and Maya open their original
local Chat/Monitor frontend after readiness, alongside the same worker and visible
terminal. Do not start a second AppImage/engine or duplicate weights. Keep DSH
separate; other backend launchers remain backend-only. Headless SSH and
`--no-browser` suppress automatic browser opening. The local HTTP adapter keeps
context/config/runtime self-updates out of the native UI; retain existing admission,
source pins, dual-GPU placement and latched watchdogs. Frontend sampling state
is private (`*.shared-settings.json` ignored). See
`hardware/NATIVE-FRONTENDS-2026-10-20.md`.


### GLM quant selection — October 20

The user requested a matched Maya-S/S24 trial and a strict less-than10% speed-loss gate for EACH code/prose decode and native-prefill six-trial median. Current selection is Maya-S,32K, same both-GPU/RAM40/MTP/reserves. Preserve DeepSeek quant/context/guards; the later source/stream policy below applies. See `linux/hardware/MAYA-S-VS-S24-2026-10-20.md` and its numeric record; initial Maya three-trial speeds remain historical.

### Strata Linux app / Intel desktop follow-up — October 20

App0.2.1/bundled HIP0.1.46 is installed and passes12 packaged checks. Its legacy
standalone inference preset stays inactive. IntelUHD770/i915 is verified as GNOME
primary. Managed Strata **9ae93f7b/0.1.46.1 is promoted** after all candidate and
normal actualDesktop/Ptyxis/nativeUI/authenticatedgateway checks. Deployed engine
SHA is c6706bc192c1afb09357e7d1eca9570c35c04562cde5265bd4404fe453848478.
Source477ac13c/0.1.45/binaries remain inactive verified rollback.

The user explicitly reduced actual loaded startup admission to**5GiB/card**.
Keep engine7/8GiB targets, continuous3GiB floor/hard1.5GiB stop,52G/no-swap scope,
telemetry/latching,dualGPU,Q3/13.5GiB/256K/INT8KV32K residency,MTP3,sixworkers.
Maya's6GiB actual startup rule is unchanged. Startup helper is common to candidate
and production. New three-trial medians: code75.28/prose50.31/nativePP912.2,
fresh8K TTFT9.015s. Near257984-input/256-output retrieval/code and258266-input
full-history follow-up with258239 cached passed; zero owned swap/spill. These are
new-build results, not a matched A/B speedup claim. The actual Desktop entry now
explicitly uses installed Ptyxis; PATH name llm-strata is unchanged. Native frontend
remains automatic after readiness, DSH separate. Do not alter global compute-device
variables or restart the session without the user. See `linux/hardware/STRATA-STARTUP5-2026-10-20.md`
and its numeric record; former6GiB failures stay historical in `linux/hardware/STRATA-LINUX-UPDATE-2026-10-20.md`.

### Temperature logging — October20

Standing user instruction: log temperatures from now on. Normal Linux launchers
and maintained benchmark/candidate helpers record one-second GPU/CPU thermal,
power/clock/fan and available raw SMU telemetry. Use `linux/dsh/gpu_telemetry.py`
or `linux/hardware/log-gpu-temps.py` for other tests. Future reports must retain
actual coverage, sampled peaks, unavailable sensors and flag limitations. Never
backfill missing history or treat a partial observation as a full-run maximum.
Keep raw logs and local paths private; inference settings and guards stay intact.
See `linux/hardware/THERMAL-LOGGING.md`.

### Model drive label — October 21

At the user's request the shared SATA model drive is labelled `sharedSATA1` (exFAT limit
11 characters). Mount it by UUID through `dsh/shared_storage.py`; never create model
folders on an unmounted path. Public examples keep `/mnt/shared`.
The former Bolt volume `sharedSATA2` is retired from model configuration; Bolt now resides on sharedSATA1.
Administrator unmount/fstab cleanup is required before physical removal.

### Engine preference — standing user instruction (October 22)

Before adding or keeping a model on llama.cpp GGUF, always look for a faster vLLM or SGLang build
that fits 2×24 GiB and runs on gfx1100. Test it in isolation and switch over when faster, as was
done for Bolt. Use llama.cpp only when no such build fits or works (e.g. Ornith-1.5-122B, Nemotron Super).

### Ornith-1.5-122B — active October 22

`ornith-1.5-122b` is an active llama.cpp HIP profile (Q4_K_M + projector, 32K, MTP off, 30 CPU
expert layers, 4 GiB GPU cache). No vLLM/SGLang build fits. See
`linux/hardware/ORNITH-122B-TEST-2026-10-21.md`.

### Model hub — October 22

`local-llm-hub.service` (`dsh/model_hub.py`, 127.0.0.1:30100) lists every enabled model and
starts or switches backends on demand through `dsh/start-backend-terminal`. The gateway forwards
to it, and DSH provider baseURLs point to it. Agents must hold `hardware/generated/GPU-LOCK` for
GPU tests; the hub refuses to start or switch while it exists. See
`linux/hardware/MODEL-HUB-2026-10-22.md`.

### ROCm version — October 22

Retain ROCm 7.2.3 for every engine. The 7.2.4 runtime and a 7.14.1 llama.cpp rebuild gave no
gain on vLLM Qwen, llama Qwen3.6/Sage or Ornith; 10.1 was rejected on October 21. See
`linux/hardware/ROCM-724-7141-2026-10-22.md`. `LOCAL_ROCM_RUNTIME_OVERLAY` in `hardware/rocm-env.sh`
is for isolated tests only.

### DSH default model — October 21

Standing user instruction: the DSH default for new agents is **Strata Q3**
(`strata-local` / `qwen3.8-flash-next-iq3_xxs`). It had drifted to Maya GLM through
a saved UI selection. Set it with `configure_local.configure('strata-local')`. Other
`configure()` refreshes, called without a provider argument, preserve it. Do not change it unless asked.

### Application launcher placement — October 21

Standing user instruction: Desktop UI shortcuts open browser/web interfaces;
application-menu entries open native desktop apps. Apply this to all maintained
apps. Backend terminal launchers and hardware-control shortcuts remain separate.
ComfyUI on Desktop opens the existing browser server; **Comfy Desktop** in the
menu opens the official native app. DSH, Turnstone, managed Strata Q3 and Maya
browser interfaces stay on Desktop with menu templates hidden (`NoDisplay=true`).
Native Strata App and Unsloth remain in the menu. Official Comfy Desktop1.1.7 is
installed through its Debian package; normal managed startup with its Ubuntu
sandbox passed October21. It imports the existing ROCm environment/models/workflows
without duplicate weights. Preserve `comfyui` (browser server), `comfy-desktop`
(native app), all backend PATH commands and the shared Comfy server lock.
See `linux/graphics/DESKTOP-2026-10-20.md`.

### Maya source/SDK validation — October 20

The October20 3384b5e9366e696e5f23f51772fb94a8a7948e41/v1.1.19 promotion is historical (superseded October23) with exact tested SDK7 binaries. ROCm10 failed both performance gates; DeepSeek10nostream stalled with no completed timed sample. Keep ROCm7.2.3/rocWMMA2.2.0. Selected DeepSeek requires `DS4_IQ_Q8K=0` (prior rounding; default1 reversedIQ3_S/IQ2_S parity fails) and `DS4_STREAM=0` (optional PCIe lane only; CPU experts/GPU hotcache retained). GLM-S40GiB/MTP and DeepSeek-S24threads/noDSpark remain32K/bothGPUs/native8GiB/actual6GiB startup/52G no-swap. Near31.5K/history and actualDesktop/Ptyxis/nativeUI/authenticated gateway/switchback pass; host-self routes are not a remote-peer test. GLM source19 six-sample rates18.44/16.10/518.0PP,12.363s freshTTFT; DeepSeek selectedthree6.89/7.08/188.6,33.418s. No universal source speedup; failed SDK10/old17 evidence retained. Other production engines remain unchanged; isolated comparisons are complete in linux/hardware/ROCM10-OTHER-ENGINES-2026-10-20.md. Fresh exact-production SDK7 controls update the benchmark overview; candidate SDK10 is not activated. See linux/hardware/MAYA-ROCM10-2026-10-20.md and numeric record. Never enable approximate prompt skipping or failed/untested formats.

### Maya web switching and DSH reuse — October 21

Maya now keeps its original browser page/assets on persistent loopback30031,
proxying the single native worker on30032; OpenAI router30030 is unchanged.
The sidebar selector accepts only an enabled model ID through existing guarded
`ensure_worker`, serializes with chat and preserves all profile/source/binary/
RAM/VRAM/no-swap/watchdog settings. Keep arbitrary native runtime/config/context/
load/update controls blocked. Preserve chats and refresh native model-specific
state after readiness. DSH is a separate frontend: repeated startup must reuse
its exact owned3080 listener, never call backend handover or label it an inference
worker. Unrelated port occupants remain an error and are never killed.
See `linux/hardware/MAYA-WEB-SWITCHING-2026-10-21.md`.

### ROCm10.1 selection — October21

All production runtimes are retained; no ROCm10.1 candidate passed every promotion gate. Empero’s matched seeds 42/43/44 improved aggregate speed by only 0.30%, below the >3% gate; keep HIP 7.2.3. The candidate's near-256K functional tests passed.
Keep all model IDs/contexts/guards/offload/cache/dual-GPU settings and existing PATH/frontend policy.
No system driver/global SDK replacement occurred. Framework/AOT compatibility tests
are not an all-extension rebuild. Preserve raw/failed/untuned/diverse-seed evidence
privately; publish only curated numeric records. [Exact outcomes and limits](linux/hardware/ROCM101-2026-10-21.md).

### Sage-A1.5 test model — October 21

Official Q4_K_M and vision projector are intentionally retained, hash-verified on
Shared SATA under GGUF-Models/Sage-A1.5-GGUF. At the user's request ("profile only"),
Sage is now an active llama.cpp profile `sage-a1.5` (64K/MTP3 + projector),
(its Desktop Chat shortcut was removed October 22: model only). Do not install the Agents-A1
harness or its external accounts unless asked. DSH default: Strata (see below). Validated test:
llama.cpp4c3c5810/HIP7.2.3, both GPUs/layer split, 64K/q8_0/MTP3, alternate-layer
CPU expert backing9.08GiB with12GiB GPU cache. Tools/JSON/SSE/fresh8K/near61999
input/history/vision smoke pass, zero owned swap/spill. SDK10.1 effectively tied,
not selected;7.14.1 is researched but untested locally. Native256K metadata is
not near-window quality validation. See hardware/SAGE-A15-2026-10-21.md and
hardware/ROCM-SELECTION-2026-10-21.md (under linux/ in the public repository).

### Maya1.1.24 — October23 (source-promotion history)

25deec505b525212e05faa58697d9d2b7d17fdb3/VERSION1.1.24 and exact tested HIP7.2.3 binaries are promoted for both retained Maya-S32K profiles after native and normal integration gates. GLM MUST retain MAYA_GLM_PREFILL_FUSED=0 (newgfx1100 fused IQ2_S down parity fails on bothcards); use MMQ, do not relax tolerances. DeepSeek retains DS4_IQ_Q8K=0/DS4_STREAM=0/24threads/noDSpark; bothGPUs/layer groups, no trueTP2 for2304/256expert blocks. Original8GiB/actual6GiB reserves/52Gno-swap/latching remain. Source-promotion historical3trial GLM19.72/15.69/535.6PP/11.928sTTFT; DS6.42/6.78/299.0/21.062s. Bothnear31.5K/history/JSON/tools/SSE, actualDesktop/Ptyxis/originalbrowserselector/authAPI/switchback pass. Preserve source19 rollback and known mixed-format exclusions; new source is not a universal speedup claim. See linux/hardware/MAYA-UPDATE-2026-10-23.md and numeric record. Otherengines/weights/default unchanged.

### Maya-XS test — October23

User-requested Maya1.1.24+IQ1_S XS+matching IQ2_XXS dspark-xs2 tested on BOTHgfx1100 cards at32K/SDK7.2.3; at that test time production remained Maya-S/noDSpark. The later explicit user-authorized production promotion below supersedes that test-only status. Keep new XS/drafter assets on sharedNVMe; reused S Engram tensor payloads are fully SHA-verified via published XS headers, not whole-file identical GGUFs. Existing S/GLM/guards/default and ten-profile catalog unchanged. See linux/hardware/MAYA-XS-DSPARK-2026-10-23.md and numeric record; retain all partial/failed preparation evidence privately.

### Maya-XS production — October23 (retained XS selection)

User explicitly authorized production XS+matchingDSpark. DeepSeek keeps sameAPIid deepseek-v4.1-flash-1017-maya,32K/24threads/bothAMD/SDK7.2.3/source25deec5/exacttestedbinary, DS4_IQ_Q8K0/STREAM0 andallguards. XS IQ1_S admission is restricted to matchingdrafter on/32K/24threads with existing source/binary/config/pack fingerprints. GLM-Sv2/MTP/fused0 and otherengines/defaultStrata unchanged. NormalDesktop/Ptyxis/nativeUI/authAPI/GLM-XS-GLM-XS passed; finalXS worker intentionally ready. Earlier31.28/15.36/445.5/14.156 and1024HTML12.54 rates remain savedexperiment, no production speed rerun. S rollback assets were retained at that time; S-only assets were removed October26. S Engram5/6 remain ACTIVE XS dependencies and must not be removed. maya/install.sh deepseek only verifies sealed XS metadata/dependencies to avoid duplicate161GBstock download. Publicconfigs require localvalidation. See linux/hardware/MAYA-XS-PRODUCTION-2026-10-23.md and numeric proof.

### Maya dual DeepSeek selection — October23 (historical; S retired October26)

Historical October23 deployment, superseded by the October26 S retirement: the user requested both DeepSeek quants selectable. XS ID deepseek-v4.1-flash-1017-maya remains unchanged; S was active as deepseek-v4.1-flash-1017-maya-s,32K/24threads/noDSpark, exact retained source25deec5/SDK7.2.3 binary/pack/guards/bothAMD. Three Maya profiles, eleven total; one worker at a time. GLM and Strata DSH default unchanged. Separate S expert routing seed copied from preserved S rollback; full six-file published SHA verified anew. NormalDesktop/Ptyxis/nativeUI S-XS-S-XS and authenticated host-self API/tools/JSON/SSE pass; no throughput/full-window rerun. Existing S/XS dated speeds retain their original methods/quality distinction. Both quants use shared S Engram5/6; never delete those. S was active, not merely rollback; old manifest remains historical. The former deepseek-s installer verified sealed existing S; that action is now retired. Public reference configs require localvalidation. See linux/hardware/MAYA-DUAL-DEEPSEEK-2026-10-23.md and numeric proof.

### Maya-S DSpark1.1.24 retest — October23 (historical; S retired October26)

User requested fresh S drafter test on installedsource25deec5/1.1.24 exactSDK7.2.3 binary. MatchedA1none-Bon-A2none,32K/24threads/bothAMD/identicalinitialSseed/allguards,three256-output code/prose and fresh~6.3Kactual DeepSeek probes; controls7K/candidate31.5K retrieval/history, JSON/tools/SSE/greedysmoke and thermals retained. Fixed>=5%geomean/nometric>5%worse plusallgates. S DSpark was not selected; the historical S profile used --dspark none. No general AMD incompatibility is inferred. XS+xs2/GLM/otherengines/default/guards/catalog11 unchanged. Old1.1.17 rejection remains historical with128-outputmethod; no isolated cross-version speedclaim. Final normalXSworker ready. See linux/hardware/MAYA-S-DSPARK-2026-10-23.md and numeric proof.

### Strata Qwen matching table — October24

User-authorized current8183c6b6/HIP7.2.3 retest selected the existing gfx1100/hipBLASLt100202 table explicitly via STRATA_HIPBLASLT_TUNING. Keep prefill2048/split26/overlap/13.5GiB/native256K/INT8KV32K/all existing guards.4096 failed actual5GiB/card startup (4.655/5.510GiB),8192 unattempted; do not relax reserves to select them. Independent repeat and normal near258K/history/JSON/tools/SSE/originalUI/authenticatedhostself API pass, zero owned swap/spill. Older9ae table/prose regression remains historical. Table changes rounding; public profiles need exact SDK/local validation. DeepSeek/Maya/defaults unchanged. See linux/hardware/STRATA-TUNING-2026-10-24.md and numeric record.


### Organization and archives — October 24

Repositories are `linux-llm-amd` / `linux-llm-amd-public` and
`windows-llm-nvidia` / `windows-llm-nvidia-public`. Preserve private/public
boundaries. Active Ubuntu source paths stay fixed for installed launchers and the
daily publisher. Archive retired setup source under `archives/`; never move live
runtime environments, weights, dependencies or private state as a documentation
cleanup. Keep exact dated measurements and hardware attribution. Review archive
links after moving source. No retired setup becomes active through reorganization.


### Minor inference worker swap allowance — October25 (historical)

Superseded as the default by the October26 low-churn policy above; the stricter
64 MiB validation option and these dated results remain available.

User instruction: a few MB of inference swap is acceptable; reject major swap.
This supersedes the exact-zero worker-swap acceptance rule above: use an inclusive
64 MiB (67,108,864 bytes) aggregate owned-worker cap for runtime update baselines
and candidates, in every model record and the full launch/load/test/shutdown
lifecycle. Larger amounts fail. Keep zero dedicated VRAM spill, valid telemetry,
complete coverage and all performance/quality gates. Background system swap is
allowed. Existing worker cgroup limits, RAM/VRAM admission and latched watchdogs
remain. Historical zero-swap results and nightly outcomes retain their original
policy/date; replay is not a fresh GPU test or permission to promote a candidate
without normal validation. See linux/hardware/daily-update/README.md.


## Seven-repository maintenance — current policy

The user's October 25 split supersedes earlier instructions to retain retired
NVIDIA/Windows setup trees here. Retired source/settings now belong only in the
private central archive; keep pointers rather than copied recipes. Earlier public
history and current AMD benchmark/regression evidence remain intact. This README
is the canonical policy and `AGENTS.md` is its agent entry point. English is the primary communication language;
all GitHub-facing content is English. Preserve all active AMD profiles, paths,
guards, publisher checkout paths, model dependencies and schedules.
