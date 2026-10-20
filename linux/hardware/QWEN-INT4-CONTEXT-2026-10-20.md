# Qwen INT4 larger contexts and profile retirement — October 20, 2026

Hardware: i9-13900KS, 64 GB RAM (61.51 GiB visible), two RX 7900 XTX 24 GB,
CPU PCIe4 x8/x8. Switch is not installed; direct P2P is disabled. Both cards
participate via TP2 host transport. No engine, weight quant, CPU-offload policy,
RoPE setting or model download changed.

## Selected profiles

SGLang retains only TP2 DFlash2 at **163,840 tokens**, BF16 KV. vLLM
retains compiled MTP3 at **163,840 tokens**, `bfloat16` KV.
The separate SGLang MTP profile is retired. Both new profiles passed fresh
near-window markers and full-history follow-ups, with zero owned swap/spill.
[Context selection, actual counts and limits](results/qwen-int4-context-2026-10-20.json).

Builds remain SGLang `f84475ccf593087df3d1da13c9e675eadee12352` with its retained
local RDNA verification repair, and vLLM `0.32.1rc1.dev36+ge68efc685.rocm72`
with the retained Radeon prefill tiles. Target: existing AutoRound GPTQ INT4/group64.
Dense weights remain GPU resident. SGLang uses the existing compressed-tensors
DFlash2 draft, eight draft tokens/window 2048 and BF16 Mamba state, eight state
slots, chunks 2048, one request, static fraction 0.85. vLLM retains compiled MTP3,
full-decode graphs 1/4, chunks 2048, BF16 activations/Mamba, utilization 0.82 and
RCCL Simple. Context and the tested fixed KV budget are the only vLLM changes.

| Profile | Context | KV | Fresh ~8K engine prefill t/s | Fresh prefill external TTFT s | Short TTFT s, code / prose | Short decode t/s, code / prose |
|---|---:|---|---:|---:|---:|---:|
| SGLang DFlash2 | 163,840 | bfloat16 | 1314.8 | 6.235 | 0.102 / 0.097 | 178.82 / 63.40 |
| vLLM MTP3 | 163,840 | bfloat16 | 1413.8 | 5.806 | 0.066 / 0.092 | 130.31 / 68.96 |

Three timed trials per short code/prose workload after one excluded warm-up,
256-output cap, temperature 0.6/top-p0.95/seed42/thinking off. Three fresh salted
~8K marker prompts are greedy and use 64-output caps. Exact tokens, output counts,
phase observations and memory are retained in the numeric record. SGLang and
vLLM engine-phase definitions differ; external TTFT includes other request work.
Loading/compilation are excluded. Stateful caches/desktop activity remain, so
these are local observed medians, not a controlled causal or statistical claim.
The earlier 64K DFlash result 205.12/73.44 t/s remains history; the new larger
window's measured short rates are lower. No zero-regression claim is made.

## Actual long-context checks

| Profile | Fresh input / output | Fresh TTFT s | History input / output | Follow-up TTFT s | Minimum whole-card free GiB, GPU0 / GPU1 | Minimum available RAM GiB |
|---|---:|---:|---:|---:|---:|---:|
| SGLang DFlash2 | 160,861 / 22 | 283.113 | 160,908 / 22 | 0.795 | 3.48 / 4.47 | 43.95 |
| vLLM MTP3 | 160,868 / 22 | 183.591 | 160,915 / 22 | 1.467 | 5.92 / 7.32 | 46.63 |

Both recovered all three markers near the beginning/middle/end and completed
full-history follow-ups, plus arithmetic, ordered JSON, synthetic tool roundtrip
and SSE. SGLang reports 160,832 cached tokens for its follow-up. vLLM does not
expose an API cache token count in these responses; the low follow-up latency
is not converted into a fabricated cached count or native prefill rate.
These are functional probes with short outputs, not general full-window quality
or sustained long-context decode benchmarks. Context includes input and output.

