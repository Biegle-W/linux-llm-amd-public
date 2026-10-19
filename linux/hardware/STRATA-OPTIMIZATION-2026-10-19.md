# Strata dual-AMD handoff and desktop headroom — October 19, 2026

**Historical 32K tuning:** the later [native256K profile](STRATA-CONTEXT-2026-10-19.md) supersedes the active settings below. Original measurements are preserved.

Scope: existing Qwen3.8-Flash-Next GSQ-RCO IQ3_XXS, Strata HIP 0.1.45,
source `477ac13cbe8e582c20484871ce459d20d82df09d`, two RX7900XTX 24 GB,
i5-13600KF/Z690 CPU PCIe4 x8/x8 and 32 GB RAM. Both GPUs are required.
No model download, quantization, runtime replacement, driver/BIOS/clock change,
frontend change or single-GPU test is part of this work.

## Desktop protection

The active profile reserves **7,168 MiB on each card**, checked before backend
handover; runtime admission rejects profiles below 6 GiB per card. Stage-specific dense weights are trimmed
with an explicit layer boundary at 26. This recovers some duplicated storage
while retaining the same two cards and 32,768-token total context.

`dsh/strata_memory.py` and the router sample physical RAM, owned-worker swap,
dedicated VRAM residency and whole-card free VRAM every **0.5 seconds**:

- Below 3 GiB free on either card for two samples, or below 1.5 GiB once:
  unload only the router's Strata worker.
- Below 3 GiB available host RAM for three samples, owned swap above 256 MiB,
  or owned dedicated VRAM spill above 256 MiB: unload that worker.
- Missing/invalid GPU telemetry for three samples: fail closed by unloading it.
- Stop has a three-second grace period, then kills only the owned process group.
  A latched `memory_fault` prevents chat requests from automatically reloading
  the model. `/health` reports degraded; use explicit `/models/load` or restart
  after freeing resources. The independent harness, gateway and other apps remain.

The worker-only systemd `MemorySwapMax=0` scope remains. Global swap is unchanged.
The inactive 64 GB candidate reserves 6 GiB/card, the enforced minimum; its
128K context is not activated or claimed tested. The active profile uses 7 GiB/card. A reserve is not a hard allocation
partition, and sampled monitoring cannot guarantee protection from every sudden
allocation, driver failure or hardware fault.

## Measurement method

The matched serial/overlap arms use the same model/source, explicit split26,
stage trimming, 6 GiB reserve, 10 GiB CPU expert budget, 512 prefill, INT8 KV,
MTP3/minimum probability 0.7, six pool workers and one session. Only
`STRATA_SPLIT_OVERLAP` changes. Both-card native placement and the worker's
actual environment/arguments are checked before measuring.

Each arm excludes one warm-up per task, then measures three short code and
three prose requests. Greedy decoding, thinking off, no conversation checkpoint,
512-token output cap. Report native engine timing medians and actual output
lengths, not external SSE rates. A fresh repetitive 8K input separately measures
native prefill with zero cached input. Its short answer is a capacity/PP probe,
not sustained long-context decode. Cold model loading is excluded.

`hardware/bench-strata-overlap.py` measures an already running managed backend;
it neither launches another inference engine nor terminates applications.
Generated text is omitted from result artifacts; hashes and numeric timings are
retained. Warm-up, placement/rounding, ordinary desktop load and restart order can
change output and speculative acceptance, so these small samples do not prove
universal speed gains or broad quality equivalence.

## Results and retained profile

| Arm | Overlap | Prefill chunk / expert RAM budget / VRAM reserve per card | Code / prose median decode t/s | Native PP at 8,022 input t/s | Minimum free VRAM GPU0 / GPU1 GiB |
|---|---:|---|---:|---:|---|
| serial-1 | 0 | 512 / 10 GiB / 6 GiB reserve | 65.9 / 46.2 | 774.8 | 5.249 / 3.708 |
| overlap-1 | 1 | 512 / 10 GiB / 6 GiB reserve | 79.4 / 53.4 | 772.7 | 5.249 / 3.845 |
| serial-2 | 0 | 512 / 10 GiB / 6 GiB reserve | 66.3 / 46.8 | 780.8 | 5.249 / 3.81 |
| prefill-2048 | 1 | 2048 / 12 GiB / 6 GiB reserve | 81.0 / 53.7 | 984.2 | 4.568 / 3.125 |
| prefill-2048-reserve7 | 1 | 2048 / 14 GiB / 7 GiB reserve | 77.6 / 52.3 | 938.1 | 5.568 / 4.115 |

