# Strata Qwen hipBLASLt selection and bounded prefill — October24,2026

**Selected: matching gfx1100/hipBLASLt100202 table, prefill2048 unchanged.**
Pooled repeated-control comparison: fresh~8K native prefill 916.1→1208.85t/s
(+32.0%); external fresh TTFT 8.973→6.807s
(−24.1%). Code/prose remained within the fixed5% regression limits.
An independent confirmation and normal-production run passed before selection. The final corrected-route integration proof reuses the exact
completed normal-production timings; it is not another timing sample.
No claim that every decode task speeds up, or that model answers are bit-identical.

## Exact configuration

i9-13900KS/64GB (61.51GiB visible),2×RX7900XTX24GB, CPU PCIe4x8/x8, Intel desktop,
HIP7.2.3. Source `8183c6b67162340c09b67360860177c577a65f2e`, same tested production binary SHA256
`3e214bbf98e416164a7a97e41a5657dbb2bd6561d5e57ea4fa5d30cad0b82871` for every arm. Loaded libraries report
libamdhip64.so.7.2.70203/libhipblaslt.so.1.2.70203/librocblas.so.5.2.70203;
the native hipBLASLt query confirms100202 and26 accepted rows on both cards.
The existing upstream `tools/hip/gfx1100-hipblaslt-100202.txt` is selected explicitly
using `STRATA_HIPBLASLT_TUNING`; table SHA256 `a594869223200c62019d3c997345e89664d5126fcbd089a44f4f95a267ad2ff3`.
No table, engine, kernel or numerical tolerance was rewritten.

Only Qwen Flash-Next GSQ-RCO IQ3_XXS is affected. Both GPUs/split26 and overlap,
13.5GiB bounded CPU expert pool/GPU hot cache, six workers, MTP3/min-p0.7,
native262144 context/INT8 KV/32768 GPU residency, native7/8GiB reserves,
actual5GiB/card startup, continuous3GiB floor/hard1.5GiB, latched protection and
52G/MemorySwapMax0 worker scope remain. DeepSeek, Maya, other backends, DSH
default, frontend policy, assets, ports and network settings are unchanged.

## Measurements and fixed gates

Normal launch-backend/managed router for each arm; candidates use the existing
STRATA_PROFILE_CONFIG override rather than editing production during timing.
A0→B0→B1→A1, followed by the guarded4096 arm and independent confirmation.
Three timed code/prose trials per start,256-output cap, excluded task warmup,
temperature0.6/top_p0.95/seed42/thinking off. Three fresh salted~8K marker probes
per start,64-output cap, zero prefix reuse; actual counts/output lengths and
native timing fields are in [the numeric record](results/strata-tuning-2026-10-24.json).
Native PP and external SSE TTFT/decode are separate; load time is excluded.

| Arm | Trials per workload | Code / prose t/s | Native PP t/s | Fresh TTFT s |
|---|---:|---:|---:|---:|
| A0 no table | 3 | 77.78 / 50.60 | 916.9 | 8.966 |
| B0 matching table | 3 | 77.13 / 50.56 | 1208.8 | 6.810 |
| B1 matching table | 3 | 77.02 / 51.32 | 1208.9 | 6.803 |
| A1 no table | 3 | 71.44 / 47.36 | 915.3 | 8.980 |
| A pooled control | 6 | 75.48 / 48.83 | 916.1 | 8.973 |
| B pooled candidate | 6 | 77.07 / 50.69 | 1208.8 | 6.807 |
| Independent confirmation | 3 | 78.16 / 50.12 | 1213.0 | 6.787 |
| Normal production timing (r2) | 3 | 77.38 / 50.61 | 1208.2 | 6.810 |

Selection required PP≥105% of pooled controls, EACH code/prose median≥95%,
each short/fresh TTFT≤max(1.25×control,control+0.05s), all markers, strict zero
owned swap/spill, sampled≥3GiB/card and actual≥5GiB/card startup. The candidate
also had to repeat independently and pass normal integration at the same settings.
Repeated controls differ, especially decode; retain their separate rows and output
hashes. Small sequential samples, changing thermals and generated text do not
establish a universal or thermally isolated speedup. This is a settings comparison
on one exact build, not attribution to a newer engine or SDK.

## Rejected larger prefill

Prefill4096 started the native engine but the NORMAL router rejected admission:
**4.655/5.510GiB free**, below the existing5GiB/card minimum. No timing is
published for it. No guard/cache cap/context/reserve was relaxed.8192 was
deliberately **not attempted** after that failure, not claimed tested or failed.

## Table coverage and historical evidence

