# Nemotron 3.5 Super VL: bounded dual-AMD setup

Prepared October 19, 2026 for two RX 7900 XTX 24 GB cards and 32 GB host RAM.
This is a new 120B-total/12B-active model, distinct from the retained 74B Bolt.
Initial operation is text and tools only; no vision projector was downloaded.

## Downloaded weights and prepared profiles

Both Unsloth variants are pinned to revision
`75a5829055f69a0359085ae6bbd0a81b60bc05c6`. Their six shards passed exact
upstream-size and SHA-256 verification. They remain on Shared SATA; the original
download manifest is beside the quant subfolders. No additional weight cache
or primary-NVMe copy is needed.

| Candidate ID | Quant | Weight tensor GiB, including unused MTP head | CPU expert GiB | GPU cache ceiling | Context target | Admission |
|---|---|---:|---:|---:|---:|---|
| `nemotron-3.5-super-iq3` | UD-IQ3_XXS | 55.652 | 19.124 | 2 GiB total | 32,768 | At least 28 GiB total and 23.124 GiB available RAM |
| `nemotron-3.5-super-q4` | UD-Q4_K_XL | 80.931 | 47.424 | 4 GiB total | 32,768 | At least 60 GiB total and 51.424 GiB available RAM |

IQ3 is registered in the existing llama.cpp launcher, DSH and authenticated
gateway after passing the checks below. Q4 stays outside active catalogs until
RAM is physically upgraded and a separate live validation passes. Installing
RAM alone never activates Q4. The saved default model is preserved.
The model's advertised 1M window is not a local context validation.

The header-only preparation helper `nemotron_super.py` records the exact CPU
expert byte totals and layer lists in `dsh/candidates/nemotron-super.json`.
It verifies shard sizes against the previously SHA-verified download manifest
without reading weight tensors into system RAM. Explicit tensor placement uses
`n-cpu-moe=0` to avoid a second contiguous-layer override.

Both cards use llama.cpp HIP layer splitting, not tensor parallelism. Settings:
Q8 K/V, Flash Attention, one slot, batch/microbatch 512/128, six CPU threads,
`load-mode=none`, `cache-ram=0`, no prompt checkpoints, Jinja template,
thinking off, temperature 1.0/top-p 0.95/top-k 0/min-p 0. The initial baseline
has MTP off; a bounded MTP3 comparison is conditional on actual headroom.

## Safety and validation

The isolated validation helper `validate-nemotron-super.py` refuses an existing
managed inference process, benchmark or busy GPU. It binds only loopback port
18183 and never shuts down an existing workload. Every test worker has its own
no-swap systemd scope and a host-memory ceiling. A one-second monitor samples
host availability, whole-card VRAM and owned-worker swap/residency; persistent
headroom below 3 GiB stops only that test worker. Raw test logs/results are
under ignored `hardware/generated/nemotron-super/`.

Start at 16K, compare layer splits 1:1, 21:19 and 19:21, and validate 32K only
after safe allocation and functional checks. Arithmetic, JSON, streaming and
an actual function-call/result round trip are required. A near-28K marker
probe distinguishes configured capacity from actually tested input. Fixed
approximately 8K uncached input/256-output code and prose trials retain exact
counts and native prefill timing, external SSE TTFT and external decode.
MTP3 is selected only after correctness checks and at least 5% median decode
improvement without a material prefill regression. Failed trials remain evidence.

## Sources and applicability

