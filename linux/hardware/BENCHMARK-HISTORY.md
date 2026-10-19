# LLM benchmark and context history

Maintained October 19, 2026. The original compilation used saved results;
the October 19 Strata optimization adds fresh measurements and validation. Dates below are local dates in 2026.
This is the index of measured updates, including older hardware and retired
profiles; it does not imply that every historical configuration remains installed.

## October 19 publication: two hardware result sets

The public README now groups results into the current dual-AMD setup and the
archived dual-NVIDIA setup, with per-model/backend context, prefill, TTFT and
decode. This is a saved-evidence reorganization, not a runtime update or a new
benchmark. The newest llama.cpp build has functional checks only; its older
speeds remain explicitly dated. Missing metrics stay unmeasured.

Additional short TTFT medians below are extracted from existing curated timing
records, not inferred from native prompt durations. Values are seconds, code /
prose; their decode rates and methods remain in the dated sections below.

| Hardware / measured profile | Short TTFT s | Saved source |
|---|---|---|
| Dual AMD, llama.cpp Vulkan Qwen Q4/MTP3, old `f12aaa3` | 0.127 / 0.124 | [Level1 result record](level1-tests-2026-10-17.json), `llama-current-vulkan-q8-mtp3` medians |
| Dual AMD, SGLang repaired DFlash2 `f84475c` | 0.100 / 0.098 | [Clean-tuning record](dual-tuning-clean-2026-10-17.json), `sglang-dflash8-auto-verify1-walkfix-fixed` medians |
| Dual AMD, SGLang repaired MTP3 `f84475c` | 0.101 / 0.090 | Same record, `sglang-mtp3-auto-verify1-walkfix-fixed` medians |
| Dual AMD, vLLM dev329 MTP3 | 0.069 / 0.091 | [Upgrade record](runtime-upgrade-2026-10-18.json), median of three timed trials/task |

Strata's saved native prompt durations and full-request wall times are not
relabeled as TTFT. The previous public README is retained as a historical
publication snapshot in the public tree, with relative source links adjusted.

## How to read the results

- Context is the configured **total token budget**, including instructions,
  tools, history, input and output. 32K = 32,768; 40K = 40,960; 48K = 49,152;
  64K = 65,536; 128K = 131,072; 256K = 262,144; 1M = 1,048,576.
- Allocating a window is different from testing an input near its limit. The
  actual input column records retrieval/capacity probes, not sustained decode.
- PP = prefill tokens/s. **Native PP** is engine-reported prompt timing.
  **Book PP** is llama-benchy 0.4.0's latency-adjusted estimate with PP2048/TG128,
  concurrency one, three runs plus warm-up. Book depth 16K adds 16,384 tokens
  before the prompt/template; it is not the total input length.
- Code/prose are separate decode workloads, in that order when shown as a pair.
  Repeated short SSE tests report warm medians; older inventory trials, native
  timing and single smoke probes are labeled separately. `—` means unmeasured,
  not zero. TTFT includes scheduling, prefill and first output; it is **not PP**.
- Hardware, quantization, sampling, prompt/output lengths and speculative
  acceptance differ between batches. Cross-date values are a history of complete
  profiles, not a controlled GPU or version speed comparison. A three-token
  smoke response is not a useful sustained speed benchmark.

## Current profiles: fresh October 19 evidence

All nine current production profiles now have fresh prefill, external TTFT and
code/prose decode measurements on their installed builds. See
[the current benchmark report](CURRENT-AMD-BENCHMARKS.md) and
[all numeric trials](results/current-amd-2026-10-19.json). Three fresh ~8K marker
probes and three warm short runs/task; production context allocations retained.
Muse's complete final 1,024-output-allowance batch retains all three marker
outcomes, including failures, beside its timing data.
This update changes result publication, not runtime versions or model settings.

### Superseded summary before the fresh nine-profile batch

Current hardware: i5-13600KF, MSI MPG Z690 CARBON WIFI, **two RX 7900 XTX 24 GB**,
CPU PCIe4 x8/x8, **32 GB RAM**. All nine profiles use both GPUs. llama.cpp and
Strata split layers; SGLang/vLLM use TP2 with host transport, without direct P2P.
Only one configured inference backend/model is active at a time.

