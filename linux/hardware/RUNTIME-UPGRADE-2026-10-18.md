# AMD backend development updates — October 18, 2026

This is the dated installation/functional-validation record. Fresh throughput
for all nine profiles is now in [Current AMD benchmarks](CURRENT-AMD-BENCHMARKS.md).
The 32K Strata settings below describe this earlier update; its current native
256K profile is recorded in [the October 19 context report](STRATA-CONTEXT-2026-10-19.md).

Development builds selected for the current dual-Radeon workstation; live checks
are recorded below. All model assets were reused.

| Runtime | Previous | Selected development build | Validation |
| --- | --- | --- | --- |
| llama.cpp HIP and Vulkan | `f12aaa344c971556ec35be054d7aac1d901fd510` | [`31288c9c66e59377f7788d920678a565bb89dd37`](https://github.com/ggml-org/llama.cpp/commit/31288c9c66e59377f7788d920678a565bb89dd37) | Passed all five retained profiles |
| Strata HIP | 0.1.44.1, `296b59d2f73c8f04a805df29c2fa97655adace78` | [0.1.45, `477ac13cbe8e582c20484871ce459d20d82df09d`](https://github.com/Niko1221/Strata/commit/477ac13cbe8e582c20484871ce459d20d82df09d) | Passed dual-GPU 32K live validation |
| vLLM ROCm nightly | `0.32.0rc1.dev190+g3f1bcfd82.rocm723` | [`0.32.0rc1.dev329+g39983a5e7.rocm723`](https://wheels.vllm.ai/rocm/nightly/rocm723/vllm/) | Passed dual-GPU model validation; promoted |
| SGLang Radeon fork | `f84475ccf593087df3d1da13c9e675eadee12352` plus local fixes | [Same gfx1100 branch head](https://github.com/StevenChenSE/sglang/commit/f84475ccf593087df3d1da13c9e675eadee12352) | No newer fork commits; both production profiles passed |

Heads were fetched/pinned at the beginning of this update. Some timestamps are
October 19 UTC, still October 18 in Toronto. This is a development-source/nightly
update, not a stable-only update or automatic source tracking on each launch.

## Compatibility and preserved settings

All active models still use both RX 7900 XTX cards. Dense weights remain on the
GPUs; MoEs retain bounded CPU expert backing and GPU expert caching. The current
32 GB Strata profile stays at 32K; its 64 GB / 128K candidate is inactive.
Model storage, authenticated gateway and separate visible backend/DSH launchers
are unchanged. AMD llama.cpp workers now require an active systemd user manager
for their scoped no-swap protection, checked before backend handover. No new weights were downloaded. Unrelated GPU apps were preserved.

The private ROCm 7.2.3 SDK, Torch `2.13.0+git733fca1`, matched Triton and no-hostcall
RCCL are retained. The new official vLLM wheel requests this same Torch stack;
its base dependencies were checked for missing/incompatible versions.
The MTP vocabulary-sharing fix and guarded Radeon prefill/partial-query masking
patch were reapplied in an independent environment. The attention source and
patched SHA256 are unchanged, so the existing strict startup guard remains valid.
`VLLM_ENV_PATH` permits isolated candidate checks before promotion.

Official SGLang main was also fetched at
[`fea48754de4b73276cad1062d6b5ae013288204d`](https://github.com/sgl-project/sglang/commit/fea48754de4b73276cad1062d6b5ae013288204d).
Its CLI help loaded using the existing AMD stack, but GPTQ initialization did
not: initially AITER was missing; supplying already-installed AITER exposed the
explicit removal of the non-Marlin GPTQ linear path. The retained Radeon GPTQ
kernels and optimized verifier cannot be used unchanged with this refactoring;
the five local repairs remain on the hardware-specific fork. Its package requirements also moved to Torch 2.14.1. No full
model was loaded with that incompatible candidate. This is evidence against an
unchanged replacement, not proof that a new Radeon port is impossible. Keep the
latest hardware-specific branch rather than replacing its kernels with unsupported
CUDA Marlin paths. SGLang is current for that fork, **not official main**.

The llama.cpp HIP final link initially selected the system COMGR library, which
pulled system LLVM/libedit requiring newer GLIBC symbols than the private compiler
sysroot. `hardware/build-llama-hip.sh` now searches the private ROCm SDK's transitive
libraries before the system directory. Relinking succeeded; system packages were
not replaced. Both HIP and Vulkan binaries identify source `31288c9`.

C++ build directories and the old vLLM environment are retained privately for
rollback under ignored `hardware/generated/runtime-upgrade-2026-10-18/`. Old
binaries are not public Git artifacts. Source-local launch files and SGLang
patches were preserved; the fetched C++ checkouts had no tracked source edits.

## Local validation

- vLLM: both GPUs, TP2, 65,536 context, GPTQ W4A16/BF16, BF16 KV, MTP3,
  compiled graphs and 2,048-token prefill. Arithmetic, JSON, ordered 1–100 and
  tool-call/result checks passed. The 64,033-input-token marker request passed
  in 54.90 seconds (TTFT 54.56; only 22 output tokens). An 8K repeat decreased
  TTFT from 5.73 to 0.55 seconds with 7,488 prefix-cache hits. Allocator capacity
  was 98,114 tokens; sampled dedicated-VRAM spill was zero. Host swap/page-in
  activity occurred; this is not a zero-worker-swap claim or a new sustained
  decode benchmark. A background C++ build was running.
- SGLang: MTP 40,960 and DFlash2 65,536 profiles passed arithmetic, ordered JSON,
  tool-call/results, actual cache-capacity checks and dual-card residency through
  their real router. The repaired optimized verifier stayed enabled. No new
  full-window retrieval or repeated speed benchmark was run for this unchanged
  fork; earlier longer-context evidence remains separately dated.
- Fresh per-card numerical attention tests were not run: automatic approval
  review rejected those commands as conflicting with the dual-GPU policy.
  The attention source/patch hash is identical to the previously numerically
  validated code; the new wheel passed the dual-GPU production tests above.
- Strata HIP 0.1.45: 32K, two-GPU layer split, IQ3_XXS, INT8 KV and MTP3.
  Arithmetic, readable code/prose, tools/results, SSE and fresh 30,070-input-token
  retrieval passed. Worker swap and sampled nonresident VRAM were zero; minimum
  available RAM was 14.2 GiB. Whole-card peaks were 22.23 / 23.77 GiB, including
  unrelated allocations. The second card was close to full at peak; no capacity
  increase is inferred from this check. The current load built a 7.02 GiB pinned
  CPU complement inside the existing 8 GiB cap; cache sizing depends on available
  VRAM. No expert file-tier blob reads were reported after initialization; PLE
  and cold-load storage reads remain. A C++ build ran in the background.
- llama.cpp: the first unscoped run passed Qwen 27B and Muse, then the existing
  MoE guard stopped Qwen 35B loading at 618 MiB owned swap despite 20.13 GiB
  available RAM and zero VRAM spill. This was an intentional guard stop, not
  a demonstrated OOM. The normal AMD router now creates a worker-only systemd
  scope with `MemorySwapMax=0`; all model subprocesses inherit it. The existing
  low-RAM/swap/spill guard remains enabled and global swap is unchanged. The user
  service manager is checked before stopping an old backend. Scoped five-model
  integration passed: Qwen 27B and Muse through Vulkan, Qwen 35B MoE, Nemotron
  Q4 and Empero through HIP. Each configured context allocated; arithmetic,
  authenticated streaming and inventory tool-call/result round trips passed.
  Only the requested model remained loaded. Both cards held model allocations;
  owned worker swap and sampled VRAM spill were zero. The real cgroup
  `memory.swap.max=0` was independently observed on every model worker.
  The three MoEs retain CPU expert backing and GPU caches. No new near-256K
  retrieval was run on these builds; earlier long-context evidence keeps its
  previous runtime pin.

The initial vLLM test used system Python and stopped after passing the short
model checks because `tokenizers` was missing in the harness. It was rerun with
the engine's environment and passed. This was a harness dependency failure,
not a server crash. The test now checks that dependency before loading a worker.


The existing launcher/preflight and MoE memory-guard suites passed **23 unit
checks** after the scope change. Syntax and public publication checks are recorded
with the final synchronized artifacts. [Sanitized validation data](runtime-upgrade-2026-10-18.json)
exclude model output, private logs, user paths and credentials.

## Speculative-decoding research

[Qwen 27B AMD options and headline audit](QWEN27B-AMD-SPECULATION-2026-10-18.md)
compares HyperQwen/NInfer claims with experimental Radeon ExLlamaV3, hipEngine,
FreeToken and the retained SGLang fork. It separates aggregate concurrency from
single-request decode and prompt-copy drafting. Both
[lcz.me](https://lcz.me/topic/1640) and
[Level1Techs](https://forum.level1techs.com/t/dual-r9700s-amd-vllm-container-woes/250053?page=2)
were consulted; the latter uses different RDNA4 hardware. See
[the source ledger](FORUM-OPTIMIZATION-SOURCES.md). FreeToken remains retired;
research does not reinstall it or authorize a single-card serving profile.

## Strata validation timing samples

One temperature-zero request per workload, code/prose capped at 512 output tokens,
no prompt reuse. Background compilation and available-VRAM-dependent cache sizing
prevent treating these as a controlled version speed comparison.

| Workload | Input / output | Prefill t/s | Decode t/s | Wall seconds |
| --- | ---: | ---: | ---: | ---: |
| Python merge function | 29 / 375 | 87.7 | 66.7 | 5.96 |
| Lighthouse prose | 25 / 512 | 82.1 | 48.5 | 10.87 |
| Fresh retrieval | 30,070 / 19 | 801.4 | 68.7 | 37.82 |

The 19-token retrieval reply is a correctness probe, not sustained long-context
decode. Earlier [NVIDIA and AMD measurements](NVIDIA-COMPARISON-RUNTIME-AUDIT-2026-10-18.md)
retain their actual versions and methods.

## Updated vLLM short benchmark

Normal promoted environment, TP2, 64K budget, GPTQ W4A16, BF16 KV/Mamba,
compiled MTP3 and chunk 2048. Saved merge-function/lighthouse prompts,
temperature 0.6, top-p 0.95, seed 42, thinking off, at most 256 output tokens.
One excluded warm-up per workload and three warm timed requests, no background
C++ compilation. Approximate SSE decode is `(output_tokens-1)/(last-first visible
output time)`; speculative bursts limit timing precision.

| Workload | Three decode samples t/s | Median t/s |
| --- | --- | ---: |
| Code | 130.61, 130.39, 130.85 | 130.61 |
| Prose | 71.20, 72.69, 72.81 | 72.69 |

These remain in the same range as the separately dated dev190 results
(131.34 code / 77.46 prose). This is not a simultaneous old/new A/B and does
not establish a speed improvement. The earlier bulk-prefill benchmark is not
relabelled as a dev329 result; the fresh 64K retrieval timing is listed above.
