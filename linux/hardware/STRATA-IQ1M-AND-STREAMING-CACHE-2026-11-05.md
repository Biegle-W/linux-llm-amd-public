# Strata IQ1_M addition and streaming-cache work — November 5, 2026

The additional `qwen3.8-flash-next-unsloth-iq1_m` route passed its own strict two-step tool check, scored **5/6** on six fixed local quality fixtures, and measured **57.140 native tokens/s** median over three128-token probes. All13 original routes are retained; the catalog now has **14 routes /11 main weight sets:6 VRAM only,1 CPU RAM offload,7 SSD streaming**. These are short tests; sustained and full-context performance remain unqualified.

Model load was **54.471s**, separate from request latency. First/follow-up native decode was **59.1/63.6 tokens/s**. The speed-probe range was **54.201–59.934 tokens/s**; median speed TTFT was **0.501s**. The JSON arithmetic fixture failed; the other five local fixtures passed. Native log input/output counts match all11 completed API requests. Final guard passed, owned cgroups/KFD drained, zero owned swap/spill was recorded, and all pinned input file identities were unchanged at completion.

The three downloaded GGUF shards total **68,007,094,938 bytes**, pinned to revision `d96201194f103c906994f283f504209dc8d2a10c`; every SHA256 was reverified under the guard before loading. Official RX7900 engine/Control package hashes and signed feed sequence121 were verified. The metadata pack retains original quantized experts/native table bytes, without a copied `experts.bin`; its compatibility projection conversions are disclosed in the numeric limitations. The selected GSQ route and default were preserved. The new package has its own binary, Control source, backing-content and config seals. Only listener/log destinations differ between tested and deployed runtime. The legacy source updater excludes this independently sealed release package.

