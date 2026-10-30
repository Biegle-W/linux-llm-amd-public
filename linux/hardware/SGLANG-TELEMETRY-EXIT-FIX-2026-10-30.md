# SGLang stream interruption: process-exit telemetry race — October 30, 2026

The SGLang router's memory sampler is corrected and active after a scoped router restart. Five small streaming requests pass through the normal authenticated API. All 179 relevant CPU/ownership regressions pass in each checkout. This is a functional repair, with no new performance or full-context qualification claim.

## Incident and reproduction

At 03:06:42 EDT, the router logged `Owned-worker fault sample: null` followed by `telemetry_error:KeyError` and requested its worker's shutdown. The backend had become ready and served successful requests before the stop. The client consequently lost an active stream. The original log retained the exception class only, so its precise missing key cannot be recovered retroactively.

A controlled CPU child-exit reproduction against the original sampler immediately raises `KeyError: 'VmSwap'` at the same sampling path. Captured proc status still says `R`, while the subsequent stat read confirms Linux `PF_EXITING`. The sampler's earlier zombie-only check misses this interval: `proc_pid_status` obtains task state and address-space data separately, and an exiting child may have already released its address space. This is a reproduced explanation consistent with the incident; it is not an out-of-memory diagnosis.

Kernel references: [proc status implementation](https://github.com/torvalds/linux/blob/master/fs/proc/array.c), [exit sequence](https://github.com/torvalds/linux/blob/master/kernel/exit.c), and [task flags](https://github.com/torvalds/linux/blob/master/include/linux/sched.h). The installed Linux 7.0 headers confirm `PF_EXITING = 0x00000004`.

## Repair and protection

`hardware/inference_memory.py` checks proc stat only when VmSwap is absent. It skips that snapshot member only if the original identity has disappeared or changed, or if the kernel confirms terminal state or PF_EXITING. A live process with an unexplained missing counter remains an error. Malformed or unreadable identity data also remains an error. It does not substitute a zero counter.

The router now retains sanitized missing-key, reader, PID/FD and source-frame details when telemetry fails. The shared monitor uses the same formatter. Unknown keys are redacted; messages, full paths, request bodies and local variables are excluded.

Actual VRAM eviction, physical-memory admission, host pressure, owned-worker containment, swap policy and rate thresholds are unchanged. A fixture confirms that an exiting child cannot hide a surviving worker's swap or eviction. No model profile, runtime pin, context window or timeout was changed.

## Verification and limits

- Original CPU reproduction fails immediately with missing VmSwap. The patched sampler completes 120 child exits and 3,600 samples with zero failures.
- Both maintained checkouts pass 179 relevant CPU/ownership checks, covering telemetry diagnostics, missing live counters, DRM accounting, process containment, loading/serving swap behavior and existing memory guards.
- The idle fault-latched router was retired, and the normal API launcher loaded the corrected sampler. Five authenticated SSE requests completed with HTTP 200, a finish reason and `[DONE]`. The first includes normal cold loading; later requests use the same healthy worker.
- The existing DSH HTTP-activity repair remains active. The user's original DSH conversation itself was not replayed; these requests verify the repaired backend/API path.
- The nightly updater was left running in its existing client-inactivity wait; no reservation was stolen and no job was restarted. An already-running Python process retains its imported code until its next normal launch.
- Super INT4 and all owner-held model trials remain waiting for the owner's RAM update. Completed 160K, all-model and H3 qualification is not repeated.

Curated evidence: [results](results/sglang-telemetry-exit-fix-2026-10-30.json). If another stream fails, use the new sanitized fault details and the request's time/model; do not weaken memory protection to clear the error.
