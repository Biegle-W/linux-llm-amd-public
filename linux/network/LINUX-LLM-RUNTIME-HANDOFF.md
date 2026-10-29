# Local LLM consolidated handoff — Linux host and Windows clients

## Super INT4 vLLM preflight — October 29

Super INT4 small-kernel/UVA checks pass, but full-model RAM admission is refused (26.9 GiB required / 23.2 GiB available, before cache/workspace overhead). No full-model benchmark or promotion; working Super IQ3 remains selected. Download retained; no full-model worker launched and no task GPU lock remains. Further testing needs sufficient available physical RAM and a fresh guarded admission. [Report](../hardware/SUPER-INT4-VLLM-PREFLIGHT-2026-10-29.md).

**Current availability — October 29:** Qwen27B/SGLang is qualified and enabled after the ROCm multicast/VRAM-guard correction; eight working profiles remain available. Ornith, both DeepSeek XS routes and Qwen Flash Next/Strata remain paused until the owner reports more RAM. Actual spill protection and all other guards remain. [Fix and verification](../hardware/SGLANG-VRAM-GUARD-FIX-2026-10-29.md).

**SGLang resolution:** Unsupported CUDA/NVLink multicast probing on ROCm allocated a redundant logits buffer before falling back. The replayable AMD fix selects the same NCCL fallback first; the original graph-enabled 160K profile now passes isolated and normal API qualification with zero eviction. See [fresh evidence](../hardware/SGLANG-VRAM-GUARD-FIX-2026-10-29.md). The four RAM-blocked routes remain paused.

## Strata retry and current swap ceilings — October 29

Diagnostics and `loading-swap-v4` are deployed: 128 MiB/s writes / 160 MiB/s combined over complete 30-second inference windows; loading/parked swap remains allowed. All 218 CPU checks per checkout pass, including the unchanged 95% performance boundary. The Strata build and production baseline passed with zero sampler errors. Candidate launch and the restored-build load smoke hit the unchanged 25 GiB available-RAM guard; no candidate performance verdict exists. Source 7dd5cf18e68c and all three restored build files match the rollback copies. Fresh rollback loading remains unverified. The approved temporary service pause has been restored and verified; the updater is inactive with no provisional state or task GPU reservation. [Evidence and retry status](../hardware/STRATA-RETRY-SAMPLER-2026-10-29.md).

## Split llama.cpp update — complete

Empero, Super and Flint now use `eb4e244be77a906a183cd4a00fd51d9ad3200955` after all standard gates; Ornith alone retains the independent `2280f0fd163b` manual source/build hold and unchanged 60 GiB admission. The final run completed at 14:05 EDT; provisional state and its GPU reservation are clear. The next full-registry timer remains October 30 at 03:00 EDT. [Results and durable split](../hardware/LLAMA-SPLIT-UPDATE-2026-10-29.md).

## Nightly updater restored — October 29

The 03:00 daily engine updater is enabled; the vLLM follow-up completed successfully at 13:21 EDT. Qwen/Sage now use vLLM `0.33.0rc1.dev229+g3966924d5.rocm72`; Bolt retains dev435. The later llama.cpp split is recorded above; Strata rollback and remaining RAM-held selections remain. This supersedes earlier updater-pause notes only. All existing manual runtime pins, other holds and qualification/safety gates remain. The service is inactive, provisional state is clear and its GPU reservation is released; next full-registry run is October 30 at 03:00 EDT. [Current restoration/run status](../hardware/ENGINE-UPDATER-RESTORED-2026-10-29.md); final promotion or rollback results are recorded in the daily ledger.

## Ornith maximum-VRAM 32 GB test / updater audit — October 29

Ornith has a scoped working isolated 32 GB placement; production remains held. [Measured attempts and limits](../hardware/ORNITH-VRAM-32GB-2026-10-29.md). The pre-restoration read-only check found five newer configured components and SGLang current; the timer is now restored and final outcomes are recorded above. [Version/coverage audit](../hardware/ENGINE-UPDATE-AUDIT-2026-10-29.md). All owned experiment work is cleaned up; guards, held profiles and unrelated paused schedules remain. The selected vLLM wheel is updated as recorded above.

## All models on 32 GB — measured October 29

The [all-model 32 GB benchmark](../hardware/ALL-MODELS-32GB-2026-10-28.md) is complete within the recorded scopes, including Qwen-Image and FLUX. Fresh-server image request medians: qwen-image 190.720 s; flux-t2i 170.274 s; flux-edit 161.970 s. Current grouped tables distinguish measured selected runtimes, isolated native/SGLang candidates and retained profiles. All owned benchmark work is cleaned up; engine pins, contexts, guards, coordinators and paused schedules remain. No automatic promotion or restoration.

## Matched H3 on 32 GB — complete

The [matched newer H3 comparison](../graphics/H3-MATCHED-32GB-2026-10-28.md) is complete on real 32 GB RAM: three timed fresh-server trials per arm plus excluded warmups. Median request: **179.209 s single-GPU / 153.773 s actual fcys RCCL TP2** (14.2% shorter with TP2); both-ready sampler: **33.980 / 44.263 s**. Encoder costs are excluded. All eight AV/guard/cleanup checks passed; owned reservation released. Sampled visual limits remain; no production promotion.

## Temporary 32 GB SSD-streaming profiles — October 28

Activated temporary 32 GB profiles: **Qwen / Strata, GLM / Maya**. Held at the exact prior 64 GB profile: **DeepSeek XS / Maya, DeepSeek XS / Strata**. Each activation passed native safety/functional/performance/near-window/history checks and normal guarded authenticated JSON/SSE/tools/~8K/history checks. The exact 64 GB preimages are retained; restore only after at least 60 GiB physical RAM is visible and inference is idle. All other settings, guards, coordinator services and paused schedules remain. [Qualification, comparisons and limits](../hardware/SSD-STREAMING-32GB-2026-10-28.md).

## AMD router admission — October 28

AMD router admission is implemented in source and validated: fair FIFO, bounded
pending count/bytes, consistent sanitized health and preserved backend HTTP/SSE
errors. **71 CPU regressions per checkout** and two 32-token Sage JSON/SSE smokes
pass. The user-authorized idle hub/gateway restart is complete; the new router
code is active and authenticated health passes. Profiles, guards, pins and paused
schedules remain unchanged.
Effective inference capacity stays one across all five serial backend routers.
The shared FIFO has 12 pending positions from the enabled catalog and a 32 MiB
aggregate pending-body budget; full admission yields retryable 429. Final smoke
health is 0 in-flight/queued. Temporary coordinators are removed; the smoke's
launcher-owned Sage worker has completed inference-aware idle release (600 seconds).
No task-owned GPU reservation or pending inference remains. The user-authorized
production restart is now complete at 2026-10-28 19:01:11 EDT. Authenticated
health matches the hub on all three configured bindings; missing/wrong credentials
return 401. Health/catalog reads did not update inference activity. Queue is empty,
backend unloaded, idle timeout 600 seconds, capacity one, pending bound 12/32 MiB.
All 20 checked guard/profile/access/credential/unit-file hashes are unchanged.
Updater service remains inactive with no installed active timer; no schedule changed.
No router activation work remains and no GPU benchmark was repeated.
[Validation and numeric evidence](../hardware/ROUTER-ADMISSION-2026-10-28.md).

[AMD H3 encoder-format comparison](../graphics/H3-AMD-ENCODER-FORMATS-2026-10-28.md): Tested W4A8 on the same H3 encoder against corrected NVFP4. Native HIP INT8 encoding was 5.91–8.11× faster across three prompts after warmup; separate cold-file load times, RAM/VRAM, nine paired TP2 clips and quality limits are recorded. Native W4A8 preserves the sampled main scenes, with design changes and shared prompt limitations; it remains an isolated tested candidate. Both host floors remain 1 GiB; other guards and production selection remain.

Current candidate: W4A8 default and native HIP integer encoder paths have matched speed/memory and paired TP2 quality evidence. Native W4A8 preserves the sampled main scenes, with design changes and shared prompt limitations; it remains an isolated tested candidate. All comparison jobs are complete and no task-owned GPU lock remains. Production selection and paused schedules remain; no automatic promotion. Preserve completed evidence rather than rerunning these tests for documentation.

## Fresh H3 one-card versus two-card test — October28

Fresh tests completed on one physical 7900 XTX and on two 7900 XTX cards: one excluded warmup plus three timed 39-frame generations per arm, with a new isolated server for every generation. Full-request medians are 270.098 s on one card and 146.603 s on two (45.7% shorter on the two-card path). Sampler medians are 30.237/59.749 s. This establishes the measured fresh-server workflow result; loader/storage/noise/source differences limit attribution to GPU count alone. All independent guards and loading-swap-v3 remained. No production promotion or native Radiance run. [Fresh protocol, individual samples and limits](../graphics/H3-ONE-VS-TWO-2026-10-28.md).

No task-owned GPU worker or lock remains. Completed fresh trials are preserved; do not repeat them for documentation. Production selection remains. Further qualification must address output repeatability and isolate loader/noise/source differences before claiming GPU-count-only scaling.

## Swap instruction corrected; Radiance compatibility established — October28

**Historical October28 swap policy: loading-swap-v3, superseded by the October29 v4 ceilings above.** Loading, parked swap and reads are allowed. Rates/pressure are advisory; there is no default automatic swap-rate stop. An optional stop needs an explicit write budget plus matched measured inference slowdown. Old policy settings alone cannot restore historical stop rules. [Policy report](../hardware/SWAP-TASK-CONTINUITY-2026-10-28.md). No matched per-request baseline or SSD write budget is configured in generic routers, so their swap telemetry is advisory. [Radiance H3 preflight](../graphics/RADIANCE-H3-PREFLIGHT-2026-10-28.md) reaches successful gfx1100 CMake configuration but excludes the gfx12-only plugin; the compiler confirms its FP8 instruction mismatch. No model or user task was stopped during this correction, no OS swap setting or engine pin changed, and no new GPU inference/benchmark result exists. No active managed worker required a router restart. H3 follow-up and nightly updater remain paused. Next GPU work needs a validated gfx1100 kernel path and a genuinely matched workload; do not repeat strict v2 stops or relabel historical results. No task GPU lock, worker or compile job remains.

## Post-upgrade H3 takeover — October 28

Linux now exposes **30.56 GiB RAM**, up from **14.83 GiB** before the reboot. This is a physical MemTotal increase; the prior measurements retain their original hardware attribution. The full matched comparison did not complete. Keep the saved production workflow. Partial successful generations and failed attempts are retained; no SP2 speedup or production qualification is claimed. [Report](../graphics/H3-POST-UPGRADE-2026-10-28.md). Control completed a 196.228 s warmup and one 210.098 s timed request; active combined swap I/O of 14.874 MiB/s stopped the next request. SP2 reached worker startup but stopped at 2.673 GiB available RAM before denoising. The earlier client timeout is retained separately. No three-trial median or SP2 speedup is established. The next action is to address the recorded physical-RAM/active-paging blockers while retaining the guards. All owned scopes stopped; GPU-LOCK released; configuration fingerprints unchanged. H3 follow-up and engine updater remain paused. No unfinished task-owned job remains. LLM runtime pins and dated benchmark attribution are unchanged.

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
[Qualification, selected benchmarks, failures and recovery](../hardware/VLLM-DEV602-PROMOTION-2026-10-27.md).
Earlier dev435/candidate-only snapshots below retain dated evidence; this section
supersedes them as current runtime state.

Global dev435 recovery and Bolt's separate stable environment are retained privately. Bolt launcher selects its stable environment relative to the repository; restore only with owned workers stopped and GPU ownership reserved.

**NVIDIA-agent notes delivered — October27:** the user requested a
[NVIDIA-server handoff](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/main/docs/AMD-PARITY-HANDOFF-20261027.md) for agents there to address the gap queue.
It is published in both NVIDIA repositories and linked from their README/AGENTS;
their public export allowlist includes those notes. This delivery changes only
documentation/discovery/export metadata, with no runtime, benchmark, guard or
schedule change. G3's agent entry point is added; the GLM table repair and runtime
items remain for NVIDIA-host work. AMD-owned G5/G7 remain separate. Optional new
models and schedules still require the specific choices in the handoff.

## Agent handoff upkeep and parity review — October 27

Root `AGENTS.md` is a thin discovery entry point into the canonical README,
current benchmark Markdown and this handoff. After relevant changes keep both
AMD repos and these records current, with verified results, selected/candidate
status, active jobs/locks, actual blockers and next steps. Preserve historical
measurements and private evidence; do not repeat completed tests just for docs.
Review public sanitization and verify both pushes and this Shared-copy match.

