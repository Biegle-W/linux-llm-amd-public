# Choosing ROCm for two RX 7900 XTX cards — October 21, 2026

The retained **7.2.3 userspace stack is the fastest fully validated selection for
these production profiles among the local versions tested**. It is not a claim
that every 7.2.3 workload beats every newer release. Sage-specific trials are
recorded separately in [the Sage report](SAGE-A15-2026-10-21.md).

## Version numbers and driver scope

AMD's [release history](https://rocm.docs.amd.com/en/docs-7.2.3/release/versions.html)
dates 7.2.3 to May 4, 2026. It is approximately five and a half months old at
this review, rather than several major generations of hardware behind.
[10.1.0 is the latest official release](https://rocm.docs.amd.com/en/latest/about/release-notes.html)
reviewed on October 21; its compatibility matrix includes gfx1100 and Ubuntu
26.04.1/kernel 7.0. [7.14.1](https://rocm.docs.amd.com/en/docs-7.14.1/about/release-notes.html)
is a newer intermediate branch worth an isolated comparison, not a locally
validated upgrade here.

ROCm, the kernel graphics driver and framework builds are separate layers:

- Host kernel: `7.0.0-38-generic`, inbox `amdgpu`; firmware package
  `20260319.git217ca6e4.1ubuntu`.
- Native HIP applications: isolated 7.2.3 userspace libraries and compiler builds.
- SGLang/vLLM/Comfy: their own pinned PyTorch, Triton and extension dependencies;
  replacing a global SDK does not rebuild or upgrade those wheels.

The selected inference SDK therefore does not identify the age of the whole
Linux graphics stack. No system driver/kernel or global SDK replacement is
needed merely to compare another application-local ROCm version.

The [7.2.3 platform matrix](https://rocm.docs.amd.com/en/docs-7.2.3/compatibility/compatibility-matrix.html)
does not list Ubuntu26.04. The retained application-local combination is
locally tested, not a claim of full AMD support for this host OS. Newer releases
have a stronger official host-platform match; that compatibility benefit is
separate from measured inference speed.

## Local evidence takes precedence

[Ten-profile/six-engine 10.1 comparison](ROCM101-2026-10-21.md) used the same
models, engine sources, memory protections and matching workloads. No 10.1
candidate passed every promotion gate. SGLang aggregate −0.82%; Maya GLM −4.17%
and DeepSeek −4.60%; Strata gained prefill but lost 8.38% prose decode. vLLM's
three-seed confirmation gained only 1.63%, Empero 0.30%, below the 3% selection
gate. Comfy's image test improved while the video test regressed. These results
support retaining the working stacks, not a blanket statement about all AMD
software. Original trials, failures, thermal coverage and methods remain linked
in that report. No old rates are substituted for new measurements.

## Community comparisons and limits

[Ben Lee's direct post](https://lcz.me/topic/1532/95), accessed October 21
(post date not exposed in the retrieved view), compares dual 7900 XTX,
SGLang TP2/MTP3/BF16 KV at approximately 64K using
[upstream scheduler PR 34058](https://github.com/sgl-project/sglang/pull/34058)
and `max-consecutive-prefill-batches=1`. Reported 7.2.3/7.14/10 decode is
62.2/66.4/74.1 t/s; cold prefill 1338/1351/1146 t/s. Faster decode on 10
trades against slower prefill and TTFT. His [later setup](https://lcz.me/topic/1674/8)
uses Ryzen 9600X/X870E/64GB and 7.14; it is not our i9/DFlash2/160K workload.
These are another person's results, not local Sage measurements.

[Level1Techs' AMD source collection](https://forum.level1techs.com/t/the-twisted-links-of-amd-ai-collection-of-useful-links-for-amd-ai-dev-and-deployment/244053)
(ajc9988, January 7, 2026; subsequent replies) links official AMD/TheRock builds
and architecture-specific build resources. No matched dual-XTX Sage/7.14.1
benchmark was found there. [ivgranite's single-XTX notes](https://forum.level1techs.com/t/7900xtx-llm-inference-notes/250869)
(May 31, 2026; Ryzen 9600X/96GB, llama.cpp 9425/7.2.3, 32K reasoning)
report that higher tokens/second can still mean a slower complete answer when a
model generates more reasoning. Their rates cannot be compared directly with
our fixed-output tests. See the [source index](FORUM-OPTIMIZATION-SOURCES.md).

## Next defensible candidate

7.14.1 is a reasonable next **isolated** branch for matching application builds.
AMD documents an RDNA3 FP16/batch-at-least-8 PyTorch performance issue before
2.14, with `TORCH_BLAS_PREFER_HIPBLASLT=1` as the workaround. It is not evidence
that this flag improves our native GGUF or single-request W4A16/DFlash path.
The same release notes document Radeon SGLang AITER/MLA compatibility limits.
Retain the current gfx1100 fork/verification fixes until matching replacements
pass. Instinct multi-node RCCL fixes are not proof of better dual-XTX P2P.

A candidate should win matched prefill, code/prose decode and TTFT without
quality, residency, full-context, thermal or normal-launcher regressions. Keep
rollback environments and both-card/CPU-expert-cache protections. **7.14.1 has
not been tested locally in this task; do not present it as selected.**
