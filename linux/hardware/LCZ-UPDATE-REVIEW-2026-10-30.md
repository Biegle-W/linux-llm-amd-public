# LCZ update review — October 30, 2026

Follow-up: the [completed MES source audit and offline preparation](MES-SOURCE-AUDIT-2026-10-30.md) resolves exact-package inclusion/applicability below; no kernel activation or GPU trial. The original review remains dated evidence.

Read-only review of five requested topics, including reply pages and edit timestamps: 12 public API pages covering 159 posts. Dates below use America/Toronto. Author-reported performance is separate from our qualified local results. No runtime setting, driver, kernel, service, hold, guard or schedule was changed; no GPU trial was started.

| Topic | Latest findings | Assessment |
|---|---|---|
| [2728](https://lcz.me/topic/2728) | New October 30 vLLM 0.29 tiered-MoE prototype for R9700. Only two layers run and output is deliberately numerically wrong; real PLE, 48 layers, logits validation and concurrency remain pending. | Early architecture work; no demonstrated usable Flash-Next runtime or speedup. No source-package link in this topic. |
| [1532](https://lcz.me/topic/1532) | Main edit September 12; last reply September 24, an automated award. Its linked SGLang branch remains `f84475ccf593`, matching our local source. | No new October engine update in this thread. Older DFlash discussion is already behind the current source pin. |
| [2724](https://lcz.me/topic/2724) | Latest reply extends custom ComfyUI TP2 to 1080p / 12 seconds: about 25 minutes of sampling, 9 min 35 sec video VAE and 22.89 / 22.95 GiB sampling VRAM. Fifteen seconds OOMs. Host has128 GB RAM; conditioning is cached. | Not native Radiance TP2, and this result does not qualify our 32 GB host. No runner package linked. |
| [2671](https://lcz.me/topic/2671) | October 30 Windows 64 GB follow-up reports 97 tok/s decode and 1118.8 tok/s prefill, using 7168-token chunks. | A participant's Windows result, not a new Linux fix. RDNA3 head `fc8f82334239` and open AVX2 PR head `309f0c8f8cef` still match our completed trial. |
| [2694](https://lcz.me/topic/2694) | Main benchmark uses 96 GB RAM and the same Strata revision. The [latest technical reply](https://lcz.me/post/29572) adds an experimental MES kernel workaround: idle spinning disappeared, but one watchdog stall remained among 27 requests. That patch test used 256 GiB RAM. | Strongest new investigation lead; not evidence that our stalled 32 GB profile is fixed. |

## MES scope and local comparison

The [upstream issue](https://github.com/ROCm/TheRock/issues/9141#issuecomment-6211587609) discusses queue oversubscription preventing idle. Related forward-progress failures are tracked separately; matching high GPU utilization alone does not establish the same cause. The linked [reset-notification patch](https://www.mail-archive.com/amd-gfx@lists.freedesktop.org/msg153442.html) protects MES notifications during GPU reset.

The forum attachment targets Ubuntu source package 7.0.0-38.38. This host runs 7.0.0-42-generic with `sched_policy=0`. I inspected the attachment as text only; its six files cover MES, user queues and KFD. A symbol-name check found no matching notifier names, but this is not a complete installed-patch audit. Inclusion and source compatibility remain unverified; no patch was applied.

Our [completed Strata trial](STRATA-RDNA3-32GB-TRIAL-2026-10-30.md) remains unqualified: the 8K history test stalled under unchanged guards. Its memory-saving stage layout disables the author's dual-GPU DP-prefill path. High-RAM benchmark settings cannot establish performance or stability on this profile.

The remote [SGLang head](https://github.com/StevenChenSE/sglang/commit/f84475ccf593087df3d1da13c9e675eadee12352), [Strata head](https://github.com/nicejunjie/Strata-rdna3/commit/fc8f82334239199cd3cfcfa5ab5b8ac09827d19b) and [AVX2 startup PR](https://github.com/nicejunjie/Strata-rdna3/pull/1) were checked directly. No new source revision in these links warrants a runtime upgrade.

The subsequently authorized installed-kernel/backport source audit is complete; see the follow-up above for its exact scope and remaining build/qualification gates. Existing model selections, holds, guards and completed evidence remain. [Curated source-check metadata](results/lcz-update-review-2026-10-30.json).