The [read-only AMD/native Linux NVIDIA audit](../hardware/AMD-NVIDIA-GAP-AUDIT-2026-10-27.md)
records G1–G8 proposals awaiting user selection. No new GPU test, runtime/profile,
guard or schedule change occurred. NVIDIA source/docs now record native deployment
and six maintained profiles; the old prepared-only repository-map status is superseded.
The completed Sage selection below remains the last runtime change. Current audit
work owns no GPU job or lock. The H3 RAM-upgrade follow-up and updater hold remain.

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
[Comparison, compatibility results and removal](../hardware/SAGE-INT4-REPLACEMENT-2026-10-27.md).

## Loading-swap framework/INT4 retry — October27

Recorded 13 model/kernel attempts on 14.83 GiB RAM with loading swap allowed;
6 completed benchmark/memory checks, including a no-thinking Flint diagnostic.
Qwen/Bolt vLLM and Sage native INT4 text tests completed; the original Qwen
paging stop and its successful unchanged-setting confirmation are both retained.
SGLang hit VRAM/telemetry/kernel blockers; matched reasoning128 Flint remained
partial at the inference swap-write guard. Three earlier systemd-syntax setup
failures are separate. Selected versions/profiles and the paused updater remain;
no models were retired and H3 was not retried.
[All attempts, benchmark fields and thermals](../hardware/LOADING-SWAP-RETRY-2026-10-27.md).


**Standing user instruction — October 27: loading swap is allowed.**
Allow swap while loading models, and allow parked swap pages afterward. Do not
reject loading because swap is nonzero, resident swap exceeds 4 GiB, or cumulative
loading swapout exceeds 4 GiB. Prohibit sustained aggressive swap churn during
inference that risks excessive SSD writes or slows inference. The default is
`loading-swap-v2`; older zero-swap, 64/256 MiB and 4 GiB rules are historical or
explicit legacy validation modes, and must not silently override this instruction.
Keep physical-RAM admission, RAM caps, GPU reserves, zero dedicated-VRAM spill,
ownership containment, thermal monitoring and quality/performance gates.
[Current policy, implementation and validation](../hardware/LOADING-SWAP-POLICY-2026-10-27.md).



**Current-RAM retry — October27:** no additional OS-visible RAM (still14.83GiB).
Ten inactive HIP compiler temp directories were retained with SHA-256-verified
copies on the system disk;3.63GiB allocated tmpfs space was released. Both H3
arms now pass the VAE stage but hit the unchanged3GiB RAM floor during32B encoder
loading, before denoising/SP2 rank-1 startup. All five corrected framework cases,
Sage/vLLM, Flint/vLLM and explicit-GPTQ Sage/SGLang hit the unchanged4GiB system
swapout budget; automatic Sage/SGLang instead failed Marlin HIP compilation.
No new throughput/generation timings; no models, weights, engines or workflows
retired, no runtime promotion and no profile/guard/default changes. Short disk
TMPDIR is used only in isolated trials; global/production environments remain.
The H3 follow-up still waits for a real MemTotal increase and now includes short
disk-temp guidance. [Full current-RAM record](../hardware/CURRENT-RAM-RETEST-2026-10-27.md).


**Earlier October27 VRAM engine refresh (Sage GGUF superseded above):** llama.cpp19cce6919992 is selected only for
Empero/Sage/Flint through source_overrides; global2280f0fd remains for CPU models.
Source-aware router reuse includes the commit/path; mismatched pins fail before
unloading. Exact configured source binaries are also registered for owned orphan
cleanup; unrelated applications remain excluded. All three passed fresh paired timing/memory/marker gates and normal
API/tools/JSON/SSE, Sage vision and4/5GiB no-swap scopes. Full context/history
quality is not remeasured. Current 14.83GiB host stopped newer vLLMdev602 and native
Sage/FlintINT4 loading under existing guards; selected vLLMdev435 remains.
SGLang f84475cc is already the latest required gfx1100 fork. Native candidates on
SATA1/vLLM-Models/Sage-A1.5-W4A16-AutoRound and Flint-AWQ add42.75GB allocated;
they are not catalog selections. Working GGUFs remain. Both GPUs, contexts,
Flint reasoning128, swap/pressure/RAM/VRAM guards and updater hold remain.
[Results and exact pins](../hardware/VRAM-ENGINE-UPDATE-2026-10-27.md).
Public source paths are examples; clone/build the exact revision locally and set an absolute source_overrides path.


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
- Keep both AMD repositories current after authorized AMD changes. Publish only
  reviewed, sanitized files to the public repository; never copy private history,
  credentials, personal settings, raw logs or model weights.
- Read the AMD repository's root `README.md` first. It remains the sole root
  maintenance instruction file; do not recreate `AGENTS.md` or introduce
  competing root instruction files for individual agents.
- Preserve concurrent agent/user work and all existing runtime safety guards and
  maintenance holds. This scope note does not authorize GPU trials, engine
  updates, service restarts or resuming paused nightly updates.

This scope takes precedence over legacy cross-platform maintenance wording.
Work on other repositories requires a new explicit user instruction.

**Earlier October27 Flint reasoning-budget128 benchmark (2280f0fd):**

Fresh normal-launcher/authenticated API medians on both RX 7900 XTX and 14.83 GiB
host RAM: native prefill **6034.8 tokens/s**, fresh ~8K first-token TTFT
**1.396 s**, code/prose decode **46.63/46.57 tokens/s**.
First visible-answer TTFT is **4.436 s**; decode includes reasoning.
Context 32,768, storage 25.06 GB on SATA1, retained 2280f0fd/ROCm 7.2.3, VRAM-only,
reasoning 128 and all guards remain. Three runs/task, all fresh markers pass;
zero worker swap/spill, full lifecycle thermals and owned cleanup pass.
Earlier reasoning-off timings stay separate.
[Report](../hardware/FLINT-REASONING128-2026-10-27.md) and
[all trials](../hardware/results/flint-reasoning128-2026-10-27.json).

**Earlier October27 VRAM-only defaults / Flint activation (Sage now uses native INT4 above):** Empero256K/MTP3/batch512
and Sage64K/MTP3/projector/batch4096 now keep all weights on both GPUs. Flint is
selectable as `flint-40b-a2.5b`,32K/noMTP/reasoning-budget128. DIO load, zero CPU
expert placement/cache, verified4GiB high/5GiB max/no-swap workers and12GiB total/
7GiB available host admission are explicit. Existing headroom/low-churn guards
remain; CPU/SSD RAM rules stay intact. Twelve profiles: five llama.cpp, one
SGLang, two vLLM, two Strata, two Maya. Saved DSH default remains Strata Q3.
[Normal-launch activation evidence](../hardware/VRAM-DEFAULTS-2026-10-27.md).

**October27 backup cleanup / all-VRAM trials:** removed only the Super SATA
backup and GLM Maya-S24 rollback, reclaiming156.47GB. Active Super NVMe, GLM v2
and all shared DeepSeek-XS dependencies remain. Strata Qwen is SSD stream;
its bounded RAM expert tier does not remove the SSD cold/PLE path. Isolated
Empero/Sage/Flint all-VRAM experiments are user-authorized; existing guards,
production contexts and paused updater remain.
[Storage removal and trial evidence](../hardware/STORAGE-VRAM-2026-10-27.md).

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

**Model grouping (October27, standing preference):** use three categories in
future inventories/comparisons: VRAM only (Empero, Sage, Flint, Qwen27B
SGLang/vLLM, Bolt); MoE models with CPU RAM offload (Super IQ3, Ornith); MoE models with SSD streaming (Strata Qwen Q3, GLM Maya, DeepSeek XS
in Maya/Strata). Classification follows the selected loading profile; Strata Qwen
uses an SSD cold tier with bounded RAM/GPU caches. This metadata inventory changes no
runtime flags, guards or holds. Count shared weights once and list backups and
rollback/download-only files separately.
[Measured storage inventory and locations](../hardware/MODEL-STORAGE-INVENTORY.md).

**DeepSeek-S retired (October26):** S model IDs and profiles are removed from
Maya/Strata. At that retirement, eleven profiles remained: four llama.cpp, one SGLang, two vLLM,
two Strata and two Maya. S-only shards1–4, its old drafter, S metadata and routing
seeds were deleted; Shared NVMe gained186.18 GB. Keep S Engram shards5/6 in place:
XS in both engines requires their161.28 GB payload. The matching xs2 drafter,
vision and original XS metadata/seals remain. Existing RAM holds, low-churn
policy, source pins and paused updater are unchanged; no inference was run.
[Retirement and retained dependencies](../hardware/DEEPSEEK-S-RETIREMENT-2026-10-26.md).

**October 25 repository split:** AMD repositories are now `linux-llm-amd` /
`linux-llm-amd-public`, retaining their original history. Native NVIDIA Linux is
separate (`linux-llm-nvidia` / `linux-llm-nvidia-public`); Windows remains separate.
Retired settings are centralized in private `retired-llm-setting`. Active AMD
runtime paths, profiles, guards, model storage and publisher directories are
unchanged. Both AMD checkout origins now use the renamed repositories. The
canonical handoff is synchronized to the existing Shared location on the AMD host.

Updated **October 26, 2026**. The benchmark-reference hardware is i9-13900KS,
64 GB RAM and two RX 7900 XTX 24 GB; the live OS currently exposes **14.83 GiB RAM**.
Twelve catalog profiles retain Super IQ3; Muse Q4 and Super Q4_K_XL are retired.
**Nightly engine updates are paused**, not automatically resumed by qualification.
The retained versions are in the block below.
Fresh i9 benchmarks, normal-launcher proofs and the corrected-NVMe Strata pool
comparison are documented with their distinct timing methods and build scope.
This is the **single current handoff on Shared**, available as `D:\LINUX-LLM-RUNTIME-HANDOFF.md` in Windows and
`/mnt/shared/LINUX-LLM-RUNTIME-HANDOFF.md` in Linux. Its maintained
source is `network/LINUX-LLM-RUNTIME-HANDOFF.md` in the Linux repository.

