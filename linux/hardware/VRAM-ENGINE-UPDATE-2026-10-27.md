# VRAM engine updates and native INT4 trials — October 27, 2026

The three VRAM-only llama.cpp profiles passed fresh paired benchmarks on latest
source **19cce6919992** and are selected through model-specific source pins.
The default CPU-backed source remains **2280f0fd163b**. SGLang's required gfx1100
fork is already at its newest published head, **f84475ccf593**. New vLLM nightly
**dev602 /5d35ce393** is prepared but not promoted: loading could not pass the
unchanged guards on the current **14.83 GiB OS-visible host**. Sage/Flint native
INT4 checkpoints were downloaded and tried; neither reached validated generation.
There is no measured native INT4 speedup or model migration.

Hardware: Intel i9-13900KS, two RX 7900 XTX 24 GB, ROCm 7.2.3. Both GPUs, all contexts,
quantizations, MTP settings, Flint reasoning budget 128, admission, cgroups,
pressure/swap/spill guards and the paused updater are preserved.
[All attempts, counters and thermals](results/vram-engine-update-2026-10-27.json).

## VRAM only models

### Fresh llama.cpp baseline → latest build

All medians below are from this October 27 session on 14.83 GiB RAM. PP is native
fresh prefill; TTFT is external submission to first reasoning/content delta on
fresh ~8K input, excluding cold model loading. Decode is code/prose separately,
including reasoning tokens. Decimal disk GB includes associated files/projectors.
Storage paths are relative to SATA1 `/mnt/shared/SATA1`.

| Model · llama.cpp | Native prefill t/s | Fresh TTFT s | Decode code / prose t/s | Context limit tokens | Disk GB | SATA1 location |
|---|---:|---:|---|---:|---:|---|
| Empero IQ4_XS | 3407.4 → 3406.8 | 2.410 → 2.410 | 131.83/83.76 → **132.83/83.51** | 262,144 | 19.63 | `GGUF-Models/Empero-Qwen3.8-35B-A3B-Distill` |
| Sage Q4_K_M | 4588.9 → 4618.1 | 1.791 → 1.779 | 85.37/70.64 → **86.26/71.41** | 65,536 | 22.61 | `GGUF-Models/Sage-A1.5-GGUF` |
| Flint UD-Q4_K_XL | 6028.2 → 6030.6 | 1.396 → 1.394 | 46.53/46.48 → **46.73/46.82** | 32,768 | 25.06 | `GGUF-Models/Flint-40B-A2.5B` |

Flint's fresh first **visible answer** TTFT is 4.451 → 4.457 s; first-token TTFT
above includes its bounded reasoning. Empero retains MTP3 / batch512 / 256K, Sage
MTP3 / batch4096 / 64K plus vision projector, Flint noMTP / batch4096 / 32K / reasoning128.
All retain DIO and Q8_0 K/V. These are small sequential paired differences;
there is no universal speedup claim.

Three timed code/prose requests with a 256-token output cap per arm follow excluded task
warmups (seed 42, temperature 0.6 / top-p 0.95). Three independent salted marker
prompts per arm use native tokenization near 8K and cache_prompt=false; all 18
marker probes pass with zero cached prompt tokens. Actual counts are saved.
The configured 32K–256K limits are not new full-window measurements. Each arm
also includes a continuous tutorial-request loop exceeding 35 seconds.

The existing comparator requires native prefill and code/prose medians ≥95% of
the fresh baseline, short TTFT ≤max(1.25×baseline,baseline + 0.05 s), no fewer markers,
and valid model/lifecycle memory evidence. All three pass. Every llama arm
records zero worker swap/spill, valid inference windows and owned cleanup.
Scopes are verified at 4 GiB memory.high / 5 GiB memory.max / memory.swap.max 0; original
12 GiB total / 7 GiB available admission and 3 GiB continuous floor are retained.

### Full lifecycle temperatures

Sampled peaks include loading, inference and shutdown; GPU triples are edge /junction /memory °C. These are sequential runs with different thermal histories.

| Profile /arm | Samples /errors | GPU0 °C | GPU1 °C | CPU package °C |
|---|---:|---|---|---:|
| Empero IQ4_XS /baseline | 117/0 | 35.0 / 46.0 / 42.0 | 30.0 / 45.0 / 54.0 | 58.0 |
| Sage Q4_K_M /baseline | 121/0 | 40.0 / 62.0 / 46.0 | 31.0 / 47.0 / 55.0 | 63.0 |
| Flint UD-Q4_K_XL /baseline | 158/0 | 42.0 / 50.0 / 47.0 | 33.0 / 57.0 / 54.0 | 64.0 |
| Empero IQ4_XS /candidate | 116/0 | 41.0 / 52.0 / 48.0 | 32.0 / 46.0 / 56.0 | 59.0 |
| Sage Q4_K_M /candidate | 118/0 | 43.0 / 65.0 / 47.0 | 34.0 / 57.0 / 56.0 | 64.0 |
| Flint UD-Q4_K_XL /candidate | 157/0 | 42.0 / 63.0 / 48.0 | 36.0 / 60.0 / 55.0 | 65.0 |

