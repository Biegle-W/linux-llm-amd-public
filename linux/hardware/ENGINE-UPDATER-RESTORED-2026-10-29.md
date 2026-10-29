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

## First pass and targeted follow-up

The first standard pass finished and published its ledger. All five available candidates built; no version was promoted in that pass:

- llama.cpp: production coverage blocked by the normal Ornith profile's 60 GiB physical-RAM admission.
- vLLM: functional profiles passed, but Sage's 21.1-second test lacked the required complete 30-second inference-observation window. The same issue affected the 28.7-second Empero evidence.
- Strata: performance and marker checks passed, but one lifecycle sample failed with KeyError. The candidate was rejected and rollback verified; that rejection remains.
- Maya and Strata DeepSeek: normal DeepSeek profiles remain RAM-held, blocking complete production baseline coverage.

A targeted vLLM-only follow-up is running after the benchmark client repair. Fast profiles now perform additional **real, untimed generation** after the timed requests until the existing observation window closes. Those probes are recorded separately and excluded from performance medians. The 30-second window, invalid-telemetry rejection, model coverage, performance and rollback gates are unchanged. Four CPU regressions pass in each checkout, covering the real policy window, already-complete evidence, invalid telemetry and bounded missing evidence.

The targeted manual scope is temporary: the next 03:00 timer still checks the full engine registry. First-pass raw measurements and logs were preserved before rebuilding the vLLM stage. Final per-engine outcomes and selected versions are recorded in the [daily ledger](DAILY-UPDATES.md) and canonical runtime handoff. Do not duplicate the active updater or its GPU reservation.
