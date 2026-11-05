# Current models, realistic budgets and engine updates — November 5, 2026

**14 qualified normal routes are enabled.** Four native large-model checks passed after removing the three-second decode-progress cutoff. Llama9c9074 passed Flint, Ornith and the separate Empero strict check and is selected for all three; the earlier3259 Empero rejection remains historical evidence. Maya c167004 subsequently passed all three enabled profiles through the guarded selective updater and is selected. ComfyUI0.44/fb2b26f passed all six normal workflows and is selected with Torch/ROCm unchanged. Fresh owner-requested latest-guard attempts ended before inference: Flint AWQ requires unavailable FlashInfer; PLE stopped on the six-second heartbeat guard; Super stopped below the 1 GiB host reserve. PLE missed its 15-second KFD drain deadline, then drained later; that failed result remains recorded. None was promoted. The unused Strata DFlash2 source/packs were removed after pinned-hash and dependency verification; the separate SGLang drafter and all 13 selected routes remain unchanged. [Fresh outcomes](CANDIDATE-RETESTS-2026-11-05.md). Bolt now selects globaldev229 after a strict matching255473-token prefill/tool check (255658 tokens on its second request), with clean owned cleanup and zero recorded swap or VRAM spill. Its old dev435 environment is retained. The RDNA3 fork at2314df4 built and passed native/CLI audits, but its Qwen startup warm-up failed on missing `CommonAttentionMetadata._seq_lens_cpu` before any request. The exact case is final; the fork remains isolated and unpromoted. The existing 03:00 updater timer is restored without catch-up; the completed updates have passed final source/CPU review; all scoped outcomes are recorded and the failed fork remains unpromoted.

[IQ1_M qualification and cache status](STRATA-IQ1M-AND-STREAMING-CACHE-2026-11-05.md): new Unsloth UD-IQ1_M passed strict tools,5/6 local quality fixtures and57.140native tokens/s median across three short probes. All13 original routes remain;14routes/11 main weight sets are grouped below. GLM RAM24 and DeepSeek36GB-store optimization remain pending after two zero-request GLM preflight/harness stops. The current stock reboot differs from the pending cases’ tested boot; no optimization or current-boot model pass is claimed.

[Strata 0.2.11 with existing UnslothV3.1](STRATA-0211-UNSLOTH-2026-11-05.md): Strata 0.2.11/engine+Control 0.1.57 with the already downloaded Unsloth V3.1 IQ3_XXS passed the strict tool test and completed6 quality fixtures (5/6) plus3 short timing prompts (median native 52.895 tokens/s). Owned cleanup passed with zero recorded swap/spill; production GSQ/source selections remain unchanged.

## Current saved LLM measurements

Load is separate from request TTFT. The second request follows a tool result and can reuse cache. Prompts, output lengths, source versions and native paths differ; these are functional samples, not a matched speed or quality ranking.

