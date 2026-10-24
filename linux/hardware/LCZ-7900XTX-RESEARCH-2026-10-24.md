# RX 7900 XTX forum sweep — October 24, 2026

Research and read-only configuration audit, **not a new benchmark or runtime promotion**.
Target: i9-13900KS, 64 GB RAM (61.51 GiB visible), two RX 7900 XTX 24 GB on
CPU PCIe4 x8/x8, Intel desktop, ROCm7.2.3. Both GPUs remain required for every
active model. No clocks, drivers, firmware, profiles, contexts, defaults or servers
were changed by this review. Daily-update promotions are independent work.

## Coverage and evidence limits

Searched LCZ site-wide using 7900XTX, 7900 XTX, gfx1100, Strata, Maya, DeepSeek,
SGLang, vLLM, hipBLASLt, WMMA, HiCache, FP8, TurboQuant, EXL3, Hipfire, Paiton,
NUMA, power and clocks. Also followed the current [7900xtx tag index](https://lcz.me/tags/7900xtx)
and primary source links. This is a broad public/indexed search, not an exhaustive
download of every forum post. Some topic/API pages were inaccessible; excerpts
and user-supplied text are identified below. Forum dates were generally not
exposed in the fetched view: dates below are access dates unless stated otherwise.
Author reports are not local results, and matching GPU names do not match the
checkpoint, quantization, prompt, acceptance rate, context or thermal conditions.

Rechecked [ivgranite's Level1Techs XTX notes](https://forum.level1techs.com/t/7900xtx-llm-inference-notes/250869)
(May31,2026; single XTX/9600X/96GB/ROCm7.2.3/32K): time to a completed answer can
differ from decode speed because reasoning/output lengths differ. This supports
measuring completed tasks; it does not validate a Strata/Maya kernel or predict
dual-card performance. See the maintained [source ledger](FORUM-OPTIMIZATION-SOURCES.md).

## Highest-priority candidates

### 1. Audit and benchmark Strata Qwen hipBLASLt selection

[naniandemeng, LCZ2032](https://lcz.me/topic/2032) reports a single XTX/X99/64GB DDR3,
Strata0.1.27/ROCm10/Swift IQ3_XXS experiment: matching the hipBLASLt table and
covering actual GEMM shapes improved prompt processing. [Ben Lee, LCZ2027](https://lcz.me/topic/2027)
separately describes gfx1100/ROCm7.2.3, a version100202 table and later WMMA trials.
These are older single-card workloads, not expected gains for this host.

Local read-only findings:

- `dsh/strata-iq3-profile.json` enables MMQ and split overlap, with prefill2048,
  split26, six workers, 13.5GiB expert cap and native256K/INT8 KV32K residency.
- Its environment does not explicitly select a hipBLASLt table. There is no
  `tuning/` directory beside the configured binary. Reviewed saved native and
  October24 daily-launcher logs contain no `hipBLASLt tuning enabled` message.
- The retained SDK header advertises hipBLASLt1.2.2 (100202); source includes
  `tools/hip/gfx1100-hipblaslt-100202.txt`. The historical build metadata includes
  hipBLASLt support. A header and build cache do **not** prove the library loaded
  by the present binary or table hits for a workload.

This is an actionable audit gap, not proof of an existing slow fallback. First
identify the exact binary and loaded library, then run table-off/on and verbose
shape coverage through an isolated normal-launcher comparison. Calibrate only
if the matching bundled table misses relevant shapes. Preserve desktop reserves,
expert/RAM caps and contexts; check fresh prefill, code/prose decode, TTFT,
retrieval/history/tools and full-run thermals. An algorithm table can change
rounding; it needs quality checks, not only a timing pass.

Primary: [pinned AMD guide](https://github.com/Niko1221/Strata/blob/8183c6b67162340c09b67360860177c577a65f2e/docs/AMD_HIP.md),
[GEMM selection](https://github.com/Niko1221/Strata/blob/8183c6b67162340c09b67360860177c577a65f2e/src/prefill/gemm.cu),
[tuner](https://github.com/Niko1221/Strata/blob/8183c6b67162340c09b67360860177c577a65f2e/tools/hip/tune_hipblaslt.cpp).
Do not export this Qwen recipe to the separate DeepSeek engine or Maya by assumption.

### 2. Revisit bounded Qwen prefill and WMMA only after the table audit

[LCZ2059](https://lcz.me/topic/2059) reports X99/14-core/four-channel RAM/single XTX,
Qwen Flash-Next IQ3 quants, Strata0.1.34, pinned expert storage and larger prefill.
[LCZ2027](https://lcz.me/topic/2027) reports that its two WMMA opt-ins worked as a
pair; other posts report regressions. Both are version/workload-specific.

Local prefill2048 was selected with memory protection on older source/hardware;
an increase is not free VRAM. After establishing the table control, consider
2048/4096 and only an admissible8192 arm, with unchanged actual reserve and guard
limits. Do not enable every forum environment flag together. Newer source's
defaults must be inspected rather than reapplying old PRs. Prior
[overlap/prefill selection](STRATA-OPTIMIZATION-2026-10-19.md) and
[native256K validation](STRATA-CONTEXT-2026-10-19.md) remain evidence, not tests of
these new candidates. Maya GLM's failed fused path must remain disabled.

### 3. Test cache retention for real multi-agent work, not just warm repeats

[LCZ1921/11](https://lcz.me/topic/1921/11), retrieved search excerpt, reports
dual-XTX/Qwen27B/TP2/196608 context and a48GB host cache: write-through recovered
an evicted prefix whereas its write-back trial recomputed it. Full page access
failed during this review. [LCZ1791/118](https://lcz.me/topic/1791/118), T7910/dual-XTX
W8A16/EAGLE experiment, instead reports successful write-back and identifies a
local write-through patch as its earlier slowdown. These reports contradict a
universal write-policy recommendation.

Local SGLang has BF16 KV/prefix reuse, but no selected HiCache profile. Candidate:
a bounded host cache tested with A-cold → A-hot → B/C eviction → A-return,
without flushing between requests. Compare cold prefill, return TTFT, peak host
memory and zero swap/spill, for both policies supported by the exact fork. Size
is per implementation/rank: do not copy a48GB forum allocation onto this64GB
desktop. HiCache retains evicted prefixes; it does not enlarge live GPU KV.
Primary: [HiCache documentation](https://docs.sglang.io/docs/advanced_features/hicache),
[retained fork](https://github.com/StevenChenSE/sglang/tree/f84475ccf593087df3d1da13c9e675eadee12352).

### 4. CPU affinity for the large offloaded models

[LCZ557](https://lcz.me/topic/557), dual-Xeon/64GB/single XTX/ROCm7.2.0,
shows why NUMA placement matters on a dual-socket system. This machine is
single-socket: copying its NUMA command is not the same optimization.
An outstanding local candidate is a physical-core/thread and P-core affinity
sweep for CPU-expert Ornith/Super, with decode threads separated from batch
threads; Maya's24-thread DeepSeek would require its own comparison. See
[the existing research plan](SLOW-MODEL-OPTIMIZATION-RESEARCH-2026-10-22.md).
This is not a reason to overclock, change RAM timings or assume more threads help.

## Interesting engines with deployment conditions

| Lead | What the evidence actually covers | Decision for this host |
|---|---|---|
| [Hipfire LCZ2347](https://lcz.me/topic/2347), [agent follow-up2422](https://lcz.me/topic/2422), Ben Lee | v0.4.2.1/6b363a56a1ae, single XTX, Qwen27B engine-specific MQ4-XTS/Q8 KV/DFlash;8K/256-output and longer-context tests plus agent examples | Promising engine candidate, not a measured upgrade over local TP2 GPTQ. The fast single-card DFlash recipe violates the current both-card placement requirement. |
| [Hipfire primary multi-GPU guide](https://github.com/warpfront/hipfire/blob/master/docs/multi-gpu.md) | Current guide has dense TP and experimental Flash-Next EP/PP; dense TP refuses DFlash/DSpark, EP requires peer access; gfx1201 EP receipts do not validate gfx1100 | Inspect exact model/architecture/admission and prove both-card placement first. Local direct P2P is disabled; do not silently use one card or treat advertised multi-GPU as a passed profile. |
| [nasone32 RDNA3 fork](https://github.com/nasone32/llama.cpp-RDNA3-7900xtx-opt), linked in [LCZ1791/108](https://lcz.me/topic/1791/108) | Experimental internal HIP collectives, adaptive MTP, Qwen27B Q8 and Flash-Next; T7910/switch/P2P forum report | Lower-priority alternative for a specific higher-precision or kernel test. Q8 weights remain quantized; wire-Q8 and changed kernels need quality checks. No evidence it accelerates our DeepSeek/GLM packs. |
| [EXL3 ROCm port](https://github.com/phoenixhaxor/exllamav3-rocm) | Primary source documents single-XTX EXL3/DFlash2/MTP/8-bit KV, not a local dual-card MoE result | Already known lead; no new matching dual-card proof found. Do not re-download EXL3 or activate it on headline speed alone. |

## Useful reports that do not justify a local change

- **Replicas are not layer split.** [farmer node, LCZ2317](https://lcz.me/topic/2317)
  uses EPYC7452/~125GiB RAM, Strata0.1.43/Qwen IQ3_S, one engine per card and a
  shared host expert arena. Its64K/128K/240K concurrent results are not one model
  using both cards. Host consumption and700MiB/card reserve are not our budget.
  [LCZ2343](https://lcz.me/topic/2343) changes both source andROCm10.1 and also uses
  replicas; it does not isolate an SDK speedup. Keep replicas out under current policy.
- **Overlap is already selected and measured.** [LCZ2062](https://lcz.me/topic/2062)
  has x8+OCuLinkx4/no-P2P; [upstream layer-split guide](https://github.com/Niko1221/Strata/blob/8183c6b67162340c09b67360860177c577a65f2e/docs/MULTI_GPU.md)
  explains the mechanism. Our [matched overlap experiment](STRATA-OPTIMIZATION-2026-10-19.md)
  already supports the setting. It is not true TP or a promise of doubled decode.
- **PCH hostcall repair is not missing here.** [LCZ2525](https://lcz.me/topic/2525)
  was supplied verbatim by the user after direct/API access failed. B760M CPUx16+
  PCHGen3x4/DDR4-2666, Qwen27B and Flash-Next have different workloads. Its
  [CLR hostcall PR11277](https://github.com/ROCm/rocm-systems/pull/11277)
  addresses missing PCIe atomics; our host-transport TP2 already works. No reason
  to replace libamdhip64, flash firmware or install a switch based on that failure.
- **Scheduler fairness is conditional.** [Ben Lee, LCZ1532/95](https://lcz.me/topic/1532/95)
  reports dual-XTX/MTP3/BF16KV/~64K mixed requests with
  [PR34058](https://github.com/sgl-project/sglang/pull/34058). This is a concurrent
  prefill/decode fairness control, not faster solo decode. Local DFlash2 currently
  admits one request; only test it with a deliberate concurrency validation.
- **ROCm and FP8 headlines are not new wins.** [LCZ1640](https://lcz.me/topic/1640)
  records FP8-KV long-prefill problems. Our [context follow-up](QWEN-INT4-CONTEXT-2026-10-20.md),
  [ROCm10.1 comparison](ROCM101-2026-10-21.md) and
  [7.2.4/7.14.1 tests](ROCM-724-7141-2026-10-22.md) already justify retaining7.2.3/BF16.
- **GLM quant/sampling is already investigated.** [johnnybegood, LCZ2195/3](https://lcz.me/topic/2195/3),
  explicitly tested October8 on3080+3090/128GB/Maya1.0.11, changes temperature and
  quant in several comparisons. Our [matched S/S24 selection](MAYA-S-VS-S24-2026-10-20.md)
  and [S-drafter retest](MAYA-S-DSPARK-2026-10-23.md) take precedence. Changing
  temperature to boost acceptance is a sampling change, not a free kernel speedup.
- **Old llama/Vulkan recipes mostly target retired Qwen profiles.**
  [LCZ100](https://lcz.me/topic/100), [353](https://lcz.me/topic/353),
  [1164](https://lcz.me/topic/1164), [1398](https://lcz.me/topic/1398) and
  [1744](https://lcz.me/topic/1744) reinforce workload/acceptance/cache sensitivity,
  not reinstating deleted GGUFs. [LCZ1252](https://lcz.me/topic/1252) and
  [1532](https://lcz.me/topic/1532) describe the vLLM/SGLang route already in use.
- **Power, clocks and cache hit rate deserve observation.**
  [LCZ1791/104](https://lcz.me/topic/1791/104) compares an intentionally1500MHz-capped
  machine with2000MHz, not a generic undervolt gain. [LCZ1269/24](https://lcz.me/topic/1269/24)
  contains corrected power estimates and AI-assistant advice, not a Linux-XTX
  voltage validation. Review actual clocks/power/SMU flags under real work before
  any tuning. Fan control, Intel rendering and thermal logging already exist.
  [yi song, LCZ2262](https://lcz.me/topic/2262) is a useful reminder to measure
  prefix reuse in a real DSH conversation; its proposed causes are not verified
  facts about this installation. Keep stable prefixes and measure actual cache
  counters/TTFT before changing a frontend or model.

## Recommended order

1. Strata Qwen table-selection/shape audit and guarded off/on benchmark.
2. Bounded prefill-size sweep against that control; inspect current WMMA paths.
3. Real DSH multi-turn cache/eviction trace; bounded SGLang HiCache only if needed.
4. CPU-expert thread/affinity sweep on the slow large models.
5. New engines only after exact dual-card/model admission is established.

All remain candidates. Any GPU work requires the repository GPU-LOCK, full
thermal coverage and existing guard/quality gates. This review held no GPU lock
and launched no inference. No gain, general quality score or hardware purchase
is inferred from another machine's results.
