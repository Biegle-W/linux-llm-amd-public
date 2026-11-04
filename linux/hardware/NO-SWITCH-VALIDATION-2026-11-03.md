# No-switch validation — November 3, 2026

**Completed with guard blocks. Eight retained LLM/backend paths passed strict short DSH checks, and all six retained graphics workflows produced valid artifacts. No new GPU reset, bus-loss or OOM fault was recorded in the no-switch boot. The 600-second Strata test stopped early at the existing Sapphire junction-temperature limit of 90°C; GLM stopped at the existing 128 MiB free-VRAM floor. Sustained stability is not qualified.**

The external Broadcom switch is absent. Both 24 GB RX 7900 XTX cards remain, on actual Gen4 x16 and Gen4 x4 upstream paths. Driver P2P stays off (`N` / `0`), and fresh HIP probes repeatedly found no peer capability/refused enable requests. The Strata/llama comparison retained PowerColor as logical GPU0 and Sapphire as GPU1 despite bus/order changes. This qualification uses isolated views; production ordering/enable flags, engine pins, guards and schedules were not changed.

## Retained LLM paths

| Path | Result | Load seconds | DSH output tokens |
| --- | --- | ---: | ---: |
| Strata / Qwen IQ3 | passed | 77.855 | 77 |
| llama / Empero | passed | 47.957 | 76 |
| llama / Flint | passed | 51.954 | 159 |
| llama / Ornith | passed | 171.351 | 77 |
| vLLM / Sage | passed | 83.463 | 75 |
| SGLang / Qwen | passed | 80.698 | 75 |
| vLLM / Qwen | passed | 111.837 | 80 |
| vLLM / Bolt | passed | 152.590 | 84 |
| Maya / GLM | stopped: free VRAM below 128 MiB | — | — |

Each successful short probe required exactly one read tool call with matching result ID, two model steps and the exact fixture marker in the final answer. First-output/request limits stayed 20/30 s. Qwen/vLLM and Bolt initially hit the quick 210-second loading budget; each then passed under its retained native router's 900-second startup allowance (990-second enclosing diagnostic caps). No model arguments, source pin or per-request/resource guard was changed for those checks. Ornith and other held models were tested only through isolated qualification views; production pauses remain. GLM's first wrapper attempt ended before engine initialization due its different `main()` signature; the corrected attempt reached the VRAM guard before readiness and was not retried with altered reserves.

## Fixed graphics workflows

| Workflow | Result | Request seconds |
| --- | --- | ---: |
| graphics-flux-t2i | render passed; cleanup separately verified | 98.559 |
| graphics-flux-i2i | passed including guarded unload | 48.694 |
| graphics-qwen-t2i | passed including guarded unload | 92.275 |
| graphics-qwen-edit | passed including guarded unload | 44.222 |
| graphics-h3-t2v | passed including guarded unload | 151.852 |
| graphics-h3-i2v | passed including guarded unload | 108.725 |

The six outputs were decoded on CPU and spot-checked visually. PNG dimensions/nonempty content and video stream metadata were verified; video spot-checking used initial frames, not a full temporal-quality grade. The original Flux text-to-image produced a valid 1024×1024 PNG, but its outer guard stopped during teardown telemetry sampling. A fresh audit proved empty owned scopes/KFD and no GPU fault. Future diagnostic harnesses use one worker guard and explicitly terminate a completed pinned scope before accepting empty-state cleanup; five CPU boundary checks pass. Missing telemetry during active inference still fails closed, and the cleanup deadline remains 15 seconds. The completed Flux render was preserved, not repeated. Graphics used the retained 1800-second fixed-graph request budget.

## Sustained Strata limit

The repeated-request test kept the same model/profile and per-request guards as the successful short Strata check. It loaded in 78.107 s, completed three whole DSH read-tool round trips (seven requests completed; an eighth was interrupted), then the Sapphire junction sensor reached **90°C** at a sample 147.412 s from stage start. The last fully saved completed-round duration is 54.893 s. The requested 600-second test did not complete. Sapphire edge/memory peaks in that attempt were 70/74°C; PowerColor junction peaked at 85°C. These are configured guard limits/results, not a claim that 90°C establishes defective hardware. Owned processes unloaded and KFD emptied. No guard was raised and no retry followed.

## Coverage and retained state

The basic guarded stage passed SSD SMART/live-temperature admission, three address-dependent patterns over 2 GiB of host RAM, three fresh bidirectional HIP P2P-off cases, and three checked local kernel/read/write patterns on each GPU. Current owner-policy/P2P/llama/shared-storage regression subsets passed **92 checks**, plus **five** cleanup-harness checks. Historical memory/swap suites were replayed with both explicit legacy opt-ins; two historical methods retain stale fixture/default-policy assumptions and are not fully green. Live guards were not changed to satisfy them.

Retired Super IQ3 and removed old DeepSeek XS backing for Maya/Strata are unavailable; no replacement download/conversion was performed. The normal 1 GiB RAM / 128 MiB-per-card VRAM floors, disabled `MemoryHigh`, installed RAM minus 1 GiB worker cap, existing swap and SSD checks remain. All task-owned GPU work is unloaded, KFD is empty, and the persistent hold remains. Positive bounded results do not prove the switch caused earlier incidents, certify all RAM/VRAM, validate every context length or qualify sustained expert streaming.

[Machine-readable final results](results/no-switch-validation-2026-11-03.json). Further sustained testing requires addressing the observed thermal limit within a newly authorized scope; GLM also needs sufficient free-VRAM headroom. No production promotion is included in this validation.