| Model / quant | Engine / strategy | Allocated context | Actual retrieval input tested | Latest saved prefill | Latest saved decode t/s | Speed evidence |
|---|---|---:|---:|---|---|---|
| Qwen3.8-27B Q4_K_M | llama.cpp Vulkan, MTP3 | 65,536 | 59,984 on earlier single-AMD profile; no fresh dual near-limit probe in latest upgrade | Book PP 1,171.05 at depth 0 | Code 79.38 / prose 45.53 | Oct 17–18, old `f12aaa3` build [L1] |
| Muse-Glimmer-30B UD-Q4_K_XL | llama.cpp Vulkan, no speculation | 32,768 | 32,245 on earlier single-AMD profile | — on dual AMD | 34.89, one guide smoke | Oct 16, old `f12aaa3` build [D16] |
| Qwen3.6-35B-A3B MXFP4_MOE | llama.cpp HIP, CPU experts/cache, MTP3 | 262,144 | 63,911 | Native PP 417.9 at 63,911 input | 96.7, one 48-token code probe | Oct 18, old `f12aaa3` build [MOE] |
| Nemotron-3.5-Bolt-74B-A9B Q4_K_M | llama.cpp HIP, CPU experts/cache, no speculation | 262,144 | 63,911 | Native PP 424.0 at 63,911 input | 35.7, one 101-token code probe | Oct 18, old `f12aaa3` build [Q4] |
| Empero Qwen3.8-35B-A3B IQ4_XS | llama.cpp HIP, CPU experts/cache, MTP3 | 262,144 | 63,911 | Native PP 457.8 at 63,911 input | 104.9, one 128-token code probe | Oct 18, old `f12aaa3` build [MOE] |
| Qwen3.8-27B GPTQ INT4/group64 | SGLang ROCm TP2, MTP3 | 40,960 | 39,440 | Book PP 1,488.15 at depth 0 | Code 114.57 / prose 66.05 | Oct 17, repaired `f84475c` fork [C17] |
| Qwen3.8-27B GPTQ INT4/group64 | SGLang ROCm TP2, DFlash2 | 65,536 | 64,033 | Book PP 1,575.97 at depth 0 | Code 205.59 / prose 71.84 | Oct 17, repaired `f84475c` fork [C17] |
| Qwen3.8-27B GPTQ INT4/group64 | vLLM ROCm TP2, compiled MTP3 | 65,536 | 64,033; latest TTFT 54.56 s | No fresh PP on dev329; previous dev190 Book PP 1,556.04 at depth 0 | Code 130.61 / prose 72.69 | Oct 18, dev329, three warm samples/task [U18] |
| Qwen3.8-Flash-Next IQ3_XXS | Strata HIP, overlapped layer split, CPU experts/MTP3/streamed INT8 KV | 262,144 | 258,044 | Native PP 775.1 at 258,044 input | Short code 72.2 / prose 48.0; long code 39.9 | Oct 19, 0.1.45; three warm short runs, one long sample [CTX19] |

**Latest-build limits:** llama.cpp is now `31288c9c66e5`, but its five profiles
received allocation, math, streaming and tool validation only; the table's
throughput remains dated to the older build. SGLang retained `f84475ccf593`
plus repairs and received functional/cache-capacity revalidation, without fresh
timed workloads. vLLM is `0.32.0rc1.dev329+g39983a5e7.rocm723`; Strata HIP is
0.1.45 / `477ac13cbe8e`. Exact pins: [runtime upgrade][U18].

The three llama.cpp 256K MoE allocations passed approximately 64K retrieval, **not full
256K filling or sustained decode there**. The current dense-model retrieval
figures above predate dual-card migration and are explicitly not fresh dual-card
capacity measurements. Strata's 64 GB candidate retains native 256K and remains inactive/unmeasured. October 18 Strata 0.1.45 timings had background C++ compilation; October 19
Strata timing runs did not. vLLM's new
short benchmark did not. Do not infer a controlled old/new speedup.

## Update history: NVIDIA pair, 64 GB RAM

RTX 4070 12 GB + RTX 3060 12 GB. SGLang/vLLM/HyperQwen use TP2 without P2P;
llama.cpp/Strata use layer splitting and CPU backing where configured.
The retired hardware is a reference, not an active AMD profile.

### October 1–5: original retained measurements

