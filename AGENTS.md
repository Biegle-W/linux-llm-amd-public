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
passed and is enabled again; another 32 GB RAM is pending (32 GB installed).
See `linux/hardware/Z690-2026-10-17.md`. Dense-model weights remain GPU-resident; follow the newer MoE policy below.

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

The user explicitly requests CPU expert offload plus GPU hot-expert caching for
all MoE models, and plans another 32 GB RAM. This supersedes the earlier
GPU-resident-only MoE policy. Keep both RX 7900 XTX cards active. Size current
profiles for the actual 32 GB installation with bounded RAM/VRAM, swap and
residency checks; prepare separately gated 64 GB candidates. Preserve dense
Qwen 27B and Muse GPU placement. Use actual expert-count metadata to identify
MoE models. Expert caching is distinct from KV/prompt caching; do not label
`cache-ram` or static CPU placement as a hot-expert cache. Validate the installed
backend's real cache implementation and MTP behavior before activation. Use the validated bounded 32 GB Strata profile on both AMD
GPUs. Keep its
separate 64 GB candidate inactive until physical-memory and live
long-context checks pass; more installed RAM does not activate it automatically.
Do not silently re-enable full-GPU-only MoE defaults during later updates.

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

Strata desktop protection (October19): preserve at least a 6 GiB per-card startup
reserve, continuous whole-card VRAM/owned-memory watchdog and latched guard
failure. Unload only its owned worker; never reclaim space by killing unrelated
GPU apps. The current measured profile and rollback limits are maintained in
`linux/hardware/STRATA-CONTEXT-2026-10-19.md`; overlap is layer splitting, not TP.

Native 256K Strata is now validated on 32 GB RAM with INT8 KV / 32K GPU residency
and full host backing. Preserve the streamed-KV admission budget beside expert
RAM and desktop headroom. The 64 GB candidate retains native 256K and remains
inactive; do not regenerate the obsolete 32K/128K context presets. Beyond 256K
requires experimental RoPE/quality validation, not just successful allocation.

## Current benchmark publication

Use `linux/hardware/results/README.md` as the current-results entry point and
`linux/hardware/results/current-amd-2026-10-19.json` for the fresh nine-profile
AMD measurements; `hardware/results/nemotron-super-2026-10-19.json`
(under `linux/` publicly) adds the tenth active profile with a different timing workload.
Keep dated historical records; do not promote an older build's
speed into a current table. Update current README tables, dated benchmark ledger
and canonical handoff together. Distinguish native prompt timing, engine prefill
phase timing, external SSE TTFT/decode and input/TTFT proxies. New ~8K probes are
not full-window context validation. The historical NVIDIA setup remains separate.
