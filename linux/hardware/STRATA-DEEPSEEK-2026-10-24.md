# Strata DeepSeek reusing Maya weights — October 24, 2026

Both retained DeepSeek quants are selectable on Strata, alongside all existing Maya and Qwen profiles. **13 total profiles; DSH default remains Strata Q3.** No model weights were downloaded, copied, moved or requantized. Only separate Strata metadata/tokenizer copies and independent routing seeds were created.

## Installed component and access

The [official 0.2.4 release](https://github.com/Niko1221/Strata/releases/tag/v0.2.4) adds DeepSeek in Terminal/engine, not a new desktop app. Terminal 0.2.4.1 / release DeepSeek package 0.1.49; locally compiled engine reports **0.1.49.1 build 8183c6b67**; pinned source **8183c6b67162340c09b67360860177c577a65f2e**, source-built for **gfx1100/HIP 7.2.3** because the official AMD artifact targets gfx1200/1201. The exact tested binary SHA256 is `52215c1c90e51522c0cebcd5a12137114551b372df0b5158717de5b438e7fc59`. The GNU14.4/sysroot build uses the declared ggml archive revision recorded in the numeric artifact. Existing Strata Qwen 7ddc17a3 and Maya f26d8ba / 1.1.26 are independent and unchanged.

Use DSH/network model selection, or `llm-strata --model deepseek-v4.1-flash-1017-strata-s` / `--model deepseek-v4.1-flash-1017-strata-xs`. Managed router/native UI remain loopback 30020/30021; hub 30100 and authenticated gateway 10000 remain unchanged. Actual Ptyxis launch, original native UI/assets, blocked runtime edits, JSON, synthetic tool roundtrip and SSE passed for both. S→XS→Qwen Q3→XS passed with exactly one native worker. Authenticated loopback/LAN/Tailscale host self-access passed; no remote peer was tested. After the finite proof manager closed its test terminal, XS was relaunched in a persistent normal Ptyxis terminal and passed a final arithmetic smoke check; no timing was rerun.

## Shared storage and safety

Engine: `strata-dsv41/upstream` on Linux ext4. Existing weights: shared-NVMe `LLM-Models/Maya/DeepSeek-V4.1-Flash-1017-GGUF`. Independent metadata: `LLM-Models/Strata/DeepSeek-V4.1-Flash-1017/{Maya-S,Maya-XS}/pack`. Strata's [pinned packer](https://github.com/Niko1221/Strata/blob/8183c6b67162340c09b67360860177c577a65f2e/tools/dsv41/pack_gguf.py) and [DeepSeek documentation](https://github.com/Niko1221/Strata/blob/8183c6b67162340c09b67360860177c577a65f2e/docs/DEEPSEEK41.md) support Maya IQ weights. External shared Engram references need relative-path correction only; tensor offsets/shapes/types are unchanged. Every referenced bound was checked and generated Engram metadata matches Maya. Original Maya metadata hashes are unchanged. Existing published full-file verification is retained; this task did not claim a new 339 GB full-hash run. **Both active quants depend on S Engram shards 5/6; never delete them.** The existing vision asset and native default tower loading are retained to match the measured configuration; **image inference has not been tested**, and DSH advertises text only.

Both RX 7900 XTX cards, 32,768 total context and 24 CPU threads; S uses no drafter, XS matching xs2. CPU expert access plus GPU hot caching remains enabled. `--tp 2` falls back to layer groups for 2304/256 expert dimensions; this is **not true tensor parallelism**. Native 8192 MiB/card reserve and actual≥6GiB/card at readiness, 52G scope/MemorySwapMax0, strict zero owned swap/spill and continuous latched 3 GiB floor / hard 1.5 GiB protection remain. Required preload RAM: 60 GiB physical / 52 GiB available. Prompt skip/YOCO, routed expert omission and experimental persistent slots are disabled. No unrelated GPU applications are stopped.

## Measured settings

| Model ID | RAM-store GB | Code / prose t/s | Native PP t/s | TTFT s |
|---|---:|---:|---:|---:|
| `deepseek-v4.1-flash-1017-strata-s` | 0 | 7.00 / 7.16 | 168.0 | 37.491 |
| `deepseek-v4.1-flash-1017-strata-xs` | 0 | 18.25 / 12.77 | 183.7 | 34.289 |

All experimental timing arms:

| Arm /32K | Code t/s | Prose t/s | Native PP t/s | Fresh TTFT s |
|---|---:|---:|---:|---:|
| s-none | 7.000 | 7.162 | 168.000 | 37.491 |
| s-store24 | 6.885 | 6.579 | 152.900 | 41.205 |
| xs-draft | 18.246 | 12.769 | 183.700 | 34.289 |
| xs-store24 | 16.791 | 13.285 | 154.800 | 40.709 |

- S: select **s-none**. RAM-store ratios code/prose/PP 0.984/0.919/0.910; geometric mean 0.937; gate failed.
- XS: select **xs-draft**. RAM-store ratios code/prose/PP 0.920/1.040/0.843; geometric mean 0.931; gate failed.

RAM-store 24 is 24 GB decimal, bounded by the same 52G scope. Selection required ≥5% geometric-mean improvement in code/prose/nativePP, no metric>5% worse, fresh TTFT≤max(1.25×control, control+0.05s), and every functional/memory gate. Otherwise mmap0 is retained. Full selected-profile near 31.5K/history checks were repeated through normal workers.

Three timed code/prose trials with a 256-output cap after excluded task warmups, seed 42 / temperature 0.6 / top_p 0.95 / thinking off; three fresh marker probes using the shared Qwen-sized prompt generator, **actual DeepSeek input about 6.3K**, 64-output cap. All trial counts, native cache counters, SSE decode/TTFT and native prefill rates are saved. Cold load is separate. These sequential arms are not thermally equalized, a causal Maya A/B or an equal-quality S/XS comparison. Earlier Maya speeds retain their original build/method; Maya remains available.

## Correctness, failures and limits

Upstream CPU/API tests: 89 run, 1 skipped; managed guard/hub/ownership/rollback tests: 39 passed. Uniform selected IQ types 19/16/18/21/22 pass both cards with 60 cross-card buffers identical. Actual 5120/2304 shape tests cover the same five types. Selected-core dense/Engram/KV and all selected mixed IQ pairs pass both GPUs at unchanged tolerances; two selected mixed pairs also pass at actual shape. A broader GPU0 diagnostic found **Q2_K/Q3_K token/window bit-equality failures at 512/256 and 5120/2304**. Those expert types are absent from the selected packs and remain blocked; GPU1 was not run in that failed broad attempt. Previously excluded Q4_K/IQ4_XS mixed expert pairs remain unselected. Engine source and numerical tolerances were not changed. The maintained test builder restricts mixed-expert gates to the actually selected IQ pairs and retains original failure evidence.

The initial S functional helper called Maya's `/api/tokens` and got404 after successful timing/short functional tests. That harness failure is retained; the correct `/v1/messages/count_tokens` route completed S context checks without overwriting timings. The first build attempt requested an absent test target and stopped before compilation; corrected build succeeded. A first normal-proof attempt queried the restarted model hub before it bound its socket; a readiness wait fixed that harness race before inference began. The failed attempt is retained. Integration then exposed the older router discarding all profiles except its startup selection; it now retains all enabled validated profiles. Switching was revalidated, reusing the unchanged S native context proof. The initial rejected switch and all prior S checks are retained. No speed is inferred from these functional repairs.

Fresh near 31.5K marker retrieval and full-history follow-ups pass on each selected normal profile. Actual counts and cached-token counts are in the numeric record. These are narrow retrieval checks, not general model quality, full-window output or larger-context validation. No approximate prompt skipping or failed quant type is enabled.

Whole-lifecycle 1s telemetry covers loads, warmups, timing, functional checks and shutdown (production worker remains ready after the finite normal proof). Across recorded phases, sampled hotspot peaks were 91/79°C and CPU package 100°C. Coverage/sample counts, fans, power, clocks and available SMU flags are in the numeric record. Sampling cannot guarantee transient maxima; flags do not measure performance loss. No temperature history was backfilled.

## Updates and source trail

The existing 03:00 daily job now treats Strata Qwen and DeepSeek as independent components. It builds/checks/parity-tests each candidate, compares both DeepSeek profiles through normal launchers, and rolls back only its own component on failure. No new timer was created, and quants/contexts/guards stay fixed.

Both required forums were consulted. [lcz.me topic 2016, post 4](https://lcz.me/topic/2016/4), flyer666 (date absent in retrieved post), is a single RX 7900 XTX / Qwen IQ3_S report, not DeepSeek 0.2.4 evidence. [Level1Techs post15](https://forum.level1techs.com/t/llm-inference-workstation-4x-rtx6000-blackwell-pro-max-q-384gb-vram-threadripper-pro-7985wx-wrx90e-sage-se-512gb-ram-1700w/252181/15), ambientlight, September 18, 2026, describes four RTX 6000 Blackwell / Threadripper / 512 GB / SGLang DeepSeek traffic, not gfx1100/Strata. Neither supplies local speed measurements or settings adopted here. No matching gfx1100/DeepSeek 0.2.4 recipe was found in the reviewed searches. See [forum ledger](FORUM-OPTIMIZATION-SOURCES.md), [all numeric evidence](results/strata-deepseek-2026-10-24.json), and [component setup](../strata-dsv41/README.md).
