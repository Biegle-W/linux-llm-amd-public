# Strata DeepSeek with the RAM store off — November 12, 2026

**Result:** with the RAM store turned off, the route answered all 216 items of the public quality suite with no NaN error and no kernel fault, and scored 169 of 216. The setting is kept.

## What changed

- Route `deepseek-v4.1-flash-1017-strata-unsloth-q1`, engine `c1ff07f`: `--ssd-cache 36` changed to `--ssd-cache 0` in the route profile, and the profile re-sealed (owner approved).
- With the store off, the engine reads the experts that do not fit in VRAM (about 82 GB) in place from the model files and reads ahead the most-used 48 GB into the file cache. With the store on, it also copied 36 GB of experts into its own RAM pool with unbuffered reads of the same files.
- Nothing else changed: same weights, `--reserve-mib 2048`, 14 threads, same kernel.

## Why this was tried

- DeepSeek on Maya, which has no RAM store, ran the same suite on the same weights and hardware with no NaN error. Its engine log has none; the Strata log had 48.
- The first NaN on Strata appeared on November 8, in the run that turned the pre-filled store on.
- The NaN was reported on both cards on different days, which argues against one bad card.
- On November 11 the server's kernel crashed in a page-cache lookup on the model file while Strata was serving, right after a NaN error.

## Results

| Attempt | RAM store | Items answered | NaN errors | Outcome |
|---|---|---:|---:|---|
| November 11, first run | 36 GB | 4 | 1+ | stopped on NaN |
| November 11, replay | 36 GB | 82 of 88 tried | 5 | stopped after three errors in a row |
| November 11, settle off | 36 GB | 90 of 91 tried | 1 | stopped on NaN |
| November 11 evening, engine `c1ff07f` | 36 GB | 15 of 17 tried | 1 | kernel crash, reboot |
| **November 12** | **off** | **216 of 216** | **0** | **finished** |

- Run: 02:22 to 05:50 EST, 216 requests plus warm-up, temperature 0, thinking off, through the hub.
- Score: 169 correct, 32 wrong, 13 cut off at the token limit, 2 malformed. 78.2%, 95% interval 72.3–83.2%.
- By category: code 13/20, instructions 29/32, knowledge 49/60, math 32/40, reasoning 19/32, tools 27/32.
- Against DeepSeek on Maya (168): 158 items right on both, 11 only on Strata, 10 only on Maya. No detectable difference.
- Speed over the whole suite, answer tokens divided by request time: 8.6 tok/s. On the 82 items the November 11 replay answered, 8.9 tok/s with the store off against 7.4 with it on. Turning the store off did not cost speed here.
- Speed test after the suite, ten requests through the hub with the November 11 method ([results](results/strata-dsv41-speed-no-ram-store-2026-11-12.json)):

| Measure | Store on (Nov 11) | Store off (Nov 12) |
|---|---:|---:|
| First answer from a cold start | 71 s | 82 s |
| 400-token answer, first after load | 4.2 tok/s | 4.2 tok/s |
| 400-token answers after that | 8.0–10.2 tok/s | 10.7–12.2 tok/s |
| Prompt read, 4.8K-token uncached prompts | 119–132 tok/s, one at 63 | 125–143 tok/s, one at 79 |

- No NaN and no kernel message during the speed test either.
- Engine log: no new NaN line. Kernel log: no GPU reset, page fault or crash. The only kernel messages were "Failed to upload overdrive table" pairs from the fan controller, which also appear on earlier days.

## Limits

- This is one clean run. At the earlier failure rate (7 errors in about 200 requests) a clean run of 216 by chance is very unlikely, but the cause is inferred, not proven: the test shows the fault goes away with the store off, not why the store triggers it.
- The guarded tool-call figures in the benchmark list (decode 5.6, prompt read 111, load 140.1) were measured with the store on and have not been repeated.
- The other Strata routes do not use this store and were not touched.
- Whether the November 11 kernel crash had the same cause is not shown. No crash occurred in this run.
