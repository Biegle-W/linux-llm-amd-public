# Higher-quality Maya quant options — October 20, 2026

Research only, on i9-13900KS / 64 GB RAM / two RX 7900 XTX 24 GB. No weights
were downloaded, model switched, benchmark rerun or runtime/profile changed.
The current 32K profiles and [measured results](MAYA-2026-10-20.md) remain active.

## Assessment

| Model / option | Published file size, decimal GB | Precision change | Assessment for this hardware |
|---|---:|---|---|
| GLM Maya-S24, current | 94.7 | IQ2_XXS/IQ2_S/IQ3_XXS routed experts; Q4_K attention/shared experts | Retain current speed baseline: code/prose 21.13/16.54 t/s. |
| GLM Maya-S | 96.5 | Same routed experts as S24; Q6_K attention/shared experts | Smallest plausible quality upgrade. Extra GPU-resident dense weights reduce expert-cache capacity; a small speed loss is plausible, not locally measured. |
| GLM Maya-M | 116.0 | IQ2_S gate/up, IQ3_XXS/IQ3_S down, Q6_K attention/shared experts, higher-bit MTP block | Stronger token-distribution fidelity candidate, but more streaming/cache pressure. Cannot promise a small speed penalty. |
| GLM Maya-L | 156.3 | IQ3_S gate/up, IQ4_XS/Q5_K down | Largest quality-oriented option; poor first choice when maintaining current speed is the priority. |
| DeepSeek Maya-S, current | about 340, including Q6_K Engram | Mixed 2–3-bit routed experts and higher-precision sensitive tensors | Retain current code/prose 6.24/6.84 t/s baseline. |
| DeepSeek Maya-M | Not published in the checked file manifest | Placeholder describes IQ3_S experts/Q8_0 dense | Not a downloadable candidate in the installed verified manifest. |
| DeepSeek UD-Q4_K_XL / UD-Q8_K_XL | about 501 / 508 | MXFP4 routed experts; Q8_0 / BF16 dense, different Engram format | Larger supported-upstream family, not locally validated. More expert traffic is a concern; no near-current-speed claim. |

File size is neither active parameters nor required fully resident memory. The
installed GLM RAM expert tier is capped at 40 GiB. Its measured startup leaves
at least 6 GiB whole-card free on each GPU; dense weights, KV/state, scratch and
expert pools share the remaining allocation. The OS/desktop need host RAM too.
Nominal 64 GB + 48 GB therefore is not a single 112 GB weight cache. Maya can
stream bigger files, but fitting by streaming does not establish equal speed.

The GLM publisher's held-out same-top-token metric is 83.1% for S24, 83.3% for S,
86.2% for M and 90.0% for L. These are distribution-agreement measurements, not
percentages of general model intelligence. Some references use different engine
versions; published multiple-choice accuracy does not clearly separate S and M.
The S24-vs-S speed check uses one V100 restricted to 24 GB: 13.5 versus 11.8 t/s,
S24 about 14% faster. This is not a dual-Radeon prediction.

Recommendation: S is the smallest trial for a modest quality change. M is the
more meaningful fidelity trial if a potentially noticeable slowdown is acceptable.
Keep S24 for speed and DeepSeek Maya-S until another exact quant passes validation.
Neither higher-quality choice has a locally measured speed here. An optional
future A/B can define “not much slower” as at most 10% loss in EACH short code,
short prose and fresh-input prefill median at matching context/sampling, plus
near-30K retrieval, JSON/tools, both GPUs, current reserve guards and zero owned
swap/spill. That is a proposed acceptance criterion, not a completed test.

## Sources and applicability

Reviewed October 20:

- [Publisher GLM model card](https://huggingface.co/peasantsmith/GLM-5.3-Flash-Maya-GGUF): sizes, tensor recipes and held-out metrics. [Pinned S24 comparison](https://github.com/mw00/project-maya/blob/8d9a9b5d705049a87da853717cdc59440252de30/bench/results/MAYA-S24.md), [M recipe/results](https://github.com/mw00/project-maya/blob/8d9a9b5d705049a87da853717cdc59440252de30/bench/results/MAYA-M.md) and [L](https://github.com/mw00/project-maya/blob/8d9a9b5d705049a87da853717cdc59440252de30/bench/results/MAYA-L.md). Engine source and model recipes match the retained local source revision.
- [DeepSeek publisher file API](https://huggingface.co/api/models/peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF): revision `276e0badcfb4a6d8f6c2b9d4da1b468cd339c221`, six Maya-S shards and no Maya-M files. [Pinned supported-format manifest](https://github.com/mw00/project-maya/blob/8d9a9b5d705049a87da853717cdc59440252de30/tools/ds4/download_gguf.json) has an empty Maya-M files map. [Upstream model table](https://github.com/mw00/project-maya/blob/8d9a9b5d705049a87da853717cdc59440252de30/README.md) describes the larger GGUF families.
- [lcz.me topic 2195, post 3](https://lcz.me/topic/2195/3), johnnybegood, October 8 test: 3950X, 128 GB RAM, RTX 3080 20 GB + 3090 24 GB, Maya 1.0.11, 65,536 context, S24/S/M comparisons. Different sampling settings and NVIDIA kernels prevent an equal-quality speed ratio or Radeon prediction. Useful only as a quality/speed tradeoff report.
- [Level1Techs memory-budget discussion](https://forum.level1techs.com/t/advice-on-a-local-ai-server-before-buying/258001), rqzer0, October 8: hardware planning, not a Maya quant comparison. Searches found no matched two-7900-XTX/64-GB higher-quant A/B. Do not substitute older DeepSeek-R1/other-engine reports for this model.

DeepSeek's broader AMD suite still has mixed IQ4_XS/Q4_K bit-exact failures;
the exact current Maya-S avoids those formats. No support check or fingerprint
admission was relaxed. A higher quant would need its own format/kernel validation.
