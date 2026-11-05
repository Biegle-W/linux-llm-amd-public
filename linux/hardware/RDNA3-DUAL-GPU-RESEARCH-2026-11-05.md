# RDNA3 dual-GPU research — November 5, 2026

**Radiance now includes a gfx1100 backend, but optimized dual-RX-7900-XTX TP is not established.** The strongest working TP evidence on this workstation remains vLLM/SGLang for LLMs and the separate bounded H3 TP2 experiment. Normal llama.cpp, native streaming engines and the normal graphics workflows use other forms of placement.

## Radiance: current source versus forum reports

The current standalone engine is Radiance **1.17.0**, commit `19d4e8fe0e18071b9b6300f15fc4ccf38dc4fa3d` (November 4). Its `libr3d` library targets gfx11, including **gfx1100**. It uses architecture-specific kernels and software substitutions for unsupported FP8 conversion and other operations. Crucially, its documentation says **“No collective rows”**: this device library supplies no all-reduce implementations. Several MoE W4A8 paths also remain unfinished. This establishes backend coverage, not a fast TP2 result on these cards. [Pinned RDNA3 source](https://codeberg.org/StillDeadcode/radiance/src/commit/19d4e8fe0e18071b9b6300f15fc4ccf38dc4fa3d/libr3d/README.md).

The [dual-R9700 forum thread](https://lcz.me/topic/2417/95) reports RDNA3 support reaching main and describes LLM progress while image generation still needed testing. The newer [Radiance overview](https://lcz.me/topic/2826/3) discusses concurrency and H3 multi-card use, largely through R9700 examples. R9700 is RDNA4; these reports do not supply a reproducible two-24-GiB-XTX result with matching model, quantization, context, topology and complete elapsed time. Older statements that Radiance is exclusively RDNA4 predate the new backend.

Radiance's general guide documents TP and host-memory collective fallback, plus image/video model plugins and an H3 `--tp 2` example. That engine-wide example does not establish `libr3d` collective coverage. A reference fallback may change feasibility and speed; no local result currently establishes that path. Two cards retain separate memory allocations, workspace requirements and communication costs. [Engine guide](https://codeberg.org/StillDeadcode/radiance/src/commit/19d4e8fe0e18071b9b6300f15fc4ccf38dc4fa3d/docs/GUIDE.md).

A separate [gfx1100 vLLM-Radiance deployment](https://github.com/mkadrlik/vllm-radiance-p2p) documents two RX 7900 XTX cards running quantized Qwen with TP2. This is the older vLLM fork/container lineage, distinct from standalone Radiance 1.17. Its maintained profiles include Qwen3.8 27B AWQ, while older Quark profiles are marked legacy. The repository warns that mutable/default builds have targeted gfx1201 and provides a specific gfx1100 adaptation; its tuning notes disable Radiance fast reduce. This is useful third-party, hardware-specific feasibility evidence. It does not qualify our downloaded checkpoints or establish an optimized standalone RDNA3 collective path. No container or GPU test was launched here.

## What the current workstation actually proves

| Route | Dual-card method | Evidence and limit |
|---|---|---|
| Qwen27B/vLLM, Bolt, Sage, Qwen27B/SGLang | Tensor parallel, TP2 | Completed tool requests; both-direction RCCL P2P/IPC and reviewed collective paths. |
| Empero, Flint, Ornith / llama.cpp | Layer split, `tensor-split=1,1` | Cross-device peer-copy API events during inference; the current presets use `split-mode=layer`. The option name does not turn this placement into tensor parallel computation. |
| Maya / Strata DeepSeek | Dual-card layer groups and CPU/NVMe tiers | Short functional evidence; no direct peer-copy or tensor-parallel speed claim. |
| Normal Flux / Qwen Image / H3 | Denoiser, encoder and VAE placement | Completed image/video workflows; no observed cross-device copy in the reviewed request intervals. These are component workflows. |
| Separate fcys H3 TP2 | Distributed model computation | Complete finite output, both ranks and RCCL P2P/IPC observed. Cached conditioning excludes text-encoder cost. It remains isolated. |

[Local methods and transport evidence](ALL-MODEL-P2P-2026-11-05.md) · [Saved numeric cases](results/ALL-MODEL-P2P-2026-11-05.json). A short pass supplies no sustained stability, full-window-quality or matched speed ranking.

## Image and video alternatives

[Raylight](https://github.com/komikndr/raylight) uses xDiT sequence parallelism to divide token work and FSDP to shard weights; these have different memory and communication costs from LLM tensor parallelism. It lists Flux, Qwen Image, HunyuanVideo and H3 variants. Its documented AMD examples are MI210/MI300X, so this is a candidate for RX 7900 XTX, rather than a measured qualification here. Its NVIDIA NCCL package and architecture-specific attention instructions require ROCm review before reuse. CFG parallelism provides little benefit for guidance-distilled workflows with CFG=1. [xDiT source](https://github.com/xdit-project/xDiT).

The existing separate H3 TP2 result is the most direct local starting point for H3. A useful comparison must include cold loading, encoder/conditioning, denoising and VAE/output work at the same model, dimensions, frames, steps and seed. The cached 93.3-second experiment cannot be ranked against an uncached normal workflow as an end-to-end speedup.

## Downloaded weights and practical next checks

- Existing Qwen27B AutoRound GPTQ safetensors already serve vLLM and SGLang from one backing. Radiance documents W4A16 import recipes, including AutoRound, but this exact local checkpoint/plugin combination still needs compatibility verification.
- Radiance accepts supported checkpoints or converted `.rad` containers. A conversion is an additional artifact; it does not make the existing Maya/Strata GGUF metadata packs interchangeable with Radiance. Existing shared GGUF backing should be retained.
- Existing diffusion assets are useful only where the selected loader supports their architecture and precision. A listed model family alone does not prove compatibility with a particular quantized checkpoint or its text encoder/VAE.

[Conversion and format documentation](https://codeberg.org/StillDeadcode/radiance/src/commit/19d4e8fe0e18071b9b6300f15fc4ccf38dc4fa3d/docs/GUIDE.md). No Radiance installation, new weights, GPU experiment or recurring schedule was added for this research. Any later qualification needs exact source/kernel/model identities, numerical/tool or media checks, measured transport and the retained resource/100°C/owned-cleanup guards.

## Isolated RDNA3 full-stack build

The correct `perf/rdna3_full_stack` source `2314df44164584f8eb59189d82c20e5362967a2c` produced an isolated wheel and passed native-kernel import and CLI smoke audits on retained Torch2.13/HIP7.2. The generated HIP commands target only gfx1100. All80 applicable Python dependency requirements were satisfied; these are dependency checks, separate from the previously reported111 CPU tests.

Build preparation exposed missing MIOpen and hipSPARSELt metadata in the retained SDK. Matching checksum-verified ROCm7.2.3 packages were extracted only into private build overlays. Private host-math/libc linker scripts corrected incompatible Conda absolute paths. All native modules then linked, but the Rust phase reached the unchanged100°C CPU guard before wheel output because C++MAX_JOBS did not constrain Cargo. Clean owned teardown and zero swap/spill were verified. That hold was freshly reviewed and archived intact. A separate corrected build used one Cargo job and inherited affinity to two logical CPUs on distinct physical cores; actual cargo/rustc limits were verified. It completed without relaxing any guard. Original Torch/ROCm, environments, source artifacts and model/input/user state were retained.

The first actual fork-source Qwen case kept the normal163840-token allocation, TP2, MTP3, BF16 KV, custom-all-reduce setting and resource guards. Native fork attention was hash-pinned; the selected global wheel's separate optional prefill port was not applied to this fork. An extra preflight's incorrect expectation of a standalone skinny library was corrected before any model case; the actual skinny/GPTQ operators are linked into `_rocm_C` and their registrations passed. No model case was repeated.

Qwen then failed during startup warm-up with `AttributeError: 'CommonAttentionMetadata' object has no attribute '_seq_lens_cpu'`. It never became ready and accepted no inference request. The planned near160K prefill/tool check was therefore **not reached or qualified**. Final owned cgroups/KFD clients were empty, maximum recorded owned swap and VRAM spill were zero, and fresh post-stop kernel/thermal/storage/RAM checks passed. Its exact own hold was archived intact. The model case is final: no retry, local compatibility shim or production promotion was attempted. All13 previously qualified route selections remain unchanged; no scoped job or GPU lock remains. Candidate build artifacts are retained, and nothing was deleted.
