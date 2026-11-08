# Local LLM on dual AMD RX 7900 XTX

Sanitized public reference for a separately maintained private operational repository. The Linux tree is in [`linux/`](linux/); example paths use `/opt/local-llm`, `/mnt/shared` and `/mnt/shared-nvme`. Configure them locally.

Twelve qualified routes are served through one OpenAI-compatible API on TCP 10000. The [runtime handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md) lists them with their settings, guards and pins.

## Rules

**Scope and publishing**
- This server maintains only the two AMD repos above. Other Linux NVIDIA and Windows repos, and old snapshots, are references unless the owner assigns them.
- After authorized changes, keep both repos, the results and the handoff in step. Reviewed commits and normal (non-force) pushes to both `origin/main` branches are authorized. Verify the remote refs afterwards, preserve unrelated changes, and report exact blockers.
- The operational handoff has a byte-identical private copy on the shared SATA drive (Windows `D:\LINUX-LLM-RUNTIME-HANDOFF.md`). That copy is the private text, not this public one.
- Public edits are targeted and hand-sanitized: no home or mount paths, LAN or tailnet addresses, or identity names. Public profiles use `/opt/local-llm` paths. The nightly publisher's `PRIVATE` regex in `linux/hardware/daily-update/publish.py` is the check.
- Never publish credentials, personal or client settings, chat state, raw private logs, model weights, environments or runtime binaries. Private agent workflow, checkpoints and context tools stay out of public exports and the Shared handoff.

**Runtime safety**
- Preserve installed paths, exact source and weight pins, manual runtime pins, every guard, the owner-selected kernel default (`7.0.14-42-vmpt1`, stock installed as fallback), unrelated applications and paused schedules. Documentation upkeep never authorizes a trial, engine upgrade, restart, hold release or schedule change.
- GPU work is serialized behind an owned `hardware/generated/GPU-LOCK`. A lock you do not own, or unknown KFD ownership, blocks you. After a GPU fault the lock is a fault hold: no GPU work, retries or reboots until the owner releases it.
- Qualified native profiles are sealed (`config_sha256`) in `dsh/qualified-native-profiles.json` and `dsh/qualified-strata-qwen-profiles.json`. Editing a sealed profile breaks admission until it is requalified and resealed; never fake a seal.

**Engines and models**
- Daily updater policy (owner, November 7): always take the latest engine version unless it breaks something. A minor slowdown is never a reason to reject. Details are in [the updater README](linux/hardware/daily-update/README.md).
- New engines or models need isolated qualification before promotion. For a new model, check a gfx1100 vLLM or SGLang INT4 route before keeping it on GGUF.
- Deleting weights or data is the owner's call.

**Storage (90% limit)**
- No drive may go above 90% used. Before any download or copy, run `python3 dsh/shared_storage.py --place static|streaming --size-gb N`. It refuses when the drive would pass 90%, and it creates the target folder.
  - `static` goes to the shared SATA drive's `vLLM-Models`.
  - `streaming` goes to the shared NVMe drive's `LLM-Models`.
- Existing streaming packs stay in `models/streaming/` on the system drive. Never move validated assets as housekeeping.
- The check is advisory: downloaders do not call it themselves.

**Writing**
- Use English for all communication and GitHub content.
- Keep current docs short and current. Replace superseded state instead of adding to it. Each change gets one line in the [changelog](linux/hardware/CHANGELOG.md) and a dated report for its evidence.

## Layout

Paths below are inside `linux/`.

| Path | What it holds |
|---|---|
| `dsh/` | Hub (`model_hub.py`), routers, runtimes, route registries and profiles, DSH frontend |
| `network/` | API gateway, systemd units, the runtime handoff |
| `hardware/` | Operational scripts (`rocm-env.sh`, guards, updater), unit tests `test_*.py`, dated reports `*-2026-*.md`, `results/` JSON |
| `hardware/daily-update/` | Nightly updater, publisher and systemd unit sources |
| `hardware/generated/` | Ignored live state: `GPU-LOCK`, updater runs (some hold live engine builds) |
| `vllm/`, `sglang/`, `maya/`, `strata-dsv41/`, `graphics/` | Engine launchers and pins; ignored venvs and sources sit beside them |
| `bin/`, `launchers/` | `llm-*` CLI wrappers and Desktop launchers |
| `models/streaming/` | Ignored streaming weights for Strata and Maya |
| `llm-tools/` | Ignored toolchains: Python, ROCm SDK, RCCL, caches |

Dated reports stay flat in `hardware/` because many links and a few code strings point at them; find them through the [changelog](linux/hardware/CHANGELOG.md).

## Doc map

| Need | Read |
|---|---|
| Current state, routes, guards, pins, open items | [Runtime handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md) |
| Current measurements | [Current results](linux/hardware/CURRENT-AMD-BENCHMARKS.md) |
| What changed and when | [Changelog](linux/hardware/CHANGELOG.md) |
| Nightly engine updates | [Ledger](linux/hardware/DAILY-UPDATES.md) (written by `publish.py`), [method](linux/hardware/daily-update/README.md) |
| Drives and weight files | [Storage inventory](linux/hardware/MODEL-STORAGE-INVENTORY.md) |
| Card layout and crash runbook | [AMD working setup](linux/hardware/AMD-WORKING-SETUP-2026-11-07.md) |
| Clients and gateway | [Network](linux/network/README.md), [DSH](linux/dsh/README.md) |
| Image and video | [Graphics](linux/graphics/README.md) |
| Older measurements | [Benchmark history](linux/hardware/BENCHMARK-HISTORY.md) |
| Retired setups | [Archives](archives/README.md) |
