# Level1Techs candidate tests — October 17–18, 2026

Dual RX 7900 XTX 24 GB, Intel i5-13600KF/Z690, CPU PCIe4 x8/x8, 32 GB host RAM.
All model trials use Qwen3.8-27B on both cards with GPU-resident weights. Model files were reused;
no new quantization was downloaded. Normal production profiles are unchanged by
these experiments.

## Selection

Retain the current vLLM profile and current Vulkan llama.cpp profile. The
restored rocWMMA candidate loses too much long-prompt prefill speed; its book
decode improvement does not offset that cost. The published Radiance settings
work with the existing GPTQ checkpoint and ordinary host transport, but did not
establish a reason to replace the current runtime. The author's AWQ comparison
was against W8A8, not our GPTQ INT4; no redundant model download was required.

The single-queue trial passed at 124.65 code and 73.57 prose decode t/s, about 6% below the control. Its 64,033-token marker-retrieval check passed, but this is not a sustained long-context throughput test. Leave the hardware queue cap unset. This was a sequential comparison; the
queue trial also reached a higher hotspot temperature, so the test does not
isolate the queue cap from thermal and run-order effects. No new model or
normal launcher was added. The peer fast path
remains unavailable and the manual cooling comparison remains pending.

## Measurements

| Profile | Code decode t/s | Prose decode t/s | Book PP, depth 0 t/s | Book decode, depth 0 t/s | Book PP, depth 16K t/s | Book decode, depth 16K t/s | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Current vLLM GPTQ / BF16 KV / MTP3 | 133.06 | 78.50 | 1556.04 | 92.62 | 1457.42 | 67.54 | passed |
| llama.cpp HIP native / FP16 KV / MTP3 | 67.04 | 40.85 | 1150.06 | 38.80 | 1001.78 | 35.95 | passed |
| llama.cpp restored rocWMMA / FP16 KV / MTP3 | 65.81 | 35.31 | 979.69 | 44.38 | 465.65 | 46.71 | passed |
| Current llama.cpp Vulkan / Q8 KV / MTP3 | 79.38 | 45.53 | 1171.05 | 50.38 | 1031.30 | 51.48 | passed |
| Radiance GPTQ / BF16 KV / dynamic MTP2 | 68.63 | 47.91 | 1399.63 | 43.69 | 870.17 | 14.67 | passed |
| Radiance ROCM_ATTN + AITER / MTP2 | 81.82 | 56.98 | — | — | — | — | passed |
| Radiance ROCM_ATTN + AITER / native MTP3 | 98.35 | 57.99 | — | — | — | — | passed |
| Current vLLM + hardware queue cap 1 | 124.65 | 73.57 | 1577.41 | 88.86 | 1420.46 | 64.84 | passed |
| Radiance ROCM_ATTN + AITER / native MTP3 full | 95.27 | 60.35 | 1606.63 | 59.96 | 1264.54 | 21.55 | passed |

Short tasks use the saved code/prose prompts, temperature 0.6, top-p 0.95, seed 42,
thinking disabled, 256 maximum output tokens, three timed runs plus excluded
warm-up. Report medians. External SSE decode is approximately
`(completion_tokens-1)/(stream_end-first_output)`; speculative bursts limit
precision. Book tests use pinned llama-benchy 0.4.0, seed 42 text/noise, PP 2,048 / TG 128,
greedy decoding, one request at a time, no-cache, three runs plus warm-up.
Unspecified server sampling defaults are retained; cross-engine results are full-profile comparisons.
Book PP is the tool's latency-adjusted estimate. Depth 16,384 adds the prompt and
chat template. It does not mean total input is 16,384 tokens. These are workload
results, not universal speed guarantees or an exact replay of a forum benchmark.

The native/rocWMMA pair has the same GGUF Q4 weights, FP16 KV, MTP3, 64K served
context, 512 batch/128 microbatch, eight CPU threads and 1:1 layer placement.
Only the prefill dispatch changes. The normal Vulkan profile uses Q8 KV and is a
complete-profile comparison, not an isolated HIP-versus-Vulkan API test. vLLM and
Radiance use the same existing GPTQ INT4/group64 checkpoint; no AWQ-versus-GPTQ
claim can be made from these tests. All profiles are configured for 65,536 context; performance
measurements here stop at 16K depth and do not validate sustained near-64K decode.

## Current control configuration

