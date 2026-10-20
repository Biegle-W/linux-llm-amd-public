# CPU and RAM inventory — October 19, 2026

> **October 20 current state:** i9-13900KS / 64 GB validation is complete; both Super
> IQ3/Q4 are selectable and Strata retains 13.5 GiB / native 256K on shared NVMe.
> This dated report preserves its original evidence. Use the
> [current profile report](CPU-RAM-PROFILES-2026-10-20.md) for active settings and results.

Read-only checks after the hardware change confirm:

| Component | Detected configuration |
|---|---|
| CPU | Intel Core i9-13900KS; 24 cores / 32 logical CPUs |
| System RAM | 64 GB installed; 66,046,431,232 OS-visible bytes (61.51 GiB) |
| Memory availability | Approximately 56 GiB available at the readiness check; zero swap used |
| Inference GPUs | Two RX 7900 XTX, 24 GB each, amdgpu |
| Additional graphics | Intel integrated graphics detected with i915; inference policy remains both AMD cards |
| GPU uplinks | Separate CPU PCIe4 x8 paths; no purchased PEX88096 switch in the detected GPU paths |
| Kernel | 7.0.0-38-generic |

RAM slot population, configured memory speed and dual-channel operation were
not independently verified: DMI inspection required unavailable sudo access.
Capacity detection is not a memory stability test. PCIe topology was inspected;
HIP peer access, RCCL correctness and inference throughput were not retested.

The existing Shared model drive was unmounted after boot. The configured
UUID-based storage helper mounted it successfully. The retained Strata GGUF,
expert pack, MTP assets and tokenizer are present; no model was downloaded.

## Prepared profile readiness

`python3 -B hardware/check-strata-ready.py --ram 64` passed all preflight checks:
61.51 GiB OS-visible RAM, 56.41 GiB available, both AMD devices, KFD access,
retained assets and the existing HIP executable. The candidate's expert budget
is 20 GiB. It retains native **262,144 context**; more RAM does not increase the
model's native window automatically.

This is eligibility for testing, not an activated or benchmarked profile.
Production profiles, memory guards, saved defaults and CPU thread counts were
not changed. The existing bounded Strata profile remains selected until the
64 GB candidate passes actual retrieval/code, tools, streaming and memory checks.
[Necessary validation](STRATA-AFTER-RAM.md).

Nemotron Super Q4 remains an inactive candidate; the additional RAM alone does
not validate its splits, speed or context. Follow its existing
[activation gates](NEMOTRON-SUPER-2026-10-19.md#use-and-future-activation).

## Benchmark interpretation

The saved [ten-profile AMD results](CURRENT-AMD-BENCHMARKS.md) were measured on
the **i5-13600KF with 32 GB RAM**. They remain unchanged and must not be presented
as i9-13900KS/64 GB measurements. No new performance or quality result is claimed.
The archived NVIDIA/Windows setup is unchanged.
