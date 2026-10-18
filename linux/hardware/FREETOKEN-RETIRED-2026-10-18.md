# FreeToken retired — October 18, 2026

The user requested complete removal because performance was unsatisfactory.
The isolated ROCm environment, upstream checkout, Desktop frontend and saved
app state, PATH/menu launchers, configuration and FreeToken-specific caches
were removed. Shared GGUF weights and other inference engines were retained.
No new model weights were downloaded for this experiment. Do not reinstall
FreeToken or treat the following historical settings as active profiles.

## Historical measurements

Hardware: i5-13600KF, two RX 7900 XTX 24 GB cards, 32 GB system RAM.
FreeToken used **GPU1 only, TP1**; other engines retain the dual-GPU policy.
Source `8f49e0af98ba444dd261af69e82d5a1841778c68`, FreeToken 0.1.3,
Torch `2.14.0+rocm10.1.0`, reported HIP `7.16.26385`.
These are single short response samples including prefill/API overhead,
**not isolated decode throughput or matched engine comparisons**.
No separate prefill throughput was measured.

| Model / test | Allocated context | GPU expert cache | Output tokens | Seconds | End-to-end output t/s |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen 27B Q4, CLI | 8,192 | none | 100 | 2.584 | 38.7 |
| Qwen 27B Q4, Desktop | 8,192 | none | 100 | 2.650 | 37.7 |
| Empero 35B-A3B IQ4_XS, API | 4,096 | 4 GiB | 128 | 4.452 | 28.8 |
| Empero 35B-A3B IQ4_XS, API | 8,192 | 12 GiB | 128 | 4.454 | 28.7 |
| Qwen3.6 35B-A3B MXFP4, API | 4,096 | 4 GiB | 47 | 2.810 | 16.7 |
| Qwen3.6 35B-A3B MXFP4, API | 8,192 | 12 GiB | 47 | 2.771 | 17.0 |

MoE API arithmetic, JSON and complete tool-call/result round trips passed.
CPU expert banks were 15.9 GiB (Empero) and 17.7 GiB (Qwen35B), with a bounded
GPU hot-expert cache. Passing trials used a temporary per-model 26 GiB memory
limit and zero-swap cgroup; worker swap and VRAM spill were zero. Earlier
unrestricted startup attempts were stopped by swap guards. The larger cache
showed no established short-code speed improvement. Full-window 8K filling,
long sessions, MTP and hybrid CPU compute were not validated.

The earlier dense Desktop Start/Chat/Stop test passed. The later MoE Desktop
worker started, but GUI chat and Stop were **not completed before cancellation**.
The native Desktop GPU panel did not detect AMD. Nemotron `nemotron_h_moe` was
unsupported by the installed registry. Flash-Next IQ3 needed about 40 GiB of
CPU expert backing and was not admitted with 32 GB RAM. Neither was benchmarked.
The experimental loopback API on port 1919 is no longer served.

[Curated MoE test evidence](freetoken-moe-2026-10-18.json) preserves completed
measurements only; private raw logs, request traces, chat data and GPU UUIDs
were discarded. Earlier installation code and dense-test evidence remain in
Git history rather than the active workspace.

## Sources and applicability

- [Pinned upstream source](https://github.com/FlashML-org/FreeToken/tree/8f49e0af98ba444dd261af69e82d5a1841778c68),
  [AMD guide](https://github.com/FlashML-org/FreeToken/blob/8f49e0af98ba444dd261af69e82d5a1841778c68/docs/install_amd.md),
  [expert loader](https://github.com/FlashML-org/FreeToken/blob/8f49e0af98ba444dd261af69e82d5a1841778c68/python/freetoken/models/gguf/experts.py).
- [Desktop beta.23](https://github.com/FlashML-org/FreeToken-Web/releases/tag/v0.2.0-beta.23).
- [systemd memory controls](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html).
- [Level1Techs FreeToken discussion](https://forum.level1techs.com/t/freetoken-an-llm-engine-to-max-the-bandwidth-of-all-the-things/254396),
  eduncan911, August 26, NVIDIA A5500/64 GB; [lcz.me topic 2059](https://lcz.me/topic/2059),
  X99/7900 XTX/Strata. These were research leads, not matching AMD/32 GB performance baselines.