The normal vLLM runtime is `0.32.0rc1.dev190+g3f1bcfd82.rocm723`, isolated
ROCm 7.2.3, PyTorch 2.13 nightly and no-hostcall RCCL 2.27.7. It uses GPTQ
INT4/group64 weights, BF16 activations/KV/Mamba, 3.5 GiB KV per GPU, compiled
MTP3 with full decode graphs, Simple transport, tuned RDNA3 prefill and
2,048-token chunks. The single-queue trial changes only GPU_MAX_HW_QUEUES to 1.
[Existing configuration and validation](VLLM-TUNING-2026-10-17.md).

## What was tested

**Restored rocWMMA:** source `f12aaa344c971556ec35be054d7aac1d901fd510`,
rocWMMA 2.2.0 at `48b7db12a9ade97f0b7ab2ff9321ba0cbb4e5b77` (ROCm 7.2.3 tag).
The isolated port restores the removed implementation only for gfx1100/head size 256
prefill above eight queries. Modern tile/decode paths remain intact, and the
flag `GGML_HIP_LOCAL_ROCWMMA` defaults off. The current launch API's added sparse
argument required adaptation; a first numerical probe caught the missing argument
as a host assertion before the intended prefill launch. The corrected port passed
84 CPU-reference cases: 21 shapes on each GPU, with the path off and on. Required
coverage includes GQA 6, FP16/Q8 caches, query sizes 1/4/33/128 and KV sizes 512/4096, plus the
existing larger cases. The model worker's isolated library and opt-in environment
were checked. Functional probes cover arithmetic, ordered/reversed JSON and a
tool-call/result round trip. These are narrower than a broad accuracy evaluation.

[Build helper](build-rocwmma-experiment.sh), [source patch](patches/rocwmma-prefill-experiment.patch),
[CPU-reference checks](test-rocwmma-experiment.py), [upstream MIT notice](patches/LICENSE.llama.cpp).
The build uses the isolated Release/gfx1100 HIP toolchain; dynamic host-library
resolution is allowed at link time for libedit's GLIBC 2.42 symbols and checked
with `ldd -r` on the actual host before tests. No host libraries are replaced.

**Radiance:** a rootless, read-only container filesystem was used because Docker
is absent on this host. The wrapper was reviewed at
`fc022019051dbedc794572d46a6306585a61a89a`. Its stack reports vLLM 0.26.0,
PyTorch 2.11.0 + ROCm 7.14 and RCCL 2.30.4. Both cards are visible. Host RCCL 2.27.7
cannot be injected into this stack (`ncclDevCommDestroy` ABI mismatch); its own
matched library passed two-rank FP32/BF16 all-reduce/all-gather checks.
Custom collectives, P2P and fast-reduce remain disabled; the existing checkpoint
passed functional checks using native MTP3. The optional draft helper rejected
three-token `tl.arange` because the range is not a power of two, and fell back.
The initial MTP2 timing run used TRITON_ATTN and disabled AITER. Follow-up cases
use the published ROCM_ATTN backend, AITER/linear enabled, GPU_MAX_HW_QUEUES=1
and NCCL_CUMEM_ENABLE=0. The read-only container requires an explicit writable
AITER_JIT_DIR; without it, AITER import fails before model loading. That setup
issue was repaired before measuring those cases. MTP2 uses the dynamic helper;
native MTP3 disables that optional helper. Follow-up cases without book columns
were tested on short prompts only. This is not the author's AWQ configuration and does not measure
his P2P fast path.

Tested image tag digest: `sha256:6253c8e6cf9cfe7dd8ea6730caf12a36bc359dc2f8f9b3a983635f7bb7727721`.
Image config digest: `sha256:83a99bb57356e6313ef93296c7948c156488c8964c89f51e57fc649170f2a86a`.

**Direct-P2P all-reduce:** fresh HIP queries returned false in both directions,
with and without `HSA_FORCE_FINE_GRAIN_PCIE=1`. The reviewed JohnTDI initializer
returns null under that condition. Its peer-read kernel therefore cannot activate
here. No forced kernel allowlist, ACS/IOMMU changes or P2P performance claim was
made. TP2 through ordinary host transport works independently of this limitation.

**Cooling:** the administrator fan helper is prepared, but kernel fan controls
are not writable by the user and passwordless sudo is unavailable. A manual fan
A/B requires the helper and has not been completed. Automatic-fan telemetry in
the tables below does not establish a cooling-induced speedup. The helper restores
the original mode/PWM on exit or timeout and does not lower an already-higher PWM.
[Temporary helper](fan-cooling-test.py):

```bash
sudo python3 hardware/fan-cooling-test.py --percent 75 --seconds 900
```

The first vLLM attempt overlapped image downloading and hit the backend-owned
post-load swap-growth guard, despite available host RAM and no VRAM spill. Its
partial long test is excluded. The clean repeat ran after downloading and
compilation finished. Full throughput cases run sequentially with cleanup between
workers. Existing memory/residency guards remain enabled. The gateway, DSH and
unrelated applications are preserved.

