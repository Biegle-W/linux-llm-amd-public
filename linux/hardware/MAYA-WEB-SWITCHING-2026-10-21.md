# Maya web model switching and DSH reuse — October 21, 2026

Maya’s existing browser page now has **Maya model → Switch model** in its sidebar.
Choose `glm-5.3-flash-maya` or `deepseek-v4.1-flash-1017-maya`. Wait for **Loaded**
before chatting. Finish or cancel an active answer before switching. Loading
errors stay visible; after freeing the required memory, explicitly retry.
The page and its pinned assets stay available while the single worker reloads.
Native model-specific sampling/context refresh after readiness; browser chats
and an unsent draft survive the switch without a page reload.

Start with the Maya Desktop shortcut or `llm-maya`. Desktop shortcuts remain web
interfaces, application-menu entries remain native desktop applications. No new
menu entry, second engine or model copy is installed. `--no-browser` and headless
SSH behavior remain supported; DSH stays separate.

## Implementation and boundaries

- The original pinned Maya page/assets are served by a persistent local
  [web adapter](../dsh/maya_web.py) with a small
  [selector](../dsh/maya-model-switch.js). Browser URL remains loopback30031;
  the OpenAI router remains30030; its private native worker now uses30032.
- The selector submits only an enabled profile ID to the existing guarded
  `ensure_worker` path in [the router](../dsh/maya-router.py). The existing
  chat lock serializes switching and native chat. Background busy/queued work
  also rejects a switch. Cancellation can still reach an active stream.
- Strict loopback Host/same-origin checks, bounded JSON and existing configured
  native API-key requirements protect management requests. Cross-origin requests,
  unknown profiles and runtime/config overrides are rejected. Arbitrary native
  load/unload, context/config changes and self-updates remain blocked.
- GLM-S v2 and DeepSeek-S stay at32K, on **both RX7900XTX**, source3384b5e/v1.1.19,
  ROCm7.2.3. GLM40GiB/MTP and DeepSeek24threads/noDSpark/`DS4_IQ_Q8K=0`/
  `DS4_STREAM=0` remain unchanged. Profile/catalog/runtime hashes are unchanged.
  Native8GiB/card reserves, actual>=6GiB/card startup,52GiB available host admission,
  52G/no-swap worker scope and continuous latched watchdogs are retained.

DSH startup formerly treated its own occupied3080 frontend port as an inference
worker and told the user to close a backend terminal. Reopening it now verifies
this installation’s exact Node web command and socket ownership, reopens that
frontend and exits successfully. It never starts/stops inference during reuse.
An unrelated3080 listener still produces a clear conflict error and is never
terminated. [Recognition](../dsh/dsh_frontend.py), [startup](../dsh/start-dsh.py).

## Validation and limits

[Numeric functional evidence](results/maya-web-switching-2026-10-21.json) records
normal managed-launcher GLM → DeepSeek → GLM loads, native streaming and
busy-switch rejection, persistent controller/page availability, both-card startup
headroom, owned memory/scope checks and unchanged profile/runtime fingerprints.
Browser checks cover the actual selector, progress, native model/context refresh
and unsent-draft retention. The owned test worker is stopped after validation;
DSH and the gateway are preserved.

Both repositories pass108 CPU/HTTP regressions. Tests include unloaded-worker
assets/catalog, request authentication/origin/body boundaries, no configuration
overrides, switch failure/retry and busy-job serialization, plus exact DSH reuse.
PATH wrappers remain unchanged and resolve in login/noninteractive shells.
Authenticated gateway health/10-profile catalogs pass on loopback and host-self
LAN/Tailscale routes; a separate remote peer is not tested. No new ports are
exposed remotely. Native vision quality is outside this test.

Earlier startup attempts correctly refused insufficient available RAM; guards
were not lowered. Development-only frontend asset/routing issues were corrected
before the final switch checks. Raw logs and chats stay private and ignored.
The normal launcher records1s GPU/CPU thermals over the final worker lifecycle;
coverage and sampled peaks are in the numeric record, with unavailable sensors
explicit. One-second sampling can miss brief peaks and does not establish a
speed loss. No throughput benchmark, engine update or context extension is
claimed; [October20 measurements](MAYA-ROCM10-2026-10-20.md) retain their original
builds and workload definitions.

## Recorded memory and temperatures

The final lifecycle has 300 one-second thermal samples, no sampler errors or
dropped raw samples. GPU0/GPU1 sampled hotspot peaks were **52/50°C**, memory
**48/58°C**, and CPU package **81°C**. Both cards had all three temperature
sensors covered. Other CPU/board temperature sensors were not collected.
Reported SMU limit flags are retained numerically and are not evidence of a
measured performance penalty.

The separate memory observer has 183 samples, no read errors; coverage starts
during DeepSeek load and includes the GLM return. Native worker swap/spill and
scope swap remained zero. Small control-plane Python pages reached
**24.08 MiB swap**, outside the native worker’s52G/no-swap scope; this is
recorded separately rather than counted as model-worker residency. Exact startup
VRAM and sampled RAM/VRAM minima are in the numeric record.