| Date | Model / engine | Allocated context | Native PP t/s | Decode t/s | Sample |
|---|---|---:|---:|---:|---|
| Oct 5 | Flash-Next IQ2_XS, Strata 0.1.39, MTP; retired | 131,072 | 71.7 / 75.8 | 68.9 / 60.3 | Code/prose, 29/25 input, 192 output each |
| Oct 5 | Flash-Next IQ3_XXS, Strata 0.1.39, MTP | 131,072 | 55.4 / 56.2 | 48.8 / 43.9 | Same code/prose method |
| Oct 5 | Qwen27B Q4 MTP, llama.cpp v0.5.0 | 65,536 | 49.2 / 123.7 | 53.5 / 32.0 | Same code/prose method |
| Oct 1 | Muse Glimmer, llama.cpp v0.5.0 | 131,072 | 291.1 | 23.6 | Smoke: 70 input / 93 output |
| Oct 1 | Qwen35B-A3B MXFP4 MTP, llama.cpp v0.5.0 | 262,144 | 72.7 | 26.2 | Smoke: 26 input / 3 output |
| Oct 1 | Nemotron Lightning MXFP4 MTP, llama.cpp v0.5.0; retired | 1,048,576 | 55.0 | 22.1 | Smoke: 30 input / 3 output; not 1M input validation |
| Oct 1 | Empero35B-A3B IQ4 MTP, llama.cpp v0.5.0 | 262,144 | 105.7 | 32.6 | Smoke: 26 input / 3 output |
| Oct 1 | GPT-OSS-20B, llama.cpp v0.5.0; retired | 131,072 | 307.6 | 83.9 | Smoke: 81 input / 57 output |
| Before Oct 1 | GPT-OSS-120B, older llama.cpp; retired | 131,072 | 5.6 | 6.8 | Smoke: 81 input / 32 output |
| Oct 5 | Qwen27B INT4/group128 MTP, SGLang 0.5.21 | 32,768 | — | 81.0 / 52.8 | SSE code/prose, 192 output |
| Oct 1 | Qwen27B INT4/group128 MTP, vLLM 0.30.0 | 32,768 | — | 73.6 / 56.4 | SSE code/prose, 192 output |

Native long probes: Strata Q2 **126,462 input / 49 output**, PP **2,415.5**;
Strata Q3 **126,462 / 31**, PP **2,375.0**; llama Qwen Q4 **60,042 / 14**,
PP **687.9**. SGLang used **32,055 input**, TTFT **60.95 s**; vLLM used
**32,042 input**, total request **70.47 s**. These short retrieval answers are
not sustained full-window decode. Source: original saved benchmark summary
`dsh/research/saved-benchmarks-2026-10-05.json`; published historical values also
appear in the [public README][PUB]. Earlier retired Q5/Bonsai profiles are not
given invented measurements; the retained summary excluded them.

### October 5: HyperQwen comparison

Qwen27B AWQ, HyperQwen `10bb48841806` on isolated vLLM 0.30.0, INT4 KV,
three warm timed runs, 256 output, temperature 0.6/top-p 0.95/seed 42,
thinking off. Baseline was directly retested. No isolated PP saved.

| Profile | Context | Code / prose decode t/s | Code / prose TTFT ms |
|---|---:|---:|---:|
| Baseline vLLM MTP3 | 32,768 | 86.1 / 53.6 | 70 / 67 |
| HyperQwen MTP3 | 65,536 | 108.3 / 66.8 | 94 / 91 |
| HyperQwen DFlash2, 7 draft tokens | 65,536 | 170.1 / 67.3 | 66 / 99 |

DFlash2 at **59,244 input / 256 output**: **159.01 s TTFT**, **19.2 decode t/s**,
zero prefix hits. These results predate later INT8-MLP and 1 GiB KV changes.
Sources: [published historical benchmark tables][PUB] and archived
`BENCHMARKS-HYPERQWEN.md`.

### October 7: context and Strata placement tuning

Three warm 256-token short runs per task; SGLang/vLLM greedy SSE medians.

| Profile | Before → after context | Before code / prose t/s | After code / prose t/s | Actual retrieval input after update / TTFT |
|---|---|---:|---:|---|
| SGLang 0.5.21 MTP | 32,768 → 40,960 | 84.18 / 51.94 | 83.56 / 51.59 | 39,484 / 78.79 s |
| vLLM 0.30.0 MTP3 | 32,768 → 49,152 | 86.09 / 54.98 | 86.04 / 58.01 | 47,666 / 120.28 s |

