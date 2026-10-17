# Dual RX 7900 XTX protocol and speculation tests — October 17, 2026

## Scope

Test the reversible lcz.me suggestions on the existing GPU-resident profiles:
RCCL automatic protocol selection versus `NCCL_PROTO=Simple`, SGLang MTP depths
1–3, and the optional vendored vLLM verification kernel. Both RX 7900 XTX cards
remain enabled; P2P stays disabled. No driver, BIOS, clocks or kernel changes.

Hardware: i5-13600KF, MSI MPG Z690 CARBON WIFI, CPU PCIe4 x8/x8, 32 GB RAM.
Software: SGLang Radeon fork `f84475ccf593087df3d1da13c9e675eadee12352`,
vLLM `0.32.0rc1.dev190+g3f1bcfd82.rocm723`, ROCm 7.2.3 and the retained
no-hostcall RCCL 2.27.7. Target: AutoRound GPTQ W4A16 Qwen3.8-27B;
DFlash2 uses its retained W4A16 drafter. SGLang uses BF16 KV/Mamba state;
vLLM uses INT4 KV and BF16 Mamba state. All model weights stay on the GPUs.

## Method and limits

The two user-only prompts, sampling and output budget match the saved
[NVIDIA short-prompt benchmark](../../README.md#direct-hyperqwen-comparison--october-5-2026):

- Code: “Write a Python function that merges two sorted lists. Explain its time and space complexity.”
- Prose: “Write a short story about a lighthouse keeper finding a letter.”
- Temperature 0.6, top-p 0.95, seed 42, thinking disabled, maximum 256 output tokens.
- One excluded warm-up per task, followed by three timed runs per task; report medians.
- External SSE decode estimate: `(completion_tokens - 1) / (stream_end - first_output)`.

Speculative streams deliver tokens in bursts. A matching seed does not guarantee
identical text between engines. Prefix caching remains in its production setting;
short prompts have negligible reusable history. TTFT includes prefill and first
decode; it is not isolated prefill throughput. These short tasks do not predict
sustained long-context decode or prove complete program correctness.

The old NVIDIA profiles use different output-head quantization and Mamba precision,
a different engine revision and draft length. This comparison holds prompts and
sampling fixed, but does **not** isolate a GPU-only hardware speed difference.
The previous 200 t/s AMD code-copy result used a different prompt and must not be
compared directly to NVIDIA's 170 t/s merge-function result.

Unsloth Studio remained open and was not terminated. Initially it held about
18 GB resident host memory. Startup paged idle host memory to swap; startup
latency is therefore not a clean comparison. Timed requests start after model
loading and warm-up. The test samples memory every 0.5 seconds, aborting below
2 GiB available host RAM or above 256 MiB nonresident GPU allocation. Sampling
can miss short peaks. Device-wide VRAM peaks include desktop and unrelated
allocations. Raw logs, outputs and workstation details remain ignored.

## RCCL collectives

Each protocol uses a fresh two-rank process. Checked BF16 all-reduce and
all-gather at 2 B, 10 KiB, 256 KiB and 2 MiB. Each row is the median of three
batches of 30 iterations after an excluded warm-up batch. Wall time includes
input refill and collective dispatch, with synchronization at batch boundaries.
This is a small end-to-end collective test, not a link-bandwidth specification.

| Operation / payload | Auto µs | Simple µs |
|---|---:|---:|
| all_reduce / 2 B | 41.1 | 56.4 |
| all_gather / 2 B | 49.8 | 56.5 |
| all_reduce / 10,240 B | 66.8 | 64.9 |
| all_gather / 10,240 B | 53.7 | 56.1 |
| all_reduce / 262,144 B | 77.2 | 87.6 |
| all_gather / 262,144 B | 84.0 | 84.4 |
| all_reduce / 2,097,152 B | 373.4 | 372.3 |
| all_gather / 2,097,152 B | 441.7 | 435.8 |

Both protocols passed integrity checks. Neither shows the severe stall reported
in the motivating forum case. Simple does not deliver a consistent latency gain.

## Model results

Every passing case also passed arithmetic, ascending JSON, descending JSON and
a tool-call/result round trip. The optimized verifier is rejected if these fail;
throughput from an incorrect kernel is not treated as usable performance.

| Profile / protocol / verifier | Total context | Code t/s | Prose t/s | Checks |
|---|---:|---:|---:|---|
| SGLang mtp1-auto-verify0 | 40,960 | 57.37 | 49.31 | passed |
| SGLang mtp2-Simple-verify0 | 40,960 | 87.34 | 65.92 | passed |
| SGLang mtp2-auto-verify0 | 40,960 | 88.29 | 66.30 | passed |
| SGLang mtp3-auto-verify0 | 40,960 | — | — | aborted_resource_guard |
| SGLang mtp2-auto-verify1 | 40,960 | — | — | cancelled_resource_pressure |

| Saved NVIDIA profile | Code t/s | Prose t/s |
|---|---:|---:|
| vLLM MTP3, 32K | 86.1 | 53.6 |
| HyperQwen MTP3, 64K | 108.3 | 66.8 |
| HyperQwen DFlash2, 64K | 170.1 | 67.3 |

## Settings retained or changed

**Production configuration is unchanged.** Retain SGLang MTP2 at 40,960 tokens,
automatic RCCL protocol selection, and `SGLANG_RDNA_VLLM_VERIFY=0`. DFlash2
remains the SGLang default at 65,536 tokens; vLLM remains MTP3 at 65,536 tokens.
Both cards remain enabled for every model.

The measured MTP2 Simple medians were 1.1% lower for code and 0.6% lower for prose
than auto, which does not justify forcing Simple. MTP1 measured substantially
lower throughput, so it is not selected. Background memory pressure and the small
sample size limit these comparisons; they establish no universal speed ratio.

**MTP3 is unmeasured, not a demonstrated runtime incompatibility.** Its startup
was terminated by the host-memory guard at 1.85 GiB available, before model
loading completed. The subsequent optimized-verifier attempt was deliberately
cancelled while loading; it has no new quality or speed result. DFlash2 and vLLM
protocol comparisons were not started after the automatic queue was stopped.
A memory-light communication test passed for both protocols, but that does not
substitute for the unfinished model tests. No test worker remains running.
Unsloth Studio, DSH and the API gateway were preserved.

Unload the competing Unsloth model or finish the RAM upgrade before completing
those model tests. The harness now requires 12 GiB available before launch and
also aborts if swap use grows by more than 1 GiB, in addition to the original
2 GiB available-memory and residency guards. These extra guards were added after
the recorded trials; the older trials did not measure per-request swapping.
Do not interpret the cancelled optimized-verifier attempt as a correctness pass.

## Deferred and already-active suggestions

- HiCache/host KV caching and Strata wait for the additional RAM and separate validation.
- The scheduler fairness change from [SGLang PR 34058](https://github.com/sgl-project/sglang/pull/34058)
  is absent from this fork. It targets competing prefill/decode requests; the
  current profiles permit one simultaneous request. No backport was applied.
- AMD Triton KV splits already resolve to 16 in this fork; adding that same
  setting would not be a new optimization.
- Both cards use automatic clock control, with a configured upper SCLK state
  of 2,371 MHz. No 1,500 MHz cap was found. A loaded spot sample showed GPU0
  above 1,500 MHz; a spot sample does not establish sustained clocks or throttling.
- Existing 2,048-token DFlash2 prefill chunks, GPU prefix cache and Mamba cache
  slots remain. The earlier 8K-chunk comparison did not justify replacing them.

Sources motivating the tests: [RCCL Simple discussion](https://lcz.me/topic/1438),
[dual-XTX setup](https://lcz.me/topic/1814),
[DFlash2 implementation/results](https://lcz.me/topic/1640), and
[the Radeon fork](https://github.com/StevenChenSE/sglang/tree/gfx1100-support).
Their results are not measurements of this PC.

## Reproduction

Use `hardware/bench-rccl-protocol.py` with the private ROCm environment sourced,
`NCCL_PROTO` unset or `Simple`, and the SGLang ROCm Python. Use
`hardware/bench-dual-tuning.py --help` for isolated model trials. Stop configured
inference first; the harness refuses a competing configured worker and uses a
separate test port. It kills only its own process group on exit.

[Sanitized measurements](dual-tuning-2026-10-17.json) contain individual numeric
trials, quality booleans and sampled residency. They exclude generated text,
raw commands, credentials and private workstation paths.
