# Strata DeepSeek settle-off test — November 11, 2026

**Result:** turning the idle settle off does not stop the NaN fault. Session 1 answered 53 of 53 requests; session 2 failed with a NaN error on its 38th request. One fault in 91 requests.

## What was tested

- Route `deepseek-v4.1-flash-1017-strata-unsloth-q1`, `--reserve-mib 2048`, with `DS4_SETTLE_IDLE=0` and `DS4_SETTLE_MS=0` in the engine environment (confirmed from the running process in both sessions).
- Planned: four fresh engine sessions, each answering the same 53 items of the public quality suite, stopping at the first error.
- The launcher strips `DS4_*` variables, so the sealed route profile was edited and re-sealed for the test. Both profile files were restored from git when the run stopped; the sealed fingerprint is the original again and nothing in the route settings changed.

## Results

| Session | Start | End | Requests answered | Errors |
|---|---|---|---|---|
| 1 | 04:48 | 05:45 | 53 of 53 | 0 |
| 2 | 05:56 | 06:48 | 37 of 53 | 1 (NaN on the 38th request, 117 s in) |
| 3, 4 | not run | | | |

- The engine log names CUDA0 for the fault: "the router met scores that are not numbers (NaN) on CUDA0". The first November 8 event was reported on the other card's index.
- The earlier replay at the same reserve with settle on failed 5 times in 88 requests. One fault in 91 with settle off is not distinguishable from that, and it shows settle-off is not a fix.

## Server state after the test

- No GPU hold file. No kernel GPU reset, timeout or page-fault message during either session.
- One kernel message pair, "Failed to upload overdrive table", on the Sapphire card at 06:01:34, five minutes into session 2 and 47 minutes before the fault. It coincides with the fan controller failing to commit a fan curve and recovering one second later. The same pair appears nine times since November 10. Not shown to be related.
- The test engine exited; the hub and the other routes were not touched.

## Not tested

- Whether the launcher's GPU order (`ROCR_VISIBLE_DEVICES=1,0`, opposite to `hardware/rocm-env.sh`) plays a part.
- A larger reserve, a single-card layout, or the engine's own diagnostics for where the first non-finite value appears.

No further GPU work was started after the fault.
