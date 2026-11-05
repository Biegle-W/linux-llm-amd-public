# Current models, realistic budgets and engine updates — November 5, 2026

**13 qualified normal routes are enabled.** Four native large-model checks passed after removing the three-second decode-progress cutoff. Llama9c9074 passed Flint, Ornith and the separate Empero strict check and is selected for all three; the earlier3259 Empero rejection remains historical evidence. Maya c167004 subsequently passed all three enabled profiles through the guarded selective updater and is selected. ComfyUI0.44/fb2b26f passed all six normal workflows and is selected with Torch/ROCm unchanged. Correct-RDNA3 build, PLE/Super and Bolt matching long-context qualification remain pending. The existing 03:00 updater timer is restored without catch-up; the completed updates have passed final source/CPU review; in-flight outcomes will be refreshed separately.

## Current saved LLM measurements

Load is separate from request TTFT. The second request follows a tool result and can reuse cache. Prompts, output lengths, source versions and native paths differ; these are functional samples, not a matched speed or quality ranking.

| Exact model ID | Backend | Context | Load s | First TTFT s | First request s | Output tokens | Second request s |
|---|---|---:|---:|---:|---:|---:|---:|
| `deepseek-v4.1-flash-1017-maya-coder-iq2-xxs` | maya | 32,768 | 37.958 | 36.924 | 42.569 | 114 | 3.409 |
| `deepseek-v4.1-flash-1017-maya-unsloth-q1` | maya | 32,768 | 51.964 | 118.772 | 152.156 | 113 | 53.916 |
| `deepseek-v4.1-flash-1017-strata-coder-iq2-xxs` | strata | 32,768 | 26.171 | 86.028 | 100.624 | 84 | 4.782 |
| `deepseek-v4.1-flash-1017-strata-unsloth-q1` | strata | 32,768 | 25.169 | 99.371 | 146.695 | 85 | 14.388 |
| `empero-qwen3.8-35b-a3b` | llama | 262,144 | 46.717 | 2.225 | 4.194 | 64 | 1.250 |
| `flint-40b-a2.5b` | llama | 32,768 | 50.717 | 1.273 | 4.319 | 176 | 1.996 |
| `glm-5.3-flash-maya` | maya | 32,768 | 61.732 | 185.242 | 271.324 | 60 | 34.341 |
| `nemotron-3.5-bolt-vllm` | vllm | 262,144 | 148.603 | 2.180 | 4.220 | 64 | 1.256 |
| `ornith-1.5-122b` | llama | 32,768 | 155.846 | 10.694 | 18.908 | 92 | 4.347 |
| `qwen3.8-27b-sglang-dflash2` | sglang | 163,840 | 78.510 | 3.566 | 3.819 | 61 | 0.434 |
| `qwen3.8-27b-vllm` | vllm | 163,840 | 91.492 | 3.449 | 3.878 | 61 | 0.481 |
| `qwen3.8-flash-next-iq3_xxs` | strata | 262,144 | 66.738 | 7.566 | 8.509 | 63 | 7.695 |
| `sage-a1.5` | vllm | 65,536 | 98.058 | 1.157 | 1.632 | 61 | 0.321 |

Native Coder/Q1/GLM checks completed exactly one read tool and two model steps, with matching call/result IDs, the exact final marker and verified owned unload. Native settings retain 32K context, two cards, one request, requested 8 GiB reserves and normal 6 GiB startup headroom. GLM fused prefill remains disabled after two unused parity failures; 34 required per-card parity checks passed. Strata Q1 retains its tested 36 GiB SSD cache and strong 60/52 GiB physical/available host admission.

## Earlier llama.cpp qualification

