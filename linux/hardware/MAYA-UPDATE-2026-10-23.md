# Maya 1.1.24 update — October 23, 2026

**Promoted Maya 1.1.24 /25deec5 on retained ROCm 7.2.3.** Both retained Maya-S 32K profiles passed native and normal gates. GLM keeps MMQ after the newly enabled gfx1100 fused path failed parity; source19 rollback is preserved. Other engines, weights, contexts, memory guards and the DSH Strata default are unchanged.

Pinned newest development source at review: [25deec505b525212e05faa58697d9d2b7d17fdb3](https://github.com/mw00/project-maya/commit/25deec505b525212e05faa58697d9d2b7d17fdb3), VERSION1.1.24. Control source 3384b5e/VERSION1.1.19. Both are compiled on retained ROCm 7.2.3/rocWMMA 2.2.0 with the same pinned llama.cpp 3cf03257 dependency and existing Python 3.12.14 packages. No driver/SDK or other engine update, new quantization download, context or DSH-default change.

Hardware: i9-13900KS,64GB installed/61.51GiB OS-visible,2×RX7900XTX24GB,CPU PCIe4x8/x8,Intel desktop; switch not installed. Both cards required. Same Maya-S weights on shared NVMe,32768 context,GLM40GiB RAM/MTP and DeepSeek 24 CPU threads/noDSpark/DS4_IQ_Q8K=0/DS4_STREAM=0. Native 8 GiB reserves, actual 6 GiB startup admission,52G / no-swap scope, continuous 3 GiB/hard 1.5 GiB VRAM floors and latched owned-worker cleanup retained.

## Correctness exceptions before timing

- Both cards passed 14 retained core HIP checks and 3 additional expert/native-batch checks; 16 local CPU/HTTP and 172 selected upstream CPU tests passed.
- The newly enabled gfx1100 fused GLM prefill kernel fails IQ2_XXS/IQ2_S down parity on BOTH GPUs: relative fused/FP32 error0.103594 versus MMQ0.0116823 in the GPU0 fixture. This is a tested failure, not a speed result. Set **MAYA_GLM_PREFILL_FUSED=0** in the selected GLM profile to retain MMQ. No upstream source edits or tolerance relaxation. [Enablement](https://github.com/mw00/project-maya/commit/18bc575) and [switch documentation](https://github.com/mw00/project-maya/blob/25deec505b525212e05faa58697d9d2b7d17fdb3/docs/SETTINGS.md).
- DeepSeek's legacy-rounding broad suite retains two excluded mixedQ4_K/IQ4_XS bit-exact failures/card. Neither mixed format is admitted. Selected Maya-S formats pass. Keep IQ_Q8K=0; testing a new default does not authorize changing quantization semantics.
- New source includes [AMD DeepSeek prompt/decode changes](https://github.com/mw00/project-maya/commit/3453271), [device-local Lt locking](https://github.com/mw00/project-maya/commit/4fd909e) and [long-row shared-memory sizing](https://github.com/mw00/project-maya/commit/7856997). Their presence is not a local speed claim.

## Matched measurements

Three trials each short code/prose,256-output cap, one excluded warmup/task; three fresh record prompts,64-output cap, actual counts below. Temperature0.6/top_p0.95/seed42/thinking off. Native PP is the engine prompt phase; external SSE TTFT is submission→first output; decode=(completion_tokens−1)/(stream_end−first_output). Cold load excluded. Sequential starts with copied identical expert-profile seeds, not interleaved; stateful caches and different prompt salts limit causal claims. All actual inputs/outputs, cache counts, native timing and thermal coverage remain in the numeric record.

| Model / source | Code decode t/s | Prose decode t/s | Native PP t/s | Fresh TTFT s | Actual fresh input |
|---|---:|---:|---:|---:|---:|
| GLM Maya-S / 1.1.19 control | 19.18 | 16.20 | 541.9 | 11.824 | 6,314–6,315 |
| GLM Maya-S / 1.1.24 selected candidate | 19.72 | 15.69 | 535.6 | 11.928 | 6,311–6,313 |
| DEEPSEEK Maya-S / 1.1.19 control | 6.60 | 6.65 | 185.1 | 34.045 | 6,300–6,301 |
| DEEPSEEK Maya-S / 1.1.24 selected candidate | 6.42 | 6.78 | 299.0 | 21.062 | 6,295–6,297 |

## Functional/context gates

Both selected candidate profiles pass arithmetic, constrained JSON, synthetic tool roundtrip and SSE. No model-requested real tool or internet call is executed. The full-window tests are marker/history smoke checks, not broad quality, agent or publisher-score reproduction.

- GLM: fresh 31,497 input / 19 output; history 31,531 input / 19 output, 31496 cached. Markers passed in both.
- DEEPSEEK: fresh 31,487 input / 17 output; history 31,519 input / 17 output, 31503 cached. Markers passed in both.

## Memory and thermals

- glm-baseline19: minimum available RAM 13.13 GiB; minimum whole-card free VRAM 7.65 / 7.65 GiB; owned swap/spill 0/0 bytes.
- glm-candidate24: minimum available RAM 13.05 GiB; minimum whole-card free VRAM 7.62 / 7.62 GiB; owned swap/spill 0/0 bytes.
- deepseek-baseline19: minimum available RAM 49.82 GiB; minimum whole-card free VRAM 7.67 / 7.66 GiB; owned swap/spill 0/0 bytes.
- deepseek-candidate24: minimum available RAM 49.85 GiB; minimum whole-card free VRAM 7.56 / 7.55 GiB; owned swap/spill 0/0 bytes.

| Lifecycle | 1s samples | GPU junction peak °C,0/1 | VRAM peak °C,0/1 | CPU package peak °C |
|---|---:|---:|---:|---:|
| glm-baseline19 | 344 | 95.0 / 76.0 | 76.0 / 69.0 | 96.0 |
| glm-candidate24 | 274 | 102.0 / 85.0 | 88.0 / 75.0 | 100.0 |
| deepseek-baseline19 | 505 | 105.0 / 92.0 | 88.0 / 78.0 | 100.0 |
| deepseek-candidate24 | 663 | 97.0 / 84.0 | 84.0 / 80.0 | 99.0 |

Lifecycle coverage includes startup through owned cleanup. Request logs overlap these samples and must not be added as independent durations. Sampled peaks are not guaranteed transients; SMU flags are observations, not measured throttling time. Raw private logs stay excluded. Available temperature sensor counts, clocks, fans and power remain numeric; no overheating cause or thermal speed loss is inferred.

## Normal integration and rollback

Normal integration thermal coverage: 666 one-second samples, including the initial incomplete Desktop attempt, retry, reloads and idle gaps; sampled GPU junction peaks 71.0 / 59.0 °C, CPU package 82.0 °C. This is functional-check coverage, not an additional benchmark.

Actual unchanged Desktop entry→Ptyxis→managed worker/original browser UI passed for GLM→DeepSeek→GLM, including model selector, original assets/metrics, authenticated gateway and blocked runtime/context/port updates. Exact deployed binary/source/config fingerprints matched. First direct GIO attempt ended before API readiness; its scope logs are preserved; detached GIO retry passed. Cause of the first termination is not established. Final owned-worker cleanup is verified separately.

The ten-profile catalog, model hub, existing PATH names, browser/Desktop versus native/menu policy and DSH Strata default are preserved. Authenticated host-self LAN/Tailscale routes do not constitute a remote-peer test. Verified source19/binaries/config rollback remains private. No model files or environments are committed.

## Community reports and scope

The user's screenshots describe NVIDIA V100/4090 hardware and Maya-XS/DSpark, which differ from this retained Maya-S/dual-RDNA3 profile; their 70+ tok/s claims are not local results. No screenshot, personal account or raw message is exported.

[LCZ GLM report, test date2026-10-08](https://lcz.me/topic/2195/9): Maya 1.0.11,RTX3080+3090,64K,three GLM quants and changed sampling; not a matched DS4/gfx1100 comparison (author unavailable in fetched excerpt). [Level1Techs, JWNoctis,October15](https://forum.level1techs.com/t/ultimate-2x-r9700-guide-for-qwen-3-8-27b-mxfp4-200t-s-c-1-500t-s-at-c-8/257789?page=3): RDNA4/Radiance discussion warns that token accounting/cache behavior can distort reported PP; different engine/model/hardware. No forum tuning setting is deployed from those anecdotes. [Source ledger](FORUM-OPTIMIZATION-SOURCES.md).

[All trials, binaries and validation evidence](results/maya-update-2026-10-23.json) · [Benchmark history](BENCHMARK-HISTORY.md).