At 30,049 input, selected SGLang/vLLM code decode medians were **33.11 / 36.99**;
first-request TTFT **55.20 / 63.54 s**. Repeats could reuse prefixes.

Strata Q3 changed from 0.1.39/128K/40:8 layers to **0.1.40.3/256K/32:16**,
trimmed stage weights, MTP4, INT8 KV and 8,192-token prefill chunks. Its same-batch
previous/selected code medians were **48.6 → 68.8**, prose **50.1 → 64.6**.
At **14,195 input**, native PP **1,529.3 → 1,538.5**; 1,024-token long-code
decode **56.4 → 71.9**. Three short runs/task, greedy, up to 512 output.
Fuller retrieval used **257,850 input / 22 output**, PP **2,266.2**; not sustained
256K decode. This is the strongest saved NVIDIA Strata capacity test.
Sources: dated context/Strata October 7 reports; [preserved Strata comparison][NVA]
and [published historical results][PUB].

### October 14–15: development update and prefix/MLP tuning

| Engine update | Context retained | What was newly measured |
|---|---:|---|
| llama.cpp v0.5.0 → `a0e6dc7384ed` CUDA | Per-model budgets above | Functional validation, no new throughput |
| Strata 0.1.40.3 → 0.1.44.1 / `296b59d2f73c` CUDA | 262,144 | Functional validation, no new throughput |
| SGLang 0.5.21 → `0.5.22.dev20261015+ga12814c158` | 40,960 | Cache capacity/tools/retrieval; no new throughput |
| vLLM 0.30.0 → `0.32.0rc1.dev182+g429a3da66` CUDA | 49,152 | Cache capacity/tools/retrieval; no new throughput |
| HyperQwen → `95ee3b64b0df` on vLLM 0.31.0 | 65,536 | Switching/retrieval/tools; Oct 15 TTFT tests below |

HyperQwen DFlash2 INT8-MLP versus W4A16 with explicit dense prefix retention:
fresh **5,237 input** mean TTFT **8.04 → 5.93 s**, immediate repeat
**3.02 → 2.51 s**; **21,077 input** with no cached prefix **39.40 → 30.81 s**.
These are TTFT tests with 128 output, not PP/decode rates. Selected policy later
kept boundary-only retention; the dense-retention trial is not its exact default.
Source: October 14 upgrade and October 15 optimization reports, preserved in the
[NVIDIA build snapshot][NVB] and [published historical result tables][PUB].

## Update history: AMD migration, 32 GB RAM

### October 16: single RX 7900 XTX (historical)

RTX 4070 was present but unused in these selected tests. These are **historical
single-card measurements**, not permission to run current profiles on one card.

| Model / engine | Context | Prefill t/s | Decode t/s | Method |
|---|---:|---:|---:|---|
| Qwen27B Q4 MTP3, llama.cpp Vulkan `f12aaa3` | 65,536 | 802–804 | 82.4–82.5 | Two 3,424-input / 256-output inventory trials |
| Muse Glimmer, same Vulkan | 32,768 | 786–790 | 44.0 | Two 2,878-input / 256-output trials |
| Qwen35B-A3B MXFP4 MTP3, same Vulkan | 32,768 | 1,888–1,891 | 163.3–163.6 | Two 3,424-input / 256-output trials |
| Empero35B-A3B IQ4 MTP3, same Vulkan | 32,768 | 1,837–1,840 | 203.3–203.6 | Same inventory method |
| Nemotron Bolt IQ2, same Vulkan | 65,536 | 804–807 | 75.2–75.4 | Two 3,428-input / 256-output trials |
| Qwen27B GPTQ MTP3, vLLM ROCm dev190 | 65,536 | — | 29.68–34.68 | Two 3,424-input / 256-output trials; CPU compilation in background |
| Qwen27B GPTQ DFlash2, SGLang `f84475c` | 16,384 | — | Code 147.9 / prose 45.9 | Two 512-output samples/task, standard verifier |
| Qwen27B GPTQ MTP2, SGLang `f84475c`, early corrected verifier | 16,384 | — | Code 62.22 / prose 46.39 | Two 512-output samples/task |
| Qwen27B GPTQ MTP2 BF16, later SGLang context tuning | 40,960 | — | Code 61.93 / prose 42.78 | Two 512-output samples/task |

