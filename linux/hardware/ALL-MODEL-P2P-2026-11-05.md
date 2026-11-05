# All-model P2P and guarded qualification — November 5, 2026

21/27 bounded cases passed both functional and stage guards. Cases include different capacity profiles and transport-observation checks of the same model; this is not a count of distinct models. Failed, inconclusive and retired routes remain explicit below.

Nine qualified normal routes are enabled after the owner-authorized archive of the reviewed global STOP/GPU hold. All six failed or inconclusive cases remain held, and deleted XS/SuperIQ3 routes remain retired. All guards, source/weight pins, stock boot default, unrelated services and paused schedules remain.

Hardware: i5-13600KF, ASUS TX GAMING B760M WIFI, 61.55 GiB visible RAM, two RX 7900 XTX 24 GB cards behind the PEX880xx switch. Current boot uses `7.0.14-42-vmpt1`, identity GPU IOMMU domains and the verified six-bridge ACS 0x11 configuration. Runtime logical order is PowerColor then Sapphire. Stock persistent boot default, source/weight pins, unrelated services and paused schedules remain.

## Method and limits

Each LLM case uses one short strict DSH read-tool round trip: two model steps, matching tool IDs and the exact final fixture marker, followed by owned unload. This adds no full-window or sustained-stability qualification. Native/engine phase timing, API first-token latency and complete request latency remain separate in [numeric results](results/ALL-MODEL-P2P-2026-11-05.json). Single-request observations are not throughput benchmarks or causal P2P speed comparisons. Previous Unsloth/Flint comparisons and completed native checks were reused, not repeated for publication.

Seven graphics cases complete fixed workflows; three later cases extend copy-observation coverage for normal Flux, Qwen and H3 workflows. Outputs are nonempty, denoising/decoded tensors are finite, and videos pass full audio/video decode. H3 videos contain 39 frames at 608×352, stereo 32 kHz audio and 1.625 s duration. Sampler, seed, dimensions, timing, finite checks and transport observations are preserved in the numeric result. [Reviewed generated images and videos](../graphics/results/p2p-2026-11-05/README.md) accompany the results.

CPU/GPU/SSD software guards stop at 100°C; SMART health and RAM/VRAM/spill/swap, progress/heartbeat, ownership and cleanup protections remain. 12049/12049 saved stage samples have complete CPU plus both-card edge/junction/memory temperature readings. Saved sampled peaks: CPU package 91.0°C, card0/edge 44.0°C, card0/junction 70.0°C, card0/mem 42.0°C, card1/edge 43.0°C, card1/junction 77.0°C, card1/mem 60.0°C. SSD health/temperature guards were active; a per-case SSD peak was not retained, so no SSD peak is claimed. Functional stops retain their original evidence and reviewed boundaries; failed profiles were not retried.

The applied activation package passed 160 CPU checks and read-only admission checks against actual source, binary, backing, RAM/VRAM and catalog state. After activation, all 17 runtime files match the reviewed staging copies; retained source pins and native seals verify. The authenticated live API lists exactly nine routes and health is healthy; absent or incorrect keys return 401. Verification sent no inference request. Historical-policy tests use isolated fixtures; operational guards were not changed for those tests.

Public native code/profile exports are references with registry status `requires-local-validation`; admission rejects them until independently qualified and sealed on the receiving host. Source examples use `/opt/local-llm/qualified-sources`. Machine-specific inode/device/mtime seals and private runtime state are omitted; source revisions and content hashes remain as evidence.

## LLM outcomes

| Case | Result | Load (s) | Owned cleanup |
|---|---|---:|---|
| `strata-qwen-mtp` | Pass | 66.738 | Verified |
| `maya-coder` | Pass | 41.977 | Verified |
| `strata-coder` | Pass | 23.165 | Verified |
| `llama-empero` | Pass | 46.719 | Verified |
| `llama-flint` | Pass | 50.710 | Verified |
| `vllm-qwen` | Pass | 91.492 | Verified |
| `vllm-bolt` | Pass | 148.603 | Verified |
| `vllm-sage` | Pass | 98.058 | Verified |
| `sglang-qwen` | Pass | 78.510 | Verified |
| `llama-ornith` | Pass | 160.886 | Verified |
| `maya-coder-normal-admission` | decode-output guard stop | 36.452 | Verified |
| `strata-coder-normal-admission` | Pass | 26.171 | Verified |
| `maya-glm` | Enclosing diagnostic budget exhausted; full tool round trip inconclusive | 56.970 | Verified |
| `maya-q1` | decode-output guard stop | 49.699 | Verified |
| `strata-q1` | decode-output guard stop | 26.194 | Verified |
| `vllm-ple-file-gather` | loading budget exhausted | — | Verified |
| `super-int4-ep2` | Host RAM reserve below1GiB during loading; no completed inference | — | Verified |

The original small-reserve Maya Coder and Strata Coder checks passed. Distinct normal-capacity checks requested 8 GiB reserve while retaining the normal 6 GiB actual startup floor: Strata Coder passed with 7.518/7.732 GiB free at readiness; Maya Coder stopped at the three-second decode-progress guard. Only the passing Strata Coder capacity profile was activated. GLM exhausted its unchanged enclosing budget before completing the full tool round trip. Both Q1 variants stopped at the decode-progress guard and remain held.

