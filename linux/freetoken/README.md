# FreeToken ROCm experiment — October 18, 2026

Installed as `ft-rocm`. The incompatible NVIDIA-only Desktop beta
`0.2.0-beta.23`, its CUDA engine environment and original `ft` link were removed
at the user's request later on October 18. Saved Desktop application data is
retained; the AMD runtime and Qwen profile still work. This is a source-built
inference engine,
not an AMD-enabled replacement Desktop installer.

The user explicitly allows **one RX 7900 XTX for FreeToken only**. GPU1 is the
default; every other engine still requires both cards. Upstream GGUF embeddings
reject TP2 with `GGUF tables are not sharded over TP`. Passing RCCL communication
tests does not remove that model implementation restriction.

## Exact isolated stack

| Component | Installed revision/version |
|---|---|
| FreeToken source | `8f49e0af98ba444dd261af69e82d5a1841778c68` (`0.1.3` metadata) |
| Python | 3.12.14 |
| AMD PyTorch | `2.14.0+rocm10.1.0` |
| AMD torchvision | `0.29.0a0+rocm10.1.0` |
| ROCm modular SDK packages | `10.1.0`, including gfx1100 device libraries |
| Reported HIP runtime | `7.16.26385` |
| AMD Triton | `3.8.0+git669b31ac.rocm10.1.0` |

Everything is inside `freetoken/.venv-rocm`, `upstream` and ignored local cache
folders. Existing kernel drivers, production ROCm/vLLM/SGLang environments and
model files are unchanged. No additional models were downloaded.

`install.sh` records the source revision and exact package lock. The only local
upstream patch permits AMD's official torchvision alpha dependency version;
it does not change inference algorithms. Do not install CUDA-only acceleration
extras. Reproduction needs `uv`, Git, a C/C++ build toolchain, working gfx1100
kernel drivers and compatible Linux headers. Run from the repository:

```bash
./freetoken/install.sh
./freetoken/run --version
./freetoken/run serve --help
```

`bin/install.py` installs the separate `ft-rocm` PATH wrapper. The wrapper defaults
to GPU1/TP1, one request, Triton attention, native torch/RCCL routing, 128-token
prefill chunks and graphs disabled. Chunks above 128 are rejected because the
GGUF Q6_K dispatcher failed at 256 on gfx1100. It refuses
to start while known inference ports are occupied or the selected GPU has
less than 20 GiB free, including while another backend is still loading. It does not automatically
terminate programs or expand existing backend shutdown targets. Stop its own
terminal before starting another backend; existing managed launchers refuse
unknown GPU compute processes.

## Validation and limits

- Dependencies are compatible; both native pinned-memory/CPU-MoE extensions load.
- Both gfx1100 GPUs pass arithmetic and native RCCL FP32/BF16 all-reduce and
  all-gather (all-reduce: 1, 4,096 and 1,048,576 elements; all-gather: one
  value per rank); direct P2P remains disabled.
- Seven upstream ROCm architecture/launch-argument tests and local CLI tests pass.
- Qwen 35B MoE, 8K, CPU-backed experts + 6 GiB GPU cache: two startup attempts
  were stopped by our worker-swap guards at 449 MiB and 1,110 MiB respectively.
  The second retained at least 6.37 GiB available RAM and had no VRAM spill.
  These were controlled guard stops, not evidence of an upstream OOM or a
  working serving profile. Larger-RAM MoE validation remains pending.
- **Qwen 27B Q4_K_M, GPU1, 8K, prefill chunk 128: passed arithmetic, JSON
  and a complete tool-call/result round trip.** No worker swap or VRAM spill;
  GPU1 peak 18.97 GiB; minimum available system RAM 20.07 GiB. Ready in 64.08 s
  after the native GGML cache had been built (first cold native compile was slower).
- The short code probe returned 100 output tokens in 2.584 s, **38.7 output
  tokens/s end-to-end**, including prefill/API overhead. This is one short probe,
  not isolated decode throughput, a matched engine comparison or an 8K-fill test.