Near-window inputs: llama Qwen **59,984**, Muse **32,245**, Qwen MoE and Empero
**32,242** each; Bolt **59,990** at native PP **855.0**. SGLang MTP40K
retrieved **38,410 input** in **51.94 s total**. vLLM retrieved **59,995 input**
in **529.54 s total**. None establishes sustained full-window decode.

The preceding `a0e6dc7384ed` Vulkan build also tested now-retired GPT-OSS-20B:
32K, native PP **2,299.3–2,726.1**, decode **158.2–158.3** at 2,749 input;
Nemotron Lightning: 32K, PP **2,297.5–2,308.4**, decode **158.4–159.7** at
3,428 input, no MTP, two 256-output trials each. These are different models from
current Bolt Q4. GPT-OSS-120B was excluded from that GPU-resident test.

Sources: original October 16 GPU-resident, llama migration and Bolt reports;
[published AMD tables][PUB], [speculative comparison][S16] and
[SGLang context comparison][SC16]. SGLang FP8/32K was tested but not selected:
DFlash code/prose **111.34/46.90**, MTP **50.20/40.79**. More allocation did
not establish faster performance; both retain their measured candidate status.

### October 16: second RX 7900 XTX, older motherboard

Previous topology: CPU PCIe4 x16 plus chipset x4. Both cards, 32 GB RAM,
llama `f12aaa3`, SGLang `f84475c`, vLLM dev190. **One short guide smoke each**,
256-token cap, reasoning counted; no new PP. These are not comparable to the
later thinking-off code/prose medians.

| Model / engine | Context | Decode t/s |
|---|---:|---:|
| Qwen27B Q4 MTP3, llama Vulkan | 65,536 | 56.27 |
| Muse Glimmer, llama Vulkan | 32,768 | 34.89 |
| Qwen35B-A3B MXFP4 MTP3, llama Vulkan | 32,768 | 101.11 |
| Empero35B-A3B IQ4 MTP3, llama Vulkan | 32,768 | 111.16 |
| Nemotron Bolt IQ2, llama Vulkan | 65,536 | 47.82 |
| Qwen27B GPTQ DFlash2, SGLang TP2 | 16,384 | 77.70 |
| Qwen27B GPTQ MTP3, vLLM TP2 | 65,536 | 53.67 |

SGLang MTP was blocked on this topology, so has no usable benchmark here. Muse's
timed guide used its cap in reasoning; separate correctness checks passed.
Source: [dual-AMD migration][D16].

### October 17: Z690 x8/x8, SGLang context/cache and verifier updates

The motherboard changed to CPU-connected x8/x8; RAM remained 32 GB. Direct
ROCm peer access remained unavailable. First restored SGLang MTP2 sample:
**40,960 context, 75.82 decode t/s**, one guide smoke, no new PP. Source: [Z690][Z17].

Subsequent tests on that board:

| Update / SGLang profile | Context | Code / prose decode t/s | Actual retrieval input | Method / source |
|---|---:|---:|---:|---|
| DFlash2 control, no prefix cache | 16,384 | 200.65 / 61.83 | Within 16K | Two 256-output samples/task [SC17] |
| DFlash2, prefix cache + chunk2048 | 65,536 | 200.57 / 60.12 | 64,033; TTFT 66.551 s | Same prompts and two-sample method [SC17] |
| MTP2, prefix cache restored | 40,960 | 89.32 / 66.18 | 39,440; TTFT 36.983 s | Two 256-output samples/task [SC17] |
| DFlash2, repaired unified verifier selected | 65,536 | 205.59 / 71.84 | 64,033 | Three warm 256-output medians/task [C17] |
| MTP3, repaired unified verifier selected | 40,960 | 114.57 / 66.05 | 39,440 | Same three-run method [C17] |

Context tuning's code prompt differs from the later clean-retry code prompt;
do not interpret 200.57 versus 205.59 as an isolated verifier improvement.
Same-batch standard-verifier controls in the clean retry were DFlash2
**179.23/62.02** and MTP3 **104.80/66.05**; a later standard DFlash repeat
was **165.63/57.10**, demonstrating variation. Unmodified optimized verification
failed ordering and is excluded from usable results.

Repaired Book PP/decode estimates: DFlash2 depth0 **1,575.97/79.61**, depth16K
**1,310.23/93.67**; MTP3 depth0 **1,488.15/80.86**, depth16K
**1,281.71/78.73**. The much higher code rates do not describe these book tasks.

