# P2P model rollout: short DSH checks and containment — November 3, 2026

**The requested seven-route campaign is incomplete: two passed and unloaded, the SGLang attempt was interrupted by a GPU fault, and four were not attempted.** No inference worker survived the subsequent reboot. The owner reported installing more RAM afterward; the current kernel exposes **61.55 GiB**, consistent with the planned 64 GB configuration. The preceding two checks and the interrupted attempt ran with the earlier **30.60 GiB** visible RAM and must retain that attribution.

| Model / route | Short DSH outcome | Verified ordinary unload |
|---|---|---|
| Empero / HIP llama.cpp | PASS: one read tool, completed matching result, two model replies, exact final marker | yes |
| Flint / HIP llama.cpp | PASS: same strict round-trip checks | yes |
| Qwen / SGLang DFlash2 | Interrupted during initialization; no completed tool round trip | no; reboot subsequently cleared workers |
| Qwen / vLLM | Not attempted | not applicable |
| Bolt / vLLM | Not attempted | not applicable |
| Sage / vLLM | Not attempted | not applicable |
| GLM / Maya | Not attempted | not applicable |

Each attempted route used the normal guarded launcher and installed DSH headless harness, a fresh tiny marker fixture, maximum 256 output tokens per response, one tool call/two responses, and bounded readiness/request deadlines. There was no automatic retry, full-context run or throughput benchmark. Worker environment capture confirmed NCCL_P2P_DISABLE=0 and GGML_CUDA_P2P=1 during the completed checks. For layer-split native ggml, this is explicit peer-access enablement verified against the selected source and worker environment; it is not a measured per-request peer-byte trace. SGLang logs show P2P/IPC channel initialization before the fault, not a successful model/tool result.

## Fault evidence and limits

During SGLang DFlash2 draft initialization, the previous boot recorded a GPU1 SMU bus error followed by unrecoverable MES/reset errors. The last memory sample had about **18.05 GiB RAM available**, with **17.19 / 16.53 GiB used VRAM**; no OOM kill was recorded. These observations do not establish P2P as the sole cause, nor establish that the newly installed RAM resolves the GPU failure. Raw machine/client logs remain private. The interrupted attempt is retained rather than reported as a completed test or a clean pre-crash unload.

## Containment and selected settings

- The shared RCCL promotion was backed out to its prior NCCL_P2P_DISABLE=1 configuration. Earlier isolated RCCL controls showed that this flag alone does not prove actual host transport; no unverified fallback guarantee is made.
- Explicit GGML_CUDA_P2P=1 is now restricted to Empero and Flint's HIP llama launch path. Unqualified shared native promotion for Maya/Strata is removed. Their held routes are not enabled.
- SGLang DFlash2 is on a temporary application GPU-fault hold pending investigation and owner-directed resumption. Its allocation, context and pinned runtime remain intact. The other four unattempted routes retain their prior configuration; they are not P2P-qualified by this campaign.
- Existing RAM/weight holds, contexts, allocations, numeric settings, engine pins and guards otherwise remain; more RAM has not automatically restored profiles or enabled missing weights. The daily updater remains paused.

The new boot has no inference/KFD clients. Only this campaign's exact stale GPU reservation and the dead SGLang ownership record were archived and removed after checking absent PIDs and closed backend ports; no surviving or unrelated process was killed.

## Completed-check memory and guards

Values are GiB. Whole-card VRAM includes desktop activity. Summed worker RSS may count shared pages more than once; scope memory is a separate metric. Private evidence preserves lifecycle samples. Runtime guards retained the existing RAM/VRAM/spill rules and loading-swap-v4 (128 MiB/s writes / 160 MiB/s combined over complete 30-second inference windows). The observer's host I/O counters do not independently qualify inference-window rates.

| Model | Min available RAM | Peak summed RSS | Peak scope memory | Min free VRAM GPU0 / GPU1 | Peak owned swap / spill |
|---|---:|---:|---:|---|---|
| empero-qwen3.8-35b-a3b | 23.100 | 1.694 | 1.571 | 11.460 / 10.728 | 0.000 / 0.000 |
| flint-40b-a2.5b | 23.413 | 1.276 | 1.122 | 9.072 / 11.248 | 0.000 / 0.000 |

Sixteen relevant CPU pause/source-selection checks pass in each checkout after containment; shell/Python syntax checks pass. No post-crash GPU trial has run. Remaining work is to investigate the SGLang GPU failure or, on owner direction, continue only the four unattempted short checks with SGLang held. The original request is not marked complete.

[Curated outcomes and resource observations](results/p2p-dsh-rollout-2026-11-03.json). [Underlying bounded hardware P2P qualification](AMD-P2P-QUALIFIED-2026-11-03.md).
