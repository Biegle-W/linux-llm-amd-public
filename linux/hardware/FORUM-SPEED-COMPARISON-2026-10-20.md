# Why similar 7900 XTX systems report different speeds — October 20

This comparison uses saved local measurements and freshly reviewed sources.
No benchmark was rerun and no production setting changed. The Strata update is
functionally complete; that does not establish that every performance setting
has been optimized. Some headline differences disappear after separating the
metrics, while a prefill and standardized SGLang gap remains unresolved.

## What the reports actually measure

| Source | Author's hardware, model and workload | Reported result | Local comparison and limit |
|---|---|---|---|
| [lcz.me2317](https://lcz.me/topic/2317), farmer node; post date not exposed, reviewed October20 | EPYC7452, about125GiB RAM, two7900XTX, Strata0.1.43, Flash-Next IQ3_S with projection; two independent single-GPU replicas sharing a host expert arena | 70–80t/s per stream,160t/s aggregate | Current Strata IQ3_XXS code75.28/prose50.31t/s are single-request results. The headline is not160t/s for one answer. Different quant/model transformation, sampling, memory and topology preclude an exact ratio. Replicas use a different topology from the current local layer-split instance. |
| [lcz.me1640](https://lcz.me/topic/1640), flyer666; September11 benchmark refresh | Two7900XTX TP2, Qwen27B W4A16 plus W4A16 DFlash2; short favorable code/math | Code180–250t/s; English chat90–120t/s; standardized depth0/16K128.3/108.8t/s | Current160K SGLang: code178.82/prose63.40t/s on separate sampled short tasks. Code is near the reported range; prose is below it. These are different prompts, not a matched platform A/B. |
| [lcz.me2062](https://lcz.me/topic/2062/5), J I; date not exposed, reviewed October20 | Ultra7265K,64GB DDR5-6000, two7900XTX at x8/x4 without P2P, Strata0.1.38, IQ3_XXS,128K,INT8KV,MTP4/min-p0.5,auto prefill | Fixed32,768-input nativePP1838t/s; fixed128,000-input PP2129t/s, clientTTFT60.3s; decode57–66t/s across the discussed dual-card tests | Current Strata fresh8185–8188 input PP912.2t/s; near257984 input PP992.7t/s. Prefill is lower, but input length, chunks, memory/cache budgets, MTP, build and hardware differ. This deserves a matched investigation rather than a claimed2x regression. |

The current local records are [Strata](results/strata-startup5-2026-10-20.json)
and [Qwen INT4](results/qwen-int4-context-2026-10-20.json). Code/prose rates use
three timed trials, temperature0.6/top-p0.95/seed42, thinking off and256-output
caps; external SSE decode excludes time before first output. The prefill marker
tasks are fresh and uncached. Native PP, engine-phase PP, external TTFT and
aggregate throughput are distinct metrics.

## Real local constraints and unresolved causes

1. **SGLang's fast communication path differs.** Both cards participate in TP2,
   but direct peer access remains unavailable and production uses RCCL host
   transport with custom all-reduce disabled. The author's RDNA recipe uses a
   custom peer-buffer reducer. This is a plausible source of overhead; its cost
   has not been isolated. See the [saved controlled investigation](CLEAN-TUNING-2026-10-17.md)
   and [P2P diagnosis](PCIE-P2P-2026-10-17.md). The current i9/64GB report still
   records host transport; the purchased switch has not been installed/tested.
2. **Strata has deliberately different budgets.** Current settings retain
   prefill2048, MTP3/min-p0.7,13.5GiB expert RAM,32K resident INT8KV within a256K
   native window,7/8GiB reserve targets and continuous desktop protection.
   The replica report uses auto:32768 prefill, MTP4/min-p0.5, a47.96GiB shared
   expert arena and700MiB requested reserve. These are candidate explanations,
   not measurements of which knob causes the gap; do not copy those memory
   allocations or lower guards on this64GB workstation.
3. **Speculation depends on the output.** Code, prose, language, sampling and
   acceptance change tokens emitted per verifier pass. The historical local
   forum-style run measured79.61t/s at depth0 and93.67t/s at16K, versus the
   author's128.3/108.8. These used the same tool family but different passages
   and platforms. Preserve that genuine gap and its October17 i5/32GB attribution;
   it is not a new i9 measurement or a quantified P2P penalty.
4. **Thermals are an unclosed historical lead.** October17 telemetry reached
   GPU0 hotspot108C with SMU limiting activity, and a vLLM run reached107C.
   No current controlled cooling A/B quantifies a speed penalty. Those samples
   cannot establish that today's Strata run is thermal-throttled.
5. **Cache hits change apparent responsiveness.** Current SGLang's fresh160861
   input took283.113s to first output; its160908-input history follow-up took
   0.795s and reported160832 cached tokens. Neither latency implies a change
   in fresh native prefill or sustained decode. A configured160K/256K window
   alone is not the number of tokens processed by every request.

The [pinned Strata multi-GPU guide](https://github.com/Niko1221/Strata/blob/9ae93f7b1fe989d04a8e404d32cddaeeff10505f/docs/MULTI_GPU.md)
documents layer splitting and overlapped handoff, not per-layer TP collectives.
Missing P2P therefore must not be presented as the established explanation for
Strata's prefill gap. Its matching two-XTX overlap example reports70.1code/55.9prose
t/s, broadly the same range as the local75.28/50.31, with different workloads.
The [Radeon SGLang recipe](https://github.com/StevenChenSE/sglang/blob/gfx1100-support/README.zh-CN.md)
is a primary implementation lead; local build remains pinned to f84475cc with
the validated verifier repair, not an unreviewed latest branch.

Also consulted [Level1Techs7900XTX notes](https://forum.level1techs.com/t/7900xtx-llm-inference-notes/250869),
ivgranite, May31: single7900XTX/9600X/96GB, Qwen3.6 MoE MTP versus Gemma4 at32K.
Its measured time-to-answer comparison reinforces reporting output length and
wall time alongside decode; it is not a matched Strata or Qwen27B TP2 benchmark.

## What would resolve the remaining gap

Replay the same text, tokenizer, sampling, actual input/output lengths, warm-up,
cache state and timing method before computing a speed ratio. Record per-card
hotspot/clocks/power, CPU expert time, GPU expert hit rate, draft acceptance and
copy/collective time. Then compare one bounded setting at a time: Strata prefill
chunk/cache/residency policy within unchanged guards, and SGLang collectives
only after real peer capability and correctness are validated. No tests or new
optimization are authorized by this research note itself.
