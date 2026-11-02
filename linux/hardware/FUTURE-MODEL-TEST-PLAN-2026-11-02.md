# Future model checks and benchmark guardrails — November 2, 2026

The normal sequence is **admit one model → one short harness tool round trip →
unload and verify release → switch to the next model**. Apply this to future
model additions and authorized updates. The existing benchmark speeds remain
dated measurements; this plan does not request another benchmark sweep.

## Before loading

1. Select the exact model ID, quantization, engine/build, profile and harness/version.
   Default to the installed DSH harness through **AMD server**. If another harness
   is requested, record it separately; a DSH pass does not establish its behavior.
   Use only the requested models and enabled routes. RAM-held models require the
   owner's hardware update and instruction before testing; do not auto-resume them.
2. Confirm the hub has no in-flight/queued client work, identify any current owner,
   and acquire the existing startup/ownership reservation. If another client owns
   a model or request, defer the check. Do not kill unrelated apps to make room.
3. Record physical MemTotal, MemAvailable, each GPU's dedicated VRAM total/free,
   swap capacity/usage, runtime limits and guard configuration. Calculate the
   context cap from weights/expert placement, full versus resident KV, dtype,
   MTP/recurrent state, workspace/staging and desktop reserves. Swap is not RAM;
   free VRAM on separate cards is not interchangeable capacity. Reserve output
   tokens within the cap. Keep existing caps unless separately justified.
4. Use normal guarded admission. Missing required telemetry or failed RAM/VRAM
   admission means blocked, not passed. Preserve pins, holds, cgroup limits,
   eviction protection and phase-aware swap policy. Save the exact applicable
   guard values and source revision with the run; the catalog below is a dated
   source review, not a replacement for reading the actual selected profile.

## One bounded tool-call check

Create a tiny local file containing a unique marker. In a fresh harness session,
ask the selected model to read that exact file using the harness's normal `read`
tool and return the marker. Supply the exact path so discovery tools are unnecessary.
Keep the ordinary harness system prompt and tool schema; do not substitute a raw
API tool stub or a smaller harness and claim the original harness passed.

Allow **one model tool call, its actual execution/result and one final model
response**, at most two model responses. Cap each response at 256 generated tokens,
including reasoning where the engine supports that accounting. Retain any existing
model reasoning cap. Stop on an extra tool call, malformed arguments, tool error,
timeout, guard trip or incorrect/missing marker. Record the actual input, output,
reasoning tokens and tool count where available; do not turn a missing counter
into zero. No silent retry, alternate engine/harness or settings change to obtain
a pass. A later requested repair gets a separately identified attempt.

Use the established short-check deadlines: router readiness 90 seconds and harness
240 seconds, each from its recorded start, with cold/on-demand loading included
when it occurs in that phase. Do not silently extend a deadline to fit a slow
load. Distinguish blocked startup, readiness timeout, harness timeout, tool failure,
guard stop and wrong final answer. A timeout does not prove tool incompatibility.
There is no padded prompt, context filling, throughput loop, soak or extra
30-second inference merely to collect a swap window.

## Unload, then switch

Run owned cleanup after every outcome, including failed admission and cancellation.
Finish/cancel the test request, use the existing managed stop/unload path and verify
the **owned cgroup is empty**, worker identity/port is gone and model ownership is
released. Record post-unload MemAvailable, per-card VRAM and swap usage against the
pre-load baseline. File cache and desktop activity can change those readings;
identical numbers are not required and a VRAM snapshot alone is not ownership proof.

Allow up to 60 seconds for cleanup verification as a test-run deadline; retain the
existing managed stop semantics. If release cannot be verified, mark cleanup failed
and **stop the sequence**. Do not load the next model over an unverified worker.
After successful cleanup, release only the test's reservation and admit the next
requested model afresh. The final model is also unloaded; do not leave it resident
or reload the previous model just to end the run.

## Required result and benchmark fields