| Mode | Engine | Exact weight variant / API ID | Context | Load s | First TTFT s | First request s | Output tokens | Second request s |
|---|---|---|---:|---:|---:|---:|---:|---:|
| VRAM only | llama.cpp | Empero Qwen3.8-35B-A3B IQ4_XS / `empero-qwen3.8-35b-a3b` | 262,144 | 46.717 | 2.225 | 4.194 | 64 | 1.250 |
| VRAM only | llama.cpp | Flint-40B-A2.5B Unsloth UD-Q4_K_XL / `flint-40b-a2.5b` | 32,768 | 50.717 | 1.273 | 4.319 | 176 | 1.996 |
| VRAM only | SGLang | Qwen3.8-27B AutoRound W4A16 GPTQ; DFlash2 auxiliary / `qwen3.8-27b-sglang-dflash2` | 163,840 | 51.474 | 3.592 | 3.852 | 61 | 0.431 |
| VRAM only | vLLM | Nemotron-3.5-Bolt-74B-A9B AutoRound W4A16 / `nemotron-3.5-bolt-vllm` | 262,144 | 218.686 | 3.450 | 5.015 | 65 | 0.721 |
| VRAM only | vLLM | Qwen3.8-27B AutoRound W4A16 GPTQ; shared main weights / `qwen3.8-27b-vllm` | 163,840 | 89.521 | 3.387 | 3.774 | 61 | 0.407 |
| VRAM only | vLLM | Sage-A1.5 AutoRound W4A16 / `sage-a1.5` | 65,536 | 82.499 | 1.064 | 1.481 | 61 | 0.382 |
| CPU RAM offload | llama.cpp | Ornith-1.5-122B Q4_K_M; CPU experts + VRAM cache / `ornith-1.5-122b` | 32,768 | 155.846 | 10.694 | 18.908 | 92 | 4.347 |
| SSD streaming | Maya | DeepSeek-V4.1-Flash-1017 Coder IQ2_XXS; shared GGUF backing / `deepseek-v4.1-flash-1017-maya-coder-iq2-xxs` | 32,768 | 37.958 | 36.924 | 42.569 | 114 | 3.409 |
| SSD streaming | Maya | DeepSeek-V4.1-Flash-1017 Unsloth UD-IQ1_S; shared GGUF backing / `deepseek-v4.1-flash-1017-maya-unsloth-q1` | 32,768 | 51.964 | 118.772 | 152.156 | 113 | 53.916 |
| SSD streaming | Maya | GLM-5.3-Flash Maya-S v2 IQ2_XXS; RAM/VRAM tiers / `glm-5.3-flash-maya` | 32,768 | 61.732 | 185.242 | 271.324 | 60 | 34.341 |
| SSD streaming | Strata | DeepSeek-V4.1-Flash-1017 Coder IQ2_XXS; shared GGUF backing + RAM store / `deepseek-v4.1-flash-1017-strata-coder-iq2-xxs` | 32,768 | 26.171 | 86.028 | 100.624 | 84 | 4.782 |
| SSD streaming | Strata | DeepSeek-V4.1-Flash-1017 Unsloth UD-IQ1_S; shared GGUF backing +36GB store / `deepseek-v4.1-flash-1017-strata-unsloth-q1` | 32,768 | 25.169 | 99.371 | 146.695 | 85 | 14.388 |
| SSD streaming | Strata | Qwen3.8-Flash-Next GSQ IQ3_XXS; RAM/VRAM expert caches / `qwen3.8-flash-next-iq3_xxs` | 262,144 | 66.738 | 7.566 | 8.509 | 63 | 7.695 |
| SSD streaming | Strata | Qwen3.8-Flash-Next Unsloth UD-IQ1_M Dynamicv3.1; RAM/VRAM caches / `qwen3.8-flash-next-unsloth-iq1_m` | 262,144 | 54.471 | 7.847 | 8.711 | 60 | 7.693 |

## Native decode statistics

All14 current routes now have short native per-request statistics; the new IQ1_M row is in its linked evidence. Nine saved-log rows were recovered; four routes completed new native capture. A sustained matched benchmark remains missing.

| Selected route | Context | First tool request native t/s | Follow-up native t/s | Three speed prompts: median native t/s | Speed range |
|---|---:|---:|---:|---:|---:|
| Qwen3.8 27B / vLLM | 163,840 | 145.60 | 124.81 | 102.45 | 98.41–111.33 |
| Qwen3.8 27B DFlash2 / SGLang | 163,840 | 238.52 | 170.91 | 103.29 | 95.68–130.50 |
| Sage A1.5 / vLLM | 65,536 | 136.53 | 136.69 | 157.39 | 150.45–157.53 |
| Nemotron Bolt / vLLM | 262,144 | 37.22 | 37.38 | 37.63 | 37.58–37.74 |

[All13 native statistics](AMD-DECODE-EVIDENCE-2026-11-05.md) · [Four-route methods and individual samples](AMD-NATIVE-DECODE-TESTS-2026-11-05.md).

Native Coder/Q1/GLM checks completed exactly one read tool and two model steps, with matching call/result IDs, the exact final marker and verified owned unload. Native settings retain 32K context, two cards, one request, requested 8 GiB reserves and normal 6 GiB startup headroom. GLM fused prefill remains disabled after two unused parity failures; 34 required per-card parity checks passed. Strata Q1 retains its tested 36 GiB SSD cache and strong 60/52 GiB physical/available host admission.

## Earlier llama.cpp qualification

Source `3259ab6e5dd86fad1931962d784702cb53c7877b` was built in isolation. Flint and Ornith passed on that source; the subsequent9c9074 qualification below supersedes their selection. Empero’s one read tool and both requests completed, but its final answer was not exactly the marker; that old3259 check retained `eb4e244be77a906a183cd4a00fd51d9ad3200955` until the later9c9074 pass. No failed candidate was retried into a pass. The guard verified complete owned cleanup, no dedicated-VRAM spill and no new kernel fault. Allowed loading swap was observed, so this is not a zero-swap claim.