## Reproduction

```bash
bash hardware/build-rocwmma-experiment.sh
source hardware/rocm-env.sh
export LD_LIBRARY_PATH="$ROOT/llm-tools/cuda-build/lib:$LD_LIBRARY_PATH"
python3 hardware/test-rocwmma-experiment.py
python3 hardware/test-level1-peer.py
```

The model benchmark helper accepts `--launch-json` for an isolated command/env/
context/case. Ordinary runs retain their existing behavior. Models, container
filesystems, compiled binaries and raw logs stay outside tracked files. Public
paths remain examples; hardware execution used the operational installation.
The queue-cap definition is documented by
[AMD](https://rocm.docs.amd.com/en/docs-10.0.0/reference/environment-variables/index.html);
its performance effect is workload-dependent and was tested rather than assumed.

## Resource observations

| Profile | Peak hotspot GPU0 / GPU1 °C | Peak memory GPU0 / GPU1 °C | Max nonresident VRAM bytes | Max owned post-load swap growth bytes |
|---|---:|---:|---:|---:|
| Current vLLM GPTQ / BF16 KV / MTP3 | 100.00 / 88.00 | 92.00 / 82.00 | 0 | 0 |
| llama.cpp HIP native / FP16 KV / MTP3 | 98.00 / 79.00 | 88.00 / 78.00 | 0 | 0 |
| llama.cpp restored rocWMMA / FP16 KV / MTP3 | 101.00 / 84.00 | 96.00 / 83.00 | 0 | 0 |
| Current llama.cpp Vulkan / Q8 KV / MTP3 | 102.00 / 85.00 | 94.00 / 82.00 | 0 | 0 |
| Radiance GPTQ / BF16 KV / dynamic MTP2 | 103.00 / 88.00 | 101.00 / 86.00 | 0 | 0 |
| Radiance ROCM_ATTN + AITER / MTP2 | 91.00 / 77.00 | 78.00 / 74.00 | 0 | 0 |
| Radiance ROCM_ATTN + AITER / native MTP3 | 91.00 / 76.00 | 82.00 / 74.00 | 0 | 0 |
| Current vLLM + hardware queue cap 1 | 107.00 / 93.00 | 102.00 / 86.00 | 0 | 0 |
| Radiance ROCM_ATTN + AITER / native MTP3 full | 104.00 / 88.00 | 93.00 / 82.00 | 0 | 0 |

Temperatures, fan RPM and residency are sampled, so brief events can be missed.
Run order, thermals and speculative acceptance can affect rates; no independent
thermal-performance effect was isolated. Raw logs and model outputs remain ignored. The unused 23 GiB extracted
Radiance filesystem and 9.4 GiB compressed layers were removed after tests;
source pins, scripts and measurements remain available locally.
[Sanitized measurements](level1-tests-2026-10-17.json).

## Sources and applicability

- [Level1Techs dual-R9700 report](https://forum.level1techs.com/t/dual-r9700-llama-cpp-rocm-tensor-split-working-p2p-on-proxmox-qwen3-8-27b/254183),
  Twitch_Blade, August 21–25, 2026: rocWMMA/P2P leads, on RDNA4/AM4/Proxmox.
- [Original peer collective](https://github.com/JohnTDI-cpu/llama-hip-p2p-allreduce),
  reviewed `f6f66106f2a960cec2da5a2f1a0f6d476989815f`.
- [Published quantization comparison](https://github.com/mkadrlik/vllm-radiance-p2p/blob/main/docs/qwen38-27b-quant-comparison.md): AWQ versus W8A8 on the author's setup.
- [gfx1100 Radiance port](https://github.com/mkadrlik/vllm-radiance-p2p) and
  [Radiance mirror](https://github.com/magiccodingman/vllm-radiance): implementation
  sources; published AWQ/P2P claims are not local measurements.
- [rocWMMA removal PR26046](https://github.com/ggml-org/llama.cpp/pull/26046)
  and [later head size 256 native-MMA fix PR26419](https://github.com/ggml-org/llama.cpp/pull/26419):
  the forum's historical flag is not a current drop-in setting.
- [lcz.me topic1814](https://lcz.me/topic/1814), Ben Lee, September 18, 2026 measured
  comparison, and [topic1252](https://lcz.me/topic/1252), flyer666's native W4A16/MTP
  setup: baseline/methodology context. Their platforms, memory and workloads differ.
- [Full forum research trail](FORUM-OPTIMIZATION-SOURCES.md).
