# Overnight engine updater restored — October 29, 2026

The owner restored the existing 03:00 local daily engine updater and requested a current update run. This supersedes earlier updater-pause notes; other holds and manual model/runtime pins remain.

- `llm-daily-update.timer`: enabled and active; next scheduled run October 30 at 03:00 local.
- `llm-daily-update.service`: manual guarded run started October 29; qualification is in progress.
- `llm-daily-update-recover.service`: remains enabled for interrupted provisional-install recovery.
- Latest-source check: newer llama.cpp, vLLM, Strata Qwen, Maya and Strata DeepSeek candidates; the configured SGLang AMD fork matches upstream.

New builds are prepared in isolation. Production baselines, model coverage, correctness, performance, memory and rollback gates remain mandatory before promotion. RAM-held normal profiles can block a shared-engine promotion. The isolated Ornith 32 GB result does not change its normal profile admission or qualify a new engine build.

## Restoration repairs and verification

The benchmark helper environment had tokenizers 0.23.3 but lacked regex. The CPU-only helper environment now has pinned `tokenizers==0.23.3` and `regex==2026.9.29`, recorded in [requirements.txt](daily-update/requirements.txt). Imports and the actual benchmark's 8,174-token, three-marker prefill fixture passed without GPU/model initialization. Engine environments were not changed by this repair.

`RuntimeMaxSec` is ignored for `Type=oneshot`; the unit now uses `TimeoutStartSec=10h`, retaining its existing graceful stop/rollback window. Unit configuration was reloaded without restarting the active process, and the live service reports the ten-hour timeout. The unit explicitly selects `loading-swap-v3`: loading/parked swap and reads remain allowed; rates/PSI alone remain advisory. Existing independent guards, manual pins and qualification gates remain.

The six registered components are llama.cpp, vLLM ROCm nightly, the SGLang gfx1100-support fork, Strata Qwen, Maya and Strata DeepSeek. Graphics/ComfyUI/H3 are outside this updater. [Pre-restoration source audit](ENGINE-UPDATE-AUDIT-2026-10-29.md) records the selected/candidate versions at the earlier snapshot.

## Current run

The standard updater is running. No promotion outcome is claimed by this start-status record. Final per-engine results and selected versions belong in the [daily ledger](DAILY-UPDATES.md) and canonical runtime handoff after the gates and any rollback complete. Do not start a duplicate updater or GPU workload while its maintenance reservation is held.
