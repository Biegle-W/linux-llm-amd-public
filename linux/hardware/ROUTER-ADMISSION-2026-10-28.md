# AMD router admission, health and transport — October 28, 2026

Implemented and validated the requested AMD adaptation of the pinned NVIDIA
router work. The code is now active in the production hub/gateway after the
user-authorized idle restart. Earlier validation used temporary authenticated
loopback coordinators and preserved production processes; this activation was
performed separately after the user's explicit restart request.

## Admission and AMD capacity

All five AMD backend routers serialize their full inference response with their
existing request lock: `dsh/llama-router.py`, `sglang-router.py`, `vllm-router.py`,
`strata-router.py` and `maya-router.py`. Native llama.cpp/Strata/Maya profiles also
specify `parallel=1`; the tested Sage vLLM launcher keeps `max_num_seqs=1`.
The effective qualified execution capacity is therefore **one request**, not an
unbounded number of requests blocked inside a backend. No engine limit changed.
The gate supports a future explicitly qualified capacity, tested with CPU fixtures;
that is not qualification or activation of parallel backend execution.

The pending bound is derived from AMD's **12 enabled catalog profiles** (4 llama.cpp,
3 vLLM, 1 SGLang, 2 Strata, 2 Maya): one shared FIFO position per enabled profile,
not reserved per model. The catalog count determines the count bound. A separate
**32 MiB total pending-body budget** prevents twelve maximum-size bodies accumulating
inside this queue. A single HTTP request remains capped at 32 MiB. These are hub
admission limits, not a total HTTP listener/thread/body-buffer memory quota.

A full count or byte queue returns HTTP **429**, `queue_full`, and `Retry-After: 5`.
Queue wait expiration returns **503**, `queue_timeout`, with the same retry hint.
Streams already sent HTTP 200 for loading keep-alives; they carry the error status,
code and message in SSE followed by `[DONE]` instead. The unchanged drain wait is
900 seconds and guarded backend start timeout is 1800 seconds.

Tickets enter FIFO atomically. Later same-model traffic cannot pass an earlier
model switch. A switch waits for every admitted old-model reply to drain, including
when the backend kind is unchanged. Failed, expired and disconnected waiters release
their queue count/bytes. Gateway disconnect propagation also removes a nonstream
waiter while it is waiting for hub headers. Cancelling a startup wait does not kill
a launcher-owned backend. Idle teardown cannot claim the hub ahead of queued work.
Readiness probes, client checks and loading writes run outside the condition lock.

## Health and error behavior

Authenticated gateway `/health` relays the hub's single synchronized snapshot:
active backend/model, loading model, switching, in-flight count, queued count/bytes,
effective capacities, queue limits and 600-second idle timeout. Reservation is a
boolean; owner strings and private paths are excluded. `status: ok` describes the
coordinator. Active model identifies its most recently admitted target, not an
independent native-worker readiness assertion. Loading remains visible while the
backend router loads the worker before response headers. Health/catalog reads do
not load a model or update inference activity. The hub remains loopback-only;
the gateway keeps its existing bearer and network allowlist checks.

Backend nonstream HTTP status, JSON error code/type/message and useful plaintext
are retained. JSON remains valid after redaction. After streaming headers, HTTP
errors become SSE with their original status and fields; native error events also
retain status/code/message, including named error events and numeric OpenAI error
codes. Missing native status defaults to 502. Interrupted/truncated streams emit a
transport error and finish with `[DONE]`. Successful alias/tool-call events pass
byte for byte across arbitrary chunk boundaries. External bearer headers stay at
the gateway; workers receive only the existing loopback body/content type. Error
redaction covers the external key, bearer/credential fields and private paths.
No body or credential logging was added.

## Validation and limits

