# Sanitized Linux runtime handoff — October 17, 2026

**October 17–18 Level1Techs tests:** retain the normal vLLM and Vulkan profiles.
The isolated rocWMMA port passed 84 CPU-reference cases but reduced 16K prefill
from 1,001.78 to 465.65 t/s. Radiance was tested separately with existing GPTQ
weights, native host transport, and custom collectives disabled. Its optional
AITER path needs a writable JIT directory in the read-only container. No new
model quantization or normal launcher was added. The peer fast-path prerequisite
remains false in both directions; manual fan A/B is pending administrator access.
[Measurements and exact experimental scope](../hardware/LEVEL1-TESTS-2026-10-17.md).

**October 17 forum research:** Level1Techs and lcz.me are both required research
sources for HIP/ROCm/C++ tuning. Cite direct posts and primary implementation
links in both repositories. [Source review and decisions](../hardware/FORUM-OPTIMIZATION-SOURCES.md)
separates existing optimizations, untested candidates and hardware-specific
reports. This review changes no runtime flags, model profiles or benchmark data.

The current Qwen vLLM profile is `qwen3.8-27b-vllm`: the existing GPTQ INT4/group64 model, BF16 activations, BF16 KV/Mamba state, compiled MTP3, TP2 across both RX7900XTX cards, 65,536-token served context, 3.5 GiB KV allocation per GPU, and 2,048-token prefill chunks. The allocator reports 98,114 tokens. Keep the one existing vLLM launcher/model entry and launch DSH separately.

Runtime: vLLM `0.32.0rc1.dev190+g3f1bcfd82.rocm723`, isolated ROCm 7.2.3, no-hostcall RCCL 2.27.7, standard host transport, `NCCL_PROTO=Simple`. The current platform has CPU PCIe4 x8/x8 and 32 GB RAM. Weights stay GPU-resident. Peer access remains unavailable; no BIOS, P2P, fan, clock or power changes were applied.

After reinstalling the pinned wheel, apply the existing platform/MTP vocabulary-sharing fixes and `vllm/apply-rdna-prefill.py`. The latter is pinned to exact known attention-source hashes and bootstrap verifies the validated result. The normal launcher enables `VLLM_LOCAL_RDNA_PREFILL=1`; the benchmark explicitly controls it. A changed upstream source requires reviewing and validating the port. Twenty numerical/graph cases across both GPUs and both cache types passed, along with model arithmetic/JSON/tools and near-64K retrieval.

Use the existing Desktop/PATH vLLM launcher (`llm-vllm`) on Linux, then select Local vLLM / `qwen3.8-27b-vllm` in DSH. The native router is loopback `http://127.0.0.1:30010/v1`; worker port is 30011. Remote Windows/phone clients use the configured authenticated LAN/Tailscale gateway, for example `http://LINUX_HOST:18020/v1`, with a locally stored API key kept outside Git. Model ID and endpoints are unchanged. This public reference uses example paths under `/opt/local-llm`; it does not contain the private workstation's addresses, credentials or operational history.

Measured short code/prose medians improved from 79.06/42.27 to 131.34/77.46 t/s. Seeded book PP2048 estimate improved from 1,114.44 to 1,585.23 t/s and book decode from 38.97 to 88.93 t/s. The 64,033-input marker probe returned all markers at 53.73s TTFT. MTP4 was slower and is not selected. An actual production-router test verified the saved flags and prefix reuse: an identical 8K request changed TTFT from 6.50s to 0.53s and hit 7,488 cached tokens. Test workers were stopped; the gateway and unrelated applications were preserved. These tests are narrower than broad accuracy or sustained near-limit decode testing.

See [full measurements and reproduction](../hardware/VLLM-TUNING-2026-10-17.md), [sanitized per-run metadata](../hardware/vllm-tuning-2026-10-17.json), and the [retained Linux/Windows/NVIDIA catalogs](../../README.md). SGLang and other model profiles are unchanged by this task. Historical Windows and NVIDIA snapshots are preserved.

October 17 Level1Techs follow-up: source review now covers patched rocWMMA,
direct-P2P llama.cpp and a separate gfx1100 Radiance/AWQ candidate. None is
locally validated or enabled. Cooling A/B remains the first suggested diagnostic
from existing hotspot-limit telemetry. See the
[research follow-up](../hardware/FORUM-OPTIMIZATION-SOURCES.md#follow-up-additional-level1techs-leads).
