# DeepInfer compatibility assessment — October 20, 2026

**Upstream DeepInfer is not currently usable on this dual RX 7900 XTX workstation.**
This is a source/documentation assessment, not a failed local inference benchmark.
No engine was installed, no upstream script was executed and no weights were
downloaded. Active runtime profiles and the DSH default are unchanged.

Reviewed upstream main at commit
[`774ce244b87cc0eb8d4b94ab9f5de2ab22049f01`](https://github.com/deepseek-ai/DeepInfer/commit/774ce244b87cc0eb8d4b94ab9f5de2ab22049f01),
resolved with `git ls-remote` on October20. All links below pin that revision;
later upstream work could change this conclusion.

## Fit for the workstation

| Area | Published implementation | Consequence here |
|---|---|---|
| Accelerators | NVIDIA SM100 and Huawei Ascend950 | Neither RX7900XTX/gfx1100 is a documented target |
| Build selection | NVIDIA or Ascend | Installing ROCm does not select an AMD backend |
| Model | DeepSeek-V4.1-Flash | This is a specialized engine, not a replacement for every active model |
| Input checkpoint | Hugging Face checkpoint directory with config and safetensors | Existing Maya GGUF packs are not the documented loader input |
| Public workflow | Offline examples, with additional components needed for full serving | It is not a ready replacement for the current DSH/OpenAI gateway |

The model/hardware/offline scope is documented in the
[pinned README](https://github.com/deepseek-ai/DeepInfer/blob/774ce244b87cc0eb8d4b94ab9f5de2ab22049f01/README.md).
Checkpoint loading is described in the
[pinned examples guide](https://github.com/deepseek-ai/DeepInfer/blob/774ce244b87cc0eb8d4b94ab9f5de2ab22049f01/examples/README.md).

## Code-level checks

The [build script](https://github.com/deepseek-ai/DeepInfer/blob/774ce244b87cc0eb8d4b94ab9f5de2ab22049f01/build.sh)
accepts only `nvidia` or `ascend` for `DEEPINFER_ACCELERATOR`.
The [device-discovery implementation](https://github.com/deepseek-ai/DeepInfer/blob/774ce244b87cc0eb8d4b94ab9f5de2ab22049f01/deep_cluster/hardware/device.py)
checks Ascend and NVIDIA; otherwise it reports CPU and zero accelerator devices.
Its CPU topology helpers do not provide a documented CPU-only inference build.
The [extension setup](https://github.com/deepseek-ai/DeepInfer/blob/774ce244b87cc0eb8d4b94ab9f5de2ab22049f01/setup.py)
selects an Ascend extension or CUDA extension; the latter links the CUDA driver.

Inference from those checks: an environment-variable change, more RAM or a PCIe
switch cannot supply the missing AMD implementation. A working port would need
kernels, discovery/build and communication integration, then gfx1100 correctness,
quantization, dual-card and memory validation. No such locally validated port was
found in this review. This does not claim that no experimental fork exists.

## Why its performance reports do not transfer

The README attributes its published prefill and decode measurements to4 and64
SM100 GPUs respectively, within scale-up domains. Those counts describe the
benchmarks; they are **not** a claim that every example requires64 GPUs.
The [deployment Q&A](https://github.com/deepseek-ai/DeepInfer/blob/774ce244b87cc0eb8d4b94ab9f5de2ab22049f01/doc/inference_deployment_qa.md)
describes expert/data parallelism, production cache infrastructure and speculative
verification, including DSpark. These designs target a different serving system
and communication environment. No published cluster rate is treated as a local
speed or single-user latency estimate.

The reviewed examples do not establish a path equivalent to this workstation's
Maya-S/GGUF plus bounded CPU experts/GPU hot-cache/NVMe streaming. That is a
compatibility gap, not a newly measured RAM requirement. Keep the existing Maya
DeepSeek profile; this assessment does not change its quantization or guards.

## Community check and disposition

Consulted lcz.me and Level1Techs via exact-name site searches and their public
front pages on October20. Queries included `site:lcz.me "DeepInfer"` and
`site:forum.level1techs.com "DeepInfer"`. No relevant indexed DeepInfer/gfx1100
local result was returned. The lcz.me public page required JavaScript and exposed
little crawlable content, so this is not an exhaustive search of new/unindexed
posts. No forum-derived setting or performance claim is adopted; there is no
verified DeepInfer post URL to cite as a successful dual7900XTX deployment.

Disposition: **research only, no installation or new launcher**. Reconsider if
upstream or a reviewed fork adds a working gfx1100 path and compatible low-bit
expert offload/loading. The machine's currently validated Strata result is
[recorded separately](STRATA-STARTUP5-2026-10-20.md).
[Source fingerprints and assessment record](results/deepinfer-assessment-2026-10-20.json).