## Guarded updater qualification

Maya `c1670044bbc09310f35f9d00f7596c50ae8a38f1` passed required per-card parity and exactly one strict two-step read-tool round trip for each of Coder, Q1 and GLM. Only those enabled profiles were promoted. Their newer measurements replace the selected Maya rows above; the original c01 results remain separately in the numeric evidence. Owned cleanup passed with empty cgroups, no remaining KFD clients, no dedicated-VRAM spill and 110,592 bytes maximum owned swap. All 111 targeted CPU checks passed, including publication recovery, graphics source selection, supervisor-loss cleanup and final-guard rollback. The separate llama updater promoted `9c9074e14e029a16fc3298e6bc6a3ef00a0b9c11` after Ornith/Flint passed; Empero then passed its separate new-source strict check and selected that same build. All three llama checks had clean owned cleanup, zero dedicated-VRAM spill and zero recorded owned swap. No c01 or3259 case was repeated.

## Bolt latest-global qualification

Bolt now selects globaldev229 after a strict matching255473-token prefill/tool check (255658 tokens on its second request), with clean owned cleanup and zero recorded swap or VRAM spill. Its old dev435 environment is retained. The normal short sample on the same runtime had load236.700s; the matching long-context check had load230.693s, first TTFT173.642s and first request175.945s. Different prompt scopes are not a speed comparison.

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

## Earlier PLE realistic-budget outcome

The PLE host-file-gather attempt ended during loading when the unchanged six-second supervisor-heartbeat guard fired. The3600-second loading budget was not exhausted, and no inference request completed or model promotion occurred. Maximum recorded owned swap was6.474GiB, dedicated-VRAM spill was zero, and the minimum recorded available host RAM was1.247GiB. Owned cleanup passed with no remaining KFD client or new kernel GPU/OOM fault. Fresh thermal/storage/resource review passed; the known hold was archived intact and this exact PLE case will not be repeated. Super also stopped during loading on the same unchanged heartbeat guard. Its maximum recorded owned swap was8.363GiB and dedicated-VRAM spill was zero; owned cleanup and fresh health review passed. Neither exact case will repeat.

## Timing and protection

Finite phase budgets now allow 1,800 seconds for native loading, prefill and generation, and 3,600 seconds for PLE loading. Each short check permits two model steps with at most 256 output tokens each. The three-second inter-token stop is removed; the six-second supervisor heartbeat, independent phase limits, 15-second owned cleanup, 100°C CPU/GPU/SSD, storage health, RAM/VRAM, dedicated-VRAM spill and phase-aware swap protections remain. Slow offloaded output is allowed to progress within these budgets. No boot-default, unrelated service, other paused schedule or weight-deletion change is included.

## Downloaded assets and sharing

The original metadata inventory covered 179 large files in 23 groups; after the unused Strata DFlash2 and three failed-candidate removals, the completed pre-IQ1_M same-threshold rescan counted77 files in19groups. The new IQ1_M tree adds five files above4MiB; no fresh combined filesystem total is claimed here. Logical folder sizes include selected/alternative weights, shards and some converted caches; they are not an unused-space or duplicate-savings total. Empty direct-reference lists do not account for indirect pack and workflow references.

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
| Nemotron-3.5-Bolt-74B-A9B-AutoRound-W4A16 | 40.648 | Selected Bolt checkpoint; globaldev229selectedaftermatchingnear255Kpass. |
| Sage-A1.5-W4A16-AutoRound | 18.931 | Selected vLLM checkpoint. |
| Flint-AWQ |20.875 previously| Removed by owner request after final failed trial and dependency/identity review; no selected route used this download. |
| Nemotron-3.5-Super-VL-120B-A12B-W4A16-Merlin |67.912 previously| Removed by owner request after final failed trial and dependency/identity review; no selected route used this download. |
| Qwen3.8-27B-W4A16-AutoRound-GPTQ | 18.677 | One checkpoint shared by enabled vLLM and SGLang routes. |
| drafts | 1.193 | SGLang DFlash2 drafter; retain. |
| text_encoders | 48.285 | Normal Flux/Qwen/H3 workflows use the primary encoders, including distinct H3 8B and32B paths; retain. |
| diffusion_models | 43.118 | Normal Flux/Qwen/H3 denoisers; retain. |
| vae | 6.985 | Normal image/video/audio VAE assets; retain. |
| experimental | 44.859 | Staged graphics/TP artifacts; not normal production. Review individual experiment references before any removal. |
| Strata-DFlash2-a22a1744e85c | 1.926 previously | Removed by owner request after fresh pinned-hash/dependency review; selected Strata MTP and separate SGLang drafter retained. |
| DeepSeek-Coder-ISTA-20261103 | 170.170 | One shared backing used by enabled Maya and Strata Coder packs; metadata packs are not duplicate weight copies. |
| Qwen-Flash-Next-W4A16-FP8PLE-20261103 |116.252 previously| Removed by owner request after final failed trial and dependency/identity review; no selected route used this download. |
| Strata-Unsloth-Qwen3.8-Flash-Next-UD-IQ3_XXS-V3.1-d96201194f10 | 79.272 | Unselected alternative; matched short comparison did not improve the retained GSQ selection. |
| Flint-abliterated-Mix-24G-4d618d1cb1d7 | 22.346 | Unselected alternative; matched short comparison did not improve the retained Flint selection. |