Strata Q1's prepared admission originally expected the old 1 GiB reserve. That pre-engine failure and a later exclusive-log collision were preserved before the first GPU execution. Correcting the admission expectation to the already selected 8 GiB changed no model setting or resource guard. Two mutable saved-conversation cache entries were similarly removed from an overbroad asset manifest only after source review; all original manifests and immutable pins were retained.

Before Super's first launch, exFAT inode-cache changes blocked admission. All 108 affected immutable files (141,169,202,971 bytes) matched the original pinned download/upstream content. The original manifests were preserved; 246 mutable Hugging Face download-cache entries were classified separately. No model content was refreshed or re-downloaded. The staged native admission code permits an inode-only change only with the original content hash; size, timestamp, device and content mismatches still fail closed, with thermal/storage monitoring during large hash checks.

Old Maya/Strata XS backing and Super IQ3 remain retired/deleted. They were not restored as fallbacks. See each dated report for older faults and qualifications.

## Actual transport

Empero, Flint and Ornith have successful cross-GPU peer-copy API events inside completed inference intervals. Qwen27B/vLLM, Bolt, Sage and Qwen27B/SGLang have both-direction RCCL P2P/IPC selection plus successful TP2 tool requests and reviewed collective paths. Environment variables or device capability alone do not establish application transport.

The native DeepSeek IQ2/Q1 family falls back to whole-layer groups and host-mediated handoffs in the reviewed sources. Strata Qwen's `FNX_PEER` affects a separate engine path and does not establish direct peer transport for this generate path. Describe these as dual-card functional profiles; do not label them direct P2P from their short passes.

The extended trace passed 224 CPU checks, including locally loaded symbol fallback, then an exact-byte real-GPU probe of four APIs with HSA-owner coverage. Normal Flux/Qwen/H3 component workflows still show no cross-GPU copy during their requests; observed GPU copies are same-device or host transfers. This is consistent with denoiser/encoder/VAE component placement and does not make those workflows tensor parallel. Absence of copy-API events alone is not universal proof that no remote kernel access exists.

The separate pinned fcys H3 TP2 request has both-direction RCCL P2P/IPC, finite output on both ranks and a valid complete output. Cached conditioning excluded text-encoder cost. It is a bounded transport/functional check, not a matched speed comparison, sustained qualification or normal TP2 promotion. External implementation source is not redistributed with the generated artifacts.

## Graphics outcomes

| Case | Result | Complete request (s) | Owned cleanup |
|---|---|---:|---|
| `graphics-h3-tp2` | Pass | 93.316 | Verified |
| `graphics-flux-t2i` | Pass | 93.903 | Verified |
| `graphics-flux-i2i` | Pass | 45.866 | Verified |
| `graphics-qwen-t2i` | Pass | 88.880 | Verified |
| `graphics-qwen-edit` | Pass | 26.276 | Verified |
| `graphics-h3-t2v` | Pass | 136.098 | Verified |
| `graphics-h3-i2v` | Pass | 101.131 | Verified |
| `graphics-copy-coverage-flux` | Pass | 94.069 | Verified |
| `graphics-copy-coverage-qwen` | Pass | 90.236 | Verified |
| `graphics-copy-coverage-h3` | Pass | 145.892 | Verified |

ComfyUI `0.42.0` / `8f04fd6ecf4a548937971e840af2a985529fab76`, Torch `2.15.0.dev20260827+rocm7.2`, HIP `7.2.53211` and comfy-kitchen `0.2.39` are retained. The normal projected-8B H3 T2V and native-32B I2V choices remain distinct from the isolated fcys TP2 check.

## Research and final boundary

The [reviewed forum and primary-source ledger](ALL-MODEL-P2P-RESEARCH-2026-11-05.md) keeps hardware, implementation and measurement differences explicit. AMD's [ROCm7.2 RCCL guidance](https://rocm.docs.amd.com/projects/rccl/en/docs-7.2.0/how-to/rccl-usage-tips.html#enabling-peer-to-peer-transport) requires peer-capable GPUs and proper large BAR support for PCIe peer transport. The firsthand [XTX H3 comparison](https://lcz.me/topic/2664) illustrates why sampling and whole-workflow timing differ; its numbers are not assigned to this host.

Final boundary: All owned test runners/scopes exited, KFD was empty and fresh kernel/storage/temperature checks passed before activation. The owner authorized archiving the reviewed global STOP/GPU hold and enabling only nine qualified routes; failed/retired routes remain held. No new GPU trial or failed-profile retry was run.

Normal disposition: Nine qualified normal routes are enabled after the owner-authorized archive of the reviewed global STOP/GPU hold. All six failed or inconclusive cases remain held, and deleted XS/SuperIQ3 routes remain retired. All guards, source/weight pins, stock boot default, unrelated services and paused schedules remain. Existing fault and STOP history remains preserved. No automatic retry, long benchmark, boot-default change, unrelated service reset or schedule change was performed.
