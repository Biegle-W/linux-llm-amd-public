# Fresh engine update tests — October 25, 2026

User-requested fresh tests after allowing up to 64 MiB aggregate owned-worker swap. The newest upstream heads checked at the start of this run were pinned for testing; the morning evidence and failed RAM-admission attempt remain preserved privately. Hardware: Intel i9-13900KS, 64 GiB installed / 61.51 GiB OS-visible RAM, two RX 7900 XTX 24 GB on CPU PCIe 4.0 x8/x8; ROCm 7.2.3 retained.

| Engine | Tested production → candidate | Outcome |
|---|---|---|
| llama.cpp | `6b9ba4f2e8c1` → `2280f0fd163b` | Promoted; all four models passed |
| Maya | `f26d8bab43f9` / 1.1.26 → `6afa525bbabc` / 1.1.28 | Rejected on DeepSeek decode gates; production restored and normal-launcher generation smoke verified |
| Strata DeepSeek | `8183c6b67162` / 0.1.49.1 → `4b9e05a2a806` / 0.1.51 | Rejected on selected-format kernel parity before installation; production retained |

Full [numeric record](results/fresh-engine-tests-2026-10-25.json) retains all timed trials, actual input/output counts, TTFT, memory, thermal coverage, gate tables and failed parity evidence. This is one sequential paired update-gate run; it does not establish a universal source speedup or regression. vLLM, SGLang, Strata Qwen, weights, model settings and DSH default were not changed.

## Method and limits

The normal launchers ran all four llama.cpp models, all three Maya models and both Strata DeepSeek production profiles. Each timed model had separate excluded warm-ups, three sampled code and three prose trials (256-output cap, seed 42 / temperature 0.6 / top-p 0.95), then three salted fresh marker-prefill trials (64-output cap). Actual prompt lengths differ by tokenizer and are saved with every trial. Source loading and prewarm are excluded from short TTFT; the log’s post-readiness “loaded in” time is not full startup time.

Prefill and each code/prose decode median must be at least 95% of production; short TTFT must be within max(1.25× baseline, baseline + 0.05 s), with no fewer markers. Each model and the full launch/load/test/shutdown lifecycle must have valid telemetry, at most 67,108,864 bytes aggregate owned-worker swap, and zero dedicated VRAM spill. Missing telemetry or incomplete model coverage fails closed. Background system swap is excluded; global swap and the worker/RAM/VRAM guards were not changed.

The probes cover roughly 6.3K–8.2K actual prompt tokens, not the configured 32K–256K windows. There was no new full-window, visual desktop/browser, remote-peer or reboot validation. Expert routing/cache state follows the normal managed launcher; all trials and warm/cold variation remain visible.

## Paired medians

Code/prose values are external SSE decode tokens/s; PP is native/engine prefill tokens/s. All TTFT medians and actual token counts remain in the numeric record.

| Engine/model | Code baseline → candidate | Prose baseline → candidate | PP baseline → candidate |
|---|---:|---:|---:|
| llama: `empero-qwen3.8-35b-a3b` | 119.68 → 121.65 | 72.85 → 77.65 | 2967.1 → 2952.0 |
| llama: `nemotron-3.5-super-iq3` | 15.53 → 15.58 | 17.10 → 17.09 | 432.5 → 430.4 |
| llama: `sage-a1.5` | 79.83 → 81.23 | 63.93 → 67.74 | 2806.7 → 2796.4 |
| llama: `ornith-1.5-122b` | 11.42 → 11.27 | 13.31 → 13.47 | 718.4 → 711.2 |
| maya: `glm-5.3-flash-maya` | 19.04 → 18.85 | 15.52 → 15.75 | 539.3 → 537.1 |
| maya: `deepseek-v4.1-flash-1017-maya` | 22.59 → 19.00 | 13.31 → 12.42 | 634.1 → 630.6 |
| maya: `deepseek-v4.1-flash-1017-maya-s` | 5.71 → 6.64 | 6.67 → 6.27 | 381.7 → 375.9 |

