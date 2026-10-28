# AMD agent request: adopt useful NVIDIA router improvements

User instruction, October 28, 2026: apply the useful NVIDIA router improvements
to AMD — fair bounded queuing, clearer health reporting and backend errors —
while keeping AMD API-only and preserving every existing guard.

Status: implemented and validated in AMD source. See
[AMD admission/health/transport report](../hardware/ROUTER-ADMISSION-2026-10-28.md)
and its numeric evidence. Production coordinators were preserved; new source
awaits an authorized idle restart. The requirements below record the original
request and remain the implementation constraints.

## Requested implementation

1. Add fair, bounded admission around AMD's existing model hub. Make the pending
   queue explicit, avoid starving an earlier model switch behind later same-model
   requests, and remove cancelled, expired or failed waiters reliably. An idle
   teardown must not overtake queued work. Apply backpressure with a clear retryable
   error instead of silently growing the hub's request queue.
2. Expose authenticated, sanitized health information for active/loading/switching
   state, in-flight requests, queued requests, effective capacity and idle timeout.
   Keep gateway and hub status consistent. Health/catalog reads must not load a
   model or count as inference activity. Do not expose credentials or private paths.
3. Preserve backend HTTP status and useful error details, including plain-text
   failures and streamed errors. For streams whose HTTP headers already went out,
   carry status/code/message in the SSE error event and finish cleanly. Keep model
   aliases, tool calls and streaming transport intact; redact secrets and keep
   external bearer credentials at the gateway, out of hub/worker requests and logs.

## AMD-specific constraints

- Keep the external authenticated gateway and loopback model hub API-only. Do not
  import NVIDIA's desktop selectors, native web control routes, console/UI service
  requirements, extra public management endpoints or host-specific listener paths.
  Preserve AMD's existing explicitly configured client/network access policy.
- Derive capacity and queue sizing from AMD's own qualified profiles and resource
  limits. NVIDIA's one-active/eight-waiting policy is a reference example, not a
  setting to copy. Preserve AMD's qualified concurrency and do not increase any
  backend execution limit without separate state-isolation, near-window quality
  and resource validation. Fair switching needs a drain barrier even when a
  qualified backend permits several same-model requests.
- Preserve all current AMD reservations, exact backend ownership, active-reply
  draining, startup/idle locks, memory admission/caps, GPU headroom, thermal and
  telemetry controls, manual runtime pins and paused schedules. Read the latest
  AMD policy and October 28 swap correction; do not transplant NVIDIA's numeric
  reserves/RAM/swap rules or revive superseded AMD swap-rate/PSI stop rules.
- Keep AMD's existing inference-aware idle release and all protected jobs. Do not
  stop current coordinators or repeat completed GPU tests for this port. No model,
  context, precision, cache, engine, mount or schedule promotion is implied.

## Reference and validation

Reviewed NVIDIA source is pinned at public commit `06819c56bae8cbd70768d8376464681e191fffd1`:

- [FIFO admission](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/06819c56bae8cbd70768d8376464681e191fffd1/network/request_admission.py)
- [Backend transport](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/06819c56bae8cbd70768d8376464681e191fffd1/network/backend_proxy.py)
- [Router and health handling](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/06819c56bae8cbd70768d8376464681e191fffd1/network/router.py)
- [Worker lifecycle integration](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/06819c56bae8cbd70768d8376464681e191fffd1/network/worker_manager.py)
- [Admission regression tests](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/06819c56bae8cbd70768d8376464681e191fffd1/tests/test_request_admission.py)
- [Design, constraints and validation report](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/06819c56bae8cbd70768d8376464681e191fffd1/docs/ROUTER-IMPROVEMENTS-20261028.md)

NVIDIA recorded 94 CPU regressions and two sequential, 32-output-token SGLang
transport smoke requests. Those results are NVIDIA evidence, not AMD qualification.
Its first immediate final-health assertion raced asynchronous SSE cleanup; the
read-only follow-up verified release, and successful inference was not repeated.

For AMD, test fairness under continuous same-model traffic, switch draining,
capacity/backpressure, cancellation/timeouts, startup failures, idle races and
reservation/ownership preservation. Test authentication, health behavior,
backend errors/status, aliases, tool-call SSE and credential isolation. Use CPU
fixtures first; perform only the necessary safe AMD normal-path smoke checks.
Keep current profiles and guard values fixed. Record any unsupported or unqualified
concurrency rather than silently enabling it.

At completion, update AMD's canonical README/AGENTS/runtime handoff and applicable
validation evidence; publish reviewed sanitized implementation/reference changes
with independent private/public histories and archive replaced source/settings
privately. The user explicitly authorized relevant maintenance, tests/docs,
commits and normal non-force pushes for the Linux AMD pair, Linux NVIDIA pair
and private retired-llm-setting archive without repeated per-commit confirmation.

Next action: at an authorized idle maintenance boundary, restart production hub
and gateway to adopt the validated installed source, then inspect authenticated
health. Do not rerun completed GPU smoke/benchmark work solely for documentation.
