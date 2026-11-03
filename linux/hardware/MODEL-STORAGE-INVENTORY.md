# Current LLM model storage — November 2, 2026

Qwen main and DFlash2 now use sharedSATA1; retained Maya/Strata streaming assets use the system drive. Super IQ3 and old DeepSeek weight backing are removed. Seven enabled engine routes share six enabled base weight sets; Ornith and Strata Qwen remain configured but paused. Super W4A16 and Flint AWQ are retained experimental candidates. No new inference or performance result is implied. [Qwen relocation](QWEN-SATA-MIGRATION-2026-11-02.md) · [Streaming relocation](SABRENT-SYSTEM-MIGRATION-2026-11-02.md).

Current sizes below are logical bytes of each retained directory, including small metadata/support files, expressed in decimal GB; shared weight files count once. The older allocated-storage figures below retain their original scope.

| Root | Current location |
|---|---|
| System models | `/opt/local-llm/models` |
| Shared SATA | `/mnt/shared` |

## VRAM only models — selected loading configurations

| Model | Logical GB | Location relative to Shared SATA |
|---|---:|---|
| Qwen 27B W4A16 plus DFlash2 | 21.335 | `vLLM-Models/Qwen3.8-27B-W4A16-AutoRound-GPTQ`; `vLLM-Models/drafts/Qwen3.8-27B-DFlash2-W4A16` |
| Empero 35B IQ4_XS | 19.628 | `GGUF-Models/Empero-Qwen3.8-35B-A3B-Distill` |
| Flint GGUF | 25.055 | `GGUF-Models/Flint-40B-A2.5B` |
| Bolt W4A16 | 43.645 | `vLLM-Models/Nemotron-3.5-Bolt-74B-A9B-AutoRound-W4A16` |
| Sage W4A16 | 20.327 | `vLLM-Models/Sage-A1.5-W4A16-AutoRound` |

## MoE models with CPU RAM offload — configured, held

| Model | Logical GB | Location relative to Shared SATA |
|---|---:|---|
| Ornith 122B Q4_K_M plus projector | 76.756 | `GGUF-Models/Ornith-1.5-122B-GGUF` |

## MoE models with SSD streaming

| Model | Logical GB | Location relative to System models | Status |
|---|---:|---|---|
| GLM Maya-S v2 | 97.646 | `streaming/Maya/Maya-S-v2-IQ2_XXS` | Enabled |
| Strata Qwen GGUF/support/MTP | 79.129 | `streaming/Strata` | Paused for RAM; tiny DeepSeek reference metadata included |

## Downloaded experimental alternatives — no qualified production loading selection

| Candidate | Logical GB | Location relative to Shared SATA |
|---|---:|---|
| Super W4A16 Merlin mixed INT4/INT8 | 72.920 | `vLLM-Models/Nemotron-3.5-Super-VL-120B-A12B-W4A16-Merlin` |
| Flint AWQ | 22.415 | `vLLM-Models/Flint-AWQ` |

New DeepSeek Unsloth Q1 weights are not downloaded. Runtime/source pins, guards, holds and the paused updater remain. No task copy/GPU job or reservation remains. The image/video collection is separate at `/mnt/shared/Graphics-Models`.

---

# Historical October 27 model-storage snapshot

Earlier same-day Flint [reasoning128 benchmark](FLINT-REASONING128-2026-10-27.md): prefill 6034.8 tokens/s, TTFT 1.396 s (visible answer 4.436s), code/prose 46.63/46.57 tokens/s, 32K, 25.06 GB SATA1. The latest engine refresh is in [the October27 report](VRAM-ENGINE-UPDATE-2026-10-27.md); current allocations below include the later Sage INT4 replacement, with the remaining Flint alternative listed separately.

Standing benchmark listing format (October 27): every future benchmark listing,
inventory with performance, and model comparison must group all model/engine
profiles into **VRAM only models**, **MoE models with CPU RAM offload**, and
**MoE models with SSD streaming**, according to the selected loading profile.
For each profile include **prefill (tokens/s)**, **time to first token (seconds)**,
**decode (tokens/s, code/prose separately when measured)**, **context limit
(tokens)**, **storage size (GB)**, and **storage location (drive and path)**.
Keep the model/engine identity and measurement date visible; distinguish native
prefill from engine-phase timing and configured context from actual tested length.
Use "not measured" when a metric is unavailable; never estimate or omit TTFT
because only throughput was recorded. Count shared files once in storage totals
and identify sharing in individual rows. Public paths use sanitized examples.

Standing user preference: group inventories into **VRAM only models**,
**MoE models with CPU RAM offload**, and **MoE models with SSD streaming**, by the selected loading
configuration. VRAM only means GPU-resident model weights, not zero host-RAM
use. An active SSD cold/PLE tier remains SSD stream even with RAM/GPU caches.
Strata Qwen is therefore SSD stream.

