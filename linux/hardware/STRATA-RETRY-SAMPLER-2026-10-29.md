# Strata retry, sampler diagnostics and swap ceilings — October 29, 2026

The owner requested better sampler diagnostics and a fresh Strata Qwen update retry, retaining the performance tolerance and setting swap-write/combined-I/O ceilings to 128/160 MiB/s. Implementation and 217 focused CPU regressions per checkout are complete; the guarded GPU retry is next. No new Strata promotion is claimed yet.

## Current policy: loading-swap-v4

The owner-requested default permits loading and parked swap without occupancy or cumulative-write caps. During uninterrupted inference, each complete rolling window of at least 30 seconds allows **128 MiB/s swap writes** and **160 MiB/s combined swap reads+writes**. Equality passes; sustained excess fails. Shorter bursts do not establish a complete sustained window. Combined-I/O is an explicit owner-requested operational ceiling, including reads; it is not evidence of SSD damage. PSI alone remains advisory. Independent physical-RAM, RAM-cap, VRAM reserve/spill, ownership and thermal protections remain.

The performance comparator is unchanged: prefill and code/prose decode at least 95% of the same-run production baseline, the existing short-TTFT bound, all required markers, full model coverage and valid per-model plus launch-through-shutdown memory evidence. No telemetry failure is ignored. Historical policies, including v3, require `LOCAL_LLM_LEGACY_SWAP_VALIDATION=1`; an inherited old policy value alone cannot silently replace the current ceilings. Older numeric results retain their recorded policy and are not requalified under v4.

The existing updater unit explicitly selects v4 and retains its 10-hour oneshot timeout and graceful rollback handling. Its 03:00 full-registry schedule and recovery service remain enabled. The temporary manual retry will target only Strata Qwen, with `--retry-rejected`; Strata DeepSeek and other RAM-held components are not retried.

## What the diagnostics now preserve

Worker sample failures retain a UTC timestamp, monotonic time, sample-attempt index, phase, reader stage, PID, numeric file descriptor where applicable, exception type, exact known missing-counter key and sanitized traceback file/function/line references. Records are bounded to 8 details with an overflow count. Arbitrary messages, full paths, command lines, process contents and local variables are excluded; unrecognized key text is redacted. Raw runtime diagnostic records remain private.

The sampler still rejects unreadable live counters and incomplete evidence. Confirmed exited/zombie processes remain normal skips. The snapshot returned after monitoring is detached from internal state. No error is silently converted into zero swap/spill.

The original rejected candidate had 262 successful lifecycle worker samples, one `KeyError`, zero per-model errors and no observed worker swap/VRAM spill. Its performance and all three markers passed. The old collector omitted the missing key, PID, timestamp, phase and traceback, so that exact old failed sample cannot be reconstructed. Its rejection, measurements and verified rollback remain preserved; the new run uses fresh evidence.

## SSD evidence and limits

Swap is on a Crucial P3 Plus 1TB, model `CT1000P3PSSD8`, rated **220 TBW**. Before the retry, refreshed read-only NVMe SMART reports **3% endurance used**, approximately **7.99 TB lifetime host writes**, **zero media errors**, no critical warning and approximately 31–32°C. Historical controller error-log count is 66,051; this counter alone does not identify media damage. Source: [manufacturer endurance specification](https://www.crucial.com/content/dam/crucial/ssd-products/p3-plus/flyers/b2c/crucial-p3plus-productflyer-consumer.pdf).

The new rate ceilings are not SSD lifetime guarantees. Continuous 128 MiB/s host writes would total approximately 11.6 TB/day; actual duration and total writes determine wear. This task records fresh SMART and device-write counters before/after qualification, without running a disk benchmark, a self-test, changing swap devices or inventing a daily write budget. Host swap/disk counters include unrelated activity and do not attribute every byte to Strata.

## Verification and current status

**217 focused CPU regressions pass in each maintained checkout.** They cover exact ceiling equality/one-byte-over cases, separate combined-I/O enforcement, loading/parked swap, incomplete windows, forged/missing rate metadata, historical-policy replay, owned-worker-only enforcement, unchanged dedicated-VRAM protection, exact diagnostic context, redaction/bounds, source holds, comparator performance rejection and rollback. Two stale pre-existing fixtures were repaired: the benchmark fixture now verifies its already-deployed real untimed observation probes without changing timed trial counts, and the Strata startup fixture supplies the configuration file current startup reads. Production headroom thresholds were not changed.

The prior Strata rejected-run evidence was archived before its stage is reset. Current llama.cpp remains `eb4e244be77a` for Empero/Super/Flint with Ornith independently pinned to `2280f0fd163b`; vLLM remains dev229 for Qwen/Sage and dev435 for Bolt. No completed Ornith or unrelated GPU benchmark is repeated. Final retry outcome, diagnostic counters, same-run metrics and SSD write deltas will be added here after all gates and any rollback finish.
