# Public repository maintenance

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
NVIDIA and Windows snapshots unless their setups change or the user requests it.
The private repository's AGENTS.md identifies its workspace and exact handoff
locations. Keep the repository handoff and its Shared-drive copy identical.
Report any blocked commit, push or handoff synchronization explicitly.

Current hardware policy: use BOTH RX 7900 XTX cards for every active model.
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
Ten profiles are active: five llama.cpp, one SGLang, one vLLM, one Strata, two Maya.
Super IQ3 remains selectable at 32K. Muse Q4 and Super Q4_K_XL are retired at the user's request, with active setup and four weights removed; keep their dated results and non-installable regression fixture. SGLang retains only TP2 DFlash2. The user's saved
DSH default remains unchanged. Strata keeps IQ3_XXS, 13.5 GiB expert budget,
native 256K with INT8 KV /32K GPU residency, both GPUs and latched guards.
The 20 GiB candidate is not selected and remains inactive. Do not regenerate the
obsolete 32K/128K Strata presets or remove IQ3 on the basis of superseded plans.

llama.cpp 4c3c5810 and vLLM 0.32.1rc1.dev36+ge68efc685.rocm72 are promoted after
validation. SGLang f84475cc and Strata 477ac13c are retained. Current results preserve
candidate-source timings versus production rebuild functional proofs; no speedup
is claimed for these performance-neutral updates. See
`linux/hardware/CPU-RAM-PROFILES-2026-10-20.md`. Earlier i5/32 GB and NVIDIA results
must retain their original hardware/build/workload. Strata's corrected expert pack
and shared-NVMe pool measurements are distinct from old SATA-pack results.
Strata and standalone App share one new shared-NVMe asset set; engine settings
and watchdogs are independent. Maya selected profiles are validated there, with their guards described below. Keep engines/environments Linux ext4 and all model weights
excluded from Git.

## Project Maya — October 20

Maya v1.1.17 / 8d9a9b5d is active for GLM-5.3-Flash Maya-S v2 and
DeepSeek-V4.1-Flash-1017 Maya-S, each 32K, both 7900XTX cards through layer groups.
GLM retains 40 GiB bounded pinned RAM/MTP; DeepSeek 24 CPU threads/mapped experts,
GPU hot caching and no DSpark. Shared NVMe holds all weights/generated packs.
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

The user requested a matched Maya-S/S24 trial and a strict less-than10% speed-loss gate for EACH code/prose decode and native-prefill six-trial median. Current selection is Maya-S,32K, same both-GPU/RAM40/MTP/reserves. Preserve DeepSeek unchanged. See `linux/hardware/MAYA-S-VS-S24-2026-10-20.md` and its numeric record; initial Maya three-trial speeds remain historical.

## Strata Linux app / Intel desktop follow-up — October 20

App0.2.1 and packaged HIP0.1.46 are installed and pass12 packaged checks.
IntelUHD770/i915 is verified as GNOME primary after the user's logout/login.
Managed candidate9ae93f7b/0.1.46.1 reached loaded health but failed the former
actual6GiB/card startup rule twice (exact5.388/6.269GiB free). Production remains
477ac13c/0.1.45 until candidate functional/performance/context and normal proof pass.

The user's newer explicit instruction **reduces actual loaded startup admission
to5GiB/card for Strata**, superseding the old6GiB startup threshold. The engine's
7/8GiB reserve targets, continuous3GiB floor/hard1.5GiB emergency stop,52Gworker,
noswap/telemetry protections,dualGPU,Q3/13.5GiB/256K profile remain. Maya's6GiB
actual startup requirement is unchanged. Both candidate and production must use
the common Strata startup check; a lower threshold alone is not validation.
Do not change global compute-device variables or restart the session without an
explicit user request. See `linux/hardware/STRATA-STARTUP5-2026-10-20.md` and
`linux/hardware/STRATA-LINUX-UPDATE-2026-10-20.md`.