**Repository organization (October25):** private repositories remain
`linux-llm-amd` and `windows-llm-nvidia`. Public references are now separated as
[linux-llm-amd-public](https://github.com/Biegle-W/linux-llm-amd-public) and
[windows-llm-nvidia-public](https://github.com/Biegle-W/windows-llm-nvidia-public). Ubuntu's existing public history is
retained, including earlier Windows snapshots; the new Windows public repository
contains reviewed sanitized files only. Retired setup source/documentation is
indexed under [archives](../../archives/README.md), with dated hardware/results preserved.
Existing local checkout paths, installed launchers, model assets, guards, ports
and daily publisher paths remain unchanged.

**GPU-resident qualification (October 26):** authorization is restricted to
`qwen3.8-27b-vllm`, `nemotron-3.5-bolt-vllm` and
`qwen3.8-27b-sglang-dflash2`. RAM-offloaded llama.cpp, Maya and Strata stay held.
Trials use GPU-LOCK, both cards, an isolated worker cgroup (7 GiB memory.high,
8 GiB memory.max, 4 GiB memory.swap.max) and launch-through-shutdown memory/
thermal evidence. Those early trials selected `low-churn-v1` explicitly; a later
October26 user instruction makes it the default as described below. Settled swap does not waive swap-I/O,
host-pressure, correctness or zero-VRAM-spill gates. All three reviewed loading
trials exceeded the 4 GiB cumulative host swapout budget and were guard-stopped
before any complete inference window. None qualified; no throughput or correctness
claim follows. All owned units stopped, both GPUs returned to baseline, the lock
was released and the hub/API remained active. The earlier interrupted load remains
nonqualifying. Existing 64 GB results retain their original attribution.
[Exact byte counts, thermal coverage and constraints](../hardware/VRAM-QUALIFICATION-2026-10-26.md).

**Model storage migration (October 26):** Bolt W4A16 now lives on
sharedSATA1 under `vLLM-Models/Nemotron-3.5-Bolt-74B-A9B-AutoRound-W4A16`.
All 33 files (43,645,320,930 bytes) were SHA-256 matched before deleting the source
model directory from SATA2. Active launcher/profile/parser paths and the static
placement helper now use SATA1; the helper no longer waits for or mounts SATA2.
No quantization, context, runtime version or inference guard changed, and no new
inference test was run. New streaming packs still use system NVMe; do not add
models to Shared NVMe. After user unmount/shutdown/removal and the October26
reboot, SATA2 is no longer detected; its obsolete boot entry still needs
administrator `/etc/fstab` cleanup.
[Migration evidence and removal steps](../hardware/BOLT-STORAGE-MOVE-2026-10-26.md).

**October26 swap deployment history, superseded October27:** old trials used
`low-churn-v1` and fixed 4 GiB worker/cumulative-write caps, with stricter engine
no-swap scopes. They remain historical evidence. Current loading-swap permission
and `loading-swap-v2` take precedence; use the standing instruction above.
Owned cgroup containment, pinned `cgroup.kill`, fail-closed telemetry and selective
cleanup remain required. No engine was promoted or benchmark rerun for this policy
change. Nightly updates remain paused.

<!-- daily-update:begin -->
**Engine versions after the 2026-10-29 daily update** (`llm-daily-update.timer`, 03:00; details in `hardware/DAILY-UPDATES.md`):

| Engine | Production |
|---|---|
| llama.cpp | `eb4e244be77a` |
| vLLM | `0.33.0rc1.dev229+g3966924d5.rocm72` |
| SGLang | `f84475ccf593` |
| Strata | `7dd5cf18e68c` |
| Maya | `f26d8bab43f9` |
| Strata DeepSeek | `8183c6b67162` |
| llama.cpp ornith-1.5-122b (manual source pin) | `2280f0fd163b` |
| vLLM nemotron-3.5-bolt-vllm (manual runtime pin) | `0.32.1rc1.dev435+gc50aca144.rocm72` |

Last run: Strata rejected.
<!-- daily-update:end -->

**Inference-only swap / 10-minute idle policy (October24):** unrelated/background
tasks may use system swap; updates check only aggregate managed inference worker
swap and conservative system-wide swap I/O against the current October26 low-churn limits below.
Global swap is unchanged. Models and engines now unload after 600 seconds since
the last inference request completes (five-second watcher). New backend launches
receive a full grace period. Hub/direct-router/native Chat POSTs and loading are
tracked; status/health/model-list GETs do not reset the clock. Active requests,
startup, native queued jobs, unknown state and GPU-LOCK defer unloading. Cleanup
uses existing owned-backend matching, preserving DSH, gateway and unrelated apps.
The next hub/DSH/gateway request restarts the guarded backend; native backend pages
and terminals may need reopening. No new port, weight, runtime version, context,
placement, default or memory-guard change. [Policy and tests](../hardware/MODEL-HUB-2026-10-22.md#ten-minute-idle-power-saving--october24).
Live vLLM/Qwen27B unload was observed at 607.0 seconds including polling/cleanup;
zero owned inference processes remained, sampled card memory fell 16.871→0.026 GiB
each, DSH/gateway were preserved and all 13 IDs remained. Other-engine safety and
next-request reload are CPU-tested; no new all-model GPU/power benchmark.
[Functional evidence](../hardware/results/model-idle-2026-10-24.json).

**Worker swap allowance (October25, historical; superseded by the October26 default below):** update baseline eligibility and
candidate promotion now permit up to **64 MiB (67,108,864 bytes)** of aggregate
owned inference worker swap in each model record and the full loading/testing/
shutdown lifecycle. Larger swap fails; dedicated VRAM spill must remain zero.
Invalid/missing telemetry, sampling errors, absent workers and incomplete coverage
still fail closed; performance/quality gates remain. Background system swap is
allowed. Existing worker cgroup limits, RAM/VRAM admission and latched watchdogs
remain. Fresh normal-launcher tests promoted llama.cpp `2280f0fd`; Maya 1.1.28
failed DeepSeek decode gates and was rolled back/answer-smoke verified, while
Strata DeepSeek 0.1.51 failed selected IQ3_XXS parity before installation. All fresh
baselines and the tested candidate memory records met the 64 MiB cap. Existing
Maya 1.1.26 and Strata DeepSeek 0.1.49.1 are retained. No new full-window or remote-peer
check. [Fresh outcomes, timings and thermals](../hardware/FRESH-ENGINE-TESTS-2026-10-25.md).
[Policy](../hardware/daily-update/README.md#minor-worker-swap-allowance--october-25).


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
zero owned swap/spill. [Gates, failures and full-run thermals](../hardware/STRATA-TUNING-2026-10-24.md)
and [all trials](../hardware/results/strata-tuning-2026-10-24.json).

## Strata 0.2.4 DeepSeek — October 24

Strata now reuses the existing Maya-S and Maya-XS weights with independent metadata, both GPUs and 32K. **13 active profiles**; all Maya choices and the Strata Q3 DSH default remain. Separate gfx1100 / HIP 7.2.3 DeepSeek engine 0.1.49.1 at 8183c6b6; the current Qwen engine is8183c6b6 (October24 daily promotion). No weight download/duplication, no new ports.

| Model ID | RAM-store GB | Code / prose t/s | Native PP t/s | TTFT s |
|---|---:|---:|---:|---:|
| `deepseek-v4.1-flash-1017-strata-s` | 0 | 7.00 / 7.16 | 168.0 | 37.491 |
| `deepseek-v4.1-flash-1017-strata-xs` | 0 | 18.25 / 12.77 | 183.7 | 34.289 |

Exact-binary isolated timings, three code/prose trials with a 256-token output cap and three fresh prompts with ~6.3K actual input tokens; native prefill and external SSE TTFT/decode are distinct. Selected profiles pass the normal Ptyxis launcher, original UI, authenticated host-self API, near-31.5K/history checks and Q3 switchback with zero owned swap/spill. These are not a matched Maya speed comparison. [Setup, gates and thermals](../hardware/STRATA-DEEPSEEK-2026-10-24.md) · [numeric record](../hardware/results/strata-deepseek-2026-10-24.json).

DeepSeek profiles use separate `strata-dsv41/upstream` source/build on Linux ext4. Shared-NVMe metadata is under `LLM-Models/Strata/DeepSeek-V4.1-Flash-1017/{Maya-S,Maya-XS}/pack`, referencing existing Maya S/XS/drafter weights; S Engram shards 5/6 remain shared dependencies. Both profiles:32K/24threads/native8GiB actual6GiB startup/52G no-swap/latched guards; S no drafter, XS matching xs2. Prompt skip/YOCO/expert omission/persistent slots disabled. The same 30020/30021 ports and one native worker; no Windows DeepSeek-Strata pack is validated. Windows must create separate metadata/validation while keeping shared weights intact.


The previous nine Shared Markdown documents are preserved byte-for-byte in
`D:\LLM-ARCHIVE\LLM-HANDOFF-ARCHIVE\2026-10-18\` (Linux:
`/mnt/shared/LLM-ARCHIVE/LLM-HANDOFF-ARCHIVE/2026-10-18/`). They are historical
references, not alternative current configurations. Their old CUDA commands,
addresses, defaults and single-GPU policies must not override the settings here.
No model files, runtime settings, credentials or inference processes were changed
by the original consolidation; the subsequent MoE offload update is documented below.

## Maya source update — October23 (before XS production)

Maya25deec5/VERSION1.1.24 is promoted with exact tested SDK7.2.3 binaries; ten activeprofiles and Strata DSH default unchanged. At source promotion: bothGPU/32K/Maya-S models,GLM40GiB/MTP,DeepSeek24threads/noDSpark; subsequently XS production below,8GiB reserve/actual6GiB startup/52Gno-swap/continuous guards. GLM MAYA_GLM_PREFILL_FUSED=0 disables the newgfx1100 kernel that failed IQ2_S down parity. DeepSeek DS4_IQ_Q8K=0/DS4_STREAM=0 retained. Fresh3trial code/prose/PP/TTFT: GLM19.72/15.69/535.6/11.928s; DeepSeek6.42/6.78/299.0/21.062s. Both near31.5K/history/tools/JSON/SSE and normalDesktop/Ptyxis/originalbrowserselector/authenticatedgateway/switchback pass. Source19 rollback retained. [Report and temperatures](../hardware/MAYA-UPDATE-2026-10-23.md). These source-update S measurements are historical; the XS production section below defines current DeepSeek selection.

## Both DeepSeek quants — October23 history (S retired October26)

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
[Deployment and validation](../hardware/MAYA-DUAL-DEEPSEEK-2026-10-23.md).

### Maya-S DSpark retest — October23

**Historical S selection: DSpark off; S retired October26.** Fresh Maya1.1.24/ROCm7.2.3 comparison uses
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
[All trials, functional/context checks and thermal coverage](../hardware/MAYA-S-DSPARK-2026-10-23.md).


## Maya-XS + DSpark rollout history — October23 (before separate S selection)

DeepSeek now uses **Maya-XS + matching dspark-xs2** under the same model ID
`deepseek-v4.1-flash-1017-maya`:32K,both7900XTX,ROCm7.2.3/Maya1.1.24. GLM stays
Maya-S v2/MTP; all guards, ten-model catalog and Strata DSH default were preserved at that rollout; S is now separately selectable above.
Normal Desktop/Ptyxis/original UI/authenticated API and GLM→XS→GLM→XS passed;
XS is ready. [Production proof and rollback](../hardware/MAYA-XS-PRODUCTION-2026-10-23.md).
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
[XS test report](../hardware/MAYA-XS-DSPARK-2026-10-23.md). The saved S row is a separate
same-day session, not an equal-quality A/B. No NVIDIA community speed is claimed locally.

## Current status and hardware

- Intel **i9-13900KS (24 cores /32 threads)**. Historical benchmark RAM is64GB
  (61.51GiB OS-visible); the live host currently exposes **14.83GiB**.
  MSI MPG Z690 CARBON WIFI, **two RX 7900 XTX 24 GB**. Both GPUs use CPU PCIe 4.0 x8 links.
  The PEX88096 switch remains purchased but not installed or P2P-validated.
- Every active profile uses both cards. Empero, Sage and Flint keep all model
  weights on GPUs; Super and Ornith retain CPU expert backing plus GPU caches. Strata streams PLE
  and cold expert data from the new shared NVMe. SGLang/vLLM use ROCm TP2 through
  host transport: no-hostcall RCCL 2.27.7, `NCCL_P2P_DISABLE=1`, `HSA_ENABLE_SDMA=0`
  and custom all-reduce disabled. No direct P2P claim is made.
- **Twelve profiles:** four llama.cpp, one SGLang, three vLLM, two Strata, two Maya. Presence in
  the authenticated catalog does not mean weights are loaded. Only one managed
  model/backend runs at a time. Frontends, gateway and unrelated apps are preserved.
- The saved DSH default/provider is preserved. Super IQ3 remains selectable;
  Muse Q4 and Super Q4 weights/setup are retired; shared target/draft weights stay. FreeToken/HyperQwen remain retired.
- Kernel observed7.0.0-38-generic; retained native SDK7.2.3. Exact build, token counts and
  benchmark methods are in [the post-upgrade report](../hardware/CPU-RAM-PROFILES-2026-10-20.md).
  Historical i5/32 GB and NVIDIA measurements retain their own hardware attribution.
- Shared SATA and the new shared NVMe are exFAT; builds/environments stay Linux ext4.
  This machine is dual-boot: Windows boot stops the Linux service. Model-file sharing
  does not make Linux HIP binaries or absolute paths runnable in Windows.
  Retained model drives mount at boot through `/etc/fstab`; `local-llm-mounts.service` is a session-start fallback (current October 26 layout below).
  Desktop login is not required for the configured headless boot mounts and lingering services.
  [Details](#storage-and-runtime-pins).

## Ornith-1.5-122B Q4 test and Sage activation — October21

**Ornith (test only).**
- Official Q4_K_M and projector are verified on Shared SATA.
- Tested stack: llama.cpp 4c3c5810 / HIP 7.2.3, both GPUs, 30 CPU expert layers,
  4 GiB GPU cache, 32K context.
- MTP off: code/prose 11.43 / 13.34 t/s, native prefill 52.68.
- MTP3 was rejected by the predeclared gate (−27.3%). 12 batch threads made no difference.
- 30,988-token retrieval, history follow-up, vision and tools passed, with no swap or spill.
- Not in the catalog or launchers.
- [Test](../hardware/ORNITH-122B-TEST-2026-10-21.md).

**Sage (October21 GGUF activation history; replaced by INT4 above).**
- `sage-a1.5` is the eleventh llama.cpp profile: 64K, MTP3, with projector.
- (Removed October 22.) The **Sage** Desktop shortcut ran `dsh/start-sage`. That loads Sage through the
  admitted router, then opens llama.cpp's built-in Chat with Sage preselected.
- The router now passes gzip through, keeps `/models/sse` out of its lock, and forces
  `autoload=false` on model GETs.
- Harness and accounts not installed.

**Drive rename (user request):** the shared SATA model drive is now labelled
**sharedSATA1**. exFAT allows at most 11 characters. The mount script, model presets,
Strata settings and ComfyUI paths follow its mount point; the examples here keep `/mnt/shared`.
The former Bolt volume **sharedSATA2** is now retired from model configuration; physical removal awaits administrator unmount/fstab cleanup (October 26).

**Slow-model research (October 22):** the top community lead is llama.cpp `ubatch` (128 in every
profile) × `GGML_OP_OFFLOAD_MIN_BATCH` for CPU-expert prefill. Not yet tested.
[Note](../hardware/SLOW-MODEL-OPTIMIZATION-RESEARCH-2026-10-22.md).

**Boot without a login (October 23):** model drives mount from `/etc/fstab` by UUID (`nofail`)
instead of desktop-session udisks mounts, and user services run through lingering, so models serve
after a reboot with nobody logged in. Secure Boot is disabled so the DKMS motherboard fan driver
loads. The unused NVIDIA driver was purged. `amdgpu.ppfeaturemask=0xfff7ffff` enables RDNA3
OverDrive fan control; CoolerControl runs max-cooling curves on every motherboard
and GPU fan, and BIOS OS-controlled ASPM is on. Monitors go on the motherboard outputs; the 7900 XTX outputs stay dark by design.

**FLUX 3 Image Klein (October 23, user):** the official BFL ComfyUI BF16 release (distilled
transformer, Qwen3-VL-4B encoder, int8 prompt upsampler, FLUX.2 VAE; 28 GiB) is in
`sharedSATA1/Graphics-Models`, so Windows ComfyUI sees it through the same folders. Linux passed
text-to-image (1024×1024, 34 s) and a reference edit (1248×832, 48 s) on both 7900 XTX. Edits need
a local workaround: torch 2.15.0.dev20260827+rocm7.2 aborts in conv3d with a bias when MIOpen is off,
which ComfyUI's default on AMD triggers in the Qwen3-VL vision tower. Gated FLUX Kommunity License.
[Report](../graphics/FLUX3-KLEIN-2026-10-23.md).

**Qwen3.6-35B-A3B retired (October 23, user):** `qwen3.6-35b-a3b` is removed from the llama.cpp
catalog, presets and offload plan. A saved DSH selection of it moves to `empero-qwen3.8-35b-a3b`,
which matches its speed. Ten active profiles. Its 22.2 GB GGUF was deleted from SATA1 at the user's request.

**llama.cpp batch sweep (October 22):** every llama.cpp profile now overrides the inherited 512/128
batch. Native ~8K prefill, decode within 2%: Ornith 4096/4096 52.7 → 714.9 tok/s; Super 2048/1024
93.9 → 431.4; Qwen3.6, Empero and Sage 4096/4096 ~380–400 → 2,794–2,945 (fresh TTFT ~21 → ~2.8 s).
Ornith 8192 and Super ubatch ≥2048 break the 3 GiB/card guard (Super 1024 leaves 3.6 GiB).
[Report](../hardware/LLAMA-BATCH-SWEEP-2026-10-22.md).

**GPU access without a desktop:** add the inference user to the `render` and `video` groups.
Otherwise ROCm access comes only from the logind seat ACL, and ending the desktop session leaves
user-service backends with no ROCm devices. Restart the user's systemd manager afterwards.

**Sage front end removed, Ornith active, engine rule (October 22):** the Sage Desktop shortcut and
launcher were removed (`sage-a1.5` stays active). `ornith-1.5-122b` is an active llama.cpp profile
(32K, MTP off, vision). Standing rule: always look for a faster vLLM/SGLang build before llama.cpp
GGUF. Eleven active profiles.

**Model hub (October 22):** `local-llm-hub.service` runs `dsh/model_hub.py` on 127.0.0.1:30100.
Any catalog model requested there, or through the gateway (which now forwards to the hub),
starts or switches its backend via the normal guarded launcher. Nothing starts while
`hardware/generated/GPU-LOCK` exists. [Details](../hardware/MODEL-HUB-2026-10-22.md).

**ROCm update test (October 22):** the 7.2.4 runtime and 7.14.1 llama.cpp builds gave no gain over
fresh 7.2.3 controls (vLLM Qwen, llama Qwen3.6/Sage, Ornith also on 10.1); 7.2.3 is retained. The
opt-in `LOCAL_ROCM_RUNTIME_OVERLAY` hook is for isolated tests only.
[Report](../hardware/ROCM-724-7141-2026-10-22.md).

**Switch-over (user instruction):** Bolt now runs on vLLM as `nemotron-3.5-bolt-vllm`
(`vllm/start-bolt-rocm`, 262K, weights moved from sharedSATA2 to sharedSATA1 October 26). Router checks passed
(arithmetic/JSON/tools); 37.32/37.21 t/s decode, 2,959 t/s prefill. The llama.cpp `nemotron-3.5-bolt`
and `qwen3.8-27b-q4` profiles are retired; llama.cpp defaults to HIP. Their GGUF files were deleted at the user's request (October 22). Ten active profiles.

**Bolt vLLM test:** the AutoRound W4A16 build on vLLM TP2 matches llama.cpp decode (38 vs 37 t/s)
and is about 13× faster at prefill (2,910 vs 224 t/s). It passed a 255K retrieval at 262K context.
Not active; tools/JSON untested. [Report](../hardware/BOLT-VLLM-2026-10-21.md).

**vLLM alternatives (research only):** Bolt AutoRound W4A16 (43.6 GB) is the one
vLLM test candidate. Sage has no ready 4-bit vLLM build, and its FP8 build is not for RDNA3. No downloads.
[Note](../hardware/VLLM-ALTERNATIVES-BOLT-SAGE-2026-10-21.md).

**DSH default (user instruction):** Strata Q3 (`strata-local` /
`qwen3.8-flash-next-iq3_xxs`) for new agents. A running DSH applies it after restart.
- [Details](../hardware/SAGE-A15-2026-10-21.md#activation-and-desktop-web-shortcut--october-21).

### Earlier Ornith research note

Architecture/config and bounded GGUF-prefix inspection only; no full checkpoint,
load, benchmark or active profile. OfficialQ4_K_M70.64GiB and UnslothUD-IQ3_XXS
46.11GiB include MTP. Retained llama.cpp4c3 recognizes this48-layer qwen35moe
class, but exact-weight/dual-GPU/cache/tool/context validation is pending.
Q4 CPU expert backing around41GiB/4GiB aggregate hot cache/32K is a **planning
candidate**, not an admitted allocation. No Strata/Maya pack replacement or ROCm
upgrade. [Assessment and sources](../hardware/ORNITH-122B-ASSESSMENT-2026-10-21.md).
At that research stage, ten profiles, the DSH default and Sage's test-only status were unchanged.

## Sage-A1.5 downloaded test model and ROCm selection — October21

Official Sage-A1.5 Q4_K_M and its separate mmproj are checksum-verified under
`GGUF-Models/Sage-A1.5-GGUF` on Shared SATA (Windows D:). Sage was later activated
as the eleventh profile with a Desktop Chat shortcut (see above). The DSH default,
runtime versions and all guards remain unchanged. Text test selection:
llama.cpp4c3c5810/HIP7.2.3, bothAMD layers1:1,64K,q8_0KV,MTP3, CPU expert backing
9.08GiB/12GiB GPU cache. Tools/JSON/SSE/fresh8K/near61,999-input
retrieval/full-history and separate image smoke passed. Native256K is not locally
quality-validated. Code/prose83.42/66.75t/s,nativePP387.02,freshTTFT21.160s;
SDK10.1 is effectively tied and not selected. No driver/global SDK change.
[Exact tests/limits](../hardware/SAGE-A15-2026-10-21.md),
[ROCm recommendation/sources](../hardware/ROCM-SELECTION-2026-10-21.md).
7.14.1 is untested; do not silently migrate existing engines.

## ROCm10.1 six-engine validation — October21

All production runtimes are retained; no ROCm10.1 candidate passed every promotion gate. Empero’s matched seeds 42/43/44 improved aggregate speed by only 0.30%, below the >3% gate; keep HIP 7.2.3. The candidate's near-256K functional tests passed.
SGLang DFlash2/163840 and vLLM MTP3/163840 retain their existing Torch/RCCL/ROCm7.2.3
stacks. Strata Q3/13.5GiB/six workers/256K and Maya-S32K models retain7.2.3;
Comfy retains Torch2.15nightly/packaged7.2.1 for browser and native Desktop.
No kernel/driver/global SDK/weight move or guard change was made. Both GPUs,
CPU expert backing/hot caches, model IDs, contexts, API addresses/authentication,
DSH default, PATH names and frontend placement remain unchanged.

Fresh controls/candidate/reverse-order/diverse-seed/normal graphics results and
exact source/library hashes/thermals are in [ROCm10.1 report](../hardware/ROCM101-2026-10-21.md)
and [numeric evidence](../hardware/results/rocm101-2026-10-21.json). vLLM fixedseed
improvement fails diverse-seed gate; Strata faster prefill trades against slower
prose. Normal Comfy image23.686→18.331s/H3 83.831→85.279s: video regression rejects
migration. The separate52GiB pilot HIP fault is retained, not attributed to a proven
cause. Latest LLM rates are in the [current profile overview](../hardware/CURRENT-AMD-BENCHMARKS.md).
Earlier10.0 trials remain [historical](../hardware/ROCM10-OTHER-ENGINES-2026-10-20.md).
Forum claims remain separate from local measurements; [source trail](../hardware/FORUM-OPTIMIZATION-SOURCES.md).

## Project Maya: GLM-S and DeepSeek-XS selectable

Maya HIP v1.1.24 / `25deec505b525212e05faa58697d9d2b7d17fdb3` is a separate
Strata fork with its own source, Python 3.12.14 environment and pinned llama.cpp
3cf03257 dependency. ROCm SDK 7.2.3 is unchanged; isolated rocWMMA 2.2.0 headers
and the retained GCC 14.4/sysroot resolved its build dependencies. Existing engine
versions and the saved DSH default are preserved.

| API model ID | Total context | Selected quant / strategy |
|---|---:|---|
| `glm-5.3-flash-maya` | 32,768 | Maya-S, MTP, bounded 40 GiB whole-machine RAM expert tier, GPU cache, NVMe cold reads |
| `deepseek-v4.1-flash-1017-maya` | 32,768 | Maya-XS IQ1_S + matching dspark-xs2, shared Q6_K Engram, CPU-mapped experts + GPU hot cache, 24 threads |

Both use **both 7900XTX cards through layer groups**, not true TP2. DeepSeek's
requested TP2 automatically becomes width 1 because its 256-value blocks do not
divide 2,304-wide experts into two parts; neither GPU is dropped. DeepSeek's RAM
backing is mapped/page-cached; XS + DSpark reports roughly91.3GB of logical CPU-lane
weights, not fully resident RAM. The matching xs2 drafter is enabled. The old
Maya-S/source1.1.17 DSpark rejection (−20% overall) is historical and does not
define the new XS selection. The source1.1.24 XS retest improved short code52.9%,
with prose nearly unchanged; the user authorized production deployment.
[XS benchmark](../hardware/MAYA-XS-DSPARK-2026-10-23.md) and
[normal production proof](../hardware/MAYA-XS-PRODUCTION-2026-10-23.md).
**DeepSeek needs 52 GiB available RAM before loading.** Heavy desktop apps such as
Chrome can keep it from starting; close them and retry. GLM's 40 GiB RAM tier passed >=10 GiB available headroom and improved
its aggregate 22.91% over 36 GiB under the same GPU reserves, with only 3 trials
and stateful caches; this is not a universal optimum.

The **Maya** Desktop entry (application-menu entry hidden because it is a browser frontend) opens a visible terminal; `llm-maya` uses the
current terminal or SSH TTY. Both load GLM by default. Start `dsh` separately, choose **Local Maya**, then any of the three IDs.
`llm-maya --model deepseek-v4.1-flash-1017-maya` selects DeepSeek initially.
In the Maya web sidebar, choose **Maya model → Switch model**. The same page
stays open during the guarded GLM/DeepSeek reload and displays progress/errors;
finish or cancel an active reply before switching. Model-specific sampling/context
refresh after readiness; chats and all GPU/memory settings are preserved.
Reopening `dsh` reuses the existing verified frontend without touching inference.
[Web switching and DSH fix](../hardware/MAYA-WEB-SWITCHING-2026-10-21.md).
The router switches models serially and unloads the previous worker. Backend
handover recognizes only the configured Maya native binaries/server/router as
part of the configured Strata family. DSH, the gateway, ComfyUI and unrelated
applications are preserved. `llm-maya --help` /invalid IDs do not hand over a server.

Router/private worker are loopback **30030/30032**; persistent web UI/proxy
remains on **30031**. Remote clients use the same private
key and **port 10000 `/v1/chat/completions`** gateway; worker/UI/admin endpoints
are not exposed remotely. The earlier thirteen-profile auth/catalog check and
both models' actual generation, JSON and synthetic tool round trips passed on
loopback/LAN/Tailscale host-self routes. GLM→DeepSeek→GLM reload passed with one
native worker. A separate remote peer and image-request accuracy/performance
were not tested. GLM is text only; DeepSeek's installed vision tower is unvalidated.

Each native reserve is 8 GiB; actual whole-card free must be >=6 GiB/card at startup.
Continuous latched guards retain 3 GiB available RAM / 3 GiB whole-card free floors,
zero worker swap/spill and a 52G no-swap worker scope. Loading requires 60 GiB
physical / 52 GiB available RAM and 16 GiB free on each GPU after handover. Failure
unloads only the owned worker and requires explicit reload. Never lower these
limits or use swap as capacity to make a new profile pass.

Historical October20 Maya source19/SDK7 rates (superseded by source24/XS above): GLM-S six samples/workload across two starts,
code/prose18.44/16.10t/s, nativePP518.0, freshTTFT12.363s; actual fresh6308–6314.
DeepSeek-S selected `DS4_IQ_Q8K=0`/`DS4_STREAM=0`, three samples/workload,
6.89/7.08t/s,188.6PP,33.418s, actual6295–6299. Both use32K, retained native8GiB
and actual6GiB startup/52Gnoswap guards. GLM near31496 and DeepSeek31482 plus
full-history passed. Normal actualDesktop/Ptyxis/originalUI/authgateway and
GLM→DeepSeek→GLM passed; host-self routes only, no remote peer or vision test.

ROCm10 is not promoted: same-source GLM speed gate failed; DeepSeek automatic
lane lost roughly35–37% decode, and explicitnostream10 stalled the first timed
request after one token. No completed timed result is reported for that arm.
Source17 remains verified rollback; original17/quant ABBA evidence stays historical.
Selected DeepSeek disables only the extra per-token PCIe lane; CPUexpert backing
and GPUhotcache stay active. No quality-changing expert skipping or approximate
prompt skipping is enabled. Both SDKs pass fourteen GLM/core checks percard.
New default rounding1 fails reversedIQ3_S/IQ2_S numerical parity, so prior0 is
explicit. SDK7 retains only two known excluded mixedQ4_K/IQ4_XS bitexact failures;
those types remain blocked. [Current report/trials/thermals](../hardware/MAYA-ROCM10-2026-10-20.md).

Binary/source/config fingerprints and the DeepSeek descriptor/index/Engram hash
must match before loading. Models are at `/mnt/shared-nvme/LLM-Models/Maya` on the new shared NVMe;
no model weights were left in the Maya engine folder on the Linux primary NVMe.

**Windows:** reuse the GGUF/draft/vision assets, but build/validate Windows engines
separately. The Linux DeepSeek pack `Maya-XS/maya-ds4/ds4.txt` contains a Linux
absolute `model_dir`; generate a separate `maya-ds4-windows` pack/index and point
the Windows config to it. Do not let a Windows installer overwrite the Linux
pack. The new NVMe's Windows drive letter is unknown. The handoff remains on
original Shared SATA /D:. Models and Linux runtime binaries are different assets.

## Nemotron Super: IQ3 active, Q4 retired

`nemotron-3.5-super-iq3` retains 32,768 total context, both GPUs, HIP layer split
21:19, Q8 K/V, Flash Attention, six CPU threads, batch 512/microbatch 128,
checkpoints 0 and MTP off. CPU experts occupy 19.124 GiB with a 2,048 MiB GPU
hot-expert cache ceiling. Available host RAM before load must be at least
23.124 GiB. Owned continuous guards retain 3 GiB RAM/per-card VRAM floors with
the existing sample debounce; only the owned worker may be unloaded.

It passed 28,546-input retrieval and six fixed ~8K-input/256-output trials on
4c3c5810: 15.90/16.95 t/s code/prose. A separate production rebuild passed the
normal launcher, tools/JSON/SSE, both-card placement and zero owned swap/spill.
These are fixed-input timing workloads, not short-prompt TTFT; concurrent IO
caveats remain in the [original record](../hardware/results/dual-amd-i9-64gb-2026-10-20.json).

The user's later October 20 decision removes Muse Glimmer Q4 and Super Q4_K_XL,
superseding the earlier both-quants-retained decision. Their active model,
placement, preset and candidate entries are removed; exactly four GGUF files
(95.726 GiB) were deleted. Super IQ3's three shards and shared family metadata
are retained on Shared SATA. Q4 admission test fixtures and historical speeds
remain evidence, not an installable active profile. Windows setup snapshots
are historical and do not automatically follow this Linux retirement.
[Deletion manifest and checks](../hardware/results/model-retirement-2026-10-20.json).

**Super IQ3 loads from the shared NVMe (October 20).** The production preset now points at a
copy under `/mnt/shared-nvme/LLM-Models/Nemotron-Super/`; all three shards match the
download-manifest SHA-256.

On the reference host:
- **Load time:** 42.2 s, versus 112.1 s from SATA.
- **Inference:** identical, −0.12% geometric mean.

The SATA backup was removed at the user's request October27. The active NVMe
shards remain; historical checksum/copy evidence is retained in the October20
[numeric record](../hardware/results/super-nvme-load-2026-10-20.json).

SSD streaming (`load-mode = mmap`) was rejected. It reproducibly failed the forced tool call
(llama.cpp grammar-sampler exception) and kept the same host model memory.
[Trial and decision](../hardware/SUPER-NVME-LOAD-2026-10-20.md).

## Active model catalog

The current catalog has **12 enabled profiles**: five llama.cpp, one SGLang, two vLLM, two Strata and two Maya. The current i9/64 GB report retains separate timing methods and exact build attribution.
Earlier runtime/placement checks remain in their dated reports and must not
replace the catalog and settings below.

All contexts below include system instructions, tool definitions/results,
conversation history, user input **and output**. They are configured budgets,
not guarantees of full-window speed or general long-context accuracy.

| Backend / placement | Exact API model ID | Total context | Target quantization | Speculation |
|---|---|---:|---|---|
| llama.cpp / HIP, CPU experts + cache | `nemotron-3.5-super-iq3` | 32,768 | UD-IQ3_XXS, three shards | Off |
| llama.cpp / HIP, VRAM-only | `empero-qwen3.8-35b-a3b` | 262,144* | IQ4_XS | MTP3 |
| llama.cpp / HIP, VRAM-only | `sage-a1.5` | 65,536 | Q4_K_M + vision projector | MTP3 |
| llama.cpp / HIP, CPU experts + cache | `ornith-1.5-122b` | 32,768 | Q4_K_M + vision projector | Off |
| llama.cpp / HIP, VRAM-only | `flint-40b-a2.5b` | 32,768 | UD-Q4_K_XL | Off; reasoning-budget128 |
| SGLang / ROCm TP2 | `qwen3.8-27b-sglang-dflash2` | 163,840 | GPTQ INT4/group64 | DFlash2, 8 draft tokens; BF16 KV |
| vLLM / ROCm TP2 | `qwen3.8-27b-vllm` | 163,840 | GPTQ INT4/group64 | MTP3; bfloat16 KV |
| vLLM / ROCm TP2 | `nemotron-3.5-bolt-vllm` | 262,144 | AutoRound W4A16 (GPTQ int4/group128) | Off; bfloat16 KV |
| Strata / HIP dual-card layer split | `qwen3.8-flash-next-iq3_xxs` | 262,144 | IQ3_XXS, bounded CPU expert backing + GPU cache | MTP (`--spec 3`) |
| Strata DeepSeek / HIP dual-card layer groups | `deepseek-v4.1-flash-1017-strata-xs` | 32,768 | Reused Maya-XS IQ1_S | Matching xs2 |
| Maya / HIP dual-card layer groups | `glm-5.3-flash-maya` | 32,768 | Maya-S v2, mixed IQ2/3 experts / Q6_K attention/shared | MTP |
| Maya / HIP dual-card layer groups | `deepseek-v4.1-flash-1017-maya` | 32,768 | Maya-XS IQ1_S / Q6_K Engram | Matching dspark-xs2 |

All active llama.cpp profiles use both cards and HIP, Q8_0 K/V and flash attention.
Empero uses512/512, Sage and Flint4096/4096, Ornith4096/4096 and Super2048/1024.
Empero/Sage/Flint are VRAM-only with DIO load and bounded no-swap host staging;
Super/Ornith retain their CPU expert backing and GPU hot caches. Dense
Qwen27B remains GPU-resident on SGLang/vLLM; Bolt uses vLLM W4A16. The old
llama.cpp Bolt/Qwen Q4 and Vulkan profiles are retired. Effective settings come
from the maintained model catalog, `dsh/models-hip.ini`, `dsh/moe-offload.json`
and sealed model profiles.

*MoE 256K allocation passed with approximately 64K actual retrieval, tools/JSON
and arithmetic; full 256K filling, quality and sustained speed are untested.
The launcher/router uses the selected profile's validated backend. CPU/cache profiles require their expert bytes plus 4 GiB available RAM;
loaded requests need 3 GiB. A scoped monitor stops only an unsafe owned worker
on sustained low memory, owned swap or dedicated VRAM spill. No unrelated
application/frontend is stopped. See [measurements and both forums' source trail](../hardware/MOE-OFFLOAD-2026-10-18.md).

Bolt vision remains disabled and unvalidated; this Q4 text profile uses no projector.

Bolt Q4 source: `darioooooo0o/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-GGUF`,
revision `b739f8c7c5484413ae3e55e6da8383f0f2570cee`. The two verified shards
are in `GGUF-Models/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-Q4_K_M-GGUF/Q4_K_M/`
on Shared/D:. Pass `NVIDIA-Nemotron-3.5-Bolt-74B-A9B-Q4_K_M-00001-of-00002.gguf`
to the runtime; keep shard 2 beside it. The old 24 GB IQ2 model was removed after
Q4 validation. API ID stays `nemotron-3.5-bolt`; clients need no model-ID change.
Q4 passed arithmetic/JSON/tools and 63,911-token retrieval. Short code decode:
**35.7 t/s**; long prefill: **424.0 t/s**. Single probes, not matched
IQ2/Q4 speed rankings or full 256K validation. See [replacement details](../hardware/NEMOTRON-Q4-2026-10-18.md).

SGLang retains only TP2 DFlash2 at 163,840 total tokens; the separate MTP
profile is retired. BF16 activation/KV/Mamba, Triton attention, fraction 0.85,
one request, GPU prefix caching, eight Mamba state slots, chunks/max-prefill
2048/2048, draft window 2048 and eight draft tokens remain. The optimized verifier
requires both `SGLANG_RDNA_VLLM_VERIFY=1` and
`SGLANG_LOCAL_RDNA_VERIFY_WALK_FIX=1`; never enable an unrepaired verifier.
Before loading, retain 22.75 GiB free per card. No CPU weight offload or HiCache is added.

vLLM retains compiled MTP3/TP2, full-decode graphs 1/4, chunks 2048, BF16 activations
and Mamba, Radeon prefill tiles, RCCL Simple, utilization 0.82 and 21 GiB/card
startup admission. Its selected context is 163,840, KV dtype `bfloat16`,
fixed KV budget 6 GiB per rank.
The old64K/3.5GiB BF16 setup remains historical. Fresh near-window/history,
small functional/tool/SSE checks and no-swap/spill candidate guards passed.
See [larger-context selection and exact measurements](../hardware/QWEN-INT4-CONTEXT-2026-10-20.md)
and [numeric evidence](../hardware/results/qwen-int4-context-2026-10-20.json).
Allocated context is input plus output; long requests are naturally slower than
short prompts. Do not present warm-history latency as cold prefill speed.

The catalog refresh preserves the user's saved DSH provider/model, including a
non-local provider; it does not force a default. The original consolidation
recorded Local vLLM, but a user can change that selection in DSH at any time.
Existing conversations may retain another model. The SGLang launcher defaults
to DFlash2; the llama.cpp router initially starts its dense Vulkan parent.
Selecting a MoE in Local llama.cpp switches only its native worker to HIP.
Choose a model belonging
to the backend actually running. A DSH model selection does not launch another
backend, and the gateway requires an explicit model ID in each generation request.
Older Strata defaults in historical notes/private network metadata are not active
catalog entries and must not be copied into a client configuration.

## Strata Linux app update and verified Intel desktop — October 20

**Installed:** `/opt/appimages/Strata-0.2.1-linux-amd-rx7900.AppImage`,
existing Strata App menu/icon and packaged HIPengine0.1.46 (`a7bdbfdabc9a+rocm`).
Official SHA256/engine manifest and all12 packaged self-tests pass without a model
load. SharedNVMe weights, app model settings and managed `llm-strata` name remain.
Standalone legacy inference settings remain inactive/unbenchmarked.

**Managed active engine:**0.1.46.1/source
`9ae93f7b1fe989d04a8e404d32cddaeeff10505f`, HIP/gfx1100 with isolatedROCm7.2.3.
The exact measured/deployed engine SHA256 is
`c6706bc192c1afb09357e7d1eca9570c35c04562cde5265bd4404fe453848478`.
Source477ac13c/0.1.45 and verified binaries remain inactive rollback.

**Desktop and admission:** GNOME's post-login journal verifies IntelUHD770/i915
primary. User-selected actual loaded startup admission is**5GiB/card**, replacing
the former6GiB gate. Engine7/8GiB reserve targets,continuous3GiB floor/hard1.5GiB
stop,latched telemetry/owned-memory protection and52G/no-swap worker remain.
Maya's6GiB startup rule and other engines are unchanged. Both RX7900XTX participate;
no global compute-device variables or drivers changed. Startup free was
5.356/6.268GiB for the candidate,5.354/6.268GiB for normal API proof and
5.356/6.268GiB for actual Desktop-entry proof. Zero owned swap/spill throughout.

**Validation/results:** all candidate functional/tools/SSE/near32K checks,three
short/fresh8K trials and near-window/history gates pass. NativePP median912.2t/s,
fresh8K TTFT9.015s,code/prose decode75.28/50.31t/s (short TTFT0.229/0.233s).
Fresh marker inputs8185–8188/output20–22; short inputs29/25 and256 outputs.
Actual257984-input/256-output retrieval/code and258266-input/22-output full-history
follow-up (258239 cached) pass all markers. Configured262144 capacity is separate
from tested input. Old0.1.45/NVIDIA/SATA records keep their builds/methods; no
matched upstream A/B or speedup is claimed from threshold/rendering changes.

**Normal launch:** visible Ptyxis,exact native Chat/Monitor assets and blocked
runtime/context/self-update writes pass. Authenticated host-self loopback/LAN/
Tailscale JSON/tool-roundtrip/SSE pass; no external remote peer was tested.
The actual Desktop StrataQ3 file now explicitly starts installed Ptyxis because
GIO Terminal=true did not dispatch here; the corrected actualfile was launched
with gio and passed readiness/arithmetic. PATH llm-strata is unchanged. Strata
opens its native frontend after readiness,DSH stays separate. No duplicate engine
or weights were started. Owned test workers were stopped before GPU handoff.
Windows keeps separate engine/display configuration; shared weights stay intact.

[Current rollout and limits](../hardware/STRATA-STARTUP5-2026-10-20.md) ·
[All fresh trials](../hardware/results/strata-startup5-2026-10-20.json) ·
[Historical app/display and former6GiB failures](../hardware/STRATA-LINUX-UPDATE-2026-10-20.md).

## DeepInfer assessment — research only, October20

Upstream774ce244b87cc0eb8d4b94ab9f5de2ab22049f01 documents NVIDIA SM100 and
Ascend950, and its reviewed build/device selector has no ROCm/gfx1100 backend.
The examples expect a Hugging Face config/safetensors checkpoint, not the existing
Maya-S GGUF pack. No DeepInfer installation, weight download, launcher, model
profile or local benchmark was created. Keep the validated Maya DeepSeek profile;
current active engines/model IDs and connection settings are unchanged.
[Assessment and pinned primary sources](../hardware/DEEPINFER-ASSESSMENT-2026-10-20.md).

## Start, stop and switch

October21 standing placement rule: Desktop UI shortcuts open browser/web
interfaces; application-menu entries open native desktop apps. Desktop **ComfyUI**
opens the browser server; menu **Comfy Desktop1.1.7** opens the official app.
DSH, Turnstone, managed Strata Q3 and Maya web interfaces remain on Desktop with
menu templates hidden. Native Strata App and Unsloth stay in the menu. Backend
terminal launchers and hardware-control shortcuts are preserved. `comfy-desktop`
uses the official Debian package/sandbox, validated October21; `comfyui` retains
the separate browser server. Both Comfy launchers share an exclusive server lock.
The native menu now restores official `StartupWMClass=Comfy Desktop`, matching
its observed Wayland app ID, and uses the packaged `comfyui-desktop-2` icon.
This fixes the missing identity hint in our override; model/runtime settings stay
unchanged. Protocol/metadata/icon resolution and normal reopen passed; direct
visual dock inspection is not automated.

October 19 app-menu integration: **Strata App** opens the existing AMD RX7900
AppImage, with its official bundled 512×512 logo. The installed entry is
`~/.local/share/applications/Strata.desktop`; icon name is `strata-desktop`.
Tracked source and reinstall instructions: [launchers/STRATA-APP.md](../launchers/STRATA-APP.md).
**Strata Q3** and `llm-strata` still start the managed DSH backend. The app owns
its own settings/model worker; it does not inherit the managed profile or memory
watchdog. Avoid loading both workers concurrently. Registration was validated
without starting the app or interrupting the existing backend.

Desktop icon update, October 18: all six LLM launchers now use official upstream
logo/favicon assets (llama.cpp, SGLang, vLLM, Strata Q3, dsh and Turnstone),
replacing the initial custom icons. See [logo sources and original licenses](../launchers/icons/README.md)
and `launchers/icons/SOURCES.json` for pinned URLs, SHA-256 values and extraction
notes. Artwork is unchanged; Turnstone's existing embedded favicon was decoded
from its official HTML. `Icon=` points to the corresponding SVG/PNG in the runtime
workspace; retain those files and update paths if moving the setup. Backend
commands and terminal visibility remain; Strata now uses the tested dual-AMD profile below. DSH
uses the official desktop PNG with its own opaque light tile/background; the
transparent web favicon was replaced for visibility against wallpaper.

October 18 menu preference: Turnstone was removed from the application menu.
Its Desktop launcher and `turnstone` PATH command remain available; this change
did not stop or uninstall Turnstone or affect any inference backend.

Backend Desktop launchers **llama.cpp**, **SGLang** and **vLLM** start only their
backend, with live terminal logs. Models load on the first matching request.
The **dsh** and **Turnstone** launchers are separate optional harnesses; external
OpenAI-compatible clients do not need either one.

| PATH command | Purpose |
|---|---|
| `llm-llama` | llama.cpp model router |
| `llm-sglang` | SGLang router; DFlash2 only, retired MTP unavailable |
| `llm-vllm` | vLLM router, Qwen 27B |
| `llm-strata` | Retained but blocked until the planned RAM expansion and dual-AMD validation |
| `dsh` | DSH frontend only |
| `turnstone --no-browser` | Turnstone frontend without opening a host browser |
| `llm-upgrade-check` | Hardware/readiness inspection; success is not an inference test |

Commands are installed in `~/.local/bin`, with sources in the
repository's `bin/`. Use these managed entry points. Starting a backend stops
only this user's configured llama.cpp, vLLM, SGLang, HyperQwen or Strata inference
servers and their owned workers/log monitors; active replies are interrupted.
DSH, Turnstone, the gateway, unrelated Python/training jobs and graphics apps
must remain running. Never use blanket Python/GPU process killing. A busy unknown
port or unrelated compute workload blocks startup rather than being terminated.
Clicking the same backend again restarts it. Keep its terminal/SSH session open;
Ctrl+C or disconnect stops a foreground backend. Raw research launchers bypass
managed handover and are not routine client entry points.

The vLLM Desktop entry now uses `dsh/start-backend-terminal vllm`: startup output
is saved in `dsh/logs/vllm-launcher.log`, and interactive failures wait for Enter
before the terminal closes. CLI/SSH failures still return normally. Worker logs:
`dsh/logs/vllm-qwen3.8-27b-vllm.log`, SGLang's model-specific files, and
`dsh/logs/llama.cpp.log`. Logs, sessions and credentials remain ignored by Git.

From Windows PowerShell or another SSH client, for example:

```powershell
ssh -t operator@<LINUX_LAN_IP> llm-vllm
# Through Tailscale instead:
ssh -t operator@<LINUX_TAILSCALE_IP> llm-vllm
```

Use another terminal for a frontend if wanted:

```powershell
ssh -L 3080:127.0.0.1:3080 -t operator@<LINUX_TAILSCALE_IP> dsh
# Or Turnstone:
ssh -L 3081:127.0.0.1:3081 -t operator@<LINUX_TAILSCALE_IP> turnstone --no-browser
```

Browse client localhost:3080 for DSH or localhost:3081 for Turnstone. Forward a
different client port if occupied. These harness ports remain Linux-loopback-only.
DSH is `@deepseek-ai/dsh@0.2.1-rc.2`, Node.js 24.21.0. It migrated legacy
`data/settings.yaml` into `data/profiles/web/cordis.patch.yml`, retaining the
imported backup; preserve settings, sessions and credentials. Turnstone 1.9.0a3
uses its own environment and private `turnstone/data/login.txt` for login details.
No password or API key is contained in this guide. Tool execution/web browsing is
a harness/client function, not an ability granted by the inference API alone.

## Connect any Windows, phone or other API client to Linux

| Setting | Current Linux value |
|---|---|
| Protocol | OpenAI-compatible **Chat Completions** |
| LAN base URL | `http://<LINUX_LAN_IP>:10000/v1` |
| Tailscale base URL | `http://<LINUX_TAILSCALE_IP>:10000/v1` |
| Linux MagicDNS alternative | `http://<LINUX_TAILSCALE_DNS>:10000/v1` |
| Authentication | Actual private bearer API key |
| vLLM / ROCm TP2 | `qwen3.8-27b-vllm` | 163,840 | GPTQ INT4/group64 | MTP3; bfloat16 KV |
| Streaming / timeout | On / 600 seconds; allow for cold model loading |
| Initial client output limit | 2,048 tokens, within the total context budget |

The host must remain booted into Linux, awake and logged into its user session.
LAN clients need the permitted home network; Tailscale clients need authorized
tailnet access to TCP 10000. The real key is in Linux
`/opt/local-llm/dsh/data/network-api.key`; obtain/configure it
privately on the client. The old Windows Strata placeholder **`local-strata` is
not a valid key for this Linux gateway**. The same real key serves both addresses
and all enabled backend profiles. Use HTTP as shown; a `.ts.net` name does not
make this raw endpoint HTTPS. Tailscale carries remote transport encrypted.
No public Internet forwarding, Funnel or new tailnet-policy grant was added.

Read-only Windows PowerShell connection check:

```powershell
$env:LOCAL_LLM_BASE_URL = 'http://<LINUX_TAILSCALE_IP>:10000/v1'
$env:LOCAL_LLM_API_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'API key' -AsSecureString)).Password
curl.exe --noproxy '*' --connect-timeout 5 --max-time 30 `
  -H "Authorization: Bearer $env:LOCAL_LLM_API_KEY" `
  "$env:LOCAL_LLM_BASE_URL/models"
```

For Bash:

```bash
export LOCAL_LLM_BASE_URL='http://<LINUX_TAILSCALE_IP>:10000/v1'
read -r -s -p 'API key: ' LOCAL_LLM_API_KEY
printf '\n'
export LOCAL_LLM_API_KEY
curl --noproxy '*' --connect-timeout 5 --max-time 30 \
  -H "Authorization: Bearer $LOCAL_LLM_API_KEY" \
  "$LOCAL_LLM_BASE_URL/models"
```

After configuring the environment, this Python example sends a streamed request
when run by the client (requires its own `openai` package):

```python
import os
from openai import OpenAI
client = OpenAI(base_url=os.environ['LOCAL_LLM_BASE_URL'],
                api_key=os.environ['LOCAL_LLM_API_KEY'], timeout=600)
for chunk in client.chat.completions.create(
    model='qwen3.8-27b-vllm',
    messages=[{'role': 'user', 'content': 'Hello!'}],
    max_tokens=2048, stream=True,
):
    if chunk.choices:
        print(chunk.choices[0].delta.content or '', end='', flush=True)
print()
```

`GET /v1/models` lists all eleven enabled profiles even when their backends are
stopped. `backend_available` means the corresponding router is available; it
need not have loaded weights yet. Authenticated `GET /health` reports available
profiles by backend. The gateway starts at user login and **does not start GPU
backends**. Internal routers/workers remain loopback-only:

| Backend | Router / worker ports |
|---|---|
| llama.cpp | 8080 / 8081 |
| SGLang | 30000 / 30001 |
| vLLM | 30010 / 30011 |
| Strata / HIP | 30020 / 30021 |
| Maya / HIP | 30030 / 30031 |

Do not use those internal ports for remote clients or confuse Linux's port 8081
with the historical Windows Strata API. The gateway exposes chat/completions,
model listing and authenticated health; it does not expose DSH, worker management
or the Responses API. Browser CORS is not enabled; use a native client or a
server-side connector. Tool-calling clients must execute tools and return results.

## Storage and runtime pins

Linux runtime/repository root: `/opt/local-llm` on ext4 NVMe.
Shared SATA model root: `/mnt/shared/GGUF-Models` = `D:\GGUF-Models`.
New shared NVMe root: `/mnt/shared-nvme/LLM-Models` (UUIDCONFIGURE_SHARED_NVME_UUID).
**Its Windows drive letter is not established; do not assume D:.** The canonical
Shared handoff itself remains on the original Shared SATA drive / Windows D:.

- Resident GGUF models remain on the shared SATA, except Super IQ3. Super IQ3 loads from its
  verified shared-NVMe copy; the SATA backup was removed October27.
- Managed Strata and standalone App share `Strata/models/IQ3_XXS`,
  `Strata/packs/iq3_xxs`, tokenizer, MTP and retained unique app assets under the NEW
  shared NVMe root. Both app and backend point directly at the same files; no new
  shortcuts or symlinks. Main GGUF/MTP matched; the generated expert-pack mismatch
  was resolved by a complete source-derived reference SHA-256 check. See
  [verified asset inventory](../hardware/results/streaming-storage-2026-10-20.json).
- Maya is installed/validated under `Maya/` on that new NVMe. Original 13 downloads
  total 443,117,880,880 bytes and passed published checksums; two raw vision source
  files were losslessly converted/replaced. Current 35-file model/pack inventory is
  413.580 GiB, with generated immutable assets hashed. Source/runtime stays Linux
  ext4; no full expert or Engram duplicate is generated. [Inventory](../hardware/results/streaming-storage-2026-10-20.json).
- Linux-only GPTQ target `models/Qwen3.8-27B-W4A16-AutoRound-GPTQ/` and DFlash2
  draft `models/drafts/Qwen3.8-27B-DFlash2-W4A16/` remain on Linux NVMe, shared by
  SGLang/vLLM. Windows cannot use those Linux absolute paths.
- **Current model volumes (October 26).** Only sharedSATA1 (GGUF files plus
  `vLLM-Models/` for Bolt/static checkpoints) and Shared NVMe (existing streaming
  models and Super IQ3) are configured. SATA2 is retired from model discovery.
- `/etc/fstab` provides headless boot mounts; lingering starts user services
  without desktop login. The login `local-llm-mounts.service` is a fallback and
  runs `dsh/shared_storage.py --all`, which verifies only the two retained volumes.
  Replace public UUID placeholders before installing examples.
- The obsolete SATA2 fstab entry remains pending administrator cleanup, and the
  retired drive is no longer detected after user removal and reboot. Remove only
  its old boot entry; see the migration report linked above for original evidence.
- Launcher preflight checks only the model's actual volume: llama.cpp may use SATA1
  or Shared NVMe; Strata/Maya check Shared NVMe; Bolt/vLLM checks SATA1; internal
  Qwen checkpoints need no shared-drive mount. Wrong UUIDs, unknown locations and
  absent model roots are rejected without creating replacement model trees.
- Storage verification: 16 CPU tests pass in each checkout, Bolt's 33 copied files
  match SHA-256, and its nine indexed shards exist. No inference or reboot test
  was repeated. The October 20 login/remount and October 23 headless boot proofs
  remain historical, not new measurements of the post-migration layout.
- Builds, SDKs, environments, caches, harness data and private settings remain Linux-specific.
  Weights, binaries, credentials, raw logs and private archives stay excluded from Git.
  SSD speed affects cold loads and actual PLE/expert streaming; resident-model
  decode results cannot establish that storage speed never matters.

| Component | Selected source /version |
|---|---|
| llama.cpp Vulkan/HIP |`4c3c5810f87efe177949f1b85ae509d38a2a311f`|
| SGLang gfx1100 fork |`f84475ccf593087df3d1da13c9e675eadee12352`, local repairs|
| vLLM |`0.32.1rc1.dev36+ge68efc685.rocm72`, local repairs|
| ROCm SDK /PyTorch /RCCL |7.2.3 /`2.13.0+git733fca1` /no-hostcall 2.27.7|
| Strata HIP |0.1.46.1 /`9ae93f7b1fe989d04a8e404d32cddaeeff10505f`|
| Maya HIP | `1.1.24 / 25deec505b525212e05faa58697d9d2b7d17fdb3` on retained ROCm7.2.3; isolated llama dependency `3cf03257`, rocWMMA `48b7db12` |

llama.cpp 4c3c5810 and vLLM dev36 passed their fixed promotion criteria; throughput
was performance-neutral within noise. The vLLM wheel SHA-256 is
`68cb33f115094f816077c193f8b51eac0ea01052254653b9b336e534d7a71f79`.
SGLang's Radeon-specific fork remains; official main is not a tested drop-in
replacement. [Upgrade mechanisms, sources and evidence](../hardware/CPU-RAM-PROFILES-2026-10-20.md).
Worker-only `MemorySwapMax=0` scopes and RAM/VRAM/spill guards remain mandatory;
the systemd user manager is required. A failure is not permission to weaken guards,
use global swap changes or kill other applications. Source authorities are the
`dsh/*profiles.json`, llama INIs,`llama-runtime.json`,`moe-offload.json` and private
network configuration. Latest development/nightly preference still requires
pinned candidates and local validation; this guide does not schedule upgrades.

## FreeToken removed — October 18

The user requested complete removal because performance was unsatisfactory.
The AMD source/runtime, extracted Desktop frontend, saved app state, menu/PATH
launchers, environment setting and FreeToken-specific caches are removed.
The former single-GPU exception is retired. Shared GGUF weights, production
ROCm and the other inference engines remain. No FreeToken API is served on
port 1919. No model backend was started during removal. Do not reinstall it
without a new request.

[Historical measurements and validation limits](../hardware/FREETOKEN-RETIRED-2026-10-18.md)
remain as reference. MoE API tests passed, but the final MoE GUI chat/Stop test
was cancelled before completion; it must not be reported as passed.

## October 27 forum source clarification — research only

The [supplied-link audit](../hardware/FORUM-LINK-AUDIT-2026-10-27.md) confirms
the linked SGLang gfx1100 revision is already installed. Strata's explicit
two-window pipeline and neutral-penalty requirement are source-confirmed leads,
not selected profile changes; retain the existing memory admission and tuning.
The [corrected H3 review](../graphics/H3-MULTIGPU-RESEARCH-2026-10-27.md) includes
[J I's dual-XTX ComfyUI SP2 report](https://lcz.me/post/28082), an inspectable AMD
SP loader and Bunsei's separate R9700 Radiance TP2 fork. The subsequent
[user-authorized guarded H3 SP2 attempt](../graphics/H3-SP2-2026-10-27.md) found
stock ComfyUI0.42 API incompatibility and reduced-RAM guard stops. No completed
matched generation benchmark or local speedup is available. An isolated
CPU-checked compatibility pilot remains experimental; the active installation,
profiles, workflows and update schedule are unchanged.

## Image/video generation models — October 18

The graphics collection now has **seven weight files / 70.40 GiB** in the
Shared SATA `Graphics-Models` directory: Qwen-Image 2.1 BF16 with BF16 encoder
and FP32 VAE; H3 fl2va pruned INT8 ConvRot with native NVFP4-AWQ encoder,
FP16 video VAE and FP32 audio VAE. Qwen's existing weights were losslessly
repacked; the H3 VAEs were moved intact. The H3 model/encoder replacements
were downloaded at pinned Comfy-Org revision
`e5eb578a89295337b8ff433a035929ce0279e0b6` and SHA-256 verified.

The old Qwen Q4/alternate encoders, H3 Q2/old GGUF encoders, embedding model
and original repacked shard copies were removed from the five Unsloth cache
repositories after verification. Net model-byte reduction: 22.78 GiB.
No model weights or partial downloads are included in Git; no shortcuts were
created. User media, app state, other LLM models and launchers are unchanged.

[Current inventory and limits](../hardware/UNSLOTH-MODEL-INVENTORY-2026-10-18.md),
[collection and Comfy path configuration](../graphics/README.md).
On Windows, use the corresponding `D:/Graphics-Models` path.

**ComfyUI is installed and both families passed generation on October 18.**
Official **Comfy Desktop 1.1.7** / Debian1.1.7-261013p26tnl6re is installed;
October21 normal managed startup, repeated PATH launch, package AppArmor and
filtered child processes passed, with no sandbox-disabling flags or debug port.
The visible native menu app imports the existing Git/ROCm environment; the
Desktop ComfyUI shortcut opens the browser interface.
Models remain on Shared SATA; both saved workflows/user state and outputs are
reused without copies. `comfyui` remains the separate visible-terminal/browser
launcher; quit either interface before switching. Native app startup, both GPU
discovery, workflow/model availability and unchanged inventories passed; no new
generation or speed benchmark was run. [Desktop setup and package hash](../graphics/DESKTOP-2026-10-20.md). Web UI: `http://127.0.0.1:8188` (loopback; use SSH forwarding remotely).
Choose saved workflows **Qwen-Image 2.1 BF16** or **MiniMax H3 INT8**.
The runtime is `runtime/comfyui` in the Linux repository, isolated Python 3.12.14,
ComfyUI 0.42.0 at `8f04fd6ecf4a548937971e840af2a985529fab76`, Torch
`2.15.0.dev20260827+rocm7.2`, Kitchen 0.2.39, aimdo 0.5.6, frontend 1.55.18.

Denoiser runs on GPU 0; encoder/VAEs on GPU 1. Both-card activity was confirmed.
Direct component loaders use core APIs without the duplicate-encoder retarget
copy. This is staged placement, not TP. Historical October18/i5/32GB proof: Qwen passed512x512/40 base steps in
100.9 s total (~13 s denoising); H3 passed 608x352/39 frames/20 base steps in
232.4 s total (~29 s denoising), with coherent motion and finite 32 kHz stereo
audio. H3 used swap during loading on the 32 GB host. Models were unloaded after
that dated test. October21 full normal-RAM controls complete with zero owned swap/spill; current server state is independent of that historical session. The existing LLM kill guard does not
terminate ComfyUI; run large graphics and LLM workloads separately.

[Validation details](../graphics/VALIDATION-2026-10-18.md),
[install/start guide](../graphics/INSTALL.md),
[exact versions](../graphics/runtime-versions.json).
No new weight quant or Turbo adapter was downloaded. Larger sizes, 124+ frame
video, I2V/editing, Turbo and Windows execution remain unvalidated. The earlier
Unsloth Q2 corrupt render is historical and not a controlled comparison with this
native INT8 pipeline. The seven real model files remain on Shared SATA.

## Strata and retired setups

Current managed Strata Q3 `qwen3.8-flash-next-iq3_xxs`: HIP0.1.46.1/source9ae93f7b,
both RX 7900 XTX, native 262,144 total context, INT8 KV with 32K GPU residency/full host
backing, split 26/overlap, MTP3/minimum probability 0.7, prefill 2048,**6 workers /
all CPUs, 13.5 GiB expert budget**,7/8GiB engine reserve targets,5GiB actual startup minimum. Parking/adaptation stay
off; no RoPE extension. Physical-RAM admission now requires 60 GiB for this validated
64 GB setup, plus the streamed-KV/expert/desktop available-RAM budget. Increasing
expert budget to 20 GiB is not selected; the separate candidate remains inactive.

The corrected shared-NVMe pack passed both pool comparisons, tools/results, JSON, SSE,
and **257,984 actual input / 256 output**, then cached full-history
follow-up. All markers found; owned swap/spill were zero. Allocated native 256K and
actual tested input are separate facts. Old SATA-pack results retain their old
asset attribution. [Original pool comparison](../hardware/CPU-RAM-PROFILES-2026-10-20.md) and [current tests/timings](../hardware/STRATA-STARTUP5-2026-10-20.md).

`llm-strata` /Desktop Strata Q3 start the backend in a visible terminal and open
its native Chat/Monitor after readiness. DSH is separate. Router30020 and worker30021 are loopback; the existing authenticated
LAN/Tailscale gateway exports the model. The continuous0.5s watchdog and latched
failure remain: below 3 GiB per card twice or1.5 GiB once unloads only its worker;
RAM, owned swap/spill and missing telemetry are also checked. Explicit reload or
restart is required after failure. It never kills frontends or unrelated apps.

The separate Strata App shares these weights but retains its own legacy inactive
preset; its generation has not been validated here and it does not inherit the
managed profile/watchdog. Do not start competing copies. [Menu/assets](../launchers/STRATA-APP.md).

Q2, HyperQwen, old CUDA setups, GPT-OSS, Qwen27BQ5, Bonsai and old Lightning remain
retired. Historical NVIDIA/Windows configurations are reference snapshots only.

### Workspace archive and completed cleanup — October 18

The retired NVIDIA recovery collection is now in
`/mnt/shared/LLM-ARCHIVE/NVIDIA/2026-10-18/nvidia-recovery.tar.zst` (example mount):
10.16 GiB compressed, with `MANIFEST.json`, `SHA256SUMS` and recovery instructions.
Full tar content/metadata comparison passed. It includes old pre-October-14
rollback environments and the later configuration snapshot; these have different
versions and must not be treated as one tested runtime. See the
[archive boundaries and recovery notes](../hardware/NVIDIA-ARCHIVE-2026-10-18.md).

**All five cleanup groups were explicitly approved and removed.** The
[completed scope and checks](../hardware/CLEANUP-REVIEW-2026-10-18.md) record 73
exact directory roots/installer files and **55.58 GiB observed NVMe recovery**.
Removed: unused NVIDIA rollback originals/Flash-MTP source, old CUDA kernels,
downloaded ROCm installers, unselected test build/cache files and UV package cache.
The archive SHA-256 was rechecked before removal; current model-file metadata
matched before/after and required runtime paths remain. Current AMD compiled
kernel caches and `llm-tools/cuda-build` remain; the latter is still required for
C++ builds/JIT. No runtime configuration or benchmark result changed. Historical
setup records, patches, source pins and benchmarks remain in both Git repositories,
including the public NVIDIA/Windows reference trees. Private binary archives and
cleanup logs are excluded from Git. Future package installations may redownload
packages; repeating removed experiments requires rebuilding their caches.

For future Strata changes, repeat both-GPU, residency, tools, streaming and actual
long-input checks before changing the validated profile. Native 256K is now tested on 64 GB;20 GiB expert backing is not selected. Preserve the Shared Windows-compatible packs. The old single-AMD
candidate and 4070/3060 CUDA layer splits are historical references.

The Windows handoffs were last validated on the **old NVIDIA hardware**. Their
Strata 0.1.44.1/CUDA 13.0, llama.cpp b11630, port 8081, Windows MagicDNS name and
36,919-token retrieval record describe that historical system. They do not prove
native Windows ROCm/HIP support or current dual-AMD readiness. The Windows agent
must inspect its actual hardware/runtime/profile before reuse. Keep Windows
binaries/environments/credentials separate from Linux; share compatible model
assets only. The original recipes, checksums, benchmark caveats and Windows
network administration instructions remain intact in the dated archive.

## Measurements and open work

The [current eleven-profile report](../hardware/CURRENT-AMD-BENCHMARKS.md) and
[dated ledger](../hardware/BENCHMARK-HISTORY.md) preserve engine/native prompt
phase timing separately from external SSE TTFT/decode and input/TTFT proxies.
Nine active profiles use short prompts plus fresh ~8K probes; Super IQ3 uses
fixed ~8K-input workloads. The original thirteen-profile data, retired Muse's
2/3 marker result, retired Super Q4 and SGLang MTP remain historical evidence.
No old speed is promoted into a new context or build.

**All eleven re-measured — October23:** every active profile passed again with its production
launcher and the shared method after the fan-control changes; nine are within ±5.5% of their previous
rates, Strata prose is −10.6% (different generated text) and DeepSeek-XS decode −11% versus its isolated
test harness. GPU hotspots peaked at 84 / 73 °C with GPU fans at 3,600 / 3,100 RPM. See
[report](../hardware/ALL-MODELS-2026-10-23.md) and [numeric record](../hardware/results/all-models-2026-10-23.json).

The [new Qwen context record](../hardware/results/qwen-int4-context-2026-10-20.json)
adds actual 160,861-input SGLang DFlash2 and 160,868-input vLLM BF16 retrieval plus
full-history follow-ups. Both selected contexts are 163,840 total tokens, both
GPUs and zero observed owned swap/spill. The first vLLM 160K attempt was stopped
by another configured Maya launch; the user-authorized identical retry passed.
192K DFlash failed the desktop reserve; 192K INT8 vLLM was stopped after its
speed screen failed. Neither is active. No general full-window quality guarantee
or sustained long-context decode result is inferred from short marker outputs.

Earlier normal API proofs covered authenticated host self-access on
loopback/LAN/Tailscale, not a remote peer. The current catalog has twelve IDs; the
retired IDs must be removed from client selectors. The October27 VRAM defaults add near258K Empero,62K Sage and30K Flint
marker/history evidence; these functional checks are not general quality claims.
[Activation evidence](../hardware/VRAM-DEFAULTS-2026-10-27.md).
Maya's [initial numeric record](../hardware/results/maya-dual-amd-2026-10-20.json)
preserves original17 controls; [current19/SDK tests](../hardware/results/maya-rocm10-2026-10-20.json) retain new trials, thermals and failed10 arms. The purchased
PCIe switch is still pending installation and P2P/RCCL validation.


## Troubleshooting and maintenance

**Thermal logging.** Future normal backend launches automatically log GPU/CPU
temperatures, power, clocks, fan speeds/utilization and available raw SMU flags
under ignored `dsh/logs/thermals/`. Maintained benchmark stream trials and native
candidate helpers attach sampled summaries. The existing in-flight DeepSeek
comparison has a read-only partial observer from15:15 October20 Toronto time;
older trials cannot be reconstructed. One-second samples can miss transients;
missing sensors/unknown masks stay unavailable. Flags do not prove a measured
thermal slowdown. No fan, clock, model, reserve, worker guard or runtime setting
changed. [Coverage, limits and observer commands](../hardware/THERMAL-LOGGING.md).

**Staging upgrades.** Candidate engines and profiles are tested through the normal
guarded launchers with opt-in switches: `LLAMA_SRC`, `LLAMA_CPP_DIR`, `VLLM_ENV_PATH`
and `STRATA_PROFILE_CONFIG`. Unset or empty means production. Compare candidates
against a same-hardware baseline with `hardware/compare-runtime-candidate.py --baseline`.
[Staging guide](../hardware/CANDIDATE-STAGING.md).

Earlier October 19 public documentation cleanup (before the fresh benchmark batch): the
[public README](https://github.com/Biegle-W/linux-llm-amd-public#amd-latest-setup-and-results)
now presents two hardware result sets: latest dual-AMD setup and archived dual-NVIDIA.
Each model/backend has context, prefill, TTFT and decode fields, with measured
build/date, missing metrics and older-build timings labeled. Short and long-input
workloads are separate. The old public README is preserved in
`linux/hardware/README-ARCHIVE-2026-10-19.md` in the public repository; the dated
benchmark ledger retains all intermediate experiments. No benchmark, runtime,
profile, launcher or client endpoint changed during this documentation task.

| Symptom | Action |
|---|---|
| Terminal closes immediately | vLLM now preserves startup errors; inspect its launcher log. Check per-GPU free VRAM and runtime probe. |
| HTTP 401 | Configure the actual private Linux API key, not `local-strata`. |
| HTTP 404 / unknown model | Copy an exact enabled ID from `/v1/models`; do not use Q2, HyperQwen or retired IDs. |
| HTTP 503 | Start the required backend and inspect its terminal; gateway availability is separate from worker readiness. |
| Refused / timed out | Check Linux session, address, service, client LAN/Tailscale path and TCP 10000 access. |
| Models fail after reboot / "Cannot mount" | Check `findmnt`, retained-drive UUIDs and `/etc/fstab` boot mounts first. The user mount service is a fallback (`systemctl --user status local-llm-mounts.service`); session-based udisks recovery may require desktop login. SATA2 is no longer a configured model volume. Do not redownload. |
| Context error | Input, history, tools and output together must fit the selected context. |
| Very slow first request | Inspect loading/JIT/host RAM/swap; prefix caching helps repeated prefixes, not every new prompt. |

Read-only host service check:

```bash
systemctl --user status local-llm-api.service
```

For an intentionally changed Linux network address, update private configuration
and this guide, then restart the gateway; preserve the key:

```bash
cd /opt/local-llm
python3 network/configure.py
systemctl --user restart local-llm-api.service
```

These are maintenance instructions for a future authorized change; they were not
run during consolidation. `python3 -B network/check.py` derives the expected catalog and contexts from enabled
local profiles and checks authentication, health and retired-Q2 rejection without
loading models. It writes nothing unless `--output` is supplied. `--generate`
remains an explicit optional generation test; it was not used during maintenance.

The latest October 18 authenticated API/generation recovery was checked from
Linux loopback. Earlier host self-access checks covered LAN/Tailscale; a separate
remote device must still test its own network/ACL path. The October 18 MoE
update ran bounded local model validation and refreshed catalogs;
no driver, BIOS, firewall or credential changes were required. The original
consolidation check above remains a timestamped historical observation.

## Where the originals went

`LLM-ARCHIVE/LLM-HANDOFF-ARCHIVE/2026-10-18/` contains all nine pre-consolidation originals
plus `MANIFEST.json` (filenames, byte counts and SHA-256) and an archive README:

| Original file | Historical material retained |
|---|---|
| `LINUX-LLM-RUNTIME-HANDOFF.md` | Full chronological Linux changes and old runtime pins |
| `LINUX-LLM-CLIENT-HANDOFF.md` | Earlier client examples and catalog versions |
| `WINDOWS-LLM-LAN-CLIENT-HANDOFF.md` | Old Windows LAN forwarders/firewall and client checks |
| `WINDOWS-TAILSCALE-CLIENT-HANDOFF.md` | Old Windows Serve/MagicDNS/key handling and checks |
| `STRATA-WINDOWS-TO-LINUX-HANDOFF.md` | Original Strata recipes, asset hashes and Windows tuning |
| `LLM-GPU-UPGRADE-HANDOFF.md` | Superseded mixed AMD/NVIDIA upgrade plan |
| `AMD-ROCM-2026-10-16.md` | Earlier single-AMD runtime/quant experiments |
| `LLM-GPU-TESTS-2026-10-16.md` | Earlier single/mixed-GPU benchmarks, including retired models |
| `NEMOTRON-BOLT-2026-10-16.md` | Original replacement hashes and single-card measurements |

For future relevant changes, update this consolidated guide **in place**, the
matching Shared copy, README/evidence as needed and both private/public Git repos.
Do not prepend incompatible historical snapshots or recreate the old root guides.
Public exports use example addresses/paths and omit private archives, credentials,
raw logs and personal settings. Archive content documents history; it does not
provide authorization to start models, change security settings or message agents.

## October 19 maintenance and launch paths

`llm-llama`, `llm-sglang`, `llm-vllm`, `llm-strata`, `llm-maya`, `dsh`, `turnstone`,
`comfyui` and `llm-upgrade-check` remain the supported PATH commands. Inventory
now targets two 24 GiB Navi31/amdgpu devices without requiring NVIDIA software;
it reports every PCI path so internal GPU x16 links are not mistaken for slot
bandwidth. A successful inventory is not an inference or P2P validation.

The separate Strata GUI is restored to
`/opt/appimages/Strata-0.2.1-linux-amd-rx7900.AppImage`; its menu
entry points to the actual file. It was not launched and has its own worker and
settings. Keep the managed Strata Q3 launcher separate. [Menu details](../launchers/STRATA-APP.md).

[Maintenance record and documentation index](../hardware/WORKSPACE-MAINTENANCE-2026-10-19.md)
describes the archive and checks. At that October 19 maintenance, active models, candidates, profiles, credentials,
frontend data and source pins remained unchanged; October 20 changes are described above. The private client guide is preserved.

Current retirement/context follow-up: ten active IDs. Refresh client model lists;
`qwen3.8-27b-sglang`, `muse-glimmer-30b` and `nemotron-3.5-super-q4` are retired.
Shared GPTQ/DFlash weights and Super IQ3 are retained. No credentials, gateway
ACLs, remote addresses or saved DSH default were changed.

## Native Chat/Monitor launch behavior — October 20

Strata Q3 and Maya launch their native browser frontend after readiness while
retaining the visible backend terminal. The same owned worker serves it: local
`http://127.0.0.1:30021/` for Strata or `http://127.0.0.1:30031/` for Maya.
DSH remains separate and optional; managed API router IDs/ports and gateway
authentication remain unchanged. Use `--no-browser` to suppress automatic opening;
headless SSH prints the URL. Native chat/monitor/sampling remain; runtime/context
changes and self-updates stay in the validated managed-profile workflow. Browser
chat/settings are private and excluded from Git. The separate standalone Strata
AppImage is preserved and is not started by this managed launcher.
[Frontend setup and validation limits](../hardware/NATIVE-FRONTENDS-2026-10-20.md).

[Normal launcher/frontend proofs](../hardware/results/launcher-validation-2026-10-20.json)
cover the selected SGLang/vLLM160K profiles, Strata Q3 and both Maya models.
JSON/tools/SSE, both GPUs, zero owned swap/spill, original UI assets and blocked
runtime writes passed. Browser-open dispatch is logged; desktop browser rendering
was not automated. Network checks are host self-access, not a remote client.

Maya quant research: [candidate assessment](../hardware/MAYA-QUANT-OPTIONS-2026-10-20.md).
The later [S/S24 A/B](../hardware/MAYA-S-VS-S24-2026-10-20.md) selected Maya-S. DeepSeek-S32K is unchanged; preserve source/format/memory guards.