The matching table was absent from the retained profile environment and adjacent
binary directory, and controls log no table activation. Table runs confirm actual
100202 selection on both GPUs, not just the presence of a header/file. B0's final
two active GEMM summaries recorded5076 tuned launches/12 fallbacks and4296/0.
The missing real shape is BF16 N10240/K2560/ldy10240 at the actual chunk/tail
lengths. Tiny64×64 warmup misses are separate. Coverage counts do not weight cost;
the selected table is useful but not exhaustive. Further calibration is unmeasured.

This is **not the first local table test**: the [October20 SDK/table experiment](ROCM10-OTHER-ENGINES-2026-10-20.md)
on source9ae93f7b found+31.1% PP but−9.1% prose decode and did not activate the table.
Those original samples/rejection remain. The present source8183c6b6 repeat and
normal/context gates provide a separate selection basis.

Initial B0/B1 inference/timing/markers passed, but the verification helper read the
router log rather than native `cfg.log` and falsely reported no table. The initial
failure and interrupted untimed next-arm start are preserved privately. Corrected
verification used already-captured native monitor logs, worker environment and
both-card allocation proof; no timed requests were overwritten. Larger-chunk,
confirmation and production runs use the corrected native-log selection.
The first near-window helper then called retired `/api/tokens` and received404
before long input; the job automatically restored the original profile. Its fresh
arithmetic smoke passed. The final helper uses source-confirmed
`/v1/messages/count_tokens`; it repeats functional/context verification only and
reuses the earlier identical normal-production benchmark. Both failed helper
records remain separate from native results. No
engine/tolerance change or relaxed gate repaired the harness mistake.

## Normal integration and memory

Fresh near-window **257990 input/22 output**,
all three distributed markers passed; full-history follow-up
**258037 input/22 output**, reported cached
**258011** tokens, passed. These short retrieval outputs do not
establish broad full-window generation quality. Arithmetic/JSON/synthetic
tool-call roundtrip/SSE, original native assets and blocked runtime mutations,
authenticated loopback/LAN/Tailscale host self-access passed. No remote peer was
tested. Both GPU allocations, exact arguments/libraries and worker scope were
checked. All completed selected/control arms had zero observed owned swap/spill.
Initial host was idle; finite workers are stopped after validation, with no idle
unloading policy or unrelated-service shutdown added.

## Thermals

Read-only 1s collectors cover each arm's load, warmups, timing and shutdown.
The r2-production arm includes timing/short checks; r3-production separately covers
corrected-route functional/near-window checks without another timing run. Full summaries retain
sensor coverage, fans, power, clocks and available raw SMU flags; raw logs remain
private. Sampled peaks are not guaranteed transient maxima, and flags do not
measure speed loss. No clock/voltage/fan changes were made for this test.

| Arm | Lifecycle samples | GPU0 / GPU1 hotspot°C | CPU package peak°C |
|---|---:|---:|---:|
| a0 | 106 | 72.0 / 72.0 | 97.0 |
| b0 | 101 | 71.0 / 65.0 | 100.0 |
| b1 | 99 | 73.0 / 66.0 | 98.0 |
| a1 | 108 | 78.0 / 74.0 | 100.0 |
| r2-table-4096 | 40 | 52.0 / 46.0 | 74.0 |
| r2-confirm | 99 | 75.0 / 64.0 | 100.0 |
| r2-production | 103 | 73.0 / 66.0 | 100.0 |
| r3-production | 262 | 85.0 / 70.0 | 94.0 |

## Sources and reproducibility

[LCZ2032](https://lcz.me/topic/2032), naniandemeng/singleXTX/X99/64GBDDR3/Strata0.1.27/ROCm10,
and [LCZ2027](https://lcz.me/topic/2027), BenLee/gfx1100/ROCm7.2.3, motivate the
table-selection/shape audit; their speeds are not imported. AccessedOctober24,
post dates absent from fetched view. [Level1Techs XTX notes](https://forum.level1techs.com/t/7900xtx-llm-inference-notes/250869),
ivgranite/May31/9600X/96GB/32K, support checking completed-answer wall time and
workload differences, not this table's numerical gain. [Source ledger](FORUM-OPTIMIZATION-SOURCES.md).
Primary [pinned AMD guide](https://github.com/Niko1221/Strata/blob/8183c6b67162340c09b67360860177c577a65f2e/docs/AMD_HIP.md),
[GEMM implementation](https://github.com/Niko1221/Strata/blob/8183c6b67162340c09b67360860177c577a65f2e/src/prefill/gemm.cu)
and [matching table](https://github.com/Niko1221/Strata/blob/8183c6b67162340c09b67360860177c577a65f2e/tools/hip/gfx1100-hipblaslt-100202.txt).
Use the maintained benchmark-current-amd.py/normal launcher and fixed profile
gates with GPU-LOCK and complete telemetry. Numeric evidence includes all trials,
actual counts, accepted/rejected arms and validation limits; no weights or private
logs are published. Public profiles require local validation against the installed SDK.
