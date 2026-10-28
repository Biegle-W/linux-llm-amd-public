# H3 comparison after the RAM upgrade — October 28, 2026

Linux now exposes **30.56 GiB RAM**, up from **14.83 GiB** before the reboot. This is a physical MemTotal increase; the prior measurements retain their original hardware attribution. The full matched comparison did not complete. Keep the saved production workflow. Partial successful generations and failed attempts are retained; no SP2 speedup or production qualification is claimed.

## Workload and results

The experiment began October 27 and continued across local midnight; this report is dated October 28. Python 3.12.14 and Torch 2.15.0.dev20260827+rocm7.2 are retained. All 1,303 tracked ComfyUI source files in the isolated snapshot match the installed core; the observer is a separate private custom node.

The saved current workflow and isolated ComfyUI 0.42.0 / 8f04fd6e compatibility pilot use the same INT8 FL2VA checkpoints, 608×352, 39 frames, 24 fps, 20 steps, seed 42 and audio. Each arm targets one excluded full warmup followed by three timed full requests. Cache-disabled component loading is included in full-request timing. An unsuccessful or incomplete arm has no three-trial median.

| Arm | Outcome | Completed generations | Median server full request s | Median sampler span s | Lowest available RAM GiB | Peak worker swap GiB | Guard faults |
|---|---|---:|---:|---:|---:|---:|---|
| control | guard_stopped | 2/4 | not measured | not measured | 3.125 | 6.643 | swap_activity_inference_swap_io_rate |
| sp2 | guard_stopped | 0/4 | not measured | not measured | 2.673 | 6.288 | host_available_below_3GiB |

Sampler spans are instrumented wall times around the sampler call; nested loading is separately phase-tagged. They are not pure GPU-kernel timings. The numeric record retains all per-trial server/external times and observed phase spans; failed lifecycle duration is not generation latency. Component decode spans are recorded separately. No LLM prefill, TTFT, token decode or context limit applies to this diffusion workload. The four shared H3 model files and storage attribution remain in the [earlier H3 report](H3-SP2-2026-10-27.md).

## Exact outcomes and retained interruptions

The control completed warmup **196.228 s** and one timed full request **210.098 s**. Their closed sampler spans are **29.590 s** and **28.324 s**; these two values are not a three-trial median. The next timed request stopped during denoising when a complete active window measured **14.874 MiB/s combined swap I/O**, above the unchanged 8 MiB/s limit. Swapout in that evaluated window was only **0.001549 MiB/s**: the stop concerns active paging reads/combined churn, not a loading-write or parked-swap cap. All control outputs up to the failed request are preserved.

The SP2 retry reached the isolated loader's 8 GiB activation reservation and rank-1 process startup. It crossed the 3 GiB physical available-RAM floor at **2.673 GiB**, before a ready distributed model or any denoising. No SP2 generation completed, so there is no SP2 decode/quality result, no matched three-trial comparison and no measured SP2 speedup. The 32 GB configuration has not qualified this workload.

An earlier SP2 attempt was interrupted by a three-second client history-poll timeout during text-encoder loading, without a hardware guard fault. It is recorded separately as a harness interruption. The fresh SP2-only retry tolerates transient history-request errors within the original 1,800-second workflow deadline; hardware guards are unchanged. It required no transient poll retries before its substantive RAM stop. No control failure was discarded or rerun.

Sampled GPU hotspot peaks were **75/57°C** for control and **37/53°C** for the SP2 retry; CPU package peaks were **78°C** and **82°C**. Thermal/SMU flag counts are retained as reported samples, not measured time throttled. Owned dedicated-VRAM spill remained zero. Both scopes verify unlimited swap occupancy and preserve the physical-RAM/VRAM limits.


## Policy, evidence and limitations

Loading swap and parked swap pages are allowed. The fresh harness verifies `memory.swap.max=max`, retains the host-sized worker RAM cap, immediate 3 GiB available-RAM floor, 2 GiB free-VRAM/four-sample limit, hard 1.5 GiB VRAM floor, zero dedicated-VRAM spill and the unchanged 8 GiB SP2 activation reserve. GPU-LOCK, the Comfy server lock, owned-scope cleanup, thermal monitoring and the common short disk-backed compiler temporary directory cover both arms.

Active text encoding, denoising and VAE decoding are observed through source-only wrappers; nested `load_models_gpu` is loading and resets inference rate windows. They do not change model calculations. Maintained `loading-swap-v2` monitoring applies the 30-second 1 MiB/s swapout and 8 MiB/s combined-I/O limits, plus full-memory PSI above 10% for three active samples. System swap counters include unrelated work and cannot attribute every byte to H3.

control: swap-evidence validation reports inference_swap_io_rate; sp2: no complete continuous 30-second active-compute window was sampled; sustained-churn qualification is incomplete; sp2: swap-evidence validation reports no_inference_window.

Completed output validation covers **2 files**: full video/audio decoding, dimensions, frame count, frame rate, duration, stereo audio, finite PCM samples and nonzero audio energy. Sampled visual review is recorded in the numeric evidence. Audio content was not semantically auditioned. Failed arms without output have no media-quality result.

**20 maintained swap-policy CPU tests** and the nested instrumentation boundary check pass. The first repository-local test attempt could not create temporary files in the read-only sandbox; exact copies passed in writable scratch. No production source, checkpoint, workflow, model precision, context, engine pin, default, guard or schedule changed. Qwen/Sage remain vLLM dev602, Bolt remains explicitly dev435, Sage remains text-only, and the updater stays paused. Earlier LLM speeds were not rerun or reattributed to this RAM configuration. Historical holds are not automatically lifted by adding RAM.

All owned workers are stopped, GPU-LOCK is released, and production configuration fingerprints match. The previously paused H3 follow-up remains paused, avoiding an automatic duplicate. No task-owned runtime or lock remains. The concrete next step is to use the recorded outcome and exact blocker, if any, before proposing another H3 change; do not repeat this comparison solely to refresh documentation.

[Numeric results and media checks](../hardware/results/h3-post-upgrade-2026-10-28.json) · [current LLM results](../hardware/CURRENT-AMD-BENCHMARKS.md) · [swap policy](../hardware/LOADING-SWAP-POLICY-2026-10-27.md).
