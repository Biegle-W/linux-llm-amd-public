# Overnight engine updater restored — October 29, 2026

**Owner pause — October 29:** Ornith, DeepSeek XS on Maya and Strata, Qwen Flash Next on Strata, and Qwen27B on SGLang are disabled until the owner reports more RAM is available. Seven working profiles remain enabled; nightly qualification skips the paused routes. No automatic RAM-detection resume. [Paused models and resume rules](MODEL-RAM-PAUSE-2026-10-29.md).

The 03:00 local nightly updater is restored and the requested current-source update is complete. The full registry remains scheduled for **October 30 at 03:00 EDT**; recovery is enabled. The vLLM follow-up finished at 13:21; the later llama.cpp follow-up finished at 14:05 EDT. Both runs completed successfully, cleared provisional state and released their GPU reservations. Hub and gateway retained their existing processes.

## Final engine selections

| Component | Outcome | Selected version / reason |
|---|---|---|
| vLLM, Qwen and Sage | **Promoted** | `0.33.0rc1.dev229+g3966924d5.rocm72`; all standard same-night gates passed |
| Bolt vLLM | Manual pin retained | `0.32.1rc1.dev435+gc50aca144.rocm72`; excluded from global comparison |
| llama.cpp | **Split promotion complete** | Global `eb4e244be77a` for Empero/Super/Flint; Ornith alone retains independent `2280f0fd163b` manual source/build hold and 60 GiB admission |
| SGLang AMD fork | Already current | `f84475ccf593` |
| Strata Qwen | Retry RAM-blocked; restored files verified, fresh load pending | `7dd5cf18e68c`; latest baseline passed with zero sampler errors, candidate and rollback load checks hit 25 GiB RAM admission. Earlier one-KeyError rejection remains historical. See [retry status](STRATA-RETRY-SAMPLER-2026-10-29.md). |
| Maya | Baseline blocked | `f26d8bab43f9`; normal DeepSeek profile remains RAM-held |
| Strata DeepSeek | Baseline blocked | `8183c6b67162`; normal DeepSeek profile remains RAM-held |

All five available candidates built. The initial pass promoted none; after repairing fast-profile observation evidence, the targeted vLLM follow-up promoted vLLM. The later owner-authorized split follow-up promoted llama.cpp `eb4e244be77a` for its three unpinned models; [split results and preserved client failure](LLAMA-SPLIT-UPDATE-2026-10-29.md). Prior skipped/rejected outcomes remain in the ledger. Graphics/ComfyUI/H3 are outside this six-component registry. The isolated Ornith 32 GB proof does not change normal-profile admission.

## vLLM same-night measurements

Normal launcher, unchanged profiles, 30.56 GiB physical RAM. Prefill is engine-phase throughput; fresh prefill TTFT excludes model loading. Code/prose are three-trial median decode rates; extra observation probes are excluded.

| Model | Prefill t/s, baseline → selected | Fresh prefill TTFT s, baseline → selected | Code t/s | Prose t/s | Context tokens |
|---|---:|---:|---:|---:|---:|
| Qwen3.8-27B | 1457.00 → 1471.74 | 5.681 → 5.614 | 142.75 → 142.51 | 78.44 → 75.84 | 163,840 |
| Sage-A1.5 | 5276.47 → 5324.55 | 1.574 → 1.559 | 148.48 → 148.76 | 139.60 → 139.70 | 65,536 |

Both retained all three retrieval markers and passed arithmetic, complete model coverage, performance and valid per-model plus launch-through-shutdown memory gates. Qwen prose is 3.3% slower and remains within the unchanged 95% performance floor; no broad speedup is claimed. Dedicated-VRAM spill and lifecycle sampling errors are zero. Candidate lifecycle sampled worker swap peaked at 3,232,501,760 bytes; v3 allows loading/parked swap and reads, with rates/pressure advisory. This pass does not assert zero swap or add a swap-rate stop.

The run tests short text and ~8K prefill; it retains configured context limits and earlier capability evidence. It does not add full-context, tools, JSON/SSE integration or vision qualification for the new wheel. Sage remains text-only. [Curated numeric results](results/engine-updater-restored-2026-10-29.json), [daily ledger](DAILY-UPDATES.md) and canonical runtime handoff retain the gates and exact versions.

## Restoration repairs and verification

The benchmark helper environment had tokenizers 0.23.3 but lacked regex. Its separate CPU-only environment now pins `tokenizers==0.23.3` and `regex==2026.9.29` in [requirements.txt](daily-update/requirements.txt). Imports and the actual 8,174-token, three-marker prefill fixture passed without GPU initialization.

`RuntimeMaxSec` is ignored for `Type=oneshot`; the unit now uses `TimeoutStartSec=10h`, retaining the graceful rollback stop window. Reloading the unit preserved the running job. `loading-swap-v3` is explicit; independent RAM, VRAM, ownership and thermal protections remain.

Fast profiles previously finished before the required complete 30-second inference-observation window (Sage 21.1 s, Empero 28.7 s). The benchmark now appends **real, untimed generation** until that existing window closes. Separate probe records are excluded from performance medians. Four CPU regressions pass in each checkout, covering the real policy window, already-complete evidence, invalid telemetry and bounded missing evidence. Missing/invalid readings still fail closed. Sage used nine baseline and eight candidate observation probes in the successful follow-up.

The temporary vLLM-only manual scope was removed from systemd; the next timer checks the full registry. First-pass raw evidence was retained before the follow-up. The recovery service, manual runtime pins, other holds and all qualification/rollback gates remain. No completed Ornith or other benchmark was repeated for documentation. [Pre-restoration source audit](ENGINE-UPDATE-AUDIT-2026-10-29.md) is a historical snapshot.