### Framework profiles: new attempts, no fresh throughput

The latest retry waits for host full-memory PSI recovery before each launch;
it preserves the same low-churn bounds. Failed initialization/loading produces
no benchmark medians. Earlier attempts rejected immediately by residual PSI are
retained separately and are not evidence of engine performance regressions.

| Profile / tested engine | Prefill t/s | TTFT s | Decode code/prose t/s | Context limit | Disk GB | Storage location |
|---|---|---|---|---:|---:|---|
| Qwen27B · vLLM dev435 baseline /dev602 candidate | not measured | not measured | not measured | 163,840 | 20.05 shared base | System `/opt/local-llm/models/Qwen3.8-27B-W4A16-AutoRound-GPTQ` |
| Bolt W4A16 · vLLM dev435 baseline /dev602 candidate | not measured | not measured | not measured | 262,144 | 43.65 | SATA1 `vLLM-Models/Nemotron-3.5-Bolt-74B-A9B-AutoRound-W4A16` |
| Qwen27B · SGLang f84475cc DFlash2 | not measured | not measured | not measured | 163,840 | 21.34 incl shared base +draft | System model above + `models/drafts/Qwen3.8-27B-DFlash2-W4A16` |

Qwen base storage is shared between engines and counted once. These current
attempts do not replace separately dated 64 GB historical throughput records.
Fresh final-retry loading outcomes:

- `vllm:baseline:qwen3.8-27b-vllm`: guard_stopped; guard reasons swapout_budget; owned shutdown True.
- `vllm:baseline:nemotron-3.5-bolt-vllm`: guard_stopped; guard reasons swapout_budget; owned shutdown True.
- `vllm:candidate:qwen3.8-27b-vllm`: guard_stopped; guard reasons swapout_budget; owned shutdown True.
- `vllm:candidate:nemotron-3.5-bolt-vllm`: guard_stopped; guard reasons swapout_budget; owned shutdown True.
- `sglang:baseline:qwen3.8-27b-sglang-dflash2`: guard_stopped; guard reasons memory_full_psi; owned shutdown True.
- SGLang cold retry after sustained quiet preflight: guard_stopped; guard reasons swapout_budget; owned shutdown True.

### Exact-model native INT4 alternatives

| Candidate / tested engine | Prefill t/s | TTFT s | Decode code/prose t/s | Test context | Disk GB allocated | SATA1 location |
|---|---|---|---|---:|---:|---|
| Sage W4A16 AutoRound · latest vLLM /SGLang | not measured | not measured | not measured | 65,536 | 20.33 | `vLLM-Models/Sage-A1.5-W4A16-AutoRound` |
| Flint AWQ INT4 · latest vLLM, experimental ROCm path | not measured | not measured | not measured | 32,768 | 22.42 | `vLLM-Models/Flint-AWQ` |

Sage is the exact A1.5 model, symmetric group 128 W4A16 AutoRound/GPTQ. vLLM
routes it through its INC/AutoRound handler; SGLang has its AutoRound/GPTQ
fallback. Both reached weight loading and stopped at the 4 GiB host swapout budget.
A changed SGLang retry disabled multithreaded loading and reached loading again,
then stopped at the host-memory floor. Trials retained TP2, BF16 KV and MTP3
(vLLM MTP /SGLang EAGLE). These native trials were language-only; vision parity
was not established, and the selected GGUF retains its projector.

Flint's exact checkpoint is asymmetric group 64 AWQ, not the official MLX INT4
format. Stock new-vLLM Flint initialization requires FlashInfer and fails its
import on this ROCm environment even with TRITON attention requested. An isolated
ROCm-only experiment substituted standard vLLM Attention and PyTorch fp32 norms,
passing original sinks, sliding/full attention and NoPE/RoPE arguments to the
standard backend, with backend-owned KV writes,
AWQ/Triton MoE and per-request `thinking_token_budget=128`. It cleared initialization
and began real weight loading, then stopped at the worker-swap and system
swapout limits. This **does not validate model output, kernel parity, or speed**;
the patch and candidate environment are not production-selected. The installed
SGLang fork lacks Flint; CUDA-oriented community plugins target other SGLang
versions, so no claim of a working AMD SGLang Flint deployment is made.

No ready exact Empero GPTQ/AWQ checkpoint was found in the checked listings.
Its exact BF16 weights are about 71.90 GB, exceeding 48 GB VRAM. Base Qwen checkpoints
would be different weights and were not substituted. GGUF/MLX/NVFP4 listings do
not establish a compatible native AMD INT4 checkpoint.

The two new candidate downloads total 42.74 GB logical / 42.75 GB allocated, with weight shards matched against publisher LFS SHA-256; associated small files
were fetched at pinned revisions and locally hashed. Working GGUFs remain; the catalog
still has 12 profiles. [Storage inventory](MODEL-STORAGE-INVENTORY.md).

## MoE models with CPU RAM offload