Source `3259ab6e5dd86fad1931962d784702cb53c7877b` was built in isolation. Flint and Ornith passed on that source; the subsequent9c9074 qualification below supersedes their selection. Empero’s one read tool and both requests completed, but its final answer was not exactly the marker; that old3259 check retained `eb4e244be77a906a183cd4a00fd51d9ad3200955` until the later9c9074 pass. No failed candidate was retried into a pass. The guard verified complete owned cleanup, no dedicated-VRAM spill and no new kernel fault. Allowed loading swap was observed, so this is not a zero-swap claim.

## Guarded updater qualification

Maya `c1670044bbc09310f35f9d00f7596c50ae8a38f1` passed required per-card parity and exactly one strict two-step read-tool round trip for each of Coder, Q1 and GLM. Only those enabled profiles were promoted. Their newer measurements replace the selected Maya rows above; the original c01 results remain separately in the numeric evidence. Owned cleanup passed with empty cgroups, no remaining KFD clients, no dedicated-VRAM spill and 110,592 bytes maximum owned swap. All 111 targeted CPU checks passed, including publication recovery, graphics source selection, supervisor-loss cleanup and final-guard rollback. The separate llama updater promoted `9c9074e14e029a16fc3298e6bc6a3ef00a0b9c11` after Ornith/Flint passed; Empero then passed its separate new-source strict check and selected that same build. All three llama checks had clean owned cleanup, zero dedicated-VRAM spill and zero recorded owned swap. No c01 or3259 case was repeated.

## Bolt latest-global candidate

The latest-global Bolt candidate `0.33.0rc1.dev229+g3966924d5.rocm72` passed its strict two-step tool check: load 236.700s, first TTFT 3.435s and first request 5.101s. Its prior dev435 hold was caused by near255Kprefill behavior; this short check does not resolve that condition. The manual pin remains until a matching guarded long-context check passes.

## Saved graphics measurements

| Workflow | Elapsed s | Scope |
|---|---:|---|
| graphics-h3-tp2 | 93.316 | Isolated H3 TP2; cached conditioning excludes encoder cost |
| graphics-flux-t2i | 94.478 | Normal fixed workflow on selected ComfyUI0.44/fb2b26f |
| graphics-flux-i2i | 44.297 | Normal fixed workflow on selected ComfyUI0.44/fb2b26f |
| graphics-qwen-t2i | 91.297 | Normal fixed workflow on selected ComfyUI0.44/fb2b26f |
| graphics-qwen-edit | 25.936 | Normal fixed workflow on selected ComfyUI0.44/fb2b26f |
| graphics-h3-t2v | 128.521 | Normal fixed workflow on selected ComfyUI0.44/fb2b26f |
| graphics-h3-i2v | 109.363 | Normal fixed workflow on selected ComfyUI0.44/fb2b26f |

The six normal rows now use the newly selected ComfyUI0.44/fb2b26f source; each passed finite tensor, saved-media and owned-cleanup checks, including full AV decoding for videos. Torch/ROCm and existing input/user state were preserved. Original seven graphics measurements remain in the numeric evidence; the separate cached-conditioning TP2 experiment was not rerun. Prompts, caches and output work differ, so no matched speed ranking is claimed. [Gallery and exact workflow limits](../graphics/results/p2p-2026-11-05/README.md).

## Timing and protection

Finite phase budgets now allow 1,800 seconds for native loading, prefill and generation, and 3,600 seconds for PLE loading. Each short check permits two model steps with at most 256 output tokens each. The three-second inter-token stop is removed; the six-second supervisor heartbeat, independent phase limits, 15-second owned cleanup, 100°C CPU/GPU/SSD, storage health, RAM/VRAM, dedicated-VRAM spill and phase-aware swap protections remain. Slow offloaded output is allowed to progress within these budgets. No boot-default, unrelated service, other paused schedule or weight-deletion change is included.

## Downloaded assets and sharing

The metadata inventory covers 179 large files in 23 groups. Logical folder sizes include selected/alternative weights, shards and some converted caches; they are not an unused-space or duplicate-savings total. Empty direct-reference lists do not account for indirect pack and workflow references.

