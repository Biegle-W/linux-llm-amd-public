# Strata: 5 GiB loaded startup requirement — October 20

The user explicitly requested reducing the free-VRAM requirement after the
Intel-rendered desktop retest left 5.388/6.269 GiB free on the two RX 7900 XTX
cards. The actual loaded startup minimum is now **5 GiB per card**. This replaces
the former 6 GiB admission rule for managed Strata only; Maya is unchanged.

The engine's allocation targets remain **7/8 GiB**, with the existing minimum
requested reserve validation. Allocation targets and measured whole-card free
memory are separate checks. Q3 weights, 13.5 GiB expert RAM cap, 256K context,
INT8 KV with 32K GPU residency, six CPU pool workers, layer split 26, MTP3 and
both GPUs remain unchanged.

The production router and isolated candidate use the same startup check in
`dsh/strata_memory.py`. The continuous latched watchdog is unchanged: below
3 GiB free for two samples or below 1.5 GiB immediately unloads only the owned
worker; host-memory, telemetry, swap and spill protections remain. The production
worker scope now explicitly carries `MemoryMax=52G` as the candidate scope does,
with `MemorySwapMax=0`. No other backend's guard or automatic-stop boundary changes.

Twenty-one CPU guard/readiness tests pass, including exact 5 GiB acceptance,
one-byte-below rejection on either card, missing-card rejection and router tests
showing that a failed startup stops only its owned worker. Previously measured
6 GiB-gate failures remain in the [earlier evidence](results/strata-linux-update-2026-10-20.json)
and [report](STRATA-LINUX-UPDATE-2026-10-20.md).

[Numeric policy/validation record](results/strata-startup5-2026-10-20.json).

## Validation status

GPU validation is queued after the other agent's clean GPU-lock handoff.
Development engine 0.1.46.1 / source
[`9ae93f7b`](https://github.com/Niko1221/Strata/commit/9ae93f7b1fe989d04a8e404d32cddaeeff10505f)
remains a candidate; production is still 0.1.45 /477ac13c. The lower startup
threshold does not establish generation correctness, throughput, near-window
quality or promotion eligibility. Those checks must complete before activation.