### October 17: vLLM cache/compiler/prefill update

Same dev190 source, Qwen27B GPTQ target, TP2, **65,536 context throughout**.
Three warm short-task medians per profile. Source: [vLLM tuning][V17].

| Update | Code / prose decode t/s | Book depth0 PP / decode t/s |
|---|---:|---:|
| Original INT4 KV, no compile, chunk512 | 79.06 / 42.27 | 1,114.44 / 38.97 |
| INT8 KV, no compile | 107.59 / 54.88 | — |
| INT8 KV + compilation, chunk512 | 130.98 / 71.33 | — |
| Selected BF16 KV + compile + tuned prefill, chunk2048 | 131.34 / 77.46 | 1,585.23 / 88.93 |

Selected depth16K Book PP/decode: **1,431.67/65.13**. Fresh **64,033 input**
retrieval TTFT **53.73 s**, versus **130.38 s** for tuned INT8 KV. These
22-token retrieval answers are not sustained decode. MTP4 was slower in these
short tests (**124.13/57.81**) and was not selected.

### October 17–18: HIP/rocWMMA/Radiance/queue candidates

All Qwen27B on both AMD cards, **65,536 context**, same three-run code/prose
method. Book PP/decode below is depth0; depth16K results remain in the report.
These are candidates/control repetitions, not additional active model options.
Source: [Level1Techs candidate tests][L1], including its primary/forum citations.

| Profile | Code / prose decode t/s | Book depth0 PP / decode t/s | Decision |
|---|---:|---:|---|
| vLLM dev190 selected-profile control | 133.06 / 78.50 | 1,556.04 / 92.62 | Retained |
| llama Vulkan Q8 KV/MTP3 control | 79.38 / 45.53 | 1,171.05 / 50.38 | Retained |
| llama HIP native FP16 KV/MTP3 | 67.04 / 40.85 | 1,150.06 / 38.80 | Not selected |
| llama HIP restored rocWMMA | 65.81 / 35.31 | 979.69 / 44.38 | Not selected |
| Radiance ROCM_ATTN+AITER/native MTP3 full | 95.27 / 60.35 | 1,606.63 / 59.96 | Not selected |
| vLLM queue cap1 | 124.65 / 73.57 | 1,577.41 / 88.86 | Not selected |

### October 18: MoE expert offload and Q4 replacement

llama HIP `f12aaa3`, both GPUs, Q8 KV, CPU expert backing plus actual GPU
hot-expert caching. Each **allocated 262,144** and retrieved **63,911 input**.
Single native code probes with different output lengths; no matched ranking.

| Model / update | Code decode t/s (output tokens) | Native PP at 63,911 input | Source |
|---|---:|---:|---|
| Qwen35B-A3B MXFP4, MTP3 | 96.7 (48) | 417.9 | [MoE offload][MOE] |
| Empero35B-A3B IQ4, MTP3 | 104.9 (128) | 457.8 | [MoE offload][MOE] |
| Bolt IQ2, no MTP; later retired | 40.7 (87) | 526.4 | [MoE offload][MOE] |
| Bolt Q4_K_M, no MTP, 12 CPU layers/7 GiB cache | 35.7 (101) | 424.0 | [Q4 replacement][Q4] |

Qwen/Empero increased allocation from 32K to 256K, Bolt from 64K to 256K;
these changes added CPU expert backing/cache and changed engine/placement.
They did not establish speed at a filled 256K window. Full 256K remains untested.

### October 18: Strata AMD activation and latest runtime update

Strata IQ3_XXS uses both GPUs, **32,768 context**, INT8 KV, MTP3, 512-token
prefill, bounded 8 GiB CPU expert budget. One native timing sample/task.

| Build | Code / prose decode t/s | Code / prose native PP t/s | Native PP at 30,070 input | Retrieval output tokens |
|---|---:|---:|---:|---:|
| HIP 0.1.44.1 / `296b59d2f73c` | 59.8 / 47.8 | 85.5 / 80.1 | 763.1 | 19 |
| HIP 0.1.45 / `477ac13cbe8e` | 66.7 / 48.5 | 87.7 / 82.1 | 801.4 | 19 |

The newer samples had background compilation and different available cache
headroom; this is **not a controlled version comparison**. Sources:
[AMD activation][ST18] and [runtime upgrade][U18].

