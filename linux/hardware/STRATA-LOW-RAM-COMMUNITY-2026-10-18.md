# Strata with 32 GB RAM and 48 GB VRAM — October 18, 2026

Scope: Qwen3.8-Flash-Next in Strata. These are community reports and source
checks, not new local inference measurements. The retained Linux Strata profile
remains inactive; no model was loaded by this research.

## Closest first-person reports

| Source | RAM / GPU | Model and context | Reported result |
|---|---|---|---|
| [Strata #364](https://github.com/Niko1221/Strata/issues/364), davidmoller-rldatix, October 1 | 32 GB / 2x RTX 3090 24 GB | Swift IQ3_XXS, 262,144 context; engine 0.1.31 | About 95-100 output tok/s; 19,673 of 24,576 expert slots GPU-resident |
| [lcz.me 2053](https://lcz.me/topic/2053), Wing Wah Law, date not rendered | Reported 30 GB DDR5 / one W7800 48 GB, gfx1100 | ISTA IQ3_XXS, Strata 0.1.34 HIP; 80-120K actual conversation | Mean 76.5 decode tok/s, thinking disabled; configured ceiling 262K |
| [Strata #1386](https://github.com/Niko1221/Strata/issues/1386), yalu-arch, October 7 | 125 GB / 2x RX 7900 XTX 24 GB | IQ3_S, 262K configured; HIP 0.1.40 | Median 56.6 decode tok/s; validates this GPU pair, not the 32 GB host budget |

The first matches the RAM/VRAM capacities but uses NVIDIA. The second is close
to a 32 GB host and uses RDNA3, but one 48 GB allocation differs from two 24 GB
cards. The third matches the GPUs with much more host memory. No exact
32 GB plus dual-XTX success report was established in this search. These speeds
are different models/workloads, not a ranking or a forecast for this workstation.

## Supported memory strategies

[Resident split PR #848](https://github.com/Niko1221/Strata/pull/848) shipped in
0.1.40. It excludes every stage's GPU-cached experts from the RAM complement.
[The multi-GPU guide](https://github.com/Niko1221/Strata/blob/296b59d2f73c8f04a805df29c2fa97655adace78/docs/MULTI_GPU.md)
also documents RAM budgets and host-memory layer hand-offs without P2P.
[The memory guide](https://github.com/Niko1221/Strata/blob/296b59d2f73c8f04a805df29c2fa97655adace78/docs/DETAILS.md)
provides Linux `STRATA_ARENA_MMAP=1` as a separate opt-in strategy; it must not
be treated as extra physical RAM or automatically combined with every mode.

The retained local source is already 0.1.44.1 at
`296b59d2f73c8f04a805df29c2fa97655adace78`. Its
`include/strata/core/expert_source.hpp` documents the complementary resident
copy for both `--resident-experts` and `--resident-cpu-experts`, including
pageable HIP storage. The local readiness check's 60 GiB total / 48 GiB
available thresholds are conservative planning gates, not a measured minimum
or proof that the entire approximately 40 GiB pack must occupy host RAM.
It would be incorrect to promise that 64 GB is intrinsically mandatory.

A bounded-RAM dual-HIP IQ3_XXS candidate is therefore worth a separate test:
start one session at 32K, measure actual resident bytes, expert coverage, GPU
reserves, prefill/decode, output/tools/MTP and PLE/storage activity before raising
context. Do not copy the NVIDIA speed, a single 48 GB card's fit, or its 262K
ceiling into a local validated profile. No launcher, gate, runtime or model asset
was changed by this research.

## Storage and corroboration limits

[Issue #2797](https://github.com/Niko1221/Strata/issues/2797), October 16-17,
contains XTX/Linux and 32 GB/dual-3060 reports of slow direct PLE reads, including
a SATA case. Low-RAM operation can still be storage-bound even when experts
mostly fit GPUs. This is a risk to measure, not a diagnosis for this exFAT drive.
[Level1Techs discussion](https://forum.level1techs.com/t/creating-an-agent-harness-and-self-hosting-part-2-my-hardware-setup/252909)
was checked too; it supplies general Strata setup discussion, not a matched
32 GB / dual-XTX validation found in this search.
