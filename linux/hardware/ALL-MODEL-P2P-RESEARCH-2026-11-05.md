# P2P research review — November 5, 2026

Research for the current installed gfx1100 host; external timing is not a local benchmark or qualification.

## [Firsthand X99 dual-XTX report, with mixed participant advice](https://lcz.me/topic/2774)

Working SGLang TP2 can use SHM while peer access remains unavailable. The author corrects an initial x8/x16 bandwidth calculation and describes separate BAR/topology/kernel obstacles.

Preserve independently verified local ACS/identity-domain/kernel configuration and use successful per-route P2P/IPC traces. Do not import X99 BIOS/kernel changes or claimed throughput.

## [Author implementation and W7900 measurements; XTX applicability initially inferred](https://lcz.me/topic/2643)

INT8 DiT-only TP2 uses row-parallel reductions, shared activation scales and FP32 accumulation. Encoding and VAE remain outside TP. CK attention changes the measured comparison; Radiance RDNA4 kernels are a separate path.

The already completed pinned fcys P2P/IPC request qualifies only its bounded finite/media check. Preserve default H3 component workflow and existing CK/quantization pins; no unmeasured speed claim or normal TP2 promotion.

## [Firsthand dual RX7900XTX single-vs-TP2 report](https://lcz.me/topic/2664)

At 832x480/124frames/8steps the author reports 1.59x stable sampling but 1.19x whole-generation speed, with different output details. This is a separate implementation and 96GiB host.

Treat phase speed and complete workflow latency separately. Retain the local 39-frame bounded test's own limits; do not transplant resolution, memory targets or timing.

## [Firsthand separate custom-TP2 comparison on dual XTX](https://lcz.me/topic/2582/98)

The report separates gfx1100 custom INT8/RCCL TP2 from an NVIDIA run and uses different hardware, memory, attention and software stacks.

No direct hardware-speed inference. Radiance/gfx1201 and custom gfx1100 paths must retain separate compatibility and qualification records.

## [Firsthand R9700 platform/kernel report, June-July2026](https://forum.level1techs.com/t/dual-radeon-pro-r9700-p2p-on-supermicro-h13sae-mf/251544)

Initial peer failure is followed by a 7.1-kernel bandwidth/access matrix; the author explicitly says LLM workloads had not yet been tried at that boundary.

Capability/bandwidth evidence does not qualify application inference. Different gfx1201 platform is background only; no local kernel upgrade proposed.

## [Firsthand EPYC/512GB/quad3090 runtime notes, previously read](https://digitalspaceport.com/qwen-coder-3-480b-a35b-llama-cpp-and-ik_llama-cpp-notes/)

A much larger CPU-memory/offload system and different Qwen Coder model/runtime produce configuration-specific results.

No local gfx1100 placement, context, performance or memory claim follows from these notes.

## [Primary AMD RCCL2.27.7/ROCm7.2 documentation](https://rocm.docs.amd.com/projects/rccl/en/docs-7.2.0/how-to/rccl-usage-tips.html#enabling-peer-to-peer-transport)

PCIe peer transport uses HSA_FORCE_FINE_GRAIN_PCIE=1 and requires peer-capable GPUs with proper large BAR addressing.

Retain tested fine-grain setting, topology and source/runtime pins. The environment variable alone is insufficient; local direct/IPC/RCCL correctness and application completion are required.

## [Primary current llama.cpp server documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)

Layer, row and experimental tensor splitting are distinct modes.

Retain locally tested layer splitting and exact per-model source pins. Do not replace tested placement with experimental tensor splitting.

## Local selection

Select the already qualified local route and its measured transport. P2P may be enabled only for qualified routes; native host-mediated layer handoffs and normal graphics component placement must be described accurately. No source upgrade, new benchmark or numerical/quality change is justified by these forum reports alone.
