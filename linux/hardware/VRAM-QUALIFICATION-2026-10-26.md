# GPU-resident reduced-RAM qualification — October 26, 2026

**Outcome: none of the three scoped profiles qualified.** Each normal-launcher
loading trial was stopped by the cumulative system swapout budget before a
complete inference window. These are load-time guard stops, not measured decode
regressions, model crashes, parity failures or proof of a VRAM-capacity problem.

## Tested configuration

- 13th Gen Intel(R) Core(TM) i9-13900KS; two RX 7900 XTX 24 GB; **14.83 GiB OS-visible RAM**.
- Production vLLM `0.32.1rc1.dev435+gc50aca144.rocm72`; SGLang source
  `f84475ccf593087df3d1da13c9e675eadee12352`; retained ROCm 7.2.3.
- Existing dual-GPU profiles and normal launchers; contexts/quantizations, MTP/DFlash2
  selection, weights and engine pins unchanged. No candidate install or promotion.
- Dedicated worker cgroup: **7 GiB memory.high / 8 GiB memory.max / 4 GiB memory.swap.max**,
  read back before load. Supervisor and telemetry remained outside the worker unit.
- At least 10 GiB host MemAvailable was required before each trial, preserving
  2 GiB beyond the hard worker RAM cap. Compiler parallelism was limited to one.
- Explicit test-only `low-churn-v1`: aggregate owned-worker swap ≤4 GiB; cumulative
  host swapout ≤4 GiB; zero dedicated-VRAM spill. Inference rolling windows must
  span at least 30 seconds and stay ≤1 MiB/s swapout / ≤8 MiB/s total swap I/O.
  Three consecutive <2 GiB available-memory or >10% full-memory PSI avg10 samples reject.
  No limit was raised to obtain a pass. The production default remains 64 MiB.

## Loading outcomes

All byte values are retained in the [curated numeric record](results/vram-qualification-2026-10-26.json).
Host swap I/O is a conservative system-wide bound, **not worker-attributed I/O**.

### `qwen3.8-27b-vllm`

- **Guard-stopped during loading** after 51.7 seconds of recorded lifecycle evidence.
- Observed owned-worker swap peak: **3.696 GiB**.
- Cumulative system swapout: **4.108 GiB**, above the 4 GiB budget.
- Minimum available host RAM: 5.414 GiB; maximum full-memory PSI avg10: 3.32%.
- 96 worker samples; zero worker/host telemetry errors or enforcement errors; zero sampled dedicated-VRAM spill.
- **No completed inference window, timing trial or correctness/marker qualification.**
- Owned unit stopped and no managed inference worker remained.

- Thermal coverage: 53 one-second samples, zero sampling errors; loading-only sampled peaks:
  - GPU0: edge 25°C / junction 31°C / memory 28°C.
  - GPU1: edge 21°C / junction 32°C / memory 46°C.
  - CPU package: 71°C.

### `nemotron-3.5-bolt-vllm`

- **Guard-stopped during loading** after 167.7 seconds of recorded lifecycle evidence.
- Observed owned-worker swap peak: **3.984 GiB**.
- Cumulative system swapout: **4.007 GiB**, above the 4 GiB budget.
- Minimum available host RAM: 5.124 GiB; maximum full-memory PSI avg10: 2.33%.
- 326 worker samples; zero worker/host telemetry errors or enforcement errors; zero sampled dedicated-VRAM spill.
- **No completed inference window, timing trial or correctness/marker qualification.**
- Owned unit stopped and no managed inference worker remained.

- Thermal coverage: 169 one-second samples, zero sampling errors; loading-only sampled peaks:
  - GPU0: edge 27°C / junction 34°C / memory 33°C.
  - GPU1: edge 22°C / junction 33°C / memory 47°C.
  - CPU package: 81°C.

### `qwen3.8-27b-sglang-dflash2`

- **Guard-stopped during loading** after 51.4 seconds of recorded lifecycle evidence.
- Observed owned-worker swap peak: **3.004 GiB**.
- Cumulative system swapout: **4.238 GiB**, above the 4 GiB budget.
- Minimum available host RAM: 4.908 GiB; maximum full-memory PSI avg10: 2.00%.
- 89 worker samples; zero worker/host telemetry errors or enforcement errors; zero sampled dedicated-VRAM spill.
- **No completed inference window, timing trial or correctness/marker qualification.**
- Owned unit stopped and no managed inference worker remained.

- Thermal coverage: 53 one-second samples, zero sampling errors; loading-only sampled peaks:
  - GPU0: edge 26°C / junction 33°C / memory 30°C.
  - GPU1: edge 21°C / junction 32°C / memory 46°C.
  - CPU package: 67°C.

## Monitor validation and earlier attempts

The initial 10 GiB worker budget was refused at admission with approximately
11.94 GiB available; a later 9 GiB attempt was also refused after other live
applications reduced headroom. These preflight stops performed no model load.
A separate initial Qwen/vLLM loading attempt was intentionally interrupted for
independent-review monitor corrections; it is not a qualification result. All
attempts are preserved separately in private generated evidence.

The monitor fixes serialize both readers with phase transitions, reset unsampled
phase round trips, fail on missing inference-worker observations, and latch callback
failures with one retry while continuing to sample. Independent re-review passed.
Both operational and sanitized trees pass **28 swap tests and 18 existing memory/
comparator/updater regressions**. CPU tests alone are not a model qualification.

## Final state and limits

- All three scoped loading trials completed their cleanup; both GPUs returned to
  baseline use, GPU-LOCK was released, and the hub/API gateway stayed active.
- Nightly updates remain disabled. RAM-offloaded llama.cpp, Maya and Strata were
  not tested. No model moved, download occurred, setting/pin changed or runtime upgraded.
- These conservative worker-cgroup limits materially affect host loading behavior.
  Results do not prove that every possible configuration on the same installed RAM
  must fail, nor do they invalidate the separate historical 64 GB measurements.
- No throughput, inference-rate or full-context claim is available from these stopped loads.
- AMD changes belong to `linux-llm-amd` / `linux-llm-amd-public`; Windows and native
  Linux NVIDIA remain separate; retired source/settings remain in the central archive.
