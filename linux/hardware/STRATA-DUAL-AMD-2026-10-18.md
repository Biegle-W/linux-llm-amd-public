# Strata IQ3_XXS on dual RX 7900 XTX — October 18, 2026

**Locally validated on 32 GB RAM / 48 GB aggregate VRAM.** The existing
Qwen3.8-Flash-Next GSQ-RCO IQ3_XXS files now run through the normal Strata
Desktop/PATH launcher on both cards, with DSH and the authenticated gateway.
Model assets remain on Shared SATA; no model was downloaded or copied to NVMe.

## Selected configuration

- Intel i5-13600KF, 32 GB installed (30.63 GiB visible), MSI Z690, CPU PCIe4 x8/x8.
- Strata HIP 0.1.44.1, source `296b59d2f73c8f04a805df29c2fa97655adace78`,
  gfx1100, private ROCm 7.2.3 SDK; retained separate HIP binary.
- One session, automatic split: layers 0-25 on GPU0, 26-47 plus head/drafter on
  GPU1. This is layer splitting, **not TP**; direct P2P remains unavailable.
- 32,768 total context, INT8 KV, 32K resident positions; prefill chunk 512.
- MTP `--spec 3 --spec-min-p 0.7`, six CPU expert workers, thinking disabled.
- GPU expert cache: 11,535 / 8,318 slots, 16.75 / 15.27 GiB; 19,853 of 24,576
  experts total. The remaining **7.95 GiB** are CPU-resident inside an 8 GiB
  budget, page-locked in this run. These are expert bytes, not total process RAM.
- Static profiled placement (`--adapt-every 0`), `--pcie-frac 0`, mmap fallback,
  mapped PLE reads, 3 GiB VRAM reserve/card and conversation parking disabled.
- The worker runs under `systemd-run --user --scope -p MemorySwapMax=0`; global
  swap and unrelated applications are unchanged. Physical-memory admission and a
  scoped low-RAM/worker-swap monitor remain enabled. Other GPU apps were not killed.

## Measurements and functional checks

One sequential sample per workload, temperature zero, native engine/API clocks,
512 output-token cap for code/prose. Code stopped naturally at 408 tokens;
prose reached the cap. These are smoke/throughput samples, not repeated medians
or a controlled comparison with earlier NVIDIA results.

| Workload | Input / output tokens | Prefill t/s | Decode t/s | Total request seconds |
|---|---:|---:|---:|---:|
| Merge two sorted lists, Python | 29 / 408 | 85.5 | 59.8 | 7.17 |
| Lighthouse story | 25 / 512 | 80.1 | 47.8 | 11.02 |
| Fresh synthetic long retrieval | 30,070 / 19 | 763.1 | 68.5 | 39.72 |

The long test retrieved all three codes from a repetitive synthetic ledger with
zero prompt-cache reuse. Its 39.41 seconds of prefill prove usable near-32K
retrieval for that workload, not general full-window quality or sustained 68.5
t/s at long context: its answer was only 19 tokens. Small-prompt prefill rates
are dominated by setup/first-token overhead; they are not bulk prefill capacity.

Arithmetic, readable code/prose, structured tool calls, tool-result consumption,
SSE completion and MTP draft acceptance passed through the production router.
Managed same-backend relaunch released the old worker before the new load and
left exactly one HIP engine. Authenticated generation and model discovery passed
on the configured loopback/LAN/Tailscale gateway listeners. The model is left
running in its visible terminal.

Sampled minimum available system RAM was **8.70 GiB**; owned worker swap and
nonresident VRAM were both **zero**. Peak whole-card VRAM was **22.17 / 22.92
GiB**, including other desktop/runtime allocations. The selected run reported
zero expert blob reads from the file tier after the CPU complement was built;
PLE/storage activity and cold GPU-cache filling still require SSD reads.

An initial 6 GiB expert budget left expert misses in the file tier. At 8 GiB,
the complement fit in RAM. A first unscoped long-prompt trial paged out 2.21 GiB
of owned memory and was deliberately unloaded by the guard; it was not reported
as a successful context test or assumed to be an OOM kill. The selected no-swap
scope then passed the full sequence above. Decode samples varied between starts;
no claim of a measured performance gain from the scope itself is made.

Sanitized [result data](strata-dual-amd-2026-10-18.json) omit prompts/output/private
logs. Reproduce on an already running router with
`python3 hardware/validate-strata.py --long`; it does not start another backend.

## Prepared 64 GB candidate

`dsh/strata-iq3-64gb-candidate.json` is inactive: 131,072 context, INT8 KV with
32K resident cells and host backing, 2,048-token prefill, 20 GiB expert budget,
same two GPUs and existing files. It requires 60 GiB total and 26 GiB available
RAM before loading. No 128K measurement is claimed; installation alone does not
activate it. [Upgrade steps and admission rules](STRATA-AFTER-RAM.md).

## Source trail

[Earlier community research](STRATA-LOW-RAM-COMMUNITY-2026-10-18.md) distinguished
[NVIDIA 32 GB / dual-24 GB success](https://github.com/Niko1221/Strata/issues/364),
[lcz.me's approximately 30 GB / single W7800 48 GB report](https://lcz.me/topic/2053)
and [dual-XTX with 125 GB RAM](https://github.com/Niko1221/Strata/issues/1386).
Those are other systems' results, not the numbers measured here.
[Level1Techs](https://forum.level1techs.com/t/creating-an-agent-harness-and-self-hosting-part-2-my-hardware-setup/252909)
was reviewed without a matched 32 GB / dual-XTX result. Implementation basis:
[resident split support](https://github.com/Niko1221/Strata/pull/848),
[pinned multi-GPU documentation](https://github.com/Niko1221/Strata/blob/296b59d2f73c8f04a805df29c2fa97655adace78/docs/MULTI_GPU.md)
and [memory/storage behavior](https://github.com/Niko1221/Strata/blob/296b59d2f73c8f04a805df29c2fa97655adace78/docs/DETAILS.md).

## Comparison and subsequent update

The [NVIDIA comparison and original upstream audit](NVIDIA-COMPARISON-RUNTIME-AUDIT-2026-10-18.md)
records the saved 68.8 / 64.6 t/s NVIDIA medians and the 59.8 / 47.8 AMD samples
above with their configuration/method differences. These measurements used HIP
0.1.44.1. See [the subsequent runtime update](RUNTIME-UPGRADE-2026-10-18.md) for
newly installed versions and separate validation; do not relabel these earlier
measurements as a newer build's benchmark.