Selected: **overlap enabled, 2048-token prefill, 14 GiB CPU expert budget**,
explicit split26 and stage trimming, 7 GiB reserve/card, unchanged 32K context,
INT8 KV and MTP3/minimum probability 0.7. Cold expert loading is excluded.
The matched overlap arm improved code/prose medians by **20.5%/15.6%**
versus the first serial control; repeating serial returned close to the original
speeds. The 6 GiB/2K candidate was faster (81.0/53.7 t/s, PP984.2), but left
only 3.125 GiB free on the display card, close to the 3 GiB guard threshold.
The selected 7 GiB candidate left **4.115 GiB free** there, trading about
4.2% code /2.6% prose /4.7% prefill speed for one more GiB of margin.
Compared with the first protected serial control, the retained complete profile
improved code/prose by **17.8%/13.2%** and the same 8,022-input prefill by **21.1%**.
These are small sequential samples; they do not isolate each later setting.

The selected startup reported **11.79 GiB pinned CPU expert backing** and
**14.65/13.53 GiB GPU expert caches**. Dense/head/MTP weights, KV, prompt/graph
buffers and unrelated desktop allocations occupy additional memory. The 14 GiB
value is a CPU expert budget, not a claim that exactly 14 GiB is consumed.

The matched serial→overlap comparison is separate from later complete-profile
prefill/RAM changes. Compare actual output counts/hashes in the data; identical
outputs occurred in several runs, but not every greedy output was identical.

Production validation passed arithmetic, a complete tool-call/result round trip,
authenticated gateway access (recorded separately), SSE and **30,070 input**
three-marker retrieval: native PP **1063.6 t/s**, **28.53 s total**.
Its 19-token answer is not sustained full-context decode. Latest
short-task medians are **77.6/52.3 t/s**. Full validation minimum
available RAM: **13.24 GiB**; maximum
worker swap and sampled dedicated-VRAM spill were zero. Monitoring cannot prove
long-duration stability or prevent every burst. The selected model remains in its
visible terminal; DSH stays separate and API IDs/endpoints/context are unchanged.

[Curated settings, individual timings, output hashes and memory checks](strata-optimization-2026-10-19.json).
Guard/admission/ownership regression tests passed in both repositories. Tests use
synthetic memory pressure; no GPU-exhaustion or deliberate desktop-crash test was run.


## Why TP and extra VRAM are different

Strata's supported two-card mode is **layer/pipeline splitting**, not tensor
parallelism. Overlap stages the next card's graph before the previous card has
finished, removing a host synchronization/launch from the critical path. It does
not introduce RCCL collectives, P2P or per-layer tensor sharding. The cached
weights, RAM fallback, prefill batching and kernel paths remain relevant to speed.

The earlier startup warning about borrowed experts possibly being reread from
SSD identifies a potential path, not a measurement of disk-caused slowdown.
The protected serial arm's warm 8K request recorded zero expert-blob reads;
cold startup/PLE/OS reads are separate. Larger RAM and prefill candidates must
therefore be measured rather than assumed to solve all prompt latency.

## Source trail

- [Pinned upstream multi-GPU guide](https://github.com/Niko1221/Strata/blob/477ac13cbe8e582c20484871ce459d20d82df09d/docs/MULTI_GPU.md)
  and [PR936](https://github.com/Niko1221/Strata/pull/936), bsvinay, October 5:
  dual-XTX/9900X/52 GB results motivated the overlap test. Its 53→70.1 code and
  45→55.9 prose t/s are another machine's results, not local target guarantees.
  The same guide documents stage trimming for explicit split points.
- [Pinned AMD guide](https://github.com/Niko1221/Strata/blob/477ac13cbe8e582c20484871ce459d20d82df09d/docs/AMD_HIP.md):
  desktop reserve, CPU residency and storage caveats.
- [lcz.me topic2062](https://lcz.me/topic/2062), reviewed October 19: dual7900XTX,
  Swift IQ3_XXS/128K, Strata0.1.38, x8+OCuLinkx4, roughly50 GiB host use.
  Useful layer-split/prefill comparison, different host memory and profile.
- [Level1Techs gfx1100 inference notes](https://forum.level1techs.com/t/7900xtx-llm-inference-notes/250869),
  ivgranite, reviewed October 19: general memory-budget/ROCm experience, not a
  matching Strata handoff benchmark. No local speed is inferred from it.

[Maintained forum applicability](FORUM-OPTIMIZATION-SOURCES.md).
[Earlier measurements and context history](BENCHMARK-HISTORY.md).
