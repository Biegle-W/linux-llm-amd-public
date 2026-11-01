# AMD server catalog and short harness checks — November 1, 2026

**November 1 enabled-model DSH checks:** the seven remaining enabled routes each received one short harness tool-call attempt; combined with the earlier Empero result, **4/8 passed and 4/8 did not pass**. Every tested backend was unloaded. No full-context test, new throughput benchmark, context change or retry. Historical speed figures remain historical; daily updates stay paused. [Per-route results and failures](DSH-ENABLED-TOOL-CHECKS-2026-11-01.md).

## Current owner instruction

DSH presents all enabled local model routes under one provider named **AMD server**.
The shared AMD model hub selects the engine from the model ID. Qwen 27B retains
two clearly named routes because SGLang DFlash2 and vLLM MTP are separate choices.
Engine-specific request compatibility stays on each model. Unrelated providers,
settings and conversation history are preserved. RAM-paused profiles stay paused.
Downloaded experimental variants are not advertised as configured models.

## Testing policy, effective immediately

The owner explicitly stopped routine full-context testing. This policy supersedes
older maintenance instructions requiring near-window, long-history, sustained
inference, repeated benchmark matrices or performance comparisons for ordinary
setup and updates. Retain historical evidence as historical evidence; do not rerun
it. No full-context or long benchmark run without a new explicit owner request.

Calculate a conservative context cap from the installed model architecture,
KV dtype and per-token storage, recurrent/MTP state, engine cache allocation,
weight/expert placement, available physical RAM and each GPU's available VRAM.
Keep desktop/worker/engine headroom, workspace and staging reserves. Do not count
swap as physical RAM or simply add both GPUs' free memory without accounting for
placement/replication. Cap at the model and engine limits; reserve completion
space inside that cap. If fixed weights/expert backing do not fit, reducing
context alone cannot solve admission: retain the hold and report the blocker.
For streaming engines, account for resident KV separately from total context.
Recalculate after an actual hardware or placement change; do not increase a cap
just because an idle snapshot happens to show more free memory.

Current configured caps are retained: Empero 262144; Super IQ3 32768; Flint 32768;
Qwen 27B SGLang and vLLM 163840 each; Bolt 262144; Sage 65536; GLM 32768. These
remain subject to the existing startup RAM/VRAM guards. Paused model profiles
retain their saved settings and are not resumed by this cleanup. Existing engine
allocation evidence provides conservative capacity bounds without a new
long-context inference run. A configured cap is not a quality guarantee.

For model setup, perform only one short tool-call round trip through the actual
harness and normal guarded model route. Use a tiny local fixture, bounded output
(typically 256 tokens per response), one tool execution and its final response;
no padding, near-window input, repeated loops, throughput trial or soak. Record
which harness and model were exercised. A failure is a failure; retain the exact
error rather than retrying into a pass or silently switching harnesses.

Unload the owned model immediately after the check, including failure/timeout.
Use normal activity/startup ownership guards; never interrupt another client or
unload someone else's model. Lightweight CPU configuration/schema checks remain
appropriate for code changes and do not load a model.

A short pass covers that specific tool round trip. It does not certify full-window
recall, arbitrary tools, other harnesses, intermittent failures or all models.
Reproduce a reported failure with the exact harness/request before claiming a fix.

The daily updater remains paused until the owner explicitly asks to resume it.
This cleanup neither resumes updates nor authorizes the old long benchmark path.

## Verification of this cleanup

Seven focused CPU configuration checks pass per checkout. The running DSH web
selector shows the eight enabled local routes under AMD server and retains the
separate existing cloud account. One actual installed DSH headless session on
Empero completed exactly one `read` tool call, consumed its result and returned
the fixture marker. The two short model responses totalled 85 generated tokens;
no padded prompt, context-filling request or repeat trial was used. The owned
backend was stopped afterward and both GPUs returned to idle VRAM usage.
Other models and other harnesses were not retested in this cleanup.