| Asset group | Logical GiB | Current use or disposition |
|---|---:|---|
| DeepSeek-Unsloth-Q1-20261103/UD-IQ1_S | 216.979 | One backing used by both enabled Maya and Strata Q1 packs; retain. |
| Maya/Maya-S-v2-IQ2_XXS | 90.933 | Enabled GLM backing plus derived pack/cache assets; retain. |
| Strata/packs | 1.438 | Selected Qwen native pack assets; retain. |
| Strata/mtp | 0.767 | Qwen native drafter assets; preserve selected and pinned alternatives. |
| Strata/models | 71.477 | Selected Qwen GGUF backing; retain. |
| Flint-40B-A2.5B | 23.334 | Selected llama Flint GGUF. |
| Ornith-1.5-122B-GGUF | 71.485 | Selected llama Ornith shards. |
| Empero-Qwen3.8-35B-A3B-Distill | 18.280 | Selected Empero GGUF on qualified9c9074 source. |
| Nemotron-3.5-Bolt-74B-A9B-AutoRound-W4A16 | 40.648 | Selected Bolt checkpoint; latest-global short pass, matching near255K check pending. |
| Sage-A1.5-W4A16-AutoRound | 18.931 | Selected vLLM checkpoint. |
| Flint-AWQ | 20.875 | Downloaded alternative; no qualified normal route. FlintForCausalLM is registered in current vLLM, so lack of architecture registration is not a supported rejection reason. |
| Nemotron-3.5-Super-VL-120B-A12B-W4A16-Merlin | 67.912 | Retained for the authorized guarded INT4 EP2 retry; not the retired IQ3 route. |
| Qwen3.8-27B-W4A16-AutoRound-GPTQ | 18.677 | One checkpoint shared by enabled vLLM and SGLang routes. |
| drafts | 1.193 | SGLang DFlash2 drafter; retain. |
| text_encoders | 48.285 | Normal Flux/Qwen/H3 workflows use the primary encoders, including distinct H3 8B and32B paths; retain. |
| diffusion_models | 43.118 | Normal Flux/Qwen/H3 denoisers; retain. |
| vae | 6.985 | Normal image/video/audio VAE assets; retain. |
| experimental | 44.859 | Staged graphics/TP artifacts; not normal production. Review individual experiment references before any removal. |
| Strata-DFlash2-a22a1744e85c | 1.926 | Alternate Strata drafter/pack; the selected Strata route uses MTP. Preserve pending per-file review. |
| DeepSeek-Coder-ISTA-20261103 | 170.170 | One shared backing used by enabled Maya and Strata Coder packs; metadata packs are not duplicate weight copies. |
| Qwen-Flash-Next-W4A16-FP8PLE-20261103 | 116.252 | Retained verified checkpoint for authorized host-file-gather retry. |
| Strata-Unsloth-Qwen3.8-Flash-Next-UD-IQ3_XXS-V3.1-d96201194f10 | 79.272 | Unselected alternative; matched short comparison did not improve the retained GSQ selection. |
| Flint-abliterated-Mix-24G-4d618d1cb1d7 | 22.346 | Unselected alternative; matched short comparison did not improve the retained Flint selection. |

**Nothing was deleted.** The unselected Unsloth Qwen and Flint Mix weights, Flint AWQ and experimental graphics artifacts are candidates for an owner-led retention review, not proven byte duplicates or approved removals. Same-size tensor shards can hold different tensors; the six size-collision groups do not establish duplication. No aggregate reclaimable-space claim is made. Shared Coder/Q1 backing and normal graphics encoders are active dependencies. [Matched alternative comparisons](UNSLOTH-FLINT-COMPARISONS-2026-11-04.md).

[Curated measurements](results/REALISTIC-LARGE-MODELS-2026-11-05.json) · [Current runtime handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md) · [RDNA3/Radiance and true dual-card research](RDNA3-DUAL-GPU-RESEARCH-2026-11-05.md)