Candidates ran in bounded 52G/no-swap scopes. A debounced 3 GiB available-RAM and
whole-card free floor stopped only owned workers on failure. All passing cases
had zero observed owned swap/spill. Production startup guards are strengthened to 22.75 GiB/card
for SGLang and 21 GiB/card for vLLM; test extrema are sampled, not a guarantee
against future unrelated GPU allocations.

## Selection and rejected candidates

SGLang 192K BF16 DFlash loaded and passed small functional checks but left only
2.714 GiB free on the display card. The 3 GiB test guard stopped it; it was not
activated. 160K passed all declared checks. Memory fraction/verification/cache
precision were not relaxed to admit 192K.

vLLM 128K BF16 / 5 GiB-per-rank KV is the control for 192K INT8 / 4.5 GiB-per-rank KV.
Both require the same functional/near-window/history and memory checks. The
predeclared rule admits 192K INT8 if the geometric mean of short code/prose decode
and fresh 8K engine prefill is at least 90% of the eligible control. The optional
same 192K BF16 / 7.5 GiB trial required 6 GiB measured reserve in the 128K control;
its minimum was below that threshold, so it was not attempted.

The first 160K BF16 attempt was interrupted by a normal Maya launch; its user-authorized retry passed. INT8/control composite ratio: **0.8697**. It failed the 0.90 threshold. A final 160K BF16 / 6 GiB pool adds only 1 GiB/rank over 128K, with the same 3 GiB guard. Its declared rule required all checks and at least 95% of the 128K control composite; measured ratio **0.9903**. Selected `vllm-bf16-160`.

INT8 KV changes cache precision; these limited checks do not establish broad
quality equivalence. HiCache and FP8 KV are not activated. HiCache improves
prefix retention after eviction and cannot be counted as extra live GPU KV.

## Retirements and launch/API integration

Muse Glimmer 30B Q4 and Nemotron Super Q4_K_XL are removed from active catalogs,
presets and candidates. Exactly four GGUF files total 95.726 GiB were deleted;
all Super IQ3 shards and shared family metadata remain. The separate SGLang MTP
profile is also removed; its GPTQ target is retained for DFlash2/vLLM. Historical
measurements and a non-installable Q4 test fixture remain. The active catalog
has ten profiles: five llama.cpp, SGLang DFlash2, vLLM, Strata and two Maya.
[Deletion/dependency manifest](results/model-retirement-2026-10-20.json).

PATH/Desktop command names are unchanged. Use `llm-sglang` / `llm-vllm` and start
`dsh` separately. Existing API IDs are unchanged for retained profiles; clients
must refresh their catalog rather than request retired IDs. Gateway addresses,
credentials, ACLs and the saved DSH default remain unchanged. Normal-launcher
proofs are functional checks, not extra benchmark trials. Windows/NVIDIA snapshots
remain historical; the Shared handoff supplies the current Linux API catalog.

## Sources and evidence

The [both-forum source trail](FORUM-OPTIMIZATION-SOURCES.md#qwen-int4-context-october-20)
distinguishes similar dual-XTX BF16/INT8 reports on
[lcz.me1921](https://lcz.me/topic/1921/5) and [lcz.me1674](https://lcz.me/topic/1674)
from local measurements. [Level1Techs' Crucible discussion](https://forum.level1techs.com/t/crucible-llm-bench-your-llm-and-server-is-it-fast-enough-for-everyone/257531)
supports token-count/retrieval and TTFT methodology; no matched Level1Techs
configuration was found. Primary implementation links and author/date/hardware
are in the source ledger. No third-party speed is copied into the local table.
[All candidates/trials and selection](results/qwen-int4-context-2026-10-20.json).

Both selected profiles also passed their normal visible Desktop launchers,
source/environment flags, TP2, JSON/tools/SSE, zero owned swap/spill and the
authenticated ten-ID gateway catalog. [Functional proof record](results/launcher-validation-2026-10-20.json).
