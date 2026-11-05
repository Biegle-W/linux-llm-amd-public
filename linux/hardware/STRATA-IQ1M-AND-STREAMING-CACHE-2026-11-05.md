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

## Why the streaming routes are slow; pending optimization

Saved GLM telemetry shows65.67–87.07 disk reads/token and641–2788.65 aggregate disk ms/token, versus about10.6ms/token on the CPU lane. Overlapping disk times are not added as wall time. The baseline8GB RAM tier leaves experts on disk; RAM24 is a distinct candidate within unchanged hard limits and requested8GiB GPU reserves, with fused prefill disabled. Saved DeepSeek Maya telemetry shows94.5GB of expert weights outside VRAM,28GB read-ahead and substantial file refaults; the selected source already supports the proposed bounded36GB whole-expert RAM store. Strata's selected Q1 route already uses36GB. No arithmetic-changing expert/prompt skipping is introduced.

GLM RAM24 and Maya DeepSeek36GB-store optimization remain pending. The first GLM admission stopped before engine load on two expired conversational cache slots incorrectly sealed as immutable weights; only those transient entries were removed after checking the remaining pins. A separate loaded GLM attempt issued zero requests because the harness expected `loaded:true`, while Maya reports `unloaded:false`. It was deliberately stopped with clean teardown and baseline restoration. The corrected readiness contract passed10 CPU checks. No inference result or cache optimization pass is claimed, and GLM retains RAM8. The DeepSeek36GB-store candidate has never run. After a power-loss reboot, stock7.0.0-42-generic is current; the pending cases retain their tested7.0.14-42-vmpt1 boot requirement. No previous peer test or model case was replayed.

The two failed pre-request records and reviewed holds remain preserved. Both had zero owned swap/spill, clean owned cleanup and restored target profiles. The power loss occurred after those jobs had ended. The passed IQ1_M result is retained. After reboot, all69 sealed weight/package/library files were rehashed against their original content hashes under the same guards. Only verified device/inode bindings were updated, and read-only admission then passed; this is not a new inference pass. All100°C/storage/RAM/VRAM/phase-aware-swap/spill/heartbeat/cleanup/ownership protections remain. No Radiance trial, retired-asset restoration, recurring schedule or persistent boot-default change was made.

[Numeric evidence](results/STRATA-IQ1M-AND-STREAMING-CACHE-2026-11-05.json) · [Current results](CURRENT-AMD-BENCHMARKS.md) · [Runtime handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md)