**71 focused CPU regressions per maintained checkout**: 45 new admission/HTTP/SSE
checks, 9 existing hub tests and 17 idle/ownership tests. They cover FIFO pressure,
same-backend model drain, count/byte backpressure, cancellation, queue/start timeout,
startup failure, GPU reservation, cancelled-launch ownership, idle races, loading
health, authentication, no-read activity, HTTP/plaintext errors, error SSE, aliases,
tool-call deltas and credential isolation. Chunk-boundary fixtures exercise each
split of a successful tool-call event. No GPU throughput/quality test was repeated.

Two sequential **32-output-token maximum** requests used `sage-a1.5` through the new
authenticated temporary loopback gateway/hub and unchanged normal guarded vLLM
launcher. Both returned HTTP 200 and `ROUTER_OK`; SSE included `[DONE]`.

| Request | Elapsed seconds | Response bytes | Interpretation |
|---|---:|---:|---|
| JSON | 114.305 | 755 | Includes cold backend/worker startup; not a TTFT benchmark |
| SSE | 0.137 | 884 | Warm transport smoke; not a throughput benchmark |

Final candidate health: **0 in-flight, 0 queued, 0 queued bytes**, no loading/switching.
Production coordinator identities match before/after; temporary coordinators were
removed. The normal launcher-owned Sage backend was left to the existing 600-second
inference-aware idle release. There is no task-owned GPU reservation or unfinished
inference request. All **16 profile/guard/lifecycle fingerprints** match; engine
pins, native concurrency, contexts, precision/cache settings, startup/idle ownership,
RAM/VRAM/thermal protections, loading-swap-v3 and paused schedules are preserved.
No broader model/concurrency/near-window qualification is implied by these smokes.

The first CPU fixture run had an incorrect mock catalog filename; it was corrected
before the passing runs. Completed GPU inference was not rerun for that fixture
repair or the later CPU-only SSE error variants.

[Numeric evidence](results/router-admission-2026-10-28.json) records counts, bounds,
smoke timings/checks and preservation. Exact private/public source preimages are
hash-verified in the private retired-source archive with repository/commit/blob/mode
provenance; raw logs, credentials and workflow records are excluded from publication.

## Reference and next action

Adapted from NVIDIA public commit
[`06819c56bae8cbd70768d8376464681e191fffd1`](https://github.com/Biegle-W/linux-llm-nvidia-public/commit/06819c56bae8cbd70768d8376464681e191fffd1),
particularly [admission](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/06819c56bae8cbd70768d8376464681e191fffd1/network/request_admission.py),
[transport](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/06819c56bae8cbd70768d8376464681e191fffd1/network/backend_proxy.py)
and the [design report](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/06819c56bae8cbd70768d8376464681e191fffd1/docs/ROUTER-IMPROVEMENTS-20261028.md).
AMD uses its own 12-profile/32 MiB pending policy; NVIDIA's eight-waiter setting,
desktop controls and host runtime settings were not imported. NVIDIA's reported
tests are reference evidence, not AMD qualification.

## Production activation

Completed at 2026-10-28 19:01:11 EDT after the user authorized an idle-only
restart. Both services were idle: no in-flight/queued work, established API client,
GPU reservation, backend owner or KFD client. The existing request/start locks
protected the drain boundary. Gateway ingress was stopped briefly, hub restarted,
then gateway started. Both services are active with new process identities.

Authenticated health returned 200 and matched the hub on all three configured
bindings; missing and invalid bearer keys returned 401 on each. These are host-side
connections to configured bindings, not a new remote-device connectivity test.
All three authenticated catalogs list 12 models. Health/catalog reads leave the
inference activity timestamp unchanged and do not load a model. Live state is
0 in-flight, 0 queued/bytes, no active/loading backend, 1 execution slot, 12 pending
positions, 32 MiB aggregate queued-body limit and 600-second idle timeout.

All 20 checked profile/guard/lifecycle/access/credential/service-file fingerprints
match before and after. Updater service remains inactive; its timer is not installed
and no schedule was changed. No inference or GPU test was rerun for activation.
No router activation work remains; keep the qualified settings and all guards.
