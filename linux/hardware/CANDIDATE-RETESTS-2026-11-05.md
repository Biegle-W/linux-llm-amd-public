# Fresh candidate tests and unused drafter removal — November 5, 2026

Three owner-requested isolated attempts used the current canonical guards and installed vLLM `0.33.0rc1.dev229+g3966924d5.rocm72`. All ended before inference. **No candidate was promoted; all 13 selected normal routes remain unchanged.** Earlier completed cases were preserved separately.

| Candidate | Final outcome | Inference requests | Peak recorded owned swap (GiB) | Minimum recorded available RAM (GiB) | Original 15-second cleanup |
|---|---|---:|---:|---:|---|
| Flint AWQ | Startup: required FlashInfer import missing | 0 | 0.000 | 51.749 | Passed |
| Qwen Flash Next FP8-PLE | Loading: six-second supervisor heartbeat missing, 11/25 shards | 0 | 7.670 | 1.467 | Failed KFD deadline; later empty |
| Nemotron Super VL INT4 Merlin | Loading: available host RAM below 1 GiB | 0 | 2.220 | 0.939 | Passed |

Dedicated-VRAM spill was zero in all three attempts. No new kernel GPU/bus/OOM fault was recorded. Timings and throughput are not reported because none reached model readiness or inference; these outcomes establish no speed, quality, sustained-stability or full-window qualification.

## Exact interpretation

- **Flint AWQ:** the architecture was registered and resolved as `FlintForCausalLM`. Startup then imported the FlashInfer attention backend and failed with `ModuleNotFoundError: flashinfer`. The current model implementation requires FlashInfer and includes CUDA-specific paths. This is a runtime-compatibility failure, not evidence that the architecture is unregistered or the downloaded weights are corrupt. No CUDA dependency or model port was installed as a workaround.
- **PLE:** the unchanged six-second heartbeat watchdog stopped loading after 11 of 25 shards. The 3600-second loading budget was not exhausted, and the retained router's separate roughly 20-minute startup limit did not cause this stop. Owned cgroups were emptied, but one worker's KFD registration remained beyond the 15-second cleanup deadline. The worker later exited and KFD became empty. Fresh thermal/storage/RAM/kernel checks then passed; the known owned hold was archived intact. **The original cleanup deadline failure and failed qualification remain recorded.** No cleanup limit was extended and this case was not rerun.
- **Super INT4:** the guard stopped loading when sampled available RAM reached 1,008,168,960 bytes, below the 1 GiB reserve. Owned process/device cleanup passed within the original policy. Fresh health checks passed before its known hold was archived intact. No guard was relaxed and this case was not rerun.

Each isolated candidate used 8192 configured tokens, TP2, a single session, BF16 activations and 2 GiB KV per rank. PLE retained its reviewed host-file-gather overlay, 20 GiB CPU-offload bound per rank and 512-token staging. Super retained EP2 and its 18 GiB CPU-offload bound per rank. Flint used zero CPU offload and its supplied chat template with matching GLM-style tool syntax. These are candidate settings, not new production profiles.

## Guards and scope

Canonical current defaults retained the six-second supervisor heartbeat, 15-second owned cleanup, 100°C CPU/GPU/SSD policy, SMART health, 1 GiB host availability, 128 MiB per-card live floor, zero dedicated spill and the current phase-aware swap/resource policy. The three-second decode cutoff remains removed. Loading budgets were 1800 seconds for Flint/Super and 3600 for PLE; prefill and generation each retained 1800 seconds. GPU work and heavy I/O were serialized under established ownership locks. No unrelated process was terminated and no new schedule, engine selection, Torch/ROCm or boot change was made.

## Unused Strata DFlash2 removed

The owner authorized removal if this auxiliary was no longer needed. The selected Strata profile uses MTP; enabled SGLang uses a separate DFlash2 drafter. Current DSH configurations had no reference to the unused Strata source/packs and no active owner had its files open.

All four files were freshly verified against their original pinned SHA-256 values at source revision `a22a1744e85c17364dcc54a6a420af7135d4c7f6` before removal. This stronger content check resolved inode differences from the earlier metadata inventory. Only the 1,206,140,008-byte source, 522,458,112-byte Q4_0 pack, 339,694,592-byte selector pack and 1,236-byte config were removed: **2,068,293,948 logical bytes (1.926 GiB)**. This is a logical-byte total, not a filesystem free-space delta. Small provenance and the original pinned revision remain recorded. No other model, pack, engine environment or historical result was deleted.

The same-root, same-threshold metadata rescan now counts **176 files of at least 4 MiB in 22 groups**, down from the earlier 179/23. At that checkpoint the three tested candidate downloads were retained. A later explicit owner request removed those three candidates; tested Unsloth/Flint Mix alternatives, active H3 8B/ClipProj files and selected MTP/SGLang drafter remain retained.

[Curated numeric results](results/CANDIDATE-RETESTS-2026-11-05.json) · [Current routes and measurements](REALISTIC-LARGE-MODELS-2026-11-05.md) · [Runtime handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md)

Subsequent explicit owner request removed the failed FlintAWQ, FP8-PLE and SuperINT4 downloads after dependency/identity review; [final removal and selected-route native capture](AMD-NATIVE-DECODE-TESTS-2026-11-05.md). The failure results above remain historical evidence.
