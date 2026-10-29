# Ornith maximum-VRAM placement on 32 GB — October 29, 2026

An isolated per-tensor placement passed loading, arithmetic, three short generations and a roughly 1K-token marker retrieval. Its 32K context was allocated; full-window, vision, tools and production integration remain unqualified.

Host: 30.56 GiB OS-visible physical RAM and two 24 GB RX 7900 XTX cards. Retained Q4_K_M weights, the selected llama.cpp `2280f0fd163b`, no MTP, and 32,768 context allocation. Both ROCm devices use a 1:1 layer split, `n-gpu-layers=99`, `fit=off`, `n-cpu-moe=0`, Q8_0 K/V cache and flash attention. Expert placement is explicit in tensor overrides; GPU expert cache is disabled. Batch/ubatch are 1024/512 to reserve space for more GPU weights. All tests were isolated; production profiles remain unchanged.

The retained profile assigns about 41.06 GiB of expert weights to the CPU and uses a 4 GiB GPU expert cache. These candidates replace that cache with more permanent GPU expert weights. Total GGUF tensor metadata is about 70.62 GiB; this includes inactive MTP tensors ignored by the loader. GPU weight estimates exclude projector, KV, compute and desktop overhead. Paging/file-backed weights remain necessary; combined RAM/VRAM is not a fully resident capacity claim.

| Placement | CPU expert weights GiB | Load mode | RAM high/max GiB | Result |
|---|---:|---|---|---|
| ornith-static-max7-mmap32 | 32.20 | mmap | none / 30.56 | loading deadline; no readiness |
| ornith-static-max8-dio-paged24 | 30.94 | dio | 24.00 / 30.56 | startup available-RAM admission; no worker launched |
| ornith-static-max8-dio-paged22 | 30.94 | dio | 22.00 / 30.56 | available-host-RAM floor |
| ornith-static-max9-dio-bounded22 | 29.67 | dio | 20.00 / 22.00 | available-host-RAM floor |
| ornith-static-max8-dio-bounded22 | 30.94 | dio | 20.00 / 22.00 | available-host-RAM floor |
| ornith-static-max9-dio-bounded21 | 29.67 | dio | 19.00 / 21.00 | diagnostic stop before readiness; test pageable buffers next |
| ornith-static-max9-dio-pageable21-gpu1proj | 29.67 | dio | 19.00 / 21.00 | VRAM headroom floor |
| ornith-static-max8-dio-pageable21-gpu1proj | 30.94 | dio | 19.00 / 21.00 | VRAM headroom floor |
| ornith-matrix-balanced-dio-pageable21 | 30.94 | dio | 19.00 / 21.00 | VRAM headroom floor |
| ornith-matrix-safe-dio-pageable21 | 31.78 | dio | 19.00 / 21.00 | passed scoped checks |

| Placement | Minimum host available GiB | Minimum free VRAM GiB/card | Peak scope RAM GiB | Peak worker swap GiB | Spill bytes |
|---|---:|---|---:|---:|---:|
| ornith-static-max7-mmap32 | 23.82 | 4.81 / 5.67 | 26.07 | 0.11 | 0 |
| ornith-static-max8-dio-paged24 | 25.40 | not launched | 0.00 | 0.00 | 0 |
| ornith-static-max8-dio-paged22 | 1.15 | 4.85 / 4.64 | 25.01 | 8.23 | 0 |
| ornith-static-max9-dio-bounded22 | 2.91 | 3.58 / 4.64 | 22.00 | 9.28 | 0 |
| ornith-static-max8-dio-bounded22 | 2.96 | 4.85 / 4.64 | 22.00 | 6.99 | 0 |
| ornith-static-max9-dio-bounded21 | 3.28 | 3.58 / 4.64 | 21.00 | 9.74 | 0 |
| ornith-static-max9-dio-pageable21-gpu1proj | 6.27 | 2.49 / 3.91 | 19.00 | 11.38 | 0 |
| ornith-static-max8-dio-pageable21-gpu1proj | 6.16 | 3.67 / 2.68 | 19.00 | 13.83 | 0 |
| ornith-matrix-balanced-dio-pageable21 | 6.31 | 3.07 / 2.92 | 19.00 | 13.17 | 0 |
| ornith-matrix-safe-dio-pageable21 | 6.09 | 3.38 / 3.24 | 19.05 | 14.32 | 0 |

