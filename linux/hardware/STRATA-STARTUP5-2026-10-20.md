# Strata 0.1.46.1: validated 5 GiB startup admission — October 20

**Managed Strata 0.1.46.1 / source9ae93f7b is now active.** All candidate,
near-window, normal launcher, native frontend and authenticated gateway checks
passed before final activation. The deployed binary is byte-identical to the
measured candidate. [All trials and numeric evidence](results/strata-startup5-2026-10-20.json).

The user explicitly reduced actual loaded startup admission from6 to **5 GiB
free per card** after Intel desktop rendering was verified. Engine reserve
allocation targets remain **7/8 GiB**. This changes managed Strata only; Maya's
6 GiB startup requirement and all other backends are unchanged.

## Retained configuration and build

- Hardware: i9-13900KS,64 GB RAM (61.51 GiB visible), two RX7900XTX24GB on CPU
  PCIe4 x8/x8, Intel UHD770/i915 desktop rendering. Purchased switch is not installed.
- [Upstream source9ae93f7b](https://github.com/Niko1221/Strata/commit/9ae93f7b1fe989d04a8e404d32cddaeeff10505f),
  HIP/gfx1100, isolated ROCm7.2.3. Engine version0.1.46.1.
- Deployed/benchmarked engine SHA256:
  `c6706bc192c1afb09357e7d1eca9570c35c04562cde5265bd4404fe453848478`.
- ggml archive declares3cf03257f219afbe7334045ff7c6a06ac68c627d. This is the
  archive's declared revision, not an enclosing Git repository's HEAD.
- Existing IQ3_XXS/shared-NVMe corrected pack,13.5GiB CPU expert cap, six pool
  workers/all CPUs, layer boundary26/overlap on both cards, MTP3/min-p0.7,
  prefill2048, native262144 context, INT8 KV/32768 GPU residency/full host backing.
  No weights were downloaded and the20GiB candidate stays inactive.

The common startup check is in `dsh/strata_memory.py`, used by candidate and
production router. Continuous latched protection is unchanged: below3GiB on
any card for two samples, or below1.5GiB immediately, stops only the owned worker.
Host/telemetry/swap/spill checks remain. Production and candidate workers have
52G memory caps and zero swap allowance. No unrelated application is stopped.

## Fresh measurements

Three timed trials per workload, excluded warm-ups, same shared short/fresh8K
method, seed42/temperature0.6/top-p0.95 for short prompts. Fresh marker prefill
is greedy and uncached. TTFT is external SSE submission-to-first-output;
decode is `(completion_tokens-1)/(stream_end-first_output)`. Prefill below is
native engine timing, not input divided by TTFT.

| Workload | Actual input / output | Native PP t/s | TTFT s | Decode t/s |
|---|---|---:|---:|---:|
| Code, median of3 | 29 /256 each | — | 0.229 | 75.28 |
| Prose, median of3 | 25 /256 each | — | 0.233 | 50.31 |
| Fresh marker prefill, median of3 | 8185–8188 /20–22 | 912.2 | 9.015 | — |

These are fresh results for this build and Intel-rendered desktop. They are not
a matched upstream A/B. Earlier0.1.45, SATA-pack and NVIDIA speeds remain dated;
no speedup is attributed to changing the startup threshold or moving the desktop.
The earlier0.1.45 six-worker medians were code76.61/prose53.35/nativePP914.3;
those remain historical measurements, not the current row.

## Context, memory and functional proof

Near-window retrieval plus256-token code generation passed with **257984 actual
input tokens**. A full-history follow-up used **258266 input /22 output**, with
258239 cached tokens; all three markers were recovered in both turns. Configured
262144 capacity and tested input counts are separate. This is a retrieval/code
check, not a general quality guarantee at every prompt length.

Candidate startup free VRAM was5.356/6.268GiB. Minimum through all candidate
stages was5.310/6.221GiB; host available memory stayed above32.46GiB. Owned swap
and nonresident VRAM spill were zero. Full normal launcher/API readiness observed
5.354/6.268GiB free; the actual Desktop-entry run observed5.356/6.268GiB free.

Math, code/prose, tool calls/results, tool JSON arguments, SSE and near32K
retrieval passed on the candidate. The normal production launcher additionally
passed JSON mode, tool round-trip and authenticated streaming through host-self
loopback/LAN/Tailscale. No external remote peer was tested. The native Chat/Monitor
served the exact six upstream assets and blocked runtime/context/self-update
writes. Normal checks are functional-only; they are not extra speed samples.

The desktop entry now explicitly starts the installed **Ptyxis** terminal.
`Terminal=true` through `gio` did not dispatch the command on this desktop;
explicit Ptyxis did. The corrected actual Desktop file was launched with `gio`,
reached the guarded model and answered arithmetic correctly. PATH name
`llm-strata` is unchanged and remains suitable for SSH. Strata opens its native
frontend after readiness; DSH stays separate. The standalone AppImage0.2.1 and
bundled engine0.1.46 remain separate, with inactive legacy inference settings.

## Rollback and limits

Previous source477ac13c/0.1.45 and verified binaries are retained as inactive
rollback evidence. Both owned test workers were stopped after their checks,
and only this task's GPU lock was released. No profile/weight deletion occurred.
The [former6GiB admission failures](STRATA-LINUX-UPDATE-2026-10-20.md) remain
historical, including exact snapshots. The new floor was explicitly authorized;
no further guard was lowered.
