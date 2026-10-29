# Split llama.cpp update — October 29, 2026

**Complete:** llama.cpp `eb4e244be77a906a183cd4a00fd51d9ad3200955` is selected for **Empero, Super and Flint** after the standard same-night baseline/candidate comparison. **Ornith alone retains an explicit independent old source/build pin** at `2280f0fd163b03d4331d49e08460f66502e35854`. The final updater completed at 14:05 EDT, provisional state is clear and its GPU reservation is released.

The normal Ornith profile still requires 60 GiB physical RAM on this 30.56 GiB host. Its admission failure did not establish incompatibility with newer llama.cpp. The earlier isolated 32 GB placement remains separate and was neither promoted nor rerun. No claim is made that this normal Ornith profile can load on the current RAM.

## Same-night qualification

Normal launcher, unchanged weights/quantization/contexts and eight unchanged profile/guard files. Each arm used three timed code and prose trials after excluded warmups, three fresh salted prefill/marker requests, arithmetic and per-model plus launch-through-shutdown memory monitoring. Columns show **baseline → selected candidate**; every candidate model actually used the new global source.

| Model | Baseline source | Native prefill t/s | Fresh prefill TTFT s | Code t/s | Prose t/s | Context tokens |
|---|---|---:|---:|---:|---:|---:|
| Empero | `19cce6919992` | 3421.43 → 3409.69 | 2.407 → 2.413 | 135.45 → 135.64 | 86.06 → 85.39 | 262,144 |
| Super | `2280f0fd163b` | 428.01 → 425.82 | 18.534 → 18.631 | 15.65 → 15.48 | 17.18 → 16.94 | 32,768 |
| Flint | `19cce6919992` | 5688.46 → 5726.10 | 1.100 → 1.091 | 46.97 → 46.92 | 46.95 → 46.86 | 32,768 |

All three models retained all three retrieval markers and passed the unchanged prefill/decode ≥95% floor, short-TTFT bound, coverage and memory gates. Native prefill throughput and external fresh TTFT are separate; model loading is excluded. These are short text/marker comparisons, not new full-context, history, tools/API integration or vision qualification. The shared prompt is sized with the Qwen tokenizer; Flint’s actual input was 6,022–6,026 tokens in this run. Actual input/output counts and timed medians are retained in [curated numeric results](results/llama-split-update-2026-10-29.json); earlier approximately 8K native-tokenizer results remain historical.

Candidate lifecycle: 892 worker samples, 0 sampling errors, 0 dedicated-VRAM-spill bytes; sampled worker swap peaked at 5,948,850,176 bytes. `loading-swap-v3` permits loading/parked swap and reads; rates/pressure alone remain advisory. Independent physical-RAM, RAM-cap, VRAM reserve/spill, ownership and thermal protections remain.

## Durable Ornith hold

`dsh/llama-runtime.json` retains all four model IDs. Ornith has an explicit `source_overrides` entry with a permanent independent source/build directory, exact `source_commit` and matching `manual_runtime_pin`. Its same-source HIP build completed at its permanent location; ELF runtime search paths are independent of the global build. Loader source verification passes, and its source and binary fingerprint are unchanged after the global update. Ornith was not loaded during this work.

The updater validates held source revisions/binaries, excludes only valid explicit manual holds and requires every unpinned model in baseline and candidate records. Installation clears ordinary source overrides so Empero/Super/Flint exercise the new global source; it preserves Ornith’s manual hold. Rollback restores the exact previous JSON and global source/build. Missing/changed held builds, invalid pins, empty unpinned coverage, incomplete telemetry and failed gates still block promotion. The hold survives future nightly global updates until explicitly removed after separate qualification.

The publisher reports held and global sources separately and exports sanitized example paths requiring local verification. The next **October 30, 03:00 EDT** timer checks the full six-component registry; temporary llama-only service overrides were removed. Recovery remains enabled, with the existing 10-hour oneshot timeout.

## Preserved failed attempts and client repairs

The original full-registry pass could not qualify global llama.cpp because normal Ornith failed RAM admission. The owner then authorized this split. Its first three-model baseline passed Empero/Super, but Flint failed marker retrieval before any candidate installation: the client allowed 64 total output tokens while its unchanged reasoning budget was 128. Earlier successful Flint marker samples used 145 output tokens. That failed run and its evidence remain archived.

The repaired client reads the selected preset’s bounded reasoning budget and adds the same 64-token answer allowance: Flint gets 192 total output tokens, Empero/Super keep 64. This successful baseline and candidate both used that same allowance; their actual completion counts are in the numeric record. Prompts, model reasoning settings and all required markers remain unchanged. Missing/unbounded configured budgets fail closed. Failed trials are saved before assertions, with finish reason and visible-content presence; response text remains unpublished.

Fast profiles retain the earlier real, untimed generation probes needed to close the unchanged 30-second memory-observation window; these are excluded from timing medians. **61 CPU regressions pass in each checkout**, including source selection/ownership, durable holds, publication, full coverage, lifecycle/rollback, memory-window and five reasoning/evidence checks. No guard was lowered and no completed Ornith benchmark was repeated.

The separate vLLM promotion remains selected for Qwen/Sage at dev229; Bolt stays manually pinned to dev435. Strata’s earlier candidate passed performance/markers but failed lifecycle telemetry with one KeyError; rollback was verified and it was not retried. Maya/Strata DeepSeek RAM-held outcomes remain. See the [restored-updater report](ENGINE-UPDATER-RESTORED-2026-10-29.md) and [daily ledger](DAILY-UPDATES.md).