The pageable-buffer arms explicitly use `--no-host` and `--mmproj-device ROCm1`. The selected source prefers a GPU host buffer for CPU tensors; its HIP/CUDA host allocator attempts pinned memory before falling back to a CPU buffer. Read-only diagnostics found only about 357 MB of model reads after several minutes of allocation/reclaim work in the preceding arm. That arm was deliberately stopped before readiness to test pageable buffers; this diagnosis is a source-based inference, not a captured profiler stack. The GPU1 projector placement balances its overhead against the extra permanent GPU0 weights.

The matrix-balanced arm starts from the eight-layer placement, moves `blk.9.ffn_down_exps.weight` from CPU to GPU0, and moves the equal-sized `blk.33.ffn_down_exps.weight` from GPU1 to CPU (0.421875 GiB each). Total GPU weight bytes are unchanged; the CPU override is per tensor. Exact baseline layer lists and partial overrides are in the numeric results.

The balanced arm reached readiness, then its first request was interrupted by the VRAM guard; the request reader reported no output/usage. This is attributed to the recorded VRAM guard, not a generic model-output failure. The following safer arm returns the layer9 down matrix to CPU as well as the layer33 down/up matrices, reserving another 0.421875 GiB on each constrained card compared with that balanced arm.

The 3 GiB available-host floor (three consecutive samples), 3 GiB per-card VRAM soft floor (two samples), 1.5 GiB immediate VRAM floor and zero dedicated-VRAM-spill rule remained. These are sampled observations; an allocation burst can cross a floor before the consecutive-sample stop. Soft MemoryHigh alone did not contain those bursts. Hard worker caps were reduced while retaining the independent guards. Loading/parked swap and reads are allowed; occupancy/rate/PSI alone did not cause a stop. OS swap/oomd settings were unchanged.

The first mmap arm reached its 900-second loading deadline; the owned shutdown helper initially exceeded its short wait, then an exact PID/scope/KFD audit verified cleanup before reservation release. A harness fallback initially matched “VRAM spill=0” inside a RAM-floor error; the eight-layer bounded22 retry is correctly classified as another RAM failure. The later harness restricts that fallback to actual VRAM faults. Failed and preflight-only attempts are retained.

The working placement has approximately **37.32 GiB of active model weights in VRAM**, excluding projector/KV/compute overhead. This subtracts the loader-reported inactive MTP tensors from the metadata estimate. Its logical CPU expert backing is **31.78 GiB**, so this is explicitly a paged 32 GB configuration.

Remaining sampled headroom above the 3 GiB VRAM floor was 0.376 / 0.240 GiB. Another tested expert-matrix increment is 0.421875 GiB, which exceeds either card's remaining measured budget for this context/batch scope. Further allocation refinement stopped here.

| Working placement | Load s | Median short decode tokens/s | Median short TTFT s |
|---|---:|---:|---:|
| ornith-matrix-safe-dio-pageable21 | 168.88 | 4.947 | 4.447 |

Three sequential 96-token story requests establish only this short-run scope; cache, storage and execution order limit comparisons. Arithmetic and roughly 1K marker recall passed. There is no full-window, vision, tools, broad quality or production-activation claim.

Paging materially limits usability: the fresh **1,027-token** marker request had **191.17 s to first token** (5.37 native prefill tokens/s), then decoded its 22 output tokens at **0.98 tokens/s**. Total request time was 212.51 s, with zero cached input tokens. This is substantially slower than the short story decode rate; do not use that short-run rate as an overall speed claim.

All owned GPU reservations and worker scopes are released. Production configuration hashes are unchanged. Earlier completed benchmark records remain historical evidence.

[Numeric results](results/ornith-vram32-2026-10-29.json). [Earlier all-model 32 GB series](ALL-MODELS-32GB-2026-10-28.md). [Overnight update audit](ENGINE-UPDATE-AUDIT-2026-10-29.md).
