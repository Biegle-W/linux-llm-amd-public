# NVIDIA comparison and backend version audit — October 18, 2026

**Historical snapshot before the authorized runtime update.** Current installed
versions and validation are maintained in [the upgrade record](RUNTIME-UPGRADE-2026-10-18.md).
The following comparisons retain their original measured versions.

At audit time, the running Strata executable was the **AMD HIP gfx1100 build**, not CUDA or
Vulkan. Both RX 7900 XTX cards participate by layer splitting. It uses the
private ROCm 7.2.3 SDK and remains engine 0.1.44.1 at `296b59d2f73c`.
The preceding task configured and validated existing runtimes; it did not update
all engines. This audit changes documentation only and leaves Strata running.

## Saved Strata results: best NVIDIA versus current AMD

Both use the retained GSQ-RCO IQ3_XXS model and MTP, with thinking disabled.

| Measurement / setting | RTX 4070 + RTX 3060, October 7 | Dual RX 7900 XTX, October 18 |
|---|---:|---:|
| Aggregate VRAM / installed RAM | 24 GB / 64 GB | 48 GB / 32 GB |
| Runtime | CUDA 0.1.40.3 | HIP 0.1.44.1 |
| Configured context | 262,144 | 32,768 |
| Short code decode | 68.8 t/s | 59.8 t/s |
| Short prose decode | 64.6 t/s | 47.8 t/s |
| Bulk prefill | 1,538.5 t/s, 14,195 input tokens | 763.1 t/s, 30,070 input tokens |
| Prefill chunk | 8,192 | 512 |
| MTP `spec` / minimum probability | 4 / 0.5 | 3 / 0.7 |
| Sampling | Median of three short samples | One short sample per task |

The saved AMD short samples are about **13.1% lower for code and 26.0% lower
for prose** than the selected NVIDIA medians. This does not isolate a GPU-hardware
regression: RAM, runtime/kernels, MTP settings, placement, precision rounding and
measurement method differ. The prompt wording is closely related but not exactly
identical ("to merge" versus "that merges"; "discovering" versus "finding").
No matched new NVIDIA/AMD benchmark was run for this comparison.

The prefill figures also use different prompt content and lengths; they are not
a valid estimate of a fixed percentage hardware slowdown. The old 8,192-token
chunk is 16 times the current conservative 512-token chunk, so the two profiles
have substantially different batching. The current 32K limit is a tested operating
point, not a proven maximum supported by 48 GB VRAM or Strata. The prepared 64 GB
candidate proposes 128K but still needs actual validation after RAM installation.

[Current AMD method and data](STRATA-DUAL-AMD-2026-10-18.md).
The private historical source is `dsh/research/strata-2026-10-07/REPORT.md`;
the public README and NVIDIA archive preserve the historical values. Full-window
retrieval on NVIDIA used 257,850 input tokens at 2,266.2 t/s prefill with a short
22-token answer; AMD used 30,070 input tokens and a 19-token answer. Those decode
rates must not be treated as sustained full-window throughput comparisons.

## Installed versus currently available development builds

Snapshot checked October 18 in Toronto. Some official commit timestamps are
October 19 UTC, which is still October 18 locally. These are source/rolling-wheel
heads, not a stable-release-only comparison or an AMD compatibility claim.

| Engine | Installed | Checked upstream | Status |
|---|---|---|---|
| llama.cpp HIP/Vulkan | `f12aaa344c971` (October 16) | [`31288c9c66e5` master](https://github.com/ggml-org/llama.cpp/commit/31288c9c66e59377f7788d920678a565bb89dd37) | Newer source available; not installed |
| Strata HIP | 0.1.44.1, `296b59d2f73c` | [0.1.45 source, `477ac13cbe8e`](https://github.com/Niko1221/Strata/commit/477ac13cbe8e582c20484871ce459d20d82df09d) | Newer source available; not installed |
| vLLM ROCm 7.2.3 wheel | `0.32.0rc1.dev190+g3f1bcfd82.rocm723` | [`0.32.0rc1.dev329+g39983a5e7.rocm723`](https://wheels.vllm.ai/rocm/nightly/rocm723/vllm/) | Newer nightly available; not installed |
| SGLang RDNA3 fork | `f84475ccf593` plus local fixes | Same [gfx1100-support head](https://github.com/StevenChenSE/sglang/commit/f84475ccf593087df3d1da13c9e675eadee12352); official [main `df078cc72971`](https://github.com/sgl-project/sglang/commit/df078cc729718723cbdd071e606e416c1dc96cea) differs | Current for the retained fork, not official main |

Strata's [pinned CMake metadata](https://github.com/Niko1221/Strata/blob/477ac13cbe8e582c20484871ce459d20d82df09d/CMakeLists.txt#L10)
identifies 0.1.45. Official [vLLM main](https://github.com/vllm-project/vllm/commit/b0d61e5d26561f865bf89688eb0aea5000133a42)
is also ahead of the installed wheel. Local source status and package metadata
were inspected; no Git fetch/reset, package install, build or inference restart
was performed in this audit. llama.cpp's HIP and Vulkan build-info files both
identify `f12aaa3`, matching the retained source/configuration pin.

At this audit snapshot, upgrades remained pending. Newer source must retain or adapt the local AMD fixes
and pass both-card loading, MTP/tools, context and residency checks before replacing
the working profiles. These audit findings do not establish that a newer build
is faster or that official SGLang main can replace the RDNA3 fork unchanged.
[Machine-readable snapshot](runtime-upstream-audit-2026-10-18.json).
