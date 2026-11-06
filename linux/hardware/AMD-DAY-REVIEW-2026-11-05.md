# November 5 GPU workload and crash review

**The day's logs support substantial successful use of the PCIe-switch setup. The latest crash followed a new Maya DeepSeek loading attempt, not the first use of the switch or custom kernel.** The initial GPU failure is recorded; its exact low-level trigger remains unresolved.

Scope: **00:00 through 20:34 EST on November 5**, including all four boots represented in that interval. Review covered 36,104 journal records and 92 saved supervised-stage records. Those stages include builds, downloads, audits and readiness-only runs:64 passed guard stages must not be described as 64 successful model qualifications. Raw journals and artifact-location records remain private; [curated evidence](results/AMD-DAY-REVIEW-2026-11-05.json) includes the stage inventory.

## What completed successfully

All times below are Toronto/EST. A short tool pass means the saved result and matching tool marker/IDs passed, with its owned cleanup verified; it is not sustained or full-context qualification.

| Time | Work completed | Result |
|---|---|---|
| 00:01–00:14 | Empero, Flint and Ornith on llama.cpp; Qwen27B, Bolt and Sage on vLLM; Qwen27B on SGLang | Seven short tool checks passed |
| 00:16–00:35 | Six normal Flux/Qwen/H3 graphics workflows; separate H3 TP2 case; three graphics copy-coverage cases | Saved workflow/media checks passed; H3 TP2 uses cached conditioning and is not an end-to-end dual-GPU speed claim |
| 00:39–00:42 | Strata DeepSeek Coder IQ2_XXS, normal admission | Short tool check passed |
| 03:01–03:21 | Maya Coder IQ2_XXS, Maya DeepSeek UD-IQ1_S, Maya GLM IQ2_XXS and Strata DeepSeek UD-IQ1_S | All four short tool checks passed; Maya Q1 specifically passed 03:05–03:08 |
| 03:37–03:42 | Isolated newer llama.cpp Flint and Ornith cases | Both passed; the separate Empero marker failure in this batch remains a failure |
| 04:12–04:24 | Maya c167004: Coder, DeepSeek UD-IQ1_S and GLM | All three passed; **DeepSeek UD-IQ1_S loaded and passed at 04:14–04:18**, load 51.964s |
| 04:34–04:39 | Llama9c9074: Ornith, Flint, then separate Empero check | Passed; selected source retained |
| 04:39–04:43; 05:17 onward | Bolt globaldev229 short check and separate matching near255K-context check | Both passed; long-input requests contained 255,473 and 255,658 prompt tokens |
| 04:43–04:53 | Six normal graphics workflows on ComfyUI0.44/fb2b26f | Passed; source selected |
| 11:48–11:51 | Strata0.2.11 with existing Unsloth V3.1 IQ3_XXS weights | Strict tools passed, 5/6 local fixtures; three short speed probes median 52.895 native tokens/s; selected GSQ route unchanged |
| 13:31–13:45 | Native timing checks for Qwen/vLLM, Qwen/SGLang, Sage/vLLM and Bolt/vLLM | Tool checks and three fixed128-token speed probes per route completed; SGLang's failed collector record and separate successful speed-only continuation are retained |
| 16:42–16:44 | New Strata Unsloth UD-IQ1_M route | Strict tools passed, 5/6 local fixtures; three short speed probes median 57.140 native tokens/s; route enabled |
| 18:22:31–18:22:44 | Fresh peer capability, local copy, integrity/IPC and RCCL checks after custom-kernel reboot | All four passed; scoped prerequisite evidence only |
| 18:27–18:42 | Actual restored GLM RAM24 case | Strict tools passed, 5/6 fixtures; three short speed probes median 1.995 native tokens/s; unselected because follow-up performance regressed; RAM8 restored |

The first custom-kernel boot had begun the previous day at 17:02 and continued until the 16:50 interruption, about 23 hours 48 minutes of recorded boot lifetime. That is not continuous compute stress, but the many completed workloads support the owner's observation that the setup was working. The selected GSQ Qwen Strata case passed at 23:50–23:52 on November 4, just outside this calendar-day review; it is not counted as a November 5 run.

## Stops that were not system crashes

- Overnight Maya/GLM/Strata attempts hit the then-active decode-progress rule; corrected later qualification results are listed above. The failed original records remain.
- PLE/Super attempts stopped on heartbeat/resource guards without inference or promotion. The later PLE attempt missed its original cleanup deadline and drained later; no corresponding GPU/kernel crash was persisted at that time.
- The first newer-llama Empero case failed its exact final-marker check. A separate later-source Empero case passed. Controller/guard completion alone does not turn the earlier tool failure into a pass.
- RDNA3 build attempts had build/tooling failures and one CPU thermal guard stop at 09:36; the later isolated CPU build/import audit passed. Its model startup subsequently failed on missing `_seq_lens_cpu`, before inference. The CPU thermal stop is distinct from the much cooler samples at the evening GPU failure.
- Flint AWQ failed on missing FlashInfer. One Strata preparation run rejected the wrong device order before model qualification; the corrected-order case is the 11:48 pass.
- SGLang's native-timing collector hit a nullable-text `TypeError` after its strict tool round trip. The separate speed-only continuation supplied the three valid probes; the failed collector record was not rewritten.
- GLM RAM24's 16:45 stale-slot admission and 16:47 readiness-schema stops had zero inference requests and clean owned cleanup. The 18:25 empty-launcher guard pass is not model qualification. The real restored case began 18:27 and passed.
- Download/identity/build stages are not inference successes. The 17:03–17:07 IQ1_M rehash verified 69 original content hashes without reloading the model.