The current catalog has **12 profiles / 10 model weight sets**. Empero and Sage
now default to their tested VRAM-only placements; Flint is selectable as
`flint-40b-a2.5b` at32K. Both AMD cards remain required. Existing CPU/SSD profiles
retain their physical-RAM admission and other guards; DSH's saved default stays
Strata Q3. Except for the explicitly recorded Sage INT4 replacement below, contexts and active model-storage paths are retained;
qualified engine changes are documented in the report below.
[Activation and normal-launch checks](VRAM-DEFAULTS-2026-10-27.md).

Sizes are decimal **GB of allocated file storage**, including associated
projectors, generated packs, drafts and retained preparation assets. Shared
weights count once. Runtime binaries/environments and directory overhead are
excluded. [Exact byte counts](results/model-storage-2026-10-27.json).

| Drive | Root |
|---|---|
| System | `/opt/local-llm/models` |
| SATA | `/mnt/shared` |
| NVMe | `/mnt/shared-nvme/LLM-Models` |

## VRAM only models

| Model | Disk GB | Location relative to the roots above |
|---|---:|---|
| Qwen3.8-27B W4A16 | 21.34 | System `Qwen3.8-27B-W4A16-AutoRound-GPTQ`; System `drafts/Qwen3.8-27B-DFlash2-W4A16` |
| Nemotron 3.5 Bolt 74B-A9B W4A16 | 43.65 | SATA `vLLM-Models/Nemotron-3.5-Bolt-74B-A9B-AutoRound-W4A16` |
| Empero Qwen3.8-35B-A3B IQ4_XS | 19.63 | SATA `GGUF-Models/Empero-Qwen3.8-35B-A3B-Distill` |
| Sage-A1.5 W4A16 AutoRound · vLLM | 20.33 | SATA `vLLM-Models/Sage-A1.5-W4A16-AutoRound` |
| Flint-40B-A2.5B UD-Q4_K_XL | 25.06 | SATA `GGUF-Models/Flint-40B-A2.5B` |

Category total: **130.00 GB**.

### Native INT4 selection and remaining alternative — October27

Sage native INT4 is now selected in vLLM; its slower GGUF/projector was removed,
reclaiming22.61GB. Native Sage uses20.33GB, already stored before migration.
[Benchmark comparison, compatibility limits and removal](SAGE-INT4-REPLACEMENT-2026-10-27.md).
Flint AWQ remains a22.42GB experimental alternative at SATA1 `vLLM-Models/Flint-AWQ`;
its diagnostic/matched-partial results are in [the retry report](LOADING-SWAP-RETRY-2026-10-27.md).
It is excluded from the active VRAM category total.

## MoE models with CPU RAM offload

| Model | Disk GB | Location relative to the roots above |
|---|---:|---|
| Nemotron 3.5 Super 120B UD-IQ3_XXS | 59.76 | NVMe `Nemotron-Super` |
| Ornith-1.5-122B Q4_K_M | 76.76 | SATA `GGUF-Models/Ornith-1.5-122B-GGUF` |

Category total: **136.52 GB**.

## MoE models with SSD streaming

| Model | Disk GB | Location relative to the roots above |
|---|---:|---|
| Qwen3.8-Flash-Next IQ3_XXS (Strata) | 128.14 | NVMe `Strata/models`; NVMe `Strata/packs`; NVMe `Strata/mtp` |
| GLM-5.3-Flash Maya-S v2 | 97.42 | NVMe `Maya/Maya-S-v2-IQ2_XXS` |
| DeepSeek V4.1 Flash 1017 Maya-XS + xs2 | 281.87 | NVMe `Maya/DeepSeek-V4.1-Flash-1017-GGUF`; NVMe `Strata/DeepSeek-V4.1-Flash-1017` |

Category total: **507.43 GB**.

Qwen27B SGLang/vLLM share20.05GB of base files; SGLang additionally uses1.28GB
of DFlash2 draft assets. DeepSeek's281.87GB is shared between Maya and Strata,
including161.28GB of Engram shards5/6; independent engine metadata is included.
Strata Qwen's128.14GB includes original GGUF/projector files, its generated
pack and retained MTP conversion/runtime artifacts.

The Super SATA backup and old GLM S24 rollback were removed at the user's request
(156.47GB reclaimed); active Super NVMe, GLM v2 and all XS dependencies remain.
Historical checksums/results remain; the S24 manifest is non-installable.
[Cleanup and isolated trial history](STORAGE-VRAM-2026-10-27.md).


Additional experimental assets: **22.42GB**; active assets **773.95GB**.
Combined model-associated storage is **796.37GB**, including the small module
cache. Exact bytes retain unchanged earlier scans and the verified Sage migration.
Nightly updates remain paused.
