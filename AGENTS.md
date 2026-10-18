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
See `linux/hardware/Z690-2026-10-17.md`. Keep GPU-resident weights until then.

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
