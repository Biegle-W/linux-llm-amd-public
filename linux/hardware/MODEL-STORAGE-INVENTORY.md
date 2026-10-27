# Model categories and disk storage — October 27, 2026

Standing user preference: group all future model inventories and comparisons into
**VRAM only models**, **CPU RAM MoE models**, and **SSD stream models**. Classify the
selected loading profile rather than the model architecture or file location.
Moving a GGUF to NVMe alone does not make a profile an SSD stream profile.
A profile with an active SSD cold/PLE path belongs to SSD stream even when it
also keeps a bounded RAM expert tier and a GPU cache; Strata Qwen is in that group.

- **VRAM only models:** serving weights stay in GPU memory; ordinary host RAM is
  still needed for loading, tokenization and the engine. This is a placement
  description, not proof that the current reduced-RAM host can load them safely.
- **CPU RAM MoE models:** offloaded experts use CPU RAM alongside GPU-resident
  weights/cache; the retained llama.cpp CPU-offload profiles are in this group.
- **SSD stream models:** the large file-backed cold tier remains on SSD with
  bounded RAM/GPU tiers. These labels do not enable an engine flag or alter
  validated settings, admission rules, swap policy or maintenance holds.

The current catalog has **11 profiles / 9 distinct model weight sets**. Measurements
below use decimal **GB (1 GB = 1,000,000,000 bytes)** of allocated file storage.
They include retained model-directory weights, tokenizers, vision projectors,
generated packs and associated draft/preparation assets. The exact logical and
allocated byte counts are in the [numeric inventory](results/model-storage-2026-10-27.json).
Directory-entry overhead and engine binaries/environments are excluded.

## Storage roots

| Drive | Model root |
|---|---|
| System NVMe | `/opt/local-llm/models` |
| Shared SATA SSD | `/mnt/shared-sata1` |
| Shared NVMe | `/mnt/shared-nvme/LLM-Models` |

## VRAM only models

| Model / engine | Disk GB | Location relative to the roots above |
|---|---:|---|
| Qwen3.8-27B W4A16 / SGLang + vLLM | 21.34 | System `Qwen3.8-27B-W4A16-AutoRound-GPTQ`; System `drafts/Qwen3.8-27B-DFlash2-W4A16` |
| Nemotron 3.5 Bolt 74B-A9B W4A16 / vLLM | 43.65 | SATA `vLLM-Models/Nemotron-3.5-Bolt-74B-A9B-AutoRound-W4A16` |

Category total: **64.99 GB**, counting shared assets once.

## CPU RAM MoE models — current production profiles

| Model / engine | Disk GB | Location relative to the roots above |
|---|---:|---|
| Empero Qwen3.8-35B-A3B IQ4_XS / llama.cpp | 19.63 | SATA `GGUF-Models/Empero-Qwen3.8-35B-A3B-Distill` |
| Nemotron 3.5 Super 120B UD-IQ3_XXS / llama.cpp | 59.76 | NVMe `Nemotron-Super` |
| Sage-A1.5 Q4_K_M / llama.cpp | 22.61 | SATA `GGUF-Models/Sage-A1.5-GGUF` |
| Ornith-1.5-122B Q4_K_M / llama.cpp | 76.76 | SATA `GGUF-Models/Ornith-1.5-122B-GGUF` |

Category total: **178.76 GB**, counting shared assets once.

Empero and Sage also passed separately tested **VRAM-only candidates on both
GPUs** (256K/MTP3/512-token prompt batch and64K/MTP3/4096-token prompt batch,
respectively). Their production CPU-offload profiles are unchanged; the category
here follows the active configuration. See the [trial report](STORAGE-VRAM-2026-10-27.md).

## SSD stream models

| Model / engine | Disk GB | Location relative to the roots above |
|---|---:|---|
| Qwen3.8-Flash-Next IQ3_XXS (Strata) / Strata | 128.14 | NVMe `Strata/models`; NVMe `Strata/packs`; NVMe `Strata/mtp` |
| GLM-5.3-Flash Maya-S v2 / Maya | 97.42 | NVMe `Maya/Maya-S-v2-IQ2_XXS` |
| DeepSeek V4.1 Flash 1017 Maya-XS + xs2 / Maya + Strata | 281.87 | NVMe `Maya/DeepSeek-V4.1-Flash-1017-GGUF`; NVMe `Strata/DeepSeek-V4.1-Flash-1017` |

Category total: **507.43 GB**, counting shared assets once.

Qwen27B is **20.05 GB** of shared base weights/configuration plus **1.28 GB**
of DFlash2 draft assets used by SGLang; vLLM uses the same base. DeepSeek's
**281.87 GB** is shared by both engines, including **161.28 GB** of Engram shards5/6
and separate small Maya/Strata metadata. Do not count either weight set twice.
Strata Qwen's **128.14 GB** includes original GGUF/projector files, its generated
pack and retained MTP preparation/runtime files; this is the retained footprint,
not a claim that every file is read by the selected native path.

## Additional stored assets outside the active totals

| Asset | Disk GB | Location | Status |
|---|---:|---|---|
| Flint-40B-A2.5B UD-Q4_K_XL | 25.06 | SATA `GGUF-Models/Flint-40B-A2.5B` | Passed isolated dual-GPU VRAM-only32K text probes; not an enabled production profile |

The **59.77 GB Super SATA backup** and **96.70 GB old GLM Maya-S24 rollback**
were deleted at the user's request October27. The **59.76 GB Super serving copy**
on NVMe and **97.42 GB active GLM v2** remain. Shared DeepSeek Engram/XS files
are unchanged. Historical checksums remain; the S24 manifest cannot reinstall
retired assets. [Cleanup and VRAM trials](STORAGE-VRAM-2026-10-27.md).

Active-model associated files: **751.18 GB**.
Additional download-only files: **25.06 GB**.
A further **176,128 bytes** belongs to the small Hugging Face module cache.
All scanned model roots together: **776.24 GB**
(**722.93 GiB**) of allocated file storage.

The storage inventory itself changes no runtime configuration. The separately
requested Empero/Sage/Flint VRAM trials are recorded in the linked report.
The live host remains at approximately14.83GiB RAM; RAM-offloaded profiles remain
held, the three GPU-resident qualification trials have not qualified, and nightly
updates remain paused. Historical 64GB benchmark evidence is unchanged.
