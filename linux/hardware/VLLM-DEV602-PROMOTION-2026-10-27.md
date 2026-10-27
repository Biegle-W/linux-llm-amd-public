# Conditional vLLM dev602 promotion — October 27, 2026

**Qwen and Sage are promoted to `0.32.1rc1.dev602+g5d35ce393.rocm72`. Bolt remains explicitly pinned to `0.32.1rc1.dev435+gc50aca144.rocm72`.** Bolt passed its earlier 8K performance gates and API checks, but its near 255K active prefill hit the unchanged inference swap-churn guards twice. It is not promoted. No guard or context was relaxed to obtain a pass.

The global installed environment keeps its existing path. Bolt has a separate retained stable environment selected by its normal launcher; an explicit candidate environment override remains available for guarded trials. `manual_runtime_pin` records the hold, and the daily updater excludes held profiles rather than accidentally qualifying their old runtime as a new wheel. The updater remains paused. Other engines, all model weights/quantizations/runtime arguments, twelve-profile catalog and saved Strata default remain. Sage stays text-only.

## VRAM only models

These are the latest selected-runtime performance numbers from completed October27 samples, not a new benchmark rerun. Each complete source benchmark has three code/prose trials and three fresh marker probes after excluded warmups. Prefill E is engine-phase scheduled-to-first-token throughput; TTFT is fresh ~8K request latency excluding loading (Bolt~7.9K). Decode uses the retained SSE method. Context is configured capacity; sizes are decimal allocated associated-file GB. [All numerical evidence](results/vllm-dev602-promotion-2026-10-27.json).

| Model / selected runtime | Prefill t/s | Fresh TTFT s | Decode code/prose t/s | Context tokens | Allocated GB | Storage location |
|---|---:|---:|---:|---:|---:|---|
| Qwen3.8-27B W4A16 · dev602 | 1372.5 E | 6.008 | 140.97/77.73 | 163,840 | 20.05 | System `models/Qwen3.8-27B-W4A16-AutoRound-GPTQ` |
| Nemotron 3.5 Bolt 74B-A9B W4A16 · dev435 held | 2642.4 E | 3.026 | 37.88/37.98 | 262,144 | 43.65 | SATA1 `vLLM-Models/Nemotron-3.5-Bolt-74B-A9B-AutoRound-W4A16` |
| Sage-A1.5 W4A16 AutoRound · dev602 | 5091.7 E | 1.619 | 148.64/139.62 | 65,536 | 20.33 | SATA1 `vLLM-Models/Sage-A1.5-W4A16-AutoRound` |

All three dev602 performance comparisons pass the fixed 95% of baseline prefill and each decode gate, short-TTFT limits, marker and lifecycle memory gates. That alone does not qualify promotion: Bolt's new long-context validation failed. Its dev602 performance-only figures remain preserved in the earlier [loading-swap retry](LOADING-SWAP-RETRY-2026-10-27.md). No universal speedup or equal cold-cache behavior is inferred from small sequential samples.

## New installed validation

Qwen's normal installed dev602 checks completed before the later Bolt stop in the first full attempt. Those completed checks are preserved rather than repeated. Sage completed independently after Bolt's two guarded failures. Final normal routing checks verify the actual mixed-runtime selection: Bolt reports dev435, Qwen reports dev602, native model IDs/context limits are correct, and both pass arithmetic/SSE/fresh ~8K markers plus sustained compute. The API code version omits the wheel's ROCm packaging suffix; exact distribution metadata is checked separately.

| Profile | Selected runtime | New coverage | Outcome |
|---|---|---|---|
| Qwen | dev602 | API/JSON/tools/SSE, 160,851-input ordered retrieval, 160,897-input history, conversation, 36.2s sustained compute; final routing recheck | promoted |
| Sage | dev602 | API/JSON/tools/SSE, 62,009-input ordered retrieval, 62,051-input history, conversation, 35.2s sustained compute | promoted, text-only |
| Bolt | dev435 retained | dev602 arithmetic/JSON/tools/SSE passed; requested near 255K prefill stopped twice. Final dev435 normal-route fresh markers/SSE/compute pass | dev602 not qualified |

Near-window marker/history tests are narrow coverage, not exhaustive full-context or general model quality. Bolt's configured 262,144 limit is retained, but no current-RAM full-window success is claimed. Its earlier successful full-window evidence retains its original 64 GB hardware attribution. Native Sage image failures remain preserved; image support was not re-enabled or requalified.

## Actual guard stops and setup history

The first Bolt long-prefill attempt recorded 1.591 MiB/s inference swapout and 9.081 MiB/s combined I/O; the unchanged limits are 1/8 MiB/s over active 30-second windows. A fresh-worker retry recorded 22.978/33.818 MiB/s and also stopped. Minimum available RAM was 4.185/4.532 GiB; neither the physical-RAM floor nor PSI caused these stops. Host I/O is system-wide, not proof that every byte came from Bolt or that SSD damage occurred. Both attempts stopped owned workers, released reservations and restored dev435. Successful 8K timings are not substituted for the failed long-window gate.

Three earlier setup/staging issues are recorded separately: API/wheel version suffix comparison, an exclusive log filename collision, and an owned interruption to finish runtime-pin staging before immutable qualification. Their verified rollback/cleanup and missing-window limitations are preserved; none is reported as a model incompatibility or speed result.

The final qualified segment uses loading-swap-v2: loading swap and parked pages are allowed; no static occupancy or cumulative-loading-write cap is added. Active churn/PSI monitoring, independent RAM floors, GPU reserves/admission, zero dedicated-VRAM spill, exact ownership/server/GPU locks and lifecycle thermals remain. No unrelated application was stopped, global swap setting changed or model downloaded. Full lifecycle data covers loading, compute, switching and shutdown. Sampled temperatures/SMU flags are not guaranteed transient maxima or measured slowdown.

The old global dev435 environment and original candidate are retained privately for recovery. Bolt's stable environment is independent of the global promotion. To reconsider Bolt, qualify it on the this AMD host with unchanged guards and current settings; then update both the launcher default and `manual_runtime_pin` together. Clearing only metadata is not sufficient. No automatic unpin or schedule change is authorized.

**188 focused CPU regressions passed per checkout after the pin change**, including real cgroup bounds/swap permission, phase monitoring, rollback, ownership, routing, settings preservation and new default/override/updater-hold tests. Dependency checks and patched-source fingerprints pass. Both AMD repos, README/AGENTS, current benchmark report and Shared handoff are synchronized; environments/raw logs remain private.

## MoE models with CPU RAM offload

No new benchmarks or settings changes. Super IQ3 and Ornith retain their physical-RAM requirements and dated 64 GB hardware results.

## MoE models with SSD streaming

No new benchmarks or settings changes. Strata Qwen Q3, GLM Maya and shared DeepSeek XS retain their settings and dated 64 GB hardware results. H3 and its real-RAM-upgrade follow-up are separate; the updater remains paused.
