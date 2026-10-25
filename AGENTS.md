# Public repository maintenance

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
The private Linux repository's AGENTS.md identifies its workspace and exact handoff
locations; Windows instructions are in its README. Keep the Linux repository handoff and its Shared-drive copy identical.
Report any blocked commit, push or handoff synchronization explicitly.

## Hardware-specific repositories — October 24

This is `Biegle-W/ubuntu-llm-amd-public`. Maintain Linux AMD and the historical
`archives/ubuntu-nvidia/` tree here. Windows setup, reports and retired configurations now
live at the root of `Biegle-W/windows-llm-nvidia-public`; publish Windows changes there.
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

## Current CPU/RAM and profiles — October 20

Intel i9-13900KS and 64 GB RAM (61.51 GiB OS-visible) are installed. Both RX 7900 XTX cards
remain on CPU PCIe 4.0 x8/x8; the purchased switch is not installed/validated.
Thirteen profiles are active: four llama.cpp (Empero, Super IQ3, Sage-A1.5 and Ornith-1.5-122B), one SGLang, two vLLM, three Strata and three Maya. Qwen3.6-35B-A3B was retired October 23. User instruction (October 21): Bolt runs on vLLM (`nemotron-3.5-bolt-vllm`, AutoRound W4A16) and the slower llama.cpp `nemotron-3.5-bolt` and `qwen3.8-27b-q4` profiles are retired; Qwen3.8-27B uses SGLang/vLLM. llama.cpp defaults to HIP with no Vulkan profile. Their GGUF files were deleted at the user's request (October 22).
Super IQ3 remains selectable at 32K and loads from its verified shared-NVMe copy; keep the SATA original as a backup. mmap SSD streaming was rejected (`linux/hardware/SUPER-NVME-LOAD-2026-10-20.md`). Muse Q4 and Super Q4_K_XL are retired at the user's request, with active setup and four weights removed; keep their dated results and non-installable regression fixture. SGLang retains only TP2 DFlash2. The user's saved
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

## Project Maya — October 20

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

## Forum research and source citations

