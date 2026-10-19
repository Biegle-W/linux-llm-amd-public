# Workspace maintenance — October 19, 2026

This maintenance reconciles saved records and removes approved unused files.
It does not upgrade engines, rerun benchmarks, load a model or change production
inference settings. [Documentation index](DOCUMENTATION.md).

## Current records

The README, [AMD report](CURRENT-AMD-BENCHMARKS.md), [results index](results/README.md)
and [canonical handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md) now cover all
**10 enabled profiles**. The nine-profile batch and Nemotron Super IQ3's ~8K-input
decode/TTFT trials remain separate; their numeric JSON files are unchanged.
Every measurement retains its build, context, input length and timing method.
Earlier NVIDIA/Windows snapshots remain historical and unchanged.
Legacy DSH/HyperQwen recipes now link to the current documentation index.

The PEX88096 four-slot kit (listing title “plx8096”) is purchased, **pending
installation and local validation**. The current measurements use motherboard
PCIe4 x8/x8 and host transport. [Forum and primary sources](FORUM-OPTIMIZATION-SOURCES.md#pcie-switch-purchase-october-19).

## Verified archive and cleanup

Private recovery archive on Shared:
`LLM-ARCHIVE/MAINTENANCE/2026-10-19/obsolete-working-files.tar.zst`
(**3,175,306,186 bytes**).

SHA-256: `1079044ec983ba5bb62a5655c259dfab7e7fb8acd7accaa02911ba157bc8fe88`.

The exact [cleanup manifest](CLEANUP-2026-10-19.json) lists all **34 roots** and
sizes: unused October 18 rollback environments/builds, the unused SGLang-main
checkout, closed historical DSH test logs and seven legacy engine logs.
The full private per-file manifest is `MANIFEST.private.json` beside the archive.
All **177,653 entries** were checked, including regular-file SHA-256,
link targets and the complete entry set, before removing originals. Source
metadata and dependencies were checked again immediately before deletion.
Restore original relative paths into the private repository before following
older rollback instructions; the archive is private, not a GitHub artifact.

Candidate regular-file allocated-byte totals were **11.81 GiB**; these include
shared/hardlinked runtime files and are not a prediction of freed space.
Observed NVMe free-space increase during deletion: **1.51 GiB**
(1,622,269,952 bytes). Concurrent filesystem activity can affect this delta.
Eight top-level Python bytecode caches were removed (1,011,712 allocated bytes).
No tracked files or detected active-process/environment dependency referred to
removed roots. Some other-user process trees were unreadable; the audit records
that limit and does not claim visibility into every system process.

Model path/size/mtime inventories were identical before and after deletion.
Active runtimes, source/build dependencies, the AMD-used `llm-tools/cuda-build`,
selected ROCm kernel caches, current evidence, sessions and settings were retained.
The untracked private client guide was preserved and excluded from publication.

## Launchers and read-only checks

The separate Strata App was restored from Trash to the actual executable
`~/Applications/Strata-0.2.0-beta-linux-amd-rx7900.AppImage`, with matching
SHA-256 `134758d4f430925750232e4d0e2d49e1e34764cbc9c9cac8ad98d1f45f375d73`.
Downloads is no longer needed. Menu Exec/TryExec targets and the official icon
were validated without launching it. Managed Strata Q3 remains separate.

`llm-upgrade-check` now detects both 24 GiB Navi31/amdgpu cards, requires no
NVIDIA software and reports parent PCI links. `network/check.py` derives the
expected catalog from enabled local profiles; no stale fixed profile count is
used. Its normal invocation writes nothing and never generates text.

Authenticated gateway health, all ten IDs/contexts and rejection of absent/wrong
keys and retired Q2 passed on loopback, LAN and Tailscale host self-access.
No managed backend was available/loaded during this check. These checks do not
prove connectivity from a separate client or generation readiness.

Final syntax, link, wrapper/PATH and publication checks are recorded in the
validation section below. The repository and Shared copies of the private
handoff are synchronized after documentation is complete.

## Validation results

- Private and public hardware suites: **60 tests each passed**, including GPU
  identity/capacity and parent-link inventory regression checks; workers are mocked.
- Python AST, JSON, Bash syntax, desktop-entry syntax and changed Markdown file
  targets passed in both repositories. No Windows runtime execution was attempted.
- All eight supported PATH commands resolved in login and noninteractive Bash;
  installed wrappers match repository sources and remain executable.
- Relevant Desktop/menu Exec targets, working directories and icons passed.
  The Strata App was not started.
- Host inventory confirms both AMD cards and read/write access to KFD/render
  nodes; active HIP/Vulkan/Strata executables and retained expert pack exist.
- Localhost SSH reached the server with its public host key pinned in a temporary
  file, but existing authentication was denied. End-to-end SSH PATH resolution
  remains **unverified**; permanent trust/authentication settings were not changed.
- Gateway auth/catalog/health checks passed without generation or model loading.
- Model inventories and saved numeric result files are unchanged. Public Windows
  and NVIDIA snapshot directories are unchanged.

Publication uses reviewed text files only. Private archives/manifests, models,
runtime binaries, credentials and the untracked client guide are excluded from
staging. Secret/privacy scan reports stay in ignored private maintenance output.

Gitleaks v8.30.1 found no staged leaks in either repository. Its public-history
scan reported one retired FreeToken `FREETOKEN_REVISION` Git source pin as a
generic API key; review confirmed the 40-hex value is used by `git checkout`,
not authentication. With only that exact finding classified, no other history
leaks were reported. Exact live-key and known private path/address checks also
passed against staged files and all 679 reachable public blobs. This is a scoped
publication check, not a guarantee about copies outside these repositories.
