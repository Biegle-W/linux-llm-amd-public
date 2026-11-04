# Dual RX 7900 XTX and 64 GB: successful community setups

Research checked November 3, 2026, after switch removal. These are source authors’ measurements, not reproductions on this workstation. Two close hardware matches establish that this configuration can serve Qwen and DeepSeek; they do not establish the cause of this machine’s earlier failures.

## Closest matches

| Source | Hardware and deployed setup | Reported result and limits |
| --- | --- | --- |
| [LCZ 2062](https://lcz.me/topic/2062) | Two XTX, 64 GB, Core Ultra 7 265K, Ubuntu; CPU-connected Gen4 x4 OCuLink plus x8 slot; **no P2P**. Qwen Flash Next IQ3_XXS, engine 0.1.38/HIP 7.2, 128K context, INT8 KV, automatic cache/prefill, MTP. | Approximately 57–66 output tokens/s in dual-card tests. Three samples per context level; expert caches were warm. Around 50 GiB system RAM used. This demonstrates a working narrower-link, host-transport arrangement, not a controlled PCIe comparison. |
| [Strata 4136](https://github.com/Niko1221/Strata/issues/4136) | Two Sapphire XTX, 64 GiB, i7-13700K; **CPU x16 plus chipset x4**, close to this workstation. Fedora/container deployment. Qwen IQ3_S and DeepSeek ISTA-DAS 2.00 bpw. | Qwen approximately 66–71 output tokens/s; DeepSeek approximately 22–23. Qwen held about 22.4 GiB of experts in RAM. Two repetitions per long-context level; the standard benchmark protocol was not run. The DeepSeek quant differs from our Unsloth Q1. |

## The same owner’s current configuration matters more than an old headline

The [deployment history](https://github.com/hurui200320/llm-ops/blob/master/notes/strata.md) follows the exact 64 GB/x16+x4 host through **Strata 0.2.10**, the revision staged here. On November 3 the owner tested DFlash2, then restored **MTP**: long-context output was about 53–55 tokens/s with DFlash2 versus 64–65 with MTP. These are that owner’s practical profiles, not an isolated algorithm comparison.

The notes also identify the drafter-selection trap found locally: a pipeline-window argument makes the server select MTP instead of DFlash2. A DFlash2 test must check the actual engine command and activation log. An interface selection alone is insufficient.

The owner’s [DeepSeek notes](https://github.com/hurui200320/llm-ops/blob/master/notes/deepseek/v41f1017.md) use a **36 GB native RAM store for SSD-backed experts**, 16 CPU threads and the gfx1100 prompt-kernel option `STRATA_DS4_HIPK=1`. The current vision-enabled profile reserves 900 MiB per card when sizing its cache; an earlier 1024 MiB arm also worked. That reserve is **not** a measured minimum-free-VRAM guarantee. The notes retain approximately 19 tokens/s in a November 3 long-context spot check with the same latest source.

This differs materially from our first Q1 attempt: native SSD-cache size zero, 20 CPU threads and no explicit gfx1100 prompt-kernel opt-in. Our requested 28 GB warm-cap environment setting is not implemented by this Strata component. Its actual cache must be configured through its supported native option. Qwen’s resident-budget and KV flags must not be copied into the DeepSeek engine.

## Maya evidence is adjacent, rather than an exact Q1 match

[Maya 757](https://github.com/mw00/project-maya/issues/757) reports one XTX, roughly 64 GB RAM, an i7-14700KF and ROCm 10.2. Maya 1.1.46 with **Maya-XS and DSpark**, at 64K context, measured 18.4 output tokens/s and 395 prompt tokens/s. It did not test a second GPU or Unsloth Q1. A separately reported 8,710-token prompt ran at 321 prompt tokens/s: about **27 seconds of prefill**, calculated from those figures. Our 20-second first-output gate would stop a request of that duration even on an otherwise functioning setup.

The [much faster dual-XTX Maya report](https://github.com/mw00/project-maya/issues/797) includes **128 GB RAM and an additional Strix Halo GPU helper**. The [LCZ dual-XTX RDNA3-fork report](https://lcz.me/topic/2666) also uses **128 GB**. Neither supports promising those speeds on our 64 GB machine. The [single-XTX fork guide](https://lcz.me/topic/2671) uses another ROCm/hipBLASLt combination; its tuning table and many optional switches are not a drop-in configuration here.

## Application to this workstation

- Keep P2P off: the Ubuntu success provides a directly relevant host-transport precedent. An x4 second link alone does not establish the fault cause.
- Prefer the already functional latest-Strata MTP candidate while retaining the separate DFlash2 result. Evaluate a larger admitted RAM cache separately from the source upgrade.
- For the existing Unsloth Q1 files, stage a separate DeepSeek candidate using the supported native RAM-store setting and reviewed gfx1100 kernels. Preserve our 32K test cap and independent resource, temperature, progress and ownership guards. This adapts a different-quant report; it is not a known Q1 pass.
- Preserve the Q1 and GLM first-output failures. They are timeout outcomes, not new GPU-reset evidence. The separate large-RAM GLM stop exposed a blocked process-details telemetry read. A kernel-identity-only reader corrected that monitor blockage without increasing its six-second heartbeat limit; the corrected 40 GiB-cache trial then reached the unchanged 210-second loading deadline.

The community-informed Q1 candidate used the supported 36 GB store, 14 physical CPU threads, the reviewed gfx1100 kernel option, 32K context and 1024 MiB native reserve. It loaded in 51.042 seconds, then missed the unchanged 20-second first-output deadline on the actual DSH read-tool request. Its owned scopes emptied, with no recorded new GPU fault, swap or spill. This is a local failed qualification, not a replication of the different-quant success report.

No kernel, PSU wiring, PCIe policy, guard threshold or schedule was changed by this research. Latest-engine qualification and the remaining pinned tasks are still in progress; source reports do not authorize copying their complete settings wholesale.