Super IQ3 and Ornith retain their existing llama.cpp source, flags, context and
RAM admission. They were not retested under 14.83 GiB. Ornith now has a published
AWQ INT4 candidate, but the repository lists over 85 GB of safetensor weights,
exceeding the 48 GB pair before KV/runtime overhead; it was not downloaded or
claimed to fit VRAM. Earlier statements that no ready 4-bit file existed remain
historical. Current selected-profile timing/storage records stay separately dated.

## MoE models with SSD streaming

Strata Qwen Q3, GLM Maya and DeepSeek XS (Maya/Strata) were outside this engine
update and retain their sources/placements/guards. No new benchmark is attributed
to them. DSH's default remains Strata Q3; nightly updates stay paused.

## Activation, recovery and validation limits

Only Empero/Sage/Flint use the new source through `source_overrides` in the llama
runtime JSON. The persistent source/runtime bundle is
`/opt/local-llm/llm-tools/llama-vram-19cce691` (public example path). Its nine
runtime ELF files were installed from the qualified build; CMake explicitly
rebased loader RPATH strings to the installed directory. Every byte outside
those RPATH strings was verified identical (one library is entirely unchanged),
including all compiled code, constants and GPU kernels. All llama/ggml library
resolutions point to the installed bundle; the retained SDK/toolchain libraries
remain external. No CMake cache/build tree was copied. CPU models fall back to
the unchanged 2280f0fd default. An explicit LLAMA_CPP_DIR still takes precedence for isolated
qualification. Source overrides require absolute paths and exact 40-character
commits; a moved source revision fails before a working model is unloaded.
Router reuse includes source identity as well as backend and memory limits;
the pinned revision is checked even when reusing a worker.
Public source locations are examples and require local clone/build validation.

Backend ownership also recognizes exact configured source binaries when a worker
loses its router parent. Six ownership checks pass in each checkout, and the
existing14 selective-cleanup checks pass. Ownership remains limited to configured
inference executables and their workers; unrelated apps stay excluded.

A future full-catalog daily install clears per-model source overrides for its
provisional candidate so all models really exercise that source. Its saved JSON
restores the overrides on rollback. Eleven CPU regression checks cover source
selection, explicit override priority, commit mismatch (including worker reuse),
switching sources under identical backend/limits, worker reuse and updater install/rollback. The existing VRAM reuse fixture was updated for source identity and isolated
from machine-specific installation paths; its safety assertions are retained.
The updater was not resumed. ROCm/Torch/Triton and existing RDNA repairs are retained.

Normal-launcher post-activation integration covers authenticated API arithmetic,
JSON, tool roundtrip and SSE on all three, selected contexts, Sage synthetic
vision, owned cgroups, one loaded model, native UI HTTP and reduced-RAM CPU-profile
refusal while the working GPU model stays loaded. Long-window/history behavior,
visual desktop inspection, remote-peer access and reboot are not repeated here.
A focused final Flint restart rechecks the final revision-verification code
through the same normal API/worker guards. The existing seven VRAM guard checks
and 27 updater/memory checks also pass. The first full integration reached all model checks and CPU-refusal checks,
then its bare urllib UI probe returned HTTP 415 because it omitted Accept-Encoding:gzip.
That failed attempt is retained. The focused restart and final full integration of the persistent installed
bundle use a gzip-capable request and decompress/verify the HTML. The final
installed-bundle integration passes all three model checks and the UI probe. This is a probe correction, not a relaxed
inference guard. All evidence remains separate from benchmark medians.

Full lifecycle thermal summaries retain edge/junction/memory temperatures,
power, clocks, fans, utilization, SMU flag availability and CPU package sensors.
Raw SMU limit flags do not establish a measured throughput loss; sampled peaks
cannot exclude transients. Raw private logs and credentials are excluded.

## Source pins

- [llama.cpp latest tested source 19cce691](https://github.com/ggml-org/llama.cpp/commit/19cce6919992fdffd92e0ac152caaf1e2b8f254e).
- [required SGLang gfx1100 fork head](https://github.com/StevenChenSE/sglang/commit/f84475ccf593087df3d1da13c9e675eadee12352).
- [vLLM candidate source 5d35ce393](https://github.com/vllm-project/vllm/commit/5d35ce3934a7804b298559d2d99eec33792e1eb9); official ROCm7.2 wheel SHA256 `723cebfce6fcf441fbe53a4d3717805967f603c52f4a34a46358b9c161fe7660`.
- [Sage native INT4 pinned revision](https://huggingface.co/stuchapin/Sage-A1.5-W4A16-AutoRound/tree/837d528b8386488d2066d529b5180c07b9522620).
- [Flint AWQ pinned revision](https://huggingface.co/mattbucci/Flint-AWQ/tree/2cae47a65e71d151a002172d18bcf2589fe09177).
- [Empero exact BF16 revision](https://huggingface.co/empero-ai/Qwen3.8-35B-A3B-Distill/tree/bcc2dbe2f21b213625df2dc1a5a690212373af07).
- [Ornith AWQ listing](https://huggingface.co/cyankiwi/Ornith-1.5-122B-AWQ-INT4/tree/f37c82fdabf818ea4c8643aa63157b9f17f2ae0f).