- [Unsloth's Super VL guide](https://unsloth.ai/docs/models/nemotron-3.5-super-vl)
  documents split-GGUF loading, tools, MTP and substantial non-weight memory
  requirements. Its generic memory estimates are not measurements on this PC.
- [Pinned model repository](https://huggingface.co/unsloth/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-GGUF/tree/75a5829055f69a0359085ae6bbd0a81b60bc05c6)
  supplies the weights and model architecture metadata.
- Installed [llama.cpp revision](https://github.com/ggml-org/llama.cpp/commit/31288c9c66e59377f7788d920678a565bb89dd37)
  already implements `nemotron_h_moe`, its MTP head and CPU-backed GPU expert
  caching. No runtime upgrade or engine fork was introduced for this task.
- Both forums were searched for matching Nemotron Super/dual-XTX results.
  No directly matching result was established. [lcz.me topic 1972](https://lcz.me/topic/1972/9)
  concerns single-XTX Qwen/KVMem, and [Level1Techs RAM/offload tests](https://forum.level1techs.com/t/ryzen-9950x-ram-tuning-and-benchmarks/219347)
  concern a different dense model/NVIDIA GPU. Neither supplies a speed or
  capacity prediction for this model; no settings were copied from those tests.

## Measured IQ3 results

The selected split is **21:19**, non-MTP, 32,768 total context tokens. The 1:1
and 19:21 trials were stopped by the per-card VRAM guard at 16K, without worker
swap or dedicated VRAM spill. They are rejected configurations, not benchmarks.
The 21:19 profile passed at 16K and 32K, including arithmetic, JSON, streaming
and an actual tool-call/result round trip.

| Workload | Allocated context | Actual input / output | Native prefill t/s | External TTFT s | External decode t/s |
|---|---:|---:|---:|---:|---:|
| Code, median of 3 | 32,768 | 8,108 / 256 | 95.75 | 84.699 | 14.16 |
| Prose, median of 3 | 32,768 | 8,111 / 256 | 97.13 | 83.521 | 16.32 |
| Three-marker retrieval, single probe | 32,768 | 28,546 / 22 | 100.08 | 285.249 | Not a sustained decode test |

All measured inputs were uncached. The timed code/prose inputs are fixed across
their three repeats, approximately 8K tokens, rather than short prompts; their
TTFT must not be compared with the earlier nine-profile batch's short TTFT.
SSE decode uses `(completion_tokens-1)/(stream_end-first_output)`. Native prompt
timing and external TTFT are separate measurements. The near-28K probe found
all three markers; full-window sustained generation and general long-document
accuracy have not been established.

Minimum available host RAM was **5.84 GiB**. Peak whole-card VRAM was **20.00 /
20.94 GiB**, including the desktop; worker swap and sampled nonresident VRAM
were both zero. Actual expert caches were **1,071.64 / 972.56 MiB**; decode cache
hit rate across the validation was **50.62%**. Cache misses still require PCIe
uploads. SATA cold loading took approximately **125 seconds**, excluded from
the warm TTFT measurements.

MTP3 was **not launched**: the MTP expert weights alone add 2.789 GiB, while
only about 1.03 GiB remained beyond the combined 6 GiB VRAM reserve at the
observed workload peaks. This is a capacity-based rejection, not a measured
MTP performance comparison. More host RAM permits future placement experiments;
it does not automatically enable speculation.

All trials and rejected split memory peaks are retained in the
[curated numeric record](results/nemotron-super-2026-10-19.json). Existing model
benchmarks were not rerun or relabeled. Runtime version remained unchanged.

## Use and future activation

Start the existing llama.cpp Desktop launcher or `llm-llama`, then open DSH
separately and select **Local llama.cpp / Nemotron 3.5 Super VL 120B UD-IQ3_XXS**.
API clients use `nemotron-3.5-super-iq3` through the existing authenticated
gateway; connection addresses and credentials are unchanged. Loading requires
23.124 GiB available host RAM and 21 GiB free VRAM on each GPU. Runtime guards
retain 3 GiB available RAM and 3 GiB free VRAM per card. They stop only their
owned model worker if the budget becomes unsafe.

After 64 GB is physically installed, and both GPUs are idle, validate the
inactive Q4 candidate from the runtime workspace:

```sh
source hardware/rocm-env.sh
python3 -B hardware/validate-nemotron-super.py --model nemotron-3.5-super-q4 --context 32768 --split 21,19 --phase long --tag q4-64gb-32k
```

Review that result and compare the other two splits before registering Q4.
`activate-nemotron-super.py` requires a passed functional/long-input/timing record
and the physical RAM gate; it does not start a worker or change the default.
Q4 has no local throughput or context-validation result yet. No additional
weights, vision projector or engine download is needed for this text-only plan.

Managed-launcher validation also passed authenticated gateway generation, the
10-profile catalog with Q4 hidden, exact 32K API context, repeated tools/JSON/
streaming, native zero-swap scopes and HIP -> Vulkan/Qwen -> HIP/IQ3 switching.
All test workers were stopped afterward. Start the existing backend launcher
when needed; the saved DSH default was not changed.
