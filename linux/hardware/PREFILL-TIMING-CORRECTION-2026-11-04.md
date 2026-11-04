# Prefill timing correction — November 4, 2026

The owner correctly pointed out that time to first token above 20 seconds is normal for these large models. The 20-second threshold was an agent-selected diagnostic default, not an explicitly owner-selected requirement or evidence of a model defect.

## Correct interpretation of earlier results

The Unsloth Q1 attempts on Maya and Strata, Strata Coder, and the loaded GLM attempt were stopped before their observed first output by the diagnostic timing rule. Their inference outcome is **inconclusive**, not a demonstrated inability to run the model. Raw failed records, elapsed times and cleanup evidence remain unchanged. A successful short check under the earlier limits remains a positive bounded result; Maya Coder and Strata Qwen successes are not invalidated.

Separate format incompatibilities, actual GPU faults, resource/temperature stops and loading-budget exhaustion remain distinct outcomes. Exceeding an experiment's loading/overall budget alone also does not prove a model is broken.

## Corrected diagnostic policy

- Measure TTFT and record it, without a separate fixed prefill deadline.
- HTTP header/body waits, the harness request/stream-idle setting and the round-trip wait share the **remaining existing overall stage budget**, reserving the existing 15-second owned cleanup allowance. The old 20-second socket wait, 30-second whole-request client timeout and 65-second harness cap must not silently reintroduce a prefill cutoff.
- The retained 30-second model-request output budget starts at first output. Prefill is no longer charged to that budget. The 3-second post-output stall monitor remains.
- Original model loading and total-stage caps remain: 900/990 seconds for Q1, Coder and PLE; 210/240 for the bounded GLM check. Exhaustion is reported as an inconclusive experiment budget, not a model defect.
- Free RAM 1 GiB, free VRAM 128 MiB per card, installed-RAM hard limit, current swap/SSD health checks, temperature limits, six-second supervisor heartbeat, inter-request idle, ownership and cleanup protections remain unchanged. P2P stays off.

This changes isolated diagnostic waiting and interpretation. It does not install a new production runtime, enable a catalog route, change weights/context/sampling, relax numerical tolerances or run an easier prompt.

## Verification and continuation

Eight CPU timing tests pass in each checkout: healthy 180-second prefill, first-output-based output budgeting, stalled decode, monitor heartbeat, unchanged loading/idle/cleanup limits, exact historical replay, client wait derived from the enclosing stage budget, and rejection of an unbounded/invalid budget. A private integration check verifies five corrected stage copies retain their model profiles and unrelated limits while removing the coupled client/harness cutoffs.

The original PLE attempt was already loading when the correction was requested. Its code and active process are preserved as evidence. A single one-off continuation waits for its verified owned unload and checks the fault/temperature/cleanup boundary before any further GPU task. It repeats PLE only if that attempt is invalidated by the old prefill/client timing, then performs one corrected short read-tool check for Strata Coder, Q1 on both engines and the previously loaded bounded GLM candidate. It does not repeat format math, hashes or successful Maya Coder/Qwen checks, and it never automatically promotes a runtime. Raw old timing stops remain retained.

[Timing implementation](short_test_timing.py). [CPU checks](test_short_test_timing.py). [Original results and updated qualification](MAYA-STRATA-Q1-UPGRADE-2026-11-03.md).
