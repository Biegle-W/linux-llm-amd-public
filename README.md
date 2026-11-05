# Local LLM on dual AMD RX 7900 XTX

Current as of November 5, 2026. This is the sanitized public reference for the separately maintained private AMD operational repository. Example paths and addresses require local configuration.

## Take over in a few minutes

1. Read this maintenance policy and the [current runtime handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md).
2. Read the [current result index](linux/hardware/CURRENT-AMD-BENCHMARKS.md) only when measurements matter.
3. Check both Git working trees and actual job/lock ownership before changing anything. Follow the current user request; the owner-requested engine update task is in progress.

Thirteen qualified API routes are enabled. Four realistic-budget native retries passed; llama9c9074 passed and is selected for Flint, Ornith and Empero. ComfyUI0.44/fb2b26f passed all six normal workflows and is selected. PLE stopped during loading under its unchanged heartbeat guard. Super also stopped during loading under that guard, with clean owned cleanup and no promotion. Bolt now selects globaldev229 after a strict matching255473-token prefill/tool check (255658 tokens on its second request), with clean owned cleanup and zero recorded swap or VRAM spill. Its old dev435 environment is retained. The corrected isolated RDNA3 CPU build is running with matching MIOpen and hipSPARSELt7.2.3 dependency overlays; runtime qualification remains pending and no production promotion occurred. The [runtime handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md) records exact selections, safeguards and pending work; [current results](linux/hardware/REALISTIC-LARGE-MODELS-2026-11-05.md) include all saved model/graphics timings and downloaded asset groups. Completed GPU checks are not repeated for documentation.

## Maintenance policy

- This server maintains only `Biegle-W/linux-llm-amd` and `Biegle-W/linux-llm-amd-public`. Other Linux NVIDIA/Windows repositories and old snapshots are references unless explicitly assigned.
- After authorized changes, keep both AMD repos, applicable results and the current handoff synchronized. Reviewed intended commits and normal non-force pushes to both `origin/main` branches are authorized. Verify actual remote refs; preserve unrelated changes and report exact blockers.
- Keep the Shared runtime handoff byte-for-byte equal to the operational `network/LINUX-LLM-RUNTIME-HANDOFF.md`. The operational destination is configured on the Shared SATA drive (Windows `D:\LINUX-LLM-RUNTIME-HANDOFF.md`). Public references use sanitized paths/addresses.
- Never publish credentials, personal/client settings, chat state, raw private logs, model weights, environments or runtime binaries. Private agent workflow, checkpoints and context tools stay out of public exports and Shared handoffs. Preserve existing public historical snapshots; retired source belongs in the established central archive.
- Preserve installed paths, exact source/weight pins and manual runtime pins, all guards, stock persistent boot default, unrelated applications and paused schedules. Documentation upkeep does not authorize a trial, engine upgrade, restart, hold release or schedule change.
- Engine changes prefer current upstream development builds, including prereleases, but require isolated hardware/profile qualification before promotion. Check a suitable gfx1100 vLLM/SGLang INT4 route before keeping a new model on GGUF; change selection only on measured qualified evidence. Keep required fork/runtime versions isolated.
- New static weights use configured SATA storage; streaming packs use system `models/streaming/`. Before downloads/copies, run `python3 dsh/shared_storage.py --place static|streaming --size-gb N`; retain the 90% storage admission limit. Never relocate existing validated assets as housekeeping.
- Keep communication and GitHub content in English. Keep current docs concise: replace superseded state and link dated evidence; do not prepend chronological snapshots.

## Find details when needed

| Area | Reference |
|---|---|
| API, exact routes, guards, holds, current pins | [Runtime handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md) |
| Latest qualification and measurement limits | [Current result index](linux/hardware/CURRENT-AMD-BENCHMARKS.md) |
| Historical benchmarks | [Benchmark history](linux/hardware/BENCHMARK-HISTORY.md) |
| DSH and client setup | [DSH](linux/dsh/README.md), [network](linux/network/README.md) |
| Graphics | [Graphics setup](linux/graphics/README.md) |
| Retired setup index | [Archives](archives/README.md) |
| Full previous overviews | [Documentation history](linux/hardware/history/documentation-2026-11-05/README.md) |
