# Super IQ3 on the shared NVMe and the SSD-streaming trial — October 20, 2026

The user asked for three things: copy Nemotron Super IQ3 to the faster shared NVMe, try a
separate SSD-streaming profile, and keep it only if performance increases. The
decision rule was fixed before measurement
(`hardware/generated/super-ssd-streaming-2026-10-20/CRITERIA.md`):

- every arm must pass the functional checks, the 28,546-token marker retrieval, zero
  swap/spill, no guard stop, and both GPUs;
- a candidate is kept only if the geometric mean of {code/prose native prefill,
  code/prose decode} improves by at least 5% over the mean of two baseline runs, with
  no metric more than 5% worse.

Load time alone does not qualify; the rule says to ask the user in that case.

## Setup

- **Copy.** All three IQ3_XXS shards (56 GiB) were copied to
  `/mnt/shared-nvme/LLM-Models/Nemotron-Super/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-GGUF/UD-IQ3_XXS/`.
  Their SHA-256 matches the download manifest (revision `75a5829055f69a0359085ae6bbd0a81b60bc05c6`).
  The hashes were re-verified from disk after page-cache eviction.
- **Common settings.** All arms used llama.cpp `4c3c5810`, both RX 7900 XTX cards
  (HIP layer split 21:19), 32K context, the same 16 CPU expert layers (19.124 GiB),
  a 2 GiB GPU expert cache, Q8 K/V, MTP off, and `hardware/validate-nemotron-super.py --phase long`.
- **Fair conditions.** Both copies were evicted from the page cache before each run.
  The desktop rendered on the Intel iGPU, so neither XTX card carried any desktop VRAM.
- **Hardware.** i9-13900KS, 64 GB RAM.

## Results (three-trial medians, ~8.1K input / 256 output)

| Arm | Status | Load s | Native PP code / prose t/s | Decode code / prose t/s | 28,546-input TTFT s |
|---|---|---:|---:|---:|---:|
| A1 SATA, `load-mode none` (production before) | passed | 112.1 | 98.58 / 98.06 | 15.90 / 16.94 | 273.9 |
| B NVMe, `load-mode mmap` (streaming) | **failed** | 135.8 | — | — | — |
| C NVMe, `load-mode none` | passed | **42.2** | 98.42 / 97.96 | 15.87 / 16.93 | 274.8 |
| A2 SATA, `load-mode none` (drift check) | passed | 112.1 | 98.66 / 98.09 | 15.90 / 16.92 | 274.3 |

- **Baseline drift.** A2 against A1 was at most 0.11%.
- **C (NVMe, normal load).** Against the mean of the A runs it changed by
  −0.20 / −0.12 / −0.18 / +0.02%, a −0.12% geometric mean. Inference is identical
  within noise, because the model runs from RAM and VRAM after loading. **Loading is
  2.7× faster.** Zero swap/spill on every passing arm.

**B was rejected.** During the forced tool-call check, llama.cpp's grammar sampler raised
"Unexpected empty grammar stack after accepting piece: pered (81918)", and the request
returned HTTP 500. A diagnostic smoke rerun reproduced the same exception at the same token.

The weights are byte-identical. The memory-mapped CPU expert layout is different, though,
so arithmetic takes a different deterministic path, and that path hits the sampler
error. mmap also saved no memory: the host held the same 19.58 GiB of model weights,
because ample free RAM keeps every mapped page resident.

## Decision

Neither candidate met the 5% performance rule. The user was asked about C and chose
**"Use NVMe for faster load"**:
- The production `nemotron-3.5-super-iq3` preset (`dsh/models-hip.ini`), the catalog
  (`dsh/models.json`) and its candidate metadata now point at the NVMe copy.
- `hardware/nemotron_super.py` keeps the SATA manifest as the source of truth, and
  writes new candidate paths under `RUNTIME_MODELS`.
- The SATA original is retained as a backup.

The llama.cpp launcher preflight now mounts every volume its presets reference
(`ensure_llama_models`): Shared SATA for the other llama models, plus the shared NVMe for
Super. It still refuses paths outside the configured volumes.

The normal-launcher proof (`validate-llama-launcher.py`) passed for all five current
llama.cpp profiles, with Super loaded from the space-containing NVMe path. That proof is
functional only; the speed table above is the matched measurement.

Evidence: [numeric record](results/super-nvme-load-2026-10-20.json). Raw validator
records are in ignored `hardware/generated/nemotron-super/` and `hardware/generated/super-ssd-streaming-2026-10-20/`.
Reproduce with the new opt-in `--model-path` and `--load-mode {none,mmap}` validator options.