llama.cpp passed every promotion gate. Its full baseline and candidate lifecycle monitors both recorded zero worker swap/spill. The promoted binary is built at the production path from exact source `2280f0fd163b03d4331d49e08460f66502e35854`.

Maya’s first baseline attempt stopped before inference because less than 52 GiB was available. The retry began after about 54.8 GiB was available, preserving the admission requirement. All three production and candidate benchmark records completed; the candidate failed XS code −15.9%, XS prose −6.7% and S prose −5.9%. GLM passed, and S code increased in this run; neither offsets another model’s failed gate. Restore verification used the normal GLM launcher and a generated HTTP-200 response; it is not a new full benchmark of the restored build.

Maya ran 18 kernel tests on each GPU. All 17 blocking tests per card passed. The known `hip_prefill_fused_parity` failure persists on each card; the fused path remains disabled. No tolerance was relaxed.

## Strata DeepSeek parity rejection

Both production S/XS baselines passed under the new swap cap. Candidate source `4b9e05a2a806a3fe24f7b2560d98626c37dade35` built as 0.1.51, and its CPU suite passed 59 tests with one skip (60 total). The selected-format `ds4_iq_test` failed `IQ3_XXS wmma vs scalar y` on both GPUs: worst **3.14e-3** exceeds **3e-3** tolerance. Cross-device comparison found zero differing buffers out of 60; that does not repair the scalar-reference failure. Later shape/core/slot checks and candidate inference benchmarks were not reached. No candidate binary or profile was installed.

## Memory and thermal evidence

| Engine/phase | Aggregate lifecycle swap peak (MiB) | VRAM spill bytes | Sampling errors |
|---|---:|---:|---:|
| llama baseline | 0.00 | 0 | 0 |
| llama candidate | 0.00 | 0 | 0 |
| maya baseline | 32.99 | 0 | 0 |
| maya candidate | 34.23 | 0 | 0 |
| strata-dsv41 baseline | 26.18 | 0 | 0 |

The initial observer attached during isolated builds, before GPU inference; the Maya observer covers the full retry, parity, candidate and rollback smoke. Per-model/request thermals are also retained. Sampled peaks cannot rule out between-sample transients; raw SMU limit flags do not measure a throughput loss.

| Observation | Samples / errors | GPU0 / GPU1 junction peak °C | CPU package peak °C |
|---|---:|---:|---:|
| Initial job (observer attached during builds) | 2871 / 0 | 83.0 / 73.0 | 100.0 |
| Full Maya retry | 3394 / 0 | 84.0 / 70.0 | 100.0 |

Available card edge/junction/memory sensors, power, clocks, fan RPM, busy coverage, SMU flag availability and CPU package measurements are saved in the numeric record. Sensors unavailable to the maintained logger remain unmeasured; no values were backfilled. The initial CPU peak includes compilation and is not attributed to inference alone.

## Post-test verification

Both test jobs exited successfully, no managed inference workers remained and GPU-LOCK was released. All saved model/profile settings and Maya/Strata runtime pins match the pre-test snapshot; only the promoted llama.cpp source pin changed. Restored Maya executables match their pre-test validation SHA-256 values. Read-only host self-access checks passed authentication, health, retired-Q2 rejection and the 13-model catalog through loopback, LAN and Tailscale. No generation was requested by these checks, and no separate remote peer was tested.

## Source attribution

- [llama.cpp tested commit](https://github.com/ggml-org/llama.cpp/commit/2280f0fd163b03d4331d49e08460f66502e35854).
- [Maya tested 1.1.28 commit](https://github.com/mw00/project-maya/commit/6afa525bbabc3a8f5fd165f89e9bc72155d9bd39).
- [Strata tested 0.1.51 commit](https://github.com/Niko1221/Strata/commit/4b9e05a2a806a3fe24f7b2560d98626c37dade35).
- [Updater policy and accounting](daily-update/README.md#minor-worker-swap-allowance--october-25).
