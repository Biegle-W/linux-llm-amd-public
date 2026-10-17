# Qwen 27B speculative decoding comparison — October 16, 2026

> Historical single-AMD measurements. Current dual-AMD settings and the blocked
> SGLang MTP profile are documented in the [migration report](UPGRADE-DUAL-7900XTX.md).

**Later context update:** the MTP production profile is now 40K BF16.
The measurements below retain their original 16K comparison settings.
See [the later context comparison](SGLANG-CONTEXT-2026-10-16.md).

## Scope and method

RX 7900 XTX 24 GB alone, TP1, with 32 GB host RAM. Models remain on Shared
SATA; no CPU weight offload or NVIDIA participation. Existing model files were
reused. GPU tests run sequentially with a 23 GiB whole-card VRAM stop threshold,
a 2 GiB host-available-memory floor, and a post-startup VRAM-residency monitor.
The normal API gateway and harnesses are preserved.

- llama.cpp Vulkan `f12aaa344c971556ec35be054d7aac1d901fd510`:
  UD-Q4_K_M target, 65,536 context, Q8 KV, MTP3, batch/microbatch 512/128.
- SGLang ROCm fork `f84475ccf593087df3d1da13c9e675eadee12352`:
  AutoRound GPTQ W4A16 target, 16,384 context, BF16 KV/state, Triton attention.
  DFlash uses the retained compressed-tensors W4A16 drafter, eight draft tokens
  and a 2,048-token draft window.

`hardware/test-speculative.py` reproduces the synthetic comparison. Each completed
case runs three exact arithmetic checks, an ordered JSON list, a function-call /
tool-result round trip, and a three-marker retrieval at about 13K input tokens.
These are focused smoke tests, not a general quality evaluation.

Throughput uses two trials each of inventory instructions, copying/editing a
Python file, and original prose. Each trial requests 512 output tokens at
temperature zero with thinking disabled. Decode t/s is estimated from streaming
content arrival through completion; speculative bursts make this approximate.
Cold loading is excluded. SGLang's prefix cache is flushed before timed requests.
The code workload measures a 512-token output prefix, not full-file edit correctness.
No new pure-prefill benchmark or maximum-context claim is made here.

## llama.cpp decision

Keep the existing **MTP3** production profile. Adding `ngram-map-k4v` with
`n=32, m=48, min-hits=1` passed the same checks but provided no useful speed gain
on these inputs. The source has separate n-gram and MTP draft limits; MTP3 does
not itself cap n-gram proposals at three. Results do not rule out gains for other
copy-heavy/repetitive workloads.

| Vulkan strategy | Inventory decode t/s | Code output t/s | Prose decode t/s | Peak whole-card VRAM |
|---|---:|---:|---:|---:|
| MTP3 | 81.97 | 104.91 | 56.97 | 18.61 GiB |
| n-gram map + MTP3 | 81.35 | 104.54 | 56.87 | 18.47 GiB |

Both passed arithmetic, ordered JSON, tool round trip and 13,048-token marker
retrieval, with zero sampled nonresident VRAM. This comparison did not retest
near 64K; the unchanged MTP profile retains its prior near-window validation.

## SGLang findings

The existing MTP2 profile repeatedly returned duplicated/out-of-order integers for
`Return only a JSON array of the integers from 1 through 12 in order. No markdown.`
Arithmetic, tool calls and marker retrieval still passed. After repairing JIT
compilation, plain decoding returned the correct array; MTP2 still failed it.
This is a concrete counterexample to treating the short earlier smoke checks as
sufficient quality validation. It does not establish the internal root cause.

The JIT repair adds the same private GCC 14.4 toolchain/sysroot already used by the
AOT build to `sglang/run-rocm`, including `CXX` and
`HIPCC_COMPILE_FLAGS_APPEND`. Previously the fallback KV-copy kernel hid missing
C++ headers in speculative mode, while the plain decoder's required
`clamp_position` kernel failed outright. Plain and MTP2 now run without those JIT
compile failures. No system compiler or driver was installed.

The MTP controls isolated a working configuration: **standard Triton verification
(`SGLANG_RDNA_VLLM_VERIFY=0`) with MTP2** passed the complete suite. Reducing MTP
to one draft step and disabling graphs with the optimized adapter still failed
the ordered JSON check. The standard-verification setting is now the launcher
default; MTP2, 16K context and graph execution are retained. These observations
implicate the optimized adapter path for this setup, not a proven general defect
in every MTP/DFlash implementation.

| SGLang configuration | Inventory t/s | Code output t/s | Prose t/s | Ordered JSON |
|---|---:|---:|---:|---|
| Plain, JIT repaired, optimized decode adapter | 36.73 | 36.89 | 37.57 | pass |
| MTP2, JIT repaired, optimized adapter | 58.50 | 71.63 | 50.07 | fail |
| MTP1, JIT repaired, optimized adapter | 53.68 | 58.38 | 49.68 | fail |
| MTP2, standard verification | 53.93 | 62.22 | 46.39 | pass |

