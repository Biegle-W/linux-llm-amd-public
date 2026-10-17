# AMD ROCm setup and fastest-runtime selection

> Historical single-AMD measurements. Current dual-AMD settings and the blocked
> SGLang MTP profile are documented in the [migration report](../UPGRADE-DUAL-7900XTX.md).

**Later context update:** SGLang MTP is now 40K BF16, static fraction 0.92,
MTP2. Its earlier rejected 32K attempt is superseded by the tested budget and
verification configuration. DFlash2 remains 16K. See
[the context comparison](../SGLANG-CONTEXT-2026-10-16.md).

**Superseded settings and measurements:** the later [speculative comparison](../SPECULATIVE-2026-10-16.md)
repairs SGLang JIT compilation, disables the problematic optimized verification
adapter, retains corrected MTP2 and adds a validated 16K DFlash2 profile. The
original migration measurements below are historical, not current-setting results.

The latest user preference is measured speed. Bolt remains on Vulkan after
testing HIP; Qwen’s AMD vLLM/SGLang environments use ROCm. Within those two
Qwen profiles, SGLang is the faster decode option and vLLM is the 64K capacity
option. These are different contexts/cache settings, not an isolated engine A/B.

Both runtimes use **the 7900 XTX alone, TP1**, with no CPU weight offload. The
RTX 4070 is idle for these profiles. Host RAM is still temporarily 32 GB.
Backends use the existing visible Desktop/PATH launchers; start DSH separately.

| Backend / API model | Context | Quant and cache | Native MTP | Short decode | Prefill proxy |
|---|---:|---|---|---:|---:|
| SGLang / `qwen3.8-27b-sglang` | 16,384 | GPTQ W4A16, BF16 KV | 2 steps, 3 draft tokens | 54.70–62.48 t/s | 1,022–1,075 t/s |
| vLLM / `qwen3.8-27b-vllm` | 65,536 | GPTQ W4A16, Q4 per-token/head KV, 1.75 GiB cache | 3 draft tokens | 29.68–34.68 t/s | 668–677 t/s |

These are two short local inventory-writing samples: 3,424 input tokens and 256
output tokens, greedy decoding, warm kernels, unique prompts. Decode is externally
timed after first visible text. Prefill proxy is input tokens divided by TTFT;
it includes scheduling and first decode and is not a pure kernel benchmark.
See [machine-readable results](results.json). Speeds vary with content, acceptance
rate and context; neither result is a guarantee for an entire context window.
The earlier llama.cpp Qwen Q4 MTP test (~80.6 t/s) remains faster on this hardware
for its recorded workload; changing backend is not automatically an upgrade.

Both profiles passed arithmetic and structured tool-call/tool-result checks.
SGLang recovered three markers from a **14,500-token** prompt in **15.84 seconds**.
vLLM recovered all three markers from **59,995 tokens in 529.54 seconds**.
That is about 8 minutes 50 seconds: 64K is a capacity profile, not a claim of
fast full-window prefill. No per-process VRAM eviction was observed during the
final test; ordinary resident GTT transfer buffers were about 8.1 MiB.
The short vLLM validation ran alongside CPU compilation; its timing is indicative.
SGLang's observed whole-card VRAM was about **22.89 GiB**, including the desktop.
The smaller native MTP/state allocation and CPU-rendered launcher terminal retain
roughly 1 GiB of observed free VRAM in that SGLang test. vLLM initialization
briefly approached full VRAM and logged recovered allocator retries; steady
inference used about 21.6 GiB whole-card VRAM in the final test. The launchers require 22.25 GiB free before loading.

## Runtime and storage

- vLLM official ROCm nightly `0.32.0rc1.dev190+g3f1bcfd82.rocm723`.
- SGLang Radeon fork `StevenChenSE/sglang`, `gfx1100-support`, source
  `f84475ccf593087df3d1da13c9e675eadee12352`, plus opt-in vocabulary sharing.
- Isolated PyTorch 2.13.0+git733fca1 / HIP 7.2; private ROCm 7.2.3 SDK.
- Shared checkpoint: `GGUF-Models/Qwen3.8-27B-W4A16-AutoRound-GPTQ` on SATA,
  18.68 GiB including retained vision/extra tensors. Source revision and hashes:
  [model-source.json](model-source.json).
- Target linear weights are GPTQ INT4/group64; embedding/output head and MTP remain
  unquantized. Activations and Mamba state use BF16. This is a text-only profile.
- Existing LowLatency compressed-tensors checkpoint and HyperQwen drafter are retained.
  No model weights were copied to NVMe. Environments and compiled caches live there.

The original LowLatency checkpoint has an INT8 output head. It worked in vLLM with
FP16 activations, FP8 KV and MTP3 at 64K, recovering 59,995 input tokens in 355.11 s
(354.24 s engine prefill, ~169.4 input t/s), but short decode was only 28.5–30.0 t/s.
The new GPTQ quant avoids SGLang's four-bit-kernel/INT8-head incompatibility and
supports BF16 activations in both runtimes. Its BF16 MTP metadata is corrected locally;
weight files are unchanged and SHA256-verified.