**Only the unused Strata DFlash2 auxiliary and the explicitly named failed Flint AWQ, FP8-PLE and Super INT4 downloads were removed by owner request.** The unselected Unsloth Qwen and Flint Mix weights, Flint AWQ and experimental graphics artifacts are candidates for an owner-led retention review, not proven byte duplicates or approved removals. Same-size tensor shards can hold different tensors; the six size-collision groups do not establish duplication. No aggregate reclaimable-space claim is made. Shared Coder/Q1 backing and normal graphics encoders are active dependencies. [Matched alternative comparisons](UNSLOTH-FLINT-COMPARISONS-2026-11-04.md).

[Curated measurements](results/REALISTIC-LARGE-MODELS-2026-11-05.json) · [Current runtime handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md) · [RDNA3/Radiance and true dual-card research](RDNA3-DUAL-GPU-RESEARCH-2026-11-05.md)

## Isolated RDNA3 full-stack build

The correct `perf/rdna3_full_stack` source `2314df44164584f8eb59189d82c20e5362967a2c` produced an isolated wheel and passed native-kernel import and CLI smoke audits on retained Torch2.13/HIP7.2. The generated HIP commands target only gfx1100. All80 applicable Python dependency requirements were satisfied; these are dependency checks, separate from the previously reported111 CPU tests.

Build preparation exposed missing MIOpen and hipSPARSELt metadata in the retained SDK. Matching checksum-verified ROCm7.2.3 packages were extracted only into private build overlays. Private host-math/libc linker scripts corrected incompatible Conda absolute paths. All native modules then linked, but the Rust phase reached the unchanged100°C CPU guard before wheel output because C++MAX_JOBS did not constrain Cargo. Clean owned teardown and zero swap/spill were verified. That hold was freshly reviewed and archived intact. A separate corrected build used one Cargo job and inherited affinity to two logical CPUs on distinct physical cores; actual cargo/rustc limits were verified. It completed without relaxing any guard. Original Torch/ROCm, environments, source artifacts and model/input/user state were retained.

The first actual fork-source Qwen case kept the normal163840-token allocation, TP2, MTP3, BF16 KV, custom-all-reduce setting and resource guards. Native fork attention was hash-pinned; the selected global wheel's separate optional prefill port was not applied to this fork. An extra preflight's incorrect expectation of a standalone skinny library was corrected before any model case; the actual skinny/GPTQ operators are linked into `_rocm_C` and their registrations passed. No model case was repeated.

Qwen then failed during startup warm-up with `AttributeError: 'CommonAttentionMetadata' object has no attribute '_seq_lens_cpu'`. It never became ready and accepted no inference request. The planned near160K prefill/tool check was therefore **not reached or qualified**. Final owned cgroups/KFD clients were empty, maximum recorded owned swap and VRAM spill were zero, and fresh post-stop kernel/thermal/storage/RAM checks passed. Its exact own hold was archived intact. The model case is final: no retry, local compatibility shim or production promotion was attempted. All13 previously qualified route selections remain unchanged; no scoped job or GPU lock remains. Candidate build artifacts are retained, and nothing was deleted.