Standing user instruction: consult both [lcz.me](https://lcz.me/) and
[Level1Techs Forums](https://forum.level1techs.com/) when researching local
inference optimizations, including HIP kernels, ROCm and C++ runtimes. In BOTH
GitHub repositories, cite direct topic/post URLs beside forum-derived claims,
recommendations and changes. Record author/date when available, relevant hardware,
model, quantization, context and workload. Link the primary upstream GitHub
commit/PR or official documentation supporting implementation details; pin
reviewed source revisions when practical. Mark forum reports, proposed candidates
and locally validated results separately. Never present another system's speed
as a local measurement or assume newer posts apply to gfx1100. Maintain the
source trail in hardware/FORUM-OPTIMIZATION-SOURCES.md (under linux/ in the public
repository) and link it from applicable reports/handoffs. This is a research and
citation rule, not authorization to deploy unvalidated changes or schedule checks.

## Consolidated Shared handoff

Keep `linux/network/LINUX-LLM-RUNTIME-HANDOFF.md` as the single current Shared
handoff. Update its current sections in place after relevant changes rather
than prepending incompatible chronological snapshots. It covers client access
and Windows differences as well as runtime state. Preserve the nine original
Shared files in `LLM-ARCHIVE/LLM-HANDOFF-ARCHIVE/2026-10-18/`; do not recreate the superseded
root client/upgrade/Windows handoffs. The private maintained source and Shared
copy must match exactly. Public exports use example addresses/paths and exclude
private archives and staging files. Preserve historical NVIDIA/Windows source
snapshots; historical evidence is not a current validated profile.

## MoE expert offload and caching — October 18

The user requests CPU expert offload plus GPU hot-expert caching for all MoE
models, with both RX 7900 XTX cards active. Size profiles for the actual64 GB using
bounded RAM/VRAM, swap and residency checks. Preserve dense Qwen27B GPU
placement. Identify MoEs by expert metadata; KV/prompt caching and static CPU
placement are not hot-expert caching. Validate each backend's implementation and
MTP behavior before activation. Preserve the validated13.5 GiB Strata expert cap,
streamed host KV admission, desktop headroom and continuous latched watchdog.
More installed RAM does not automatically select20 GiB or extend native context.

## FreeToken retired — October 18

The user explicitly requested complete FreeToken removal due to poor performance.
Its software, isolated environments, Desktop app state, launchers and caches are
removed. Shared model weights remain for other engines. The former single-GPU
exception is obsolete. Keep all active engines on both GPUs, and do not reinstall
FreeToken unless requested. Historical results remain in the hardware reports.

## Public documentation scope

The public repository demonstrates hardware configurations, inference-engine
setup, reproducible tuning and measured performance. Keep personal workstation
fault investigations, repair narratives and warranty disputes in private records.
Publish the measured RAM capacity needed to interpret results, without exporting
personal hardware-failure reports or troubleshooting histories. Apply this scope
when synchronizing future documentation; private and public content need not be
identical.

## Benchmark/context update ledger

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

## Current benchmark publication

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

## Qwen INT4 context follow-up — October 20

SGLang retains only TP2 DFlash2 at **163,840 tokens**, BF16 KV. vLLM
retains compiled MTP3 at **163,840 tokens**, `bfloat16` KV.
The separate SGLang MTP profile is retired. Both new profiles passed fresh
near-window markers and full-history follow-ups, with zero owned swap/spill.
[Context selection, actual counts and limits](linux/hardware/QWEN-INT4-CONTEXT-2026-10-20.md).
Keep the existing RDNA verification repair, both GPUs and startup admission.
No HiCache/FP8/CPU dense-weight offload is enabled. Current measurements live in
`hardware/results/qwen-int4-context-2026-10-20.json`; earlier contexts/rates remain historical.

## Native frontends — October 20

The user's newer request makes managed Strata Q3 and Maya open their original
local Chat/Monitor frontend after readiness, alongside the same worker and visible
terminal. Do not start a second AppImage/engine or duplicate weights. Keep DSH
separate; other backend launchers remain backend-only. Headless SSH and
`--no-browser` suppress automatic browser opening. The local HTTP adapter keeps
context/config/runtime self-updates out of the native UI; retain existing admission,
source pins, dual-GPU placement and latched watchdogs. Frontend sampling state
is private (`*.shared-settings.json` ignored). See
`hardware/NATIVE-FRONTENDS-2026-10-20.md`.


## GLM quant selection — October 20

The user requested a matched Maya-S/S24 trial and a strict less-than10% speed-loss gate for EACH code/prose decode and native-prefill six-trial median. Current selection is Maya-S,32K, same both-GPU/RAM40/MTP/reserves. Preserve DeepSeek quant/context/guards; the later source/stream policy below applies. See `linux/hardware/MAYA-S-VS-S24-2026-10-20.md` and its numeric record; initial Maya three-trial speeds remain historical.

## Strata Linux app / Intel desktop follow-up — October 20

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

## Temperature logging — October20

Standing user instruction: log temperatures from now on. Normal Linux launchers
and maintained benchmark/candidate helpers record one-second GPU/CPU thermal,
power/clock/fan and available raw SMU telemetry. Use `linux/dsh/gpu_telemetry.py`
or `linux/hardware/log-gpu-temps.py` for other tests. Future reports must retain
actual coverage, sampled peaks, unavailable sensors and flag limitations. Never
backfill missing history or treat a partial observation as a full-run maximum.
Keep raw logs and local paths private; inference settings and guards stay intact.
See `linux/hardware/THERMAL-LOGGING.md`.

## Model drive label — October 21

At the user's request the shared SATA model drive is labelled `sharedSATA1` (exFAT limit
11 characters). Mount it by UUID through `dsh/shared_storage.py`; never create model
folders on an unmounted path. Public examples keep `/mnt/shared`.
The empty spare SATA drive is labelled `sharedSATA2` and holds no models.

## Engine preference — standing user instruction (October 22)

Before adding or keeping a model on llama.cpp GGUF, always look for a faster vLLM or SGLang build
that fits 2×24 GiB and runs on gfx1100. Test it in isolation and switch over when faster, as was
done for Bolt. Use llama.cpp only when no such build fits or works (e.g. Ornith-1.5-122B, Nemotron Super).

## Ornith-1.5-122B — active October 22

`ornith-1.5-122b` is an active llama.cpp HIP profile (Q4_K_M + projector, 32K, MTP off, 30 CPU
expert layers, 4 GiB GPU cache). No vLLM/SGLang build fits. See
`linux/hardware/ORNITH-122B-TEST-2026-10-21.md`.

## Model hub — October 22

`local-llm-hub.service` (`dsh/model_hub.py`, 127.0.0.1:30100) lists every enabled model and
starts or switches backends on demand through `dsh/start-backend-terminal`. The gateway forwards
to it, and DSH provider baseURLs point to it. Agents must hold `hardware/generated/GPU-LOCK` for
GPU tests; the hub refuses to start or switch while it exists. See
`linux/hardware/MODEL-HUB-2026-10-22.md`.

## ROCm version — October 22

Retain ROCm 7.2.3 for every engine. The 7.2.4 runtime and a 7.14.1 llama.cpp rebuild gave no
gain on vLLM Qwen, llama Qwen3.6/Sage or Ornith; 10.1 was rejected on October 21. See
`linux/hardware/ROCM-724-7141-2026-10-22.md`. `LOCAL_ROCM_RUNTIME_OVERLAY` in `hardware/rocm-env.sh`
is for isolated tests only.

## DSH default model — October 21

Standing user instruction: the DSH default for new agents is **Strata Q3**
(`strata-local` / `qwen3.8-flash-next-iq3_xxs`). It had drifted to Maya GLM through
a saved UI selection. Set it with `configure_local.configure('strata-local')`. Other
`configure()` refreshes, called without a provider argument, preserve it. Do not change it unless asked.

## Application launcher placement — October 21

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

## Maya source/SDK validation — October 20

The October20 3384b5e9366e696e5f23f51772fb94a8a7948e41/v1.1.19 promotion is historical (superseded October23) with exact tested SDK7 binaries. ROCm10 failed both performance gates; DeepSeek10nostream stalled with no completed timed sample. Keep ROCm7.2.3/rocWMMA2.2.0. Selected DeepSeek requires `DS4_IQ_Q8K=0` (prior rounding; default1 reversedIQ3_S/IQ2_S parity fails) and `DS4_STREAM=0` (optional PCIe lane only; CPU experts/GPU hotcache retained). GLM-S40GiB/MTP and DeepSeek-S24threads/noDSpark remain32K/bothGPUs/native8GiB/actual6GiB startup/52G no-swap. Near31.5K/history and actualDesktop/Ptyxis/nativeUI/authenticated gateway/switchback pass; host-self routes are not a remote-peer test. GLM source19 six-sample rates18.44/16.10/518.0PP,12.363s freshTTFT; DeepSeek selectedthree6.89/7.08/188.6,33.418s. No universal source speedup; failed SDK10/old17 evidence retained. Other production engines remain unchanged; isolated comparisons are complete in linux/hardware/ROCM10-OTHER-ENGINES-2026-10-20.md. Fresh exact-production SDK7 controls update the benchmark overview; candidate SDK10 is not activated. See linux/hardware/MAYA-ROCM10-2026-10-20.md and numeric record. Never enable approximate prompt skipping or failed/untested formats.

## Maya web switching and DSH reuse — October 21

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

## ROCm10.1 selection — October21

All production runtimes are retained; no ROCm10.1 candidate passed every promotion gate. Empero’s matched seeds 42/43/44 improved aggregate speed by only 0.30%, below the >3% gate; keep HIP 7.2.3. The candidate's near-256K functional tests passed.
Keep all model IDs/contexts/guards/offload/cache/dual-GPU settings and existing PATH/frontend policy.
No system driver/global SDK replacement occurred. Framework/AOT compatibility tests
are not an all-extension rebuild. Preserve raw/failed/untuned/diverse-seed evidence
privately; publish only curated numeric records. [Exact outcomes and limits](linux/hardware/ROCM101-2026-10-21.md).

## Sage-A1.5 test model — October 21

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

## Maya1.1.24 — October23 (source-promotion history)

25deec505b525212e05faa58697d9d2b7d17fdb3/VERSION1.1.24 and exact tested HIP7.2.3 binaries are promoted for both retained Maya-S32K profiles after native and normal integration gates. GLM MUST retain MAYA_GLM_PREFILL_FUSED=0 (newgfx1100 fused IQ2_S down parity fails on bothcards); use MMQ, do not relax tolerances. DeepSeek retains DS4_IQ_Q8K=0/DS4_STREAM=0/24threads/noDSpark; bothGPUs/layer groups, no trueTP2 for2304/256expert blocks. Original8GiB/actual6GiB reserves/52Gno-swap/latching remain. Source-promotion historical3trial GLM19.72/15.69/535.6PP/11.928sTTFT; DS6.42/6.78/299.0/21.062s. Bothnear31.5K/history/JSON/tools/SSE, actualDesktop/Ptyxis/originalbrowserselector/authAPI/switchback pass. Preserve source19 rollback and known mixed-format exclusions; new source is not a universal speedup claim. See linux/hardware/MAYA-UPDATE-2026-10-23.md and numeric record. Otherengines/weights/default unchanged.

## Maya-XS test — October23

User-requested Maya1.1.24+IQ1_S XS+matching IQ2_XXS dspark-xs2 tested on BOTHgfx1100 cards at32K/SDK7.2.3; at that test time production remained Maya-S/noDSpark. The later explicit user-authorized production promotion below supersedes that test-only status. Keep new XS/drafter assets on sharedNVMe; reused S Engram tensor payloads are fully SHA-verified via published XS headers, not whole-file identical GGUFs. Existing S/GLM/guards/default and ten-profile catalog unchanged. See linux/hardware/MAYA-XS-DSPARK-2026-10-23.md and numeric record; retain all partial/failed preparation evidence privately.

## Maya-XS production — October23 (retained XS selection)

User explicitly authorized production XS+matchingDSpark. DeepSeek keeps sameAPIid deepseek-v4.1-flash-1017-maya,32K/24threads/bothAMD/SDK7.2.3/source25deec5/exacttestedbinary, DS4_IQ_Q8K0/STREAM0 andallguards. XS IQ1_S admission is restricted to matchingdrafter on/32K/24threads with existing source/binary/config/pack fingerprints. GLM-Sv2/MTP/fused0 and otherengines/defaultStrata unchanged. NormalDesktop/Ptyxis/nativeUI/authAPI/GLM-XS-GLM-XS passed; finalXS worker intentionally ready. Earlier31.28/15.36/445.5/14.156 and1024HTML12.54 rates remain savedexperiment, no production speed rerun. Keep S rollback weights/manifest; S Engram5/6 remain ACTIVE XS dependencies and must not be removed. maya/install.sh deepseek only verifies sealed XS metadata/dependencies to avoid duplicate161GBstock download. Publicconfigs require localvalidation. See linux/hardware/MAYA-XS-PRODUCTION-2026-10-23.md and numeric proof.

## Maya dual DeepSeek selection — October23 (current profiles)

User requested BOTH DeepSeek quants selectable. XS ID deepseek-v4.1-flash-1017-maya remains unchanged; S is active as deepseek-v4.1-flash-1017-maya-s,32K/24threads/noDSpark, exact retained source25deec5/SDK7.2.3 binary/pack/guards/bothAMD. Three Maya profiles, eleven total; one worker at a time. GLM and Strata DSH default unchanged. Separate S expert routing seed copied from preserved S rollback; full six-file published SHA verified anew. NormalDesktop/Ptyxis/nativeUI S-XS-S-XS and authenticated host-self API/tools/JSON/SSE pass; no throughput/full-window rerun. Existing S/XS dated speeds retain their original methods/quality distinction. Both quants use shared S Engram5/6; never delete those. S is active, not merely rollback; old manifest remains historical. Installer deepseek-s verifies sealed existing S without stock reconfiguration/download. Public reference configs require localvalidation. See linux/hardware/MAYA-DUAL-DEEPSEEK-2026-10-23.md and numeric proof.

## Maya-S DSpark1.1.24 retest — October23 (current)

User requested fresh S drafter test on installedsource25deec5/1.1.24 exactSDK7.2.3 binary. MatchedA1none-Bon-A2none,32K/24threads/bothAMD/identicalinitialSseed/allguards,three256-output code/prose and fresh~6.3Kactual DeepSeek probes; controls7K/candidate31.5K retrieval/history, JSON/tools/SSE/greedysmoke and thermals retained. Fixed>=5%geomean/nometric>5%worse plusallgates. S DSpark NOT selected; keep S --dspark none. No general AMD incompatibility is inferred. XS+xs2/GLM/otherengines/default/guards/catalog11 unchanged. Old1.1.17 rejection remains historical with128-outputmethod; no isolated cross-version speedclaim. Final normalXSworker ready. See linux/hardware/MAYA-S-DSPARK-2026-10-23.md and numeric proof.

## Strata Qwen matching table — October24

User-authorized current8183c6b6/HIP7.2.3 retest selected the existing gfx1100/hipBLASLt100202 table explicitly via STRATA_HIPBLASLT_TUNING. Keep prefill2048/split26/overlap/13.5GiB/native256K/INT8KV32K/all existing guards.4096 failed actual5GiB/card startup (4.655/5.510GiB),8192 unattempted; do not relax reserves to select them. Independent repeat and normal near258K/history/JSON/tools/SSE/originalUI/authenticatedhostself API pass, zero owned swap/spill. Older9ae table/prose regression remains historical. Table changes rounding; public profiles need exact SDK/local validation. DeepSeek/Maya/defaults unchanged. See linux/hardware/STRATA-TUNING-2026-10-24.md and numeric record.


## Organization and archives — October 24

Repositories are `ubuntu-llm-amd` / `ubuntu-llm-amd-public` and
`windows-llm-nvidia` / `windows-llm-nvidia-public`. Preserve private/public
boundaries. Active Ubuntu source paths stay fixed for installed launchers and the
daily publisher. Archive retired setup source under `archives/`; never move live
runtime environments, weights, dependencies or private state as a documentation
cleanup. Keep exact dated measurements and hardware attribution. Review archive
links after moving source. No retired setup becomes active through reorganization.