## The two interruptions were different

| Time | Evidence | Conclusion |
|---|---|---|
| Around 16:50 | Last owned GLM attempt stopped with clean cleanup at 16:50:12; journal continued to 16:50:29, then ended without an orderly shutdown sequence. Next stock boot began 16:53:24. No comparable GPU fault was recorded before this gap. | Owner-reported power-loss interruption; exact initiating cause cannot be recovered from the available journal. Do not attribute it to the later DeepSeek case. |
| 18:07–18:08 | Recorded orderly reboot from stock into the already installed custom kernel | Planned reboot, not a crash |
| 18:44–18:46 | DeepSeek candidate load, GPU nonresponse, failed recovery, display IRQ/CPU lockups; next stock boot at 19:06 | Recorded GPU/kernel crash sequence detailed below |

No comparable SMU/MES/reset/lockup sequence was found elsewhere in the November 5 journal before 18:45. Absence of a persisted message cannot rule out an unlogged failure at the earlier power interruption. After 19:06, the fault hold remained; no new model attempt was launched by this review.

## What immediately preceded the latest crash

The 18:44:48 candidate used Maya **c167004** and the same DeepSeek UD-IQ1_S backing as the 04:14 passing case. Its plan and restored baseline comparison show **`--ssd-cache 36` was the only intended model-profile change**, apart from trial log/validation metadata. This option requests a host-RAM expert store despite its name. It was a new candidate, not the already-passing no-store baseline. The changed boot, cache state and other operating conditions prevent treating the two runs as a controlled A/B.

| Time, EST | Recorded event |
|---|---|
| 18:44:48 | Candidate model load starts |
| 18:45:02.728 | Last completed telemetry row is timestamped; host memory and GPU headroom remain ample |
| 18:45:06.738 | Sapphire stops answering an SMU management query |
| Approximately 18:45:08.786 | Six-second supervisor heartbeat fault latches; time derived from saved same-boot monotonic/UTC references |
| 18:45:11.982 | MES queue removal fails; GPU reset/recovery begins |
| 18:45:13 | Guard writes its failed result with owned cgroup still populated and KFD client remaining; original cleanup failure is preserved |
| 18:45:37.424 | DMCUB/display diagnostic error |
| 18:45:41.589 | Vblank wait timeout on the other GPU's display path |
| 18:46:05 | CPU19 hard lockup in `amdgpu_device_rreg` through the display/vblank IRQ path; multiple CPU soft lockups follow |

**The first SMU timeout predates the watchdog latch.** The watchdog reacted to an existing loss of responsiveness. Queue-removal/reset failure then accompanied shutdown/recovery, and the host later hard-locked in the driver. The logs do not identify the first failing GPU instruction, prove that telemetry initiated the fault, or establish which underlying software/firmware/hardware interaction caused the initial hang.

The 49 completed samples cover 13.79s. They show minimum available RAM 52.57GiB, minimum free VRAM 7.71GiB per card, zero recorded owned swap/spill and cgroup OOM events, maximum CPU 53°C and GPU-sensor 46°C. These are **evening-case samples, not the entire day's temperature maxima**. The engine never became ready or accepted inference, and no expert-load/store-initialization completion was logged. Its last sampled worker host memory was 8.05GiB. There is no evidence that the requested 36GB RAM store had been fully allocated or caused an ordinary capacity failure. Unsampled transients and lost post-hang telemetry remain possible.

## Card identity and supported conclusion

The latest initial SMU failure identifies **Sapphire**, after its recorded slot swap; it remained model-runtime GPU1. The previous November 4 failure also identified Sapphire before the swap. The earlier review's stale-mapping claim that the latest card was PowerColor is withdrawn. A PCI address, monitoring GPU index and model-runtime GPU number are different labels. The later vblank timeout on PowerColor's path does not change which card first stopped responding.

The strongest supported statement is: **a new Maya DeepSeek load was followed by Sapphire becoming unresponsive; driver recovery failed and escalated into a host lockup.** Its ordinary no-store baseline had worked earlier that day, as had many other dual-GPU workloads. The exact first cause remains unproved. A permanently bad switch, universally bad custom kernel, defective Sapphire, or successful 36GB allocation cannot be inferred from these records alone.

The persistent GPU fault hold remains unchanged. RAM40 is prepared but unrun and blocked. No model, GPU sensor query, peer test, reset, setting change or reboot was performed for this review.

[Stock/custom comparison](AMD-CRASH-KERNEL-COMPARISON-2026-11-05.md) · [Latest qualification evidence](STRATA-IQ1M-AND-STREAMING-CACHE-2026-11-05.md) · [Runtime handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md)