Keep previous prefill, TTFT and code/prose decode fields with their original
date/build/hardware and test method. New short checks add a separate functional
result; they do not replace old speeds with estimated throughput.

| Field group | Required record |
|---|---|
| Identity | Timestamp; model/quant; engine/build/profile; harness/version; actual route; configured and calculated context cap; actual input/output/tool counts |
| Tool result | One requested tool, matching call/result ID, marker verified, status and exact failure/deadline; no retry count hidden |
| RAM | Physical total; available before/load minimum/after unload; sampled worker RSS or cgroup memory peak with metric name; admission requirement, runtime floor and cgroup high/max; unavailable measurements explicit |
| VRAM | Per-GPU total, start free, minimum free and peak used; startup admission versus post-load reserve; soft/hard thresholds and debounce; owned eviction/spill bytes and telemetry availability |
| Swap | Policy/version; allowed phases; occupancy baseline/peak/final; host swap-in/out deltas and observed rates; owned worker swap peak; 30-second inference windows evaluated or insufficient coverage |
| Cleanup | Owned cgroup empty, worker/port gone, owner/reservation released, post-unload memory, next-model start allowed; failed cleanup stops sequence |
| Coverage | Sampling interval, phases/duration, sensor gaps, sampled thermal peaks and flags; short functional scope only |

Host swap I/O is system-wide and must not be presented as worker-attributed I/O.
Under current `loading-swap-v4`, loading/parked swap is allowed. Inference ceilings
are **128 MiB/s writes and 160 MiB/s combined reads+writes over complete 30-second
windows**. Occupancy and PSI alone do not fail a check. A shorter successful check
records **insufficient window coverage**, not a passed sustained-swap qualification.
Never disable the collector or stretch the check to manufacture that verdict.

## Current normal-route guard catalog

All capacities below are GiB (binary); swap rates are MiB/s. `total/available`
means separate pre-load physical RAM gates. VRAM values apply to **each** card.
These are November 2 source annotations alongside older benchmark listings,
not newly measured memory use and not retroactive guard changes to old trials.
Historical isolated arms keep their original limits in the dated report/JSON.