## Configuration and validation limits

SGLang: Triton attention, BF16 KV, 512-token prefill chunks, one request, lazy
Mamba radix buffers, four Mamba slots, two-step MTP, decode graphs at batch one.
A nominal 32K MTP3 configuration only allocated about 24.5K actual KV and left
almost no desktop VRAM reserve, so it was rejected. MTP3 at 16K was faster on one
sample but had less reserve; MTP2 is the retained balance. ReplaySSM is disabled
because that optional kernel selects unsupported TF32 on gfx1100.

vLLM: RDNA3 W4A16 linear kernels, Triton attention, BF16 Mamba state, Q4 KV,
512-token prefill chunks, one request, MTP3 and decode graphs 1/4 with Inductor
compilation disabled. The allocated cache reports **74,898 tokens**; the served
limit is **65,536**, reserving a useful margin. Q4 cache quality checks here are
small functional tests, not comprehensive task-accuracy validation.

Use `llm-sglang` / `llm-vllm` over SSH, or their Desktop launchers. In DSH choose
**Local SGLang** or **Local vLLM**, then the existing Qwen model. Native loopback
APIs remain ports 30000 and 30010. Authenticated LAN/Tailscale clients use the
existing port-10000 gateway and existing key. No firewall or authentication changes.
Starting a backend closes only the configured inference workers, preserving DSH,
Turnstone, the gateway and unrelated applications.

[Installation/pins/local patches](INSTALL.md) · [lcz.me DFlash2 findings](DFLASH.md)

DFlash2 is researched but not activated. The forum's advertised performance and
196K/217K examples use two 7900 XTX GPUs; they cannot be copied onto this card.

## llama.cpp comparison: keep Vulkan for Bolt

The existing llama.cpp launcher / `llm-llama` keeps `vulkan-amd` in
`dsh/llama-runtime.json` because it measured faster for Bolt. A tested HIP
alternative is available in `dsh/models-hip.ini` and the separate
`llama.cpp/build-hip/bin/llama-server`. Source remains
`f12aaa344c971556ec35be054d7aac1d901fd510`. Build with
`hardware/build-llama-hip.sh`; private ROCm 7.2.3, gfx1100, HIP graphs, Q8 KV,
64K context, no speculative decoding, no CPU weight offload.

Bolt passed arithmetic, tool calls and **59,990-token retrieval** without
truncation. All **89/89 layers** and embeddings are on ROCm0; CPU model buffers
are zero. Driver residency samples showed **zero nonresident VRAM**. Whole-card
peak was **21.78 GiB**; the HIP launcher requires 22.75 GiB free before loading to
retain roughly 1 GiB of headroom. Normal small host compute/transfer buffers
remain. The test had at least 22.6 GiB host memory available; existing OS swap use
is not a CPU weight-offload configuration.

| Bolt test | HIP prefill t/s | HIP decode t/s | Previous Vulkan decode t/s |
|---|---:|---:|---:|
| 3,428 input / 256 output, trial 1 | 834.2 | 67.3 | 75.4 |
| Same workload, trial 2 | 851.5 | 67.0 | 75.2 |
| 59,990-token retrieval | 864.6 | Too few output tokens for comparison | — |

The user's latest instruction is to select the fastest setting. **HIP did not
improve Bolt's short decode speed** in these separate-session measurements. Historical Vulkan
prefill was 804–807 t/s for the short trials and 855 t/s near 60K.
The Vulkan build and `dsh/models-amd.ini` remain active. To test HIP explicitly,
set only `backend` to `hip-amd` in `dsh/llama-runtime.json` and relaunch
`llm-llama`; retain the model list and source commit. Both modes use the same
SATA GGUF and API model ID. HIP never attempts mixed AMD/NVIDIA tensor parallelism.

The Vulkan launcher identifies the 7900 XTX by name, exposes only that physical
device, and verifies its filtered `Vulkan0` identity before handover. After the
latest reboot, the unfiltered order is NVIDIA `Vulkan0`, AMD `Vulkan1`; presets
remain AMD-only and no longer depend on that changing order.

## Final integration

The existing visible terminal launchers and authenticated gateway streaming passed
for all three active models. vLLM → SGLang → Vulkan Bolt handover stopped only
configured inference workers; the API gateway remained running. SGLang's
production 14,500-token retrieval passed in 15.63 seconds with zero observed
nonresident VRAM. Direct LAN/Tailscale client paths were not retested from another
computer; addresses, key and firewall rules are unchanged. Temporary validation
workers were stopped afterward. Use the normal Desktop/PATH launchers to start.

Eight hardware/preflight checks and fourteen backend-ownership checks pass.
The vLLM ROCm environment passes its package compatibility check. SGLang's
intentional CUDA-only/optional dependency omissions are listed in INSTALL.md.
