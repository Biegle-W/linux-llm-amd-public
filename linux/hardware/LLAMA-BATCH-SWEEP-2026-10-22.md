# llama.cpp prompt batch / thread sweep — October 22, 2026

Follow-up to the [slow-model research](SLOW-MODEL-OPTIMIZATION-RESEARCH-2026-10-22.md), whose top
lead was the `ubatch-size = 128` every llama.cpp profile inherits from `[*]`. Locally measured
in two sweeps the same day; [numeric record](results/llama-batch-sweep-2026-10-22.json).

**Outcome:** all five llama.cpp profiles now override the batch size. Native ~8K prefill rose
3.7–13.6× with decode within 2% of each control:

| Profile | batch / ubatch | Native prefill t/s, before → after | Fresh ~8K TTFT s | Min free VRAM GiB |
|---|---|---:|---:|---:|
| `ornith-1.5-122b` | 4096 / 4096 | 52.7 → 714.9 (13.6×) | 155.2 → 11.5 | 4.03 / 5.02 |
| `nemotron-3.5-super-iq3` | 2048 / 1024 | 93.9 → 431.4 (4.6×) | 84.4 → 18.4 | 3.61 / 4.68 |
| `qwen3.6-35b-a3b` | 4096 / 4096 | 381.7 → 2,881.8 (7.5×) | 21.5 → 2.8 | 8.24 / 5.29 |
| `empero-qwen3.8-35b-a3b` | 4096 / 4096 | 397.2 → 2,944.7 (7.4×) | 20.6 → 2.8 | 9.65 / 6.24 |
| `sage-a1.5` | 4096 / 4096 | 385.1 → 2,793.7 (7.3×) | 21.3 → 2.9 | 9.91 / 10.11 |

Ornith and Super carry a production 3 GiB/card VRAM guard (`min_free_vram_gib` in
`dsh/moe-offload.json`); their sizes are the fastest that keep it. Super at 1024 has the
thinnest margin (0.6 GiB on card 0).

## Setup

- i9-13900KS, 64 GB RAM, 2× RX 7900 XTX (23.98 GiB each), PCIe 4.0 x8/x8; GNOME on the Intel iGPU.
- llama.cpp 4c3c5810, HIP 7.2.3. Each run used the production preset section with only
  `batch-size`, `ubatch-size`, `threads`, `threads-batch` changed, at the production context, on
  an isolated port in a no-swap 56G scope, holding `GPU-LOCK`.
- The shared `benchmark-current-amd.py` method, unchanged: three short code/prose decode runs
  (256-token cap) and three fresh ~8K marker prompts (64-token cap). Actual inputs: 8,185–8,191
  tokens (Qwen-family models), 7,922–7,927 (Super). Medians shown.

## Results

Free VRAM is the sampled whole-card minimum (23.98 GiB minus peak used). ✗ = below the
production 3 GiB/card guard.

### Sweep 1 — Ornith and Super

| Model | batch / ubatch | threads | Native prefill t/s | Fresh ~8K TTFT s | Decode code / prose | Min free VRAM GiB |
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

### Sweep 2 — smaller Super sizes, Qwen3.6, Empero, Sage (6 threads)

| Model | batch / ubatch | Native prefill t/s | Fresh ~8K TTFT s | Decode code / prose | Min free VRAM GiB |
|---|---|---:|---:|---:|---:|
| Super IQ3 | 2048 / 512 | 261.6 | 30.3 | 15.66 / 17.25 | 3.78 / 4.93 |
| **Super IQ3** | **2048 / 1024** | **431.4** | **18.4** | **15.65 / 17.23** | **3.61 / 4.68** |
| Qwen3.6 (256K) | 512 / 128 (control) | 381.7 | 21.5 | 122.33 / 75.34 | 10.64 / 10.10 |
| Qwen3.6 | 2048 / 512 | 992.6 | 8.3 | 123.40 / 75.79 | 10.44 / 9.66 |
| Qwen3.6 | 2048 / 2048 | 2,240.5 | 3.7 | 122.80 / 74.56 | 9.54 / 7.79 |
| **Qwen3.6** | **4096 / 4096** | **2,881.8** | **2.8** | **121.33 / 73.88** | **8.24 / 5.29** |
| Empero (256K) | 512 / 128 (control) | 397.2 | 20.6 | 121.99 / 74.14 | 12.07 / 11.07 |
| Empero | 2048 / 512 | 1,033.6 | 7.9 | 122.34 / 74.58 | 11.88 / 10.63 |
| Empero | 2048 / 2048 | 2,321.4 | 3.5 | 121.18 / 73.36 | 10.98 / 8.75 |
| **Empero** | **4096 / 4096** | **2,944.7** | **2.8** | **121.45 / 73.52** | **9.65 / 6.24** |
| Sage (64K) | 512 / 128 (control) | 385.1 | 21.3 | 81.19 / 65.04 | 11.12 / 12.36 |
| Sage | 2048 / 512 | 980.4 | 8.4 | 81.32 / 64.76 | 11.01 / 12.16 |
| Sage | 2048 / 2048 | 2,194.3 | 3.7 | 80.59 / 65.04 | 10.68 / 11.34 |
| **Sage** | **4096 / 4096** | **2,793.7** | **2.9** | **80.81 / 65.16** | **9.91 / 10.11** |

- Every run passed its markers and arithmetic check, with zero worker swap and zero
  non-resident VRAM. Available RAM stayed ≥14.8 GiB (Ornith), ≥37.7 GiB (Super), ≥43.7 GiB (others).
- Sweep 1 controls repeated within 0.3%, so the machine did not drift.
- Thread count and P-core pinning made no difference beyond ±1%; 6 threads are kept.
- Decode at the selected sizes is within 2% of each control (largest: Qwen3.6 prose −1.9%,
  within MTP run-to-run variation). 8192 was not tried for the 35B models.
- Thermals (sampled peaks): GPU0 junction 78–98 °C (98 °C on Super 2048/2048), GPU1 junction
  ≤70 °C, CPU package ≤89 °C. SMU limit flags are reported samples, not measured throttling time.

## Production validation and the guard

The sweep's isolated server does not run the production MoE watchdog. Ornith at 8192 was first
activated and then stopped by the guard in production twice (2.33 and 2.88 GiB free on card 0),
returning 503 through the hub. It was reverted to 4096 before any client used it.

Each selected profile was then loaded through the model hub (`127.0.0.1:30100`) and sent one fresh
11,129-token prompt (11,132 for Super's tokenizer). All answered the marker correctly and the guard
stayed clear (free VRAM per card measured about 45–60 s later). Single functional proofs, not benchmarks:

| Profile | Prompt time | Native prefill t/s | Free VRAM GiB |
|---|---:|---:|---:|
| Ornith | 16.5 s | 673.1 | 4.05 / 5.03 |
| Super IQ3 | 25.4 s | 439.1 | 3.63 / 4.70 |
| Qwen3.6 | 5.4 s | 2,042.6 | 8.27 / 5.32 |
| Empero | 5.2 s | 2,137.6 | 9.70 / 6.30 |
| Sage | 5.3 s | 2,107.8 | 9.93 / 10.11 |

## Not yet tested

- Near-full-window (256K/64K) prompts at the new sizes. llama.cpp reserves the KV cache and
  compute buffers at load, so the ~8K peaks should hold, but long-window runs were not repeated.
- The research's op-offload threshold (`GGML_OP_OFFLOAD_MIN_BATCH`) lead.