Corrected MTP2 peaked at 20.99 GiB whole-card VRAM and had zero sampled
nonresident VRAM. It passed the 13,048-token retrieval check. The speed comparison
must exclude failing configurations when selecting a production setting.

Initial DFlash8 attempts with the optimized adapter:


- At the existing memory fraction 0.85, loaded target + draft + recurrent state
  left no usable KV allocation.
- Raising the budget to 0.92 allowed 16K startup, but requests exceeded the
  23 GiB whole-card safety threshold. The test stopped its own worker.
- Two recurrent-state slots with prefix caching are unsupported: the fork needs
  four slots per request under this configuration and refused startup.
- Disabling prefix caching allowed two slots and reached inference. Arithmetic
  and a tool round trip passed, but the ordered JSON test repeated numbers and a
  longer workload again crossed the VRAM limit. No sustained DFlash t/s result
  was obtained. GPU weights remained resident in sampled measurements; crossing
  the headroom guard is not evidence of an OOM or observed weight offload.

## Activated DFlash2 profile

Standard verification also corrected DFlash's ordered JSON response. With prefix
caching enabled it measured 85.1 / 148.5 / 47.6 t/s but crashed during the 13K
prompt with `Can not alloc mamba cache`; it was not activated in that form.

The successful configuration disables prefix caching and uses two Mamba state
slots. It passed all checks, including the same 13,048-token retrieval, and peaked
at **22.69 GiB whole-card VRAM** with zero sampled nonresident VRAM.

| Activated SGLang DFlash2 | Inventory | Code output | Prose |
|---|---:|---:|---:|
| Mean decode t/s | 82.99 | 147.91 | 45.91 |

Configuration: memory fraction 0.92, 16,384 context/total tokens, four-bit
compressed-tensors drafter, eight draft tokens, 2,048 draft window, two recurrent
state slots, `--disable-radix-cache`, standard verification, one request. Existing
target/draft weights on SATA are reused. The launcher requires **23 GiB free AMD
VRAM** for this profile, separately from the less demanding MTP profile.

Start **SGLang** / `llm-sglang`, then select **Local SGLang → Qwen3.8-27B SGLang AMD
(16K, DFlash2)** in DSH. API ID: `qwen3.8-27b-sglang-dflash2`. Existing MTP remains
`qwen3.8-27b-sglang`; both share the launcher and are loaded one at a time. The
LAN/Tailscale gateway advertises both, and Turnstone's catalog is refreshed.
The overall DSH/Turnstone default remains the 64K llama.cpp Qwen Q4 profile.

DFlash wins this code-output comparison, ties llama.cpp approximately on inventory,
and loses to llama.cpp on prose. Its 16K context is smaller than llama.cpp's 64K,
and disabling prefix caching can increase later-turn prefill latency. It is an
option for appropriate workloads, not a universal replacement. These smoke tests
do not establish broad task quality equivalence.

## Normal launcher and client validation

Both production IDs passed through the normal visible SGLang launcher: arithmetic,
ordered JSON, three additional ascending/even/descending sequences, function-call
and tool-result handling, and authenticated streaming through the port-10000
gateway. Both recovered all markers from **14,500 input tokens** via the actual
worker: MTP 15.77 s, DFlash2 15.22 s total request time. These short-answer retrieval
timings are not sustained full-context decode benchmarks. Whole-card peaks during
these integration checks were approximately 20.97 and 22.65 GiB respectively.
LAN/Tailscale addresses and authentication remain unchanged; no remote Windows
or iPhone client was used in these local gateway checks.

The normal launcher passed **MTP → DFlash2 → MTP** switching with exactly one
bootstrap worker after the return switch. All validation workers were then stopped.
The DSH and Turnstone catalogs include both SGLang choices. Existing model IDs,
contexts and harness preferences are preserved. The accompanying JSON contains
sanitized measurements and focused-test evidence; raw logs remain ignored.

## Sources

- [SGLang DFlash2 author discussion](https://lcz.me/topic/1640)
- [Long-context MTP versus DFlash comparison](https://lcz.me/topic/1740)
- [Vulkan n-gram + MTP recipe](https://lcz.me/topic/1398)
- [Radeon SGLang fork recipe and numerical caveats](https://github.com/StevenChenSE/sglang/blob/gfx1100-support/README.zh-CN.md)

The SGLang forum's headline throughput uses two 7900 XTX cards. It is not a
single-card expectation for this workstation. The fork also documents greedy
output drift with speculative quantized verification; this motivated the
structured-output control tests rather than relying on throughput alone.