| Normal route | RAM admission / worker limits | VRAM admission / runtime protection | Swap |
|---|---|---|---|
| Empero / llama.cpp | ≥12 total, ≥7 available; worker high/max 4/5; runtime available floor 3 | ≥21 free before load; runtime 3 soft (2 samples), 1.5 hard; zero owned spill | v4: 128 write / 160 combined, 30 s |
| Flint / llama.cpp | ≥12 total, ≥7 available; worker high/max 4/5; runtime available floor 3 | ≥21 free before load; runtime 3 soft (2 samples), 1.5 hard; zero owned spill | v4: 128 / 160, 30 s |
| Super IQ3 / llama.cpp | ≥28 total; available ≥host experts +4 = 23.124 (rounded up); runtime available floor 3 (3 samples) | ≥21 free before load; runtime ≥3 (3 low samples); zero owned spill through the shared lifecycle guard | v4: 128 / 160, 30 s |
| Ornith / llama.cpp, held | ≥60 total; available ≥host experts +4 = 45.0625; runtime available floor 3 (3 samples) | ≥21 free before load; runtime ≥3 (3 low samples); zero owned spill through the shared lifecycle guard | v4: 128 / 160, 30 s |
| Qwen 27B / vLLM | Engine allocation/admission; no separate numeric host-RAM gate in this route; calculate physical fit before test | ≥21 free before load; allocation fraction 0.82; zero owned eviction/spill | v4: 128 / 160, 30 s |
| Sage / vLLM | Engine allocation/admission; no separate numeric host-RAM gate in this route; calculate physical fit before test | ≥21 free before load; allocation fraction 0.82; zero owned eviction/spill | v4: 128 / 160, 30 s |
| Bolt / vLLM | Engine allocation/admission; no separate numeric host-RAM gate in this route; calculate physical fit before test | ≥22 free before load; allocation fraction 0.94; zero owned eviction/spill | v4: 128 / 160, 30 s |
| Qwen 27B / SGLang DFlash2 | Engine allocation/admission; no separate numeric host-RAM gate in this route; calculate physical fit before test | ≥22.75 free before load; allocation fraction 0.85; zero actual eviction/spill, not requested/unbacked buffers | v4: 128 / 160, 30 s |
| GLM / Maya, bounded 32 GB tier | ≥29 total, ≥23 available; worker high/max 18/20; native RAM headroom 12; runtime available floor 3 | ≥16 free before load; engine reserve 8; runtime 3 soft (2 samples), 1.5 hard; zero owned spill through the shared lifecycle guard | v4: 128 / 160, 30 s |
| Qwen Flash Next / Strata, held bounded tier | ≥29 total, ≥25 available (also expert budget + full host KV +6); worker high/max 20/22; runtime available floor 3 | Engine reserve 7 initial /8 later (minimum allowed 6); loaded startup free ≥5; runtime 3 soft (2 samples), 1.5 hard; zero owned spill through the shared lifecycle guard | v4: 128 / 160, 30 s |
| DeepSeek XS / Maya, held retained tier | ≥60 total, ≥52 available; worker max 52; runtime available floor 3 | ≥16 free before load; runtime 3 soft (2 samples), 1.5 hard; zero owned spill through the shared lifecycle guard | v4: 128 / 160, 30 s |
| DeepSeek XS / Strata, held retained tier | ≥60 total, ≥52 available; worker max 52; runtime available floor 3 | ≥16 free before load; profile startup reserve 6; loaded startup free ≥5; runtime 3 soft (2 samples), 1.5 hard; zero owned spill | v4: 128 / 160, 30 s |

The shared streaming/VRAM-only runtime host floor is 3 consecutive low samples.
Other debounces are stated above. Framework routes retain their actual engine
allocation and eviction/swap guards; an allocation fraction is not a guaranteed
free-VRAM runtime floor. Do not copy another engine's numeric thresholds into them.
Unavailable live telemetry follows the existing route-specific fail-closed rules.
The shared `WorkerSwapGuard` enforces zero owned eviction/spill on all normal
routes. Additional native CPU-MoE/streaming memory watchers have 256 MiB spill
thresholds; those secondary thresholds do not permit spill past the stricter
shared lifecycle guard.

Source of truth: [MoE profiles](../dsh/moe-offload.json),
[MoE guard](../dsh/moe_memory.py), [vLLM profiles](../dsh/vllm-profiles.json),
[SGLang profiles](../dsh/sglang-profiles.json),
[ROCm admission](../dsh/rocm_runtime.py),
[streaming limits](../dsh/streaming_memory.py),
[streaming/VRAM runtime guard](../dsh/strata_memory.py),
[Strata admission](../dsh/strata_runtime.py),
[Maya admission](../dsh/maya_runtime.py),
[DeepSeek Strata admission](../dsh/strata_ds41_runtime.py),
[owned swap/lifecycle guard](../dsh/inference_swap.py),
[memory/eviction collector](inference_memory.py) and
[swap policy](swap_activity.py). Exact source hashes and the reusable result
template are in [structured policy](results/future-model-test-plan-2026-11-02.json).

## Status

Documentation/source review only. No model was loaded, unloaded or switched by
creating this plan. No new functional result, throughput or memory peak is claimed.
Daily updates remain paused; no recurring test schedule is created. Existing
November 1 results remain 4/8 passed, 4/8 did not pass, all tested workers unloaded.

[Prior policy](SHORT-HARNESS-TEST-POLICY-2026-11-01.md) ·
[Previous tool checks](DSH-ENABLED-TOOL-CHECKS-2026-11-01.md) ·
[Current benchmark listings](CURRENT-AMD-BENCHMARKS.md)
