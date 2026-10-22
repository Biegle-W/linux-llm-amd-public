# llama.cpp prompt batch / thread sweep — October 22, 2026

Follow-up to the [slow-model research](SLOW-MODEL-OPTIMIZATION-RESEARCH-2026-10-22.md), whose top
lead was the `ubatch-size = 128` every llama.cpp profile inherits from `[*]`. Locally measured;
[numeric record](results/llama-batch-sweep-2026-10-22.json).

**Outcome:** Ornith-1.5-122B now uses `batch-size = ubatch-size = 4096`: native prefill
**52.7 → 714.9 tok/s (13.6×)**, decode unchanged. Nemotron Super is unchanged: every faster size
tested breaks its 3 GiB/card VRAM guard.

## Setup

- i9-13900KS, 64 GB RAM, 2× RX 7900 XTX (23.98 GiB each), PCIe 4.0 x8/x8; GNOME on the Intel iGPU.
- llama.cpp 4c3c5810, HIP 7.2.3. Each run used the production preset section with only
  `batch-size`, `ubatch-size`, `threads`, `threads-batch` changed, on an isolated port in a
  no-swap 56G scope, holding `GPU-LOCK`.
- The shared `benchmark-current-amd.py` method, unchanged: three short code/prose decode runs
  (256-token cap) and three fresh ~8K marker prompts (actual 8,185–8,189 tokens for Ornith,
  7,922–7,927 for Super; 64-token cap). Production 32K context for both. Medians shown.

## Results

Free VRAM is the sampled whole-card minimum (23.98 GiB minus peak used).

| Model | batch / ubatch | threads | Native prefill t/s | Fresh ~8K TTFT s | Decode code / prose | Min free VRAM GiB (card 0 / 1) |
|---|---|---|---:|---:|---:|---:|
| Ornith | 512 / 128 (control) | 6 | 52.7 | 155.2 | 11.44 / 13.36 | 5.51 / 6.76 |
| Ornith | 2048 / 512 | 6 | 160.8 | 50.9 | 11.44 / 13.33 | 5.34 / 6.59 |
| Ornith | 2048 / 2048 | 6 | 471.5 | 17.4 | 11.44 / 13.34 | 4.83 / 5.97 |
| **Ornith** | **4096 / 4096** | **6** | **714.9** | **11.5** | **11.44 / 13.34** | **4.03 / 5.02** |
| Ornith | 8192 / 8192 | 6 | 986.9 | 8.3 | 11.38 / 13.31 | 2.31 / 3.27 ✗ |
| Ornith | 8192 / 8192 | 8 (P-core physical) | 979.3 | 8.4 | 11.42 / 13.34 | 2.32 / 3.27 ✗ |
| Ornith | 8192 / 8192 | 16 (P-cores 0–15) | 989.6 | 8.3 | 11.44 / 13.34 | 2.32 / 3.27 ✗ |
| Ornith | 512 / 128 (control repeat) | 6 | 52.7 | 155.4 | 11.44 / 13.33 | 5.51 / 6.76 |
| Super IQ3 | 512 / 128 (control) | 6 | 93.9 | 84.4 | 15.65 / 17.20 | 4.03 / 5.24 |
| Super IQ3 | 2048 / 2048 | 6 | 627.5 | 12.6 | 15.65 / 17.20 | 1.34 / 4.20 ✗ |
| Super IQ3 | 4096 / 4096 | 6 | 847.0 | 9.4 | 15.65 / 17.21 | 2.21 / 2.93 ✗ |
| Super IQ3 | 4096 / 4096 | 8 (P-core physical) | 849.1 | 9.3 | 15.64 / 17.20 | 2.21 / 2.93 ✗ |
| Super IQ3 | 4096 / 4096 | 16 (P-cores 0–15) | 848.7 | 9.4 | 15.65 / 17.23 | 2.21 / 2.93 ✗ |
| Super IQ3 | 512 / 128 (control repeat) | 6 | 93.8 | — | 15.63 / 17.19 | 4.03 / 5.24 |

✗ = below the production 3 GiB/card guard (`min_free_vram_gib` in `dsh/moe-offload.json`).

- Every run passed its markers and arithmetic check, with zero worker swap and zero
  non-resident VRAM. Available RAM stayed ≥14.8 GiB (Ornith) and ≥37.7 GiB (Super).
- Controls repeated within 0.3%, so the machine did not drift across the sweep.
- Thread count and P-core pinning made no difference beyond ±1%; 6 threads are kept.
- Thermals (sampled peaks): GPU0 junction 87–95 °C on Ornith and 89–98 °C on Super (98 °C on
  Super 2048); GPU1 junction ≤70 °C; CPU package ≤89 °C. SMU limit flags are reported samples,
  not measured throttling time.

## Production validation and the guard

The sweep's isolated server does not run the production MoE watchdog. Ornith at 8192 was first
activated and then stopped by the guard in production twice (2.33 and 2.88 GiB free on card 0),
returning 503 through the hub. It was reverted to 4096 before any client used it.

At 4096 through the model hub (`127.0.0.1:30100`): an 11,129-token fresh prompt prefilled at
**673.1 tok/s** (16.5 s), gave the correct marker answer, and left 4.05 / 5.03 GiB free per card
after 60 s, so the guard stayed clear. This is a single functional proof, not a benchmark.

## Not yet tested

- Super at 1024 or smaller (the only sizes that might keep ≥3 GiB/card).
- Qwen3.6, Empero and Sage (also 128 today; no VRAM guard of their own).
- The research's op-offload threshold (`GGML_OP_OFFLOAD_MIN_BATCH`) lead.
