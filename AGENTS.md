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