| Latest runtime update | Context retained | Fresh evidence after update |
|---|---|---|
| llama `f12aaa3` → `31288c9c66e5`, HIP/Vulkan | Qwen64K; Muse32K; three MoEs256K | All five allocated context, math/tools/SSE passed, worker-only no-swap scope; **no fresh throughput** |
| SGLang `f84475ccf593` + retained repairs | MTP40K / DFlash64K | Both cache capacities, math/tools passed; **no fresh throughput** |
| vLLM ROCm dev190 → dev329 | 64K | Code/prose **130.61/72.69**, three warm 256-output medians/task; **64,033 input**, TTFT **54.56 s**; no fresh Book PP |
| Strata HIP 0.1.44.1 → 0.1.45 | 32K | Native timing table above; **30,070 input**, PP **801.4**, tools/SSE passed |

No speed numbers were inferred for a build or context that was only validated.
FreeToken is retired and outside the active nine-profile catalog; its distinct
test results/limitations remain in the [retirement record][FT], not mixed into
these dual-GPU production comparisons. Image/video generation has step/time
metrics rather than LLM context/decode; see [graphics validation](../graphics/VALIDATION-2026-10-18.md).

## October 19: Strata protected overlap and prefill tuning

Both RX7900XTX cards, 32 GB RAM, HIP0.1.45 at unchanged source `477ac13cbe8e`.
Retained **32,768 context**; explicit split26/stage trimming and continuous
desktop protection. Controls reserve 6 GiB/card; the selected profile reserves 7 GiB/card. A matched serial/overlap/serial sequence used 512 prefill, 10 GiB expert
budget, three timed greedy code/prose samples per arm plus warm-up. Subsequent
prefill candidates are complete-profile comparisons, not isolated overlap gains.

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

## Recording future updates

After a runtime, hardware, quantization, context or placement change, append a
dated row with exact source/version, GPU/RAM configuration, allocated context,
actual input/output lengths, sampling/cache state, measured PP/decode or TTFT,
method and evidence link. If no benchmark was run, write **validation only**;
keep the previous speed's original date/build. Do not rerun benchmarks merely
to fill gaps without a request. Refresh the current table, both repository
READMEs and the consolidated Shared handoff when relevant.

[U18]: RUNTIME-UPGRADE-2026-10-18.md
[L1]: LEVEL1-TESTS-2026-10-17.md
[D16]: UPGRADE-DUAL-7900XTX.md
[MOE]: MOE-OFFLOAD-2026-10-18.md
[Q4]: NEMOTRON-Q4-2026-10-18.md
[C17]: CLEAN-TUNING-2026-10-17.md
[SC17]: SGLANG-DUAL-CONTEXT-2026-10-17.md
[V17]: VLLM-TUNING-2026-10-17.md
[S16]: SPECULATIVE-2026-10-16.md
[SC16]: SGLANG-CONTEXT-2026-10-16.md
[Z17]: Z690-2026-10-17.md
[NVA]: NVIDIA-COMPARISON-RUNTIME-AUDIT-2026-10-18.md
[ST18]: STRATA-DUAL-AMD-2026-10-18.md
[FT]: FREETOKEN-RETIRED-2026-10-18.md
[PUB]: https://github.com/Biegle-W/local-llm-public#saved-benchmark-results
[NVB]: https://github.com/Biegle-W/local-llm-public/blob/main/linux-nvidia/BUILD.md

[OPT19]: STRATA-OPTIMIZATION-2026-10-19.md


## October 19: native 256K Strata on 32 GB RAM

The context sweep passed 64K,128K and 256K with 32K resident INT8 KV, RAM backing,
both GPUs and unchanged HIP 0.1.45 source. Actual near-limit input/output:
**258,044/256**, native PP **775.1**, native decode **39.9 t/s**.
Short code/prose medians: **72.2/48.0**, three warm 512-token-cap samples/task.
Expert budget 13.5 GiB, reserve7/8 GiB, split 26/trim/overlap. No worker swap/spill
was sampled; tools and SSE passed. No model/runtime update or RoPE extension.
These are complete-profile comparisons, not a context-only speedup claim.
[CTX19]: STRATA-CONTEXT-2026-10-19.md

[Report and all samples][CTX19]. Earlier 32K/64 GB candidate references in the
dated history describe that earlier state; the current table is authoritative.
