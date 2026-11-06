# Local LLM on dual AMD RX 7900 XTX

Current as of November5,2026. Sanitized public reference for the separately maintained private operational AMD repository; configure example paths locally.

[IQ1_M qualification and cache status](linux/hardware/STRATA-IQ1M-AND-STREAMING-CACHE-2026-11-05.md): new Unsloth UD-IQ1_M passed strict tools,5/6 local quality fixtures and57.140native tokens/s median across three short probes. All13 original routes remain;14routes/11 main weight sets are grouped below. GLM RAM24 completed strict tools and 5/6 local fixtures, with a 1.995 native tokens/s median across three short speed probes; it was not selected because follow-up performance regressed, so RAM8 remains selected. Maya DeepSeek36GB-store failed during loading on the six-second heartbeat guard and missed its 15-second owned cleanup deadline; the boot later suffered AMDGPU/CPU lockups. The persistent GPU fault hold remains: no automatic GPU work, retry, reboot or hold release. RAM40 is prepared but unrun and blocked. Current stock7.0.0-42-generic has no fresh peer/model qualification.

## Take over in a few minutes

1. Read this maintenance policy and the [current runtime handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md).
2. Read the [current result index](linux/hardware/CURRENT-AMD-BENCHMARKS.md) only when measurements matter.
3. Check both Git working trees and actual job/lock ownership before changing anything. Follow the current user request; the owner-requested qualification outcomes are now recorded below.

Fourteen qualified API routes are enabled. Four realistic-budget native retries passed; llama9c9074 passed and is selected for Flint, Ornith and Empero. ComfyUI0.44/fb2b26f passed all six normal workflows and is selected. Fresh owner-requested latest-guard attempts ended before inference: Flint AWQ requires unavailable FlashInfer; PLE stopped on the six-second heartbeat guard; Super stopped below the 1 GiB host reserve. PLE missed its 15-second KFD drain deadline, then drained later; that failed result remains recorded. None was promoted. The unused Strata DFlash2 source/packs were removed after pinned-hash and dependency verification; the separate SGLang drafter and all 13 selected routes remain unchanged. [Fresh candidate attempts and drafter removal](linux/hardware/CANDIDATE-RETESTS-2026-11-05.md). Bolt now selects globaldev229 after a strict matching255473-token prefill/tool check (255658 tokens on its second request), with clean owned cleanup and zero recorded swap or VRAM spill. Its old dev435 environment is retained. The RDNA3 fork at2314df4 built and passed native/CLI audits, but its Qwen startup warm-up failed on missing `CommonAttentionMetadata._seq_lens_cpu` before any request. The exact case is final; the fork remains isolated and unpromoted. The [runtime handoff](linux/network/LINUX-LLM-RUNTIME-HANDOFF.md) records exact selections, safeguards and pending work; [current results](linux/hardware/REALISTIC-LARGE-MODELS-2026-11-05.md) include all saved model/graphics timings and downloaded asset groups. Completed GPU checks are not repeated for documentation.

[Native decode capture and candidate removal](linux/hardware/AMD-NATIVE-DECODE-TESTS-2026-11-05.md): all13 selected routes now have short native per-request decode statistics; the four newly tested routes also have three fixed128-token speed probes each. Failed FlintAWQ, FP8-PLE and SuperINT4 downloads were removed by explicit owner request. Selected routes/guards remain unchanged; no sustained full-catalog benchmark is claimed.

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
