# Sapphire, switch and P2P evidence audit — November 6, 2026

The recent compared failures repeatedly identify Sapphire losing PCI/SMU access while installed behind the switch. The retained logs do not establish that a direct P2P transfer was active at the failure instant. Actual direct transfers involving Sapphire also completed successfully. An older driver-P2P-disabled Strata qualification also failed after loading; its different workload and software state prevent treating it as a matched explanation for the latest SGLang failure. Site-specific failure evidence remains private. [Structured assessment](results/SAPPHIRE-SWITCH-P2P-EVIDENCE-AUDIT-2026-11-06.json).

## What the saved evidence establishes

| Record | Evidence of actual transfer | Outcome and scope |
|---|---|---|
| Fresh headless HIP capability check | Capability and enable checks establish admission only | Passed before the models; no payload correctness follows from this check alone. |
| Fresh headless direct integrity and HIP IPC | Both directions passed remote reads/writes and peer copies using three 16 MiB patterns; cross-process IPC passed both directions | Actual successful transfers on the same switch/board configuration and pre-fault boot. |
| Fresh headless RCCL check | Both ranks logged channels via `P2P/IPC`; all-reduce/all-gather values passed for float32/BF16 at 1, 4,096 and 1,048,576 elements | Actual successful collective transport, with `NCCL_PROTO=Simple` forced. Largest float32 input was 4 MiB. This does not cover every protocol, message pattern or sustained load. |
| Four headless model checks | Tools completed; the Qwen vLLM log identifies RCCL/PYNCCL, without channel transport logging | Same switch/boards/boot controls. Empero, Flint and Ornith guards passed. Qwen vLLM completed two requests and clean owned cleanup, but its separate administrative guard result-path failure remains failed. Do not label these four model runs individually traced P2P transfers. |
| Headless SGLang Qwen DFlash2 failure | Both TP ranks selected RCCL, with custom all-reduce disabled; channel transport, chosen protocol and faulting operation were unlogged | Sapphire `0b:00.0` lost PCI/SMU access at 23:01:30.761 Toronto on November 5, after graph warm-up completion messages around the idle/API-startup transition. Zero requests; failed owned cleanup. Nine routes remain unrun. |
| Older November 3 Strata retry with driver P2P disabled | Same-boot administrator evidence records driver peer access disabled, ACS redirection restored and no KFD GPU-to-GPU links. Three fresh HIP environments each reported no peer capability and refused peer enable in both directions | Loaded in 71.327 s but completed no request; qualification failed. Site-specific failure evidence remains private. The independent driver/HIP checks provide stronger evidence of disabled peer access than an environment flag. The workload and software state differ from the latest SGLang case. |

## Identity and interpretation

The corrected recent comparison follows the same Sapphire across the slot swap: earlier `13:00.0`, now `0b:00.0`, retaining logical model GPU1. Current PowerColor is `13:00.0`, logical GPU0. Physical card, retained logical role and the shared PCIe/power/firmware/driver environment remain confounded. The owner's report that Sapphire was stable alone directly in the motherboard remains relevant; there is no defective-card verdict or completed matched bypass comparison here.

The successful short transfers show that this Sapphire/switch path can carry correct P2P data. They do not establish stability for every model, size, protocol or power transition. Conversely, a successful admission check or an RCCL library/backend name cannot establish the transport used by a particular model run or at the crash instant. The retained RCCL control audit separately demonstrates why `NCCL_P2P_DISABLE=1` alone was insufficient evidence of host transport in that library; the older Strata case also had independent driver and HIP-negative proof.

The latest vLLM/SGLang comparison retains the same target weights, Torch/HIP and RCCL library and captured graphs in both backends. Protocol defaults, draft/verification kernels and Triton builds differ. SGLang's actual protocol remains unknown. A Simple-pinned comparison remains a proposal, unprepared and unrun; it cannot be described as an established fix or as an explanation for the earlier Maya failures.

The headless SGLang fault establishes that a connected physical monitor is unnecessary. Display Core and prior hotplug state remain unexcluded. The separate November 5 16:50 power interruption has no identified cause and is not assigned to this GPU failure mechanism.

## Preserved state

This audit used saved files only. All 273 headless evidence pins and 20 managed-input pins matched; the current 1,847-event GPU fault hold remained byte-identical. All 14 routes, earlier failures, journals and unrelated work remain intact. Patched `7.0.14-42-vmpt1` remains the selected default with stock fallback; the current post-crash boot remains unqualified. No GPU trial, retry, remaining-route launch, hold release, reboot, runtime change or new recurring schedule occurred. No further experiment is prepared by this audit.

## Sources

- [Headless campaign and guard distinctions](AMD-HEADLESS-KNOWN-PASSED-MODELS-2026-11-05.md)
- [Latest Qwen backend comparison](QWEN-VLLM-SGLANG-TRIGGER-COMPARISON-2026-11-05.md)
- [Older driver-P2P-off qualification](AMD-P2P-DISABLE-2026-11-03.md)
- [RCCL flag versus selected transport audit](RCCL-P2P-CONTROL-AUDIT-2026-11-03.md)
- [Corrected recent board identity across the slot swap](AMD-CRASH-KERNEL-COMPARISON-2026-11-05.md)
- [Successful workloads and separate interruptions](AMD-DAY-REVIEW-2026-11-05.md)
