# Qwen vLLM / SGLang startup-trigger comparison — November 5, 2026

**The saved evidence narrows the SGLang failure to the end of DFlash2 verification-graph warm-up and the transition into idle/API startup. It does not identify the faulting GPU instruction or prove the root cause.** This investigation changed no runtime setting and launched no GPU test. The hardware fault hold remains. [Structured findings](results/QWEN-VLLM-SGLANG-TRIGGER-COMPARISON-2026-11-05.json), [headless campaign](AMD-HEADLESS-KNOWN-PASSED-MODELS-2026-11-05.md).

## Matched conditions and differences

Both runs were headless on the same patched boot with the same target GPTQ weight path,163,840context,TP2,PowerColor13/Sapphire0b order,BF16KV,ROCmSDK7.2.3,RCCL2.27.7library and PyTorch2.13.0git733fca1/HIP7.2.53211 build. Both disabled custom all-reduce and AITER and retained all guards. This does not make their additional draft models or GPU kernels identical.

| Setting | Successful vLLM | Failed SGLang |
|---|---|---|
| Speculation | Shared target MTP,3tokens | Separate DFlash2 compressed-tensors drafter,8tokens |
| Cache allocation | Explicit6GiBKV per GPU; runtime logs say this overrides utilization profiling | Static memory fraction0.85; separate draft and hybrid caches |
| Graphs | Compiled FULL_DECODE_ONLY, sizes1/4; graph capture completed | Target verify and draft verify graphs,batch1; both completion messages logged |
| Verification | vLLM compiled MTP path | Local optimized RDNA target verification with KV-walk repair; fused draft KV materialization |
| Retained Triton build | 3.8.0+git669b31ac | 3.8.0 |
| Collective library | RCCL2.27.7, PYNCCL logged | Same RCCLlibrary path logged |
| Protocol launcher policy | Defaults `NCCL_PROTO=Simple`, unless inherited/explicit override | Does not pin `NCCL_PROTO` |
| Result | Two completed read-tool requests; clean cleanup; separate harness-path guard failure retained | No outer readiness attestation or request; GPU fault and failed cleanup |

The actual vLLM startup identifies version0.33.0rc1.dev229+g3966924d5. The retained SGLang editable source is f84475ccf593087df3d1da13c9e675eadee12352 with six local modified files, including the RDNA verification/KV-walk work. These are retained implementation differences, not changes made during this investigation or proof of a newly introduced regression.

## Aligned startup sequence

Times are EST. SGLang captured the target-verification graph at23:01:25–26 and draft-verification graph at23:01:26–29. The final telemetry sampling window began23:01:29.188876: Sapphire values became unavailable while PowerColor remained readable. At23:01:30.761818 the driver reported Sapphire lost from the bus, then SMU metrics export failed with0xFFFFFFFF. The worker API started in that same second; the outer harness never attested readiness and sent no request. Stop/reset/cleanup activity followed the fault.

**The sampling timestamp is the beginning of a snapshot, before sequential sysfs reads.** A blocked/failed read can finish later. Therefore the29.188timestamp is not evidence of a precise1.57secondearlywarning or proof that monitoring caused the fault. The kernel message follows failed PCI configuration access after an unexpected SMU response. The saved data identifies failed access and a narrow workload transition, not the underlying reason.

vLLM also completed graph capture. It then recorded Sapphire around59–63W with GFX0MHz/MCLK96MHz before a subsequent full-utilization burst of approximately302/304W on both GPUs and a successful tool check. Generic graph use, an idle-clock transition, steady high load, or the earlier53Widle sample alone is insufficient to explain the failure. This does not exclude fast unmeasured electrical transients. Recorded RAM/VRAM headroom and temperature limits were also ample in the failed case.

## What is worth isolating

The smallest concrete launcher difference to isolate first is **explicit RCCL `Simple` protocol selection**. The fresh peer RCCL probe forcedSimple, matching the vLLM default policy; it did not demonstrate every automatic protocol and message shape. AMD documents `NCCL_PROTO` as overriding automatic protocol selection. [RCCL2.27.7 environment reference](https://rocm.docs.amd.com/projects/rccl/en/docs-7.2.1/api-reference/env-variables.html).

This remains a hypothesis: actual per-collective protocol selection was not logged, failed-boot inherited environment was not captured, and standard user/system RCCL/NCCL configuration files were absent. **There is no evidence here that SGLang selectedLL/LL128 or that such a protocol is broken on these cards.** A separately authorized case could pinSimple and record actual transport/protocol while retaining the draft,graphs,source and every guard. A single successful run would not prove a fix; no such case has run or been prepared.

The DFlash-specific verification/draft kernels and different Triton build are further candidates for separate one-variable isolation. Both graph completion messages were logged, so there is no saved instruction-level evidence that a particular capture/kernel caused the loss. These SGLang differences also cannot by themselves explain the earlier Maya failure. A common Sapphire PCIe/power-state/firmware/driver problem or card/retained-logical-role interaction remains unresolved. No defective-card verdict, source update, clock change, guard relaxation or automatic retry is justified by this comparison alone.
