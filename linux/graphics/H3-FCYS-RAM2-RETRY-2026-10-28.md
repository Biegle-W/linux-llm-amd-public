# Actual fcys TP2 retry with a 2 GiB host-RAM floor — October 28, 2026

**Later AMD encoder-format comparison:** [W4A8 default/native HIP INT8 versus corrected NVFP4](H3-AMD-ENCODER-FORMATS-2026-10-28.md) records three fresh timed trials per path and nine paired TP2 quality clips. Encoder-stage speed, loading variance, memory and quality limits are separated. Production remains unchanged; earlier results below stay historical.

**Later conditioning repair:** [the corrected actual TP2 and one-card 39-frame controls](H3-FCYS-QUALITY-FIX-2026-10-28.md) identify all-NaN conditioning from the opt-in Triton NVFP4 path. Encoder-only Triton disablement restores finite conditioning and sampled red-teapot output; corrected preprocessing/TP2 retain at least 11.286 GiB host RAM available. Earlier failures and measurements below remain historical. No production promotion or new speedup.

**Later low-RAM result:** [the user-authorized 1 GiB retry and staged design](H3-FCYS-LOWRAM-2026-10-28.md) completed the actual TP2 five-frame canary after removing duplicate encoder/decoder residency. Minimum available RAM was 10.829 GiB across the successful stages; prompt compliance still failed. Earlier settings/results below remain historical.

The user-authorized rerun lowered the isolated test's immediate host-available RAM floor from **3 GiB to 2 GiB**, after the user freed more RAM. It still stopped during concurrent text-encoder loading: available RAM reached **1.848 GiB**. Neither rank reached DiT denoising, and no video/audio or speed comparison was produced.

This was a safety-reserve stop. No allocator OOM or cgroup OOM event was observed. Free GPU VRAM remained at least 11.314 GiB per card. The result does not establish a P2P or RCCL communication failure; the earlier bounded no-P2P shared-memory SUM/MAX tests passed.

## Same workload, explicitly changed host floor

The two ranks used the same unmodified fcys source, frozen ComfyUI 0.42.0, pinned INT8 plugin, CK attention, checkpoint files/storage, CPU noise seed 42, fixed teapot prompt, 608×352×5 frames at 24 fps and 20 res_multistep/simple steps as the earlier canary. Submitted graphs match after normalizing only output prefixes. The no-P2P transport remains one channel with 1 MiB buffers and Simple protocol.

The lowered 2 GiB floor applies only to this isolated retry harness. The original 3 GiB harness and measurements remain intact. Other protections remain: 2 GiB free-VRAM soft floor for four samples, 1.5 GiB hard floor, zero dedicated spill, physical-RAM scope cap, GPU/server ownership locks and complete-lifecycle thermals. Loading-swap-v3 still allows loading/parked swap and reads; swap rate and PSI are advisory, with no new write budget. Production launchers, pins, guards and paused schedules were not changed.

| Observation | Earlier 3 GiB canary | This 2 GiB retry |
|---|---:|---:|
| Host available before launch, GiB | 23.404 | 24.911 |
| Minimum host available, GiB | 2.417 | 1.848 |
| Minimum free VRAM, card 0 / card 1, GiB | 12.895 / 13.008 | 11.314 / 11.344 |
| Maximum owned swap, GiB | 11.387 | 13.605 |
| Dedicated spill, bytes | 0 | 0 |
| Denoising / media completed | No | No |

The retry's latched fault was `host_available_below_2GiB`. Swap was permitted and did not trigger the stop. Both extra available RAM and the threshold changed, so this is not a controlled estimate of the threshold's isolated effect. The 86.459 s lifecycle includes startup, loading and shutdown; it is not generation latency.

## Coverage and disposition

There were 86 memory samples with 0 sampling errors. Lifecycle thermal coverage has 88 samples and 0 sampler errors; GPU junction peaks were 40.0 / 38.0°C and CPU package peak was 78.0°C. Full per-sensor coverage and available SMU flags are retained in the [numeric record](../hardware/results/h3-fcys-ram2-retry-2026-10-28.json); flags are observations, not proof of measured throttling or slowdown.

Owned workers exited, KFD clients cleared and GPU/server locks released. The actual TP2 full workflow remains unqualified at this tested loading blocker. The prior one-card five-frame media's prompt-compliance failure also remains unresolved; no one-card rerun was needed to repeat that existing result.

A useful next implementation is bounded common preprocessing/conditioning, avoiding simultaneous duplicate text-encoder loading while passing identical saved conditioning to both ranks and a matched one-card arm. DiT/AV admission and prompt compliance must precede timed comparisons. See the [earlier operator, precision and quality qualification](H3-FCYS-QUALIFICATION-2026-10-28.md). No production promotion or native Radiance qualification follows from this retry.