[Official release](https://github.com/Niko1221/Strata/releases/tag/v0.2.11) · [Pinned Unsloth weights](https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF/tree/d96201194f103c906994f283f504209dc8d2a10c/UD-IQ1_M)

## Current inventory: execution mode → engine → exact weights

| Execution mode | Engine | Exact weight variant | API model ID | Context |
|---|---|---|---|---:|
| VRAM only | llama.cpp | Empero Qwen3.8-35B-A3B IQ4_XS | `empero-qwen3.8-35b-a3b` | 262,144 |
| VRAM only | llama.cpp | Flint-40B-A2.5B Unsloth UD-Q4_K_XL | `flint-40b-a2.5b` | 32,768 |
| VRAM only | SGLang | Qwen3.8-27B AutoRound W4A16 GPTQ; DFlash2 auxiliary | `qwen3.8-27b-sglang-dflash2` | 163,840 |
| VRAM only | vLLM | Nemotron-3.5-Bolt-74B-A9B AutoRound W4A16 | `nemotron-3.5-bolt-vllm` | 262,144 |
| VRAM only | vLLM | Qwen3.8-27B AutoRound W4A16 GPTQ; shared main weights | `qwen3.8-27b-vllm` | 163,840 |
| VRAM only | vLLM | Sage-A1.5 AutoRound W4A16 | `sage-a1.5` | 65,536 |
| CPU RAM offload | llama.cpp | Ornith-1.5-122B Q4_K_M; CPU experts + VRAM cache | `ornith-1.5-122b` | 32,768 |
| SSD streaming | Maya | DeepSeek-V4.1-Flash-1017 Coder IQ2_XXS; shared GGUF backing | `deepseek-v4.1-flash-1017-maya-coder-iq2-xxs` | 32,768 |
| SSD streaming | Maya | DeepSeek-V4.1-Flash-1017 Unsloth UD-IQ1_S; shared GGUF backing | `deepseek-v4.1-flash-1017-maya-unsloth-q1` | 32,768 |
| SSD streaming | Maya | GLM-5.3-Flash Maya-S v2 IQ2_XXS; RAM/VRAM tiers | `glm-5.3-flash-maya` | 32,768 |
| SSD streaming | Strata | DeepSeek-V4.1-Flash-1017 Coder IQ2_XXS; shared GGUF backing + RAM store | `deepseek-v4.1-flash-1017-strata-coder-iq2-xxs` | 32,768 |
| SSD streaming | Strata | DeepSeek-V4.1-Flash-1017 Unsloth UD-IQ1_S; shared GGUF backing +36GB store | `deepseek-v4.1-flash-1017-strata-unsloth-q1` | 32,768 |
| SSD streaming | Strata | Qwen3.8-Flash-Next GSQ IQ3_XXS; RAM/VRAM expert caches | `qwen3.8-flash-next-iq3_xxs` | 262,144 |
| SSD streaming | Strata | Qwen3.8-Flash-Next Unsloth UD-IQ1_M Dynamicv3.1; RAM/VRAM caches | `qwen3.8-flash-next-unsloth-iq1_m` | 262,144 |

The Qwen27B pair shares one main weight set; the two Coder routes and two DeepSeek Unsloth routes each share their GGUF backing. Streaming still uses hybrid RAM/VRAM caches; it is not entirely disk computation. These route counts exclude unselected alternatives, retired assets and graphics dependencies.

## Native per-request records

| Request | Native tokens/s | Client TTFT s | Output tokens |
|---|---:|---:|---:|
| tool-1 | 59.100 | 7.847 | 60 |
| tool-2 | 63.600 | 7.397 | 19 |
| json-math | 61.600 | 0.311 | 42 |
| stable-unique | 66.000 | 0.675 | 53 |
| sql-aggregate | 62.200 | 0.936 | 44 |
| logic | 60.300 | 0.733 | 16 |
| retrieval | 66.100 | 8.360 | 57 |
| history | 65.700 | 0.317 | 37 |
| speed-1 | 57.140 | 0.472 | 128 |
| speed-2 | 59.934 | 0.523 | 128 |
| speed-3 | 54.201 | 0.501 | 128 |

Three fixed128-token speed prompts, deterministic settings, strict tool call/result IDs and the exact returned marker were checked. Native request clocks and token counts are separate from client SSE latency. No sustained, full-window, vendor benchmark or controlled cross-quant speedup claim is made.

## Cache qualification and selection

| Case | Result | Selected state |
|---|---|---|
| GLM RAM24, Maya c167004, fused prefill disabled, requested 8 GiB per-card reserves | Strict tools passed; 5/6 local fixtures; three short speed probes median 1.995 native tokens/s | Not promoted; RAM8 restored |
| Maya DeepSeek UD-IQ1_S, intended 36GB store | Loading failed on six-second heartbeat; original 15-second owned cleanup failed; zero inference requests | No promotion; original no-store baseline restored after reboot |
| GLM RAM40 | Prepared only; no model run or qualification | Blocked by persistent GPU fault hold |

GLM RAM24 loaded in 73.342s. First/follow-up native decode was 1.56/0.98 tokens/s; the three speed probes ranged 1.333–3.464 tokens/s with median TTFT 14.432s. All 11 completed API output counts match saved native logs; JSON arithmetic was the failed fixture. Logical disk reads fell to 43.56–60.12/token from the earlier RAM8 sample's 65.67–87.07, but follow-up performance regressed. Different cache conditions and prompts prevent a controlled general speedup claim. Owned cleanup passed with zero recorded swap/spill, and the wrapper restored RAM8 and its passed registry record. These short tests do not qualify sustained or full-context performance.

Earlier stale-slot admission and readiness-schema stops remain historical zero-request records. The first removed only two expired conversational slots from immutable backing; the second expected `loaded:true` where Maya reports `unloaded:false`. Its corrected readiness contract passed 10 CPU checks. A later power-loss-truncated launcher also produced an empty readiness-only guard pass; that is not model qualification. The actual GLM RAM24 result above comes from the restored, nonempty, content-pinned case. The passed IQ1_M result and all prior final cases are retained; no completed model case was repeated for this review.

## DeepSeek loading failure and kernel crash

The first actual Maya 36 GB store case started at 18:44:48 EST on 7.0.14-42-vmpt1. The supervisor heartbeat stopped while collecting telemetry, and the original owned worker/cgroup did not drain by the 15-second deadline. The failed result remains failed even though reboot later removed the worker and KFD client. No inference or optimization pass occurred.

| Saved journal time, EST | Observation |
|---|---|
| 18:45:06 | SMU stopped responding to metrics/fan queries |
| 18:45:11 | MES REMOVE_QUEUE failed; kernel began GPU reset/recovery |
| 18:45:36–37 | Power-state/display errors and DMCUB diagnostic error |
| 18:45:41 | Display vblank wait timed out |
| 18:46:05 | CPU19 hard lockup in `amdgpu_device_rreg` via display/vblank IRQ; multiple CPU soft lockups |

Minimum recorded available host RAM was 52.57 GiB and minimum free VRAM was about 7.71 GiB per card; recorded owned swap/spill was zero. Telemetry then stopped responding, so those are not post-hang measurements. The evidence identifies a GPU/driver recovery and display-IRQ failure sequence; it does not establish a driver, PCIe or hardware root cause, and does not indicate ordinary host RAM exhaustion. Raw journals, machine IDs and client state are excluded from this report.

The machine subsequently rebooted to stock 7.0.0-42-generic. KFD was observed empty, and actual disk configs/registry records retained GLM RAM8 and Maya DeepSeek without the candidate SSD store. **The persistent watchdog GPU fault hold remains. No automatic GPU work, retry, reboot or hold release is authorized; RAM40 remains unrun and blocked.** Four fresh peer capability/local/IPC-integrity/RCCL checks passed earlier on the failed 7.0.14 boot with zero recorded swap/spill and clean owned teardown. Those passes are not current-stock-boot proof or model-loading stability proof.

## Reviewed filesystem admission

Root filesystem device numbers changed across boots. Reviewed installation/mount provenance records the same filesystem UUID while preserving original inode, byte count, mtime and content pins. Admission accepts only a device-number alias on that verified UUID with the other identities unchanged; missing, different or unqueryable UUIDs fail closed. Existing external-file content verification is retained. Only Maya Q1's runtime-written `lt-picks.txt` algorithm-choice cache was removed from immutable backing after checking the selected c167 source writer (`src/ds4/ds4_model.cu` and append logic in `src/ds4/ds4_lt.cu`); model weights and immutable metadata remain sealed.

The reviewed guard work passed 41 CPU contracts, including exact RAM40 record/reserve checks; it does not mark RAM40 passed or select it. Three export checks verify public references retain content hashes, omit local filesystem seals/UUIDs and require independent local qualification. The earlier post-power-loss 69-file IQ1_M content recheck remains identity evidence, not a new inference pass. All 100°C/storage/RAM/VRAM/phase-aware-swap/spill/heartbeat/cleanup/ownership protections, original 13 routes, retired assets, boot default and existing schedules remain preserved.

[Numeric evidence](results/STRATA-IQ1M-AND-STREAMING-CACHE-2026-11-05.json) · [Current results](CURRENT-AMD-BENCHMARKS.md) · [Runtime handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md)
