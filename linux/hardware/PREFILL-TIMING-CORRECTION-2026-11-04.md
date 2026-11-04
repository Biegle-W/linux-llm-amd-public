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

## First observed corrected results

**November 4 corrected timing results:** Strata Coder completed the strict read-tool test with first-token latency **26.922 s**, 100 generated tokens, two model steps, matching tool IDs and the correct final marker. Its raw guard failure was a cleanup-result recording race; the saved events, completed requests and inactive owned scopes were independently verified. The original 20-second rule would have rejected this successful inference. Strata Q1 reached output but stopped at the retained three-second decode-stall guard; no complete tool pass. PLE exhausted its unchanged 900-second loading budget and unloaded cleanly; that is an inconclusive loading attempt. Corrected Maya Q1 also stopped at the retained three-second decode-stall guard without completing the tool test; its owned scopes emptied. GLM completed its first request after an 81.480-second TTFT and made the requested tool call; its second step exhausted the remaining unchanged stage budget, so the full tool test is inconclusive. All requested corrected checks have stopped and unloaded; owned scopes are inactive, KFD is empty, and no new GPU reset/bus-loss/OOM pattern was recorded. No additional trial is queued. Both downloads are complete and verified. P2P remains off; no production promotion.

The successful Strata Coder request took 35.379 s overall: 26.922 s to first output, then 8.457 s of output. Its second step took 2.864 s overall with 2.157 s to first output. This directly demonstrates why prefill must be measured separately from the retained output budget. The raw cleanup failure remains recorded; independent audit establishes the bounded inference success without rerunning it.

The bounded GLM request took 96.525 s overall: 81.480 s prefill plus 15.044 s output. Its tool-result step did not produce output before the remaining original 240-second enclosing budget (with 15-second cleanup reserve) expired. It is not a complete strict tool pass. Maya Q1 and Strata Q1 both stopped at the retained three-second post-output stall monitor; that guard stop is not proof of a GPU hang or model defect. All completed attempts unloaded, with no new kernel GPU reset/bus-loss/OOM match. No model was promoted and no further GPU task is queued.