- The first dense attempt passed arithmetic/JSON but crashed on the longer tool
  prompt with `no ggml kernel for q6_K with M=256`. Chunk 128 resolved that
  tested failure without an inference source patch.

Curated [validation record](validation-2026-10-18.json). The passing profile
is deliberately small; full 8K filling, vision, MTP, graphs and MoE generation
are unvalidated.

Raw model logs and environments are ignored. Curated results are kept separately
from the raw logs; do not equate a running HTTP listener with model readiness.
No performance advantage, MTP operation or full-window accuracy is claimed.

## Start the tested Qwen profile

Close the existing inference terminal first, then run:

```bash
ft-rocm qwen
```

This fixed profile reuses the existing Qwen 27B GGUF path from `dsh/models.json`,
loads on GPU1 and stays in the foreground. API base: `http://127.0.0.1:1919/v1`;
model: `qwen3.8-27b-q4-freetoken`. It is loopback-only and is not registered in
DSH or the authenticated LAN/Tailscale gateway. Ctrl+C stops its own runtime.
For a terminal chat interface, open a second terminal after the server is ready:

```bash
ft-rocm shell
```

This attaches to the existing server without starting another model. Use
`ft-rocm serve --help` for upstream custom-serving options.
Initial FreeToken validation restored the then-running vLLM session. The later
Nemotron Q4 update left llama.cpp active; close that inference terminal before
starting FreeToken. No FreeToken model is left running by validation.

## Desktop frontend and API clients

The installed AMD engine is the source-built CLI, not a verified one-click
AMD Desktop package. The removed Desktop beta bootstrapped a CUDA engine.
Upstream still describes [AMD installation as WIP](https://github.com/FlashML-org/FreeToken/blob/8f49e0af98ba444dd261af69e82d5a1841778c68/docs/install_amd.md);
[Desktop release artifacts](https://github.com/FlashML-org/FreeToken-Web/releases)
do not establish that its GPU selector/bootstrap works with this isolated build.
The [installer](https://github.com/FlashML-org/FreeToken/blob/8f49e0af98ba444dd261af69e82d5a1841778c68/install.sh)
has a `FREETOKEN_HOME` engine-discovery mechanism, but connecting
that Desktop frontend to this ROCm environment has not been validated here.

Use `ft-rocm qwen` and an OpenAI-compatible API client on the Linux PC. Base URL
`http://127.0.0.1:1919/v1`, model `qwen3.8-27b-q4-freetoken`; this loopback test
profile does not require an API key (a client may use a dummy value such as
`local`). Close the running inference backend first. The wrapper also refuses
the owned MoE validation port 18030 to prevent overlap during Q4 testing.

## Sources

- [Pinned source](https://github.com/FlashML-org/FreeToken/tree/8f49e0af98ba444dd261af69e82d5a1841778c68),
  [AMD install guide](https://github.com/FlashML-org/FreeToken/blob/8f49e0af98ba444dd261af69e82d5a1841778c68/docs/install_amd.md),
  [RDNA ROCm foundation, merged PR 132](https://github.com/FlashML-org/FreeToken/pull/132).
  The guide's older Torch stack is superseded by the pinned source's 2.14 dependency.
- [Official AMD PyTorch installation](https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/frameworks/pytorch/install.html)
  and [AMD wheel index](https://stable.repo.amd.com/rocm/whl-next/).
- [GGUF embedding TP restriction](https://github.com/FlashML-org/FreeToken/blob/8f49e0af98ba444dd261af69e82d5a1841778c68/python/freetoken/layers/quantization/embedding/gguf.py),
  [GGML kernels, merged PR 690](https://github.com/FlashML-org/FreeToken/pull/690).
- [Level1Techs FreeToken discussion](https://forum.level1techs.com/t/freetoken-an-llm-engine-to-max-the-bandwidth-of-all-the-things/254396),
  eduncan911, August 25: research lead, not a local AMD performance measurement.
  [lcz.me topic 2059](https://lcz.me/topic/2059) is a single-XTX/64 GB **Strata**
  offload example, not FreeToken validation. See the
  [forum source trail](../hardware/FORUM-OPTIMIZATION-SOURCES.md) for distinctions.
