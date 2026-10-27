# Flint reasoning budget 128 benchmark — October 27, 2026

The unchanged selectable `flint-40b-a2.5b` profile passes a fresh normal-launcher
benchmark through the authenticated host-self API. It retains both RX 7900 XTX
cards, all-GPU weights, 32,768 context, Q8 K/V, flash attention, no MTP, batch/ubatch
4096, DIO loading and a 128-token reasoning budget. llama.cpp remains
`2280f0fd163b03d4331d49e08460f66502e35854` with ROCm 7.2.3; the i9-13900KS host exposes 14.83 GiB RAM.

## VRAM only models

| Model / engine | Native prefill tokens/s | TTFT seconds | Code / prose decode tokens/s | Context limit tokens | Allocated storage GB | Storage location | Date |
|---|---:|---:|---:|---:|---:|---|---|
| Flint-40B-A2.5B UD-Q4_K_XL / llama.cpp HIP | 6034.8 | 1.396 | 46.63 / 46.57 | 32,768 | 25.06 | `/mnt/shared/GGUF-Models/Flint-40B-A2.5B` | 2026-10-27 |

TTFT above is request submission to the first reasoning or content SSE token.
On the same fresh prompts, **first visible-answer TTFT is 4.436 s**.
Decode counts both reasoning and answer tokens. The current budget therefore
does not imply immediate visible text even though initial token emission is fast.
Other model categories were not re-benchmarked in this task.

## Method and all measured trials

Three timed code runs and three prose runs follow an excluded warmup per task,
using the existing merge-sorted-lists and lighthouse-story prompts, temperature 0.6,
top_p 0.95, seed 42 and 256 total output tokens. Each timed short run hits that cap;
these are throughput probes, not complete-answer quality tests. The normal
template setting is retained; no request overrides the reasoning budget.

Three fresh marker prompts are sized using Flint's native tokenizer, begin with
a new salt and explicitly disable prompt reuse. They have
8182, 8181, 8179 actual input tokens,
zero reported cached tokens and 145 output tokens each. All three retrieve the
expected markers. Prefill is native engine timing; TTFT is external SSE timing.
Model loading is excluded from request latency. The context is read back as 32K;
this test adds no full-window throughput or long-context quality claim.

| Task | Trial | Input tokens | Output tokens | Decode tokens/s | Native prefill tokens/s | First-token TTFT s | Visible-answer TTFT s |
|---|---:|---:|---:|---:|---:|---:|---:|
| code | 1 | 19 | 256 | 46.70 | 364.2 | 0.085 | 2.862 |
| code | 2 | 19 | 256 | 46.63 | 362.9 | 0.084 | 2.862 |
| code | 3 | 19 | 256 | 46.58 | 363.6 | 0.085 | 2.859 |
| prose | 1 | 14 | 256 | 46.48 | 329.3 | 0.076 | 2.871 |
| prose | 2 | 14 | 256 | 46.61 | 334.4 | 0.075 | 2.855 |
| prose | 3 | 14 | 256 | 46.57 | 335.2 | 0.075 | 2.858 |
| fresh prefill | 1 | 8182 | 145 | 42.54 | 6034.8 | 1.396 | 4.448 |
| fresh prefill | 2 | 8181 | 145 | 42.72 | 6031.3 | 1.398 | 4.436 |
| fresh prefill | 3 | 8179 | 145 | 42.63 | 6045.6 | 1.392 | 4.435 |

Short-prompt median first-token / visible-answer TTFT:
code 0.085/2.862 s,
prose 0.075/2.858 s.
The earlier 46.86/46.90 decode, 6027.1 prefill and 1.415 s TTFT belonged to the
reasoning-off isolated experiment. Keep that dated evidence separate; this is
not a controlled speedup comparison against it or against CPU offload.

## Worker, memory and thermal evidence

GPU-LOCK serialized the task. The live model child's arguments and cgroup limits
were checked before/after: reasoning budget 128, context 32768, zero CPU experts,
4 GiB memory.high /5 GiB memory.max /zero swap. The native router is a different
process sharing the same binary and is excluded from model-flag assertions.
The model child's cgroup peak is 1.330 GiB.

Full launch/load/warmup/test/shutdown monitoring records 305 worker samples with
zero sampling/enforcement errors, zero owned-worker swap and zero sampled VRAM
spill. The request loop lasts 44.23 s, with 144
qualifying continuous-inference window samples. Lifecycle host swapout is 0;
host swapin is 45,056 bytes. All low-churn and pressure gates pass. Minimum
available host RAM in the lifecycle is
6.216 GiB;
minimum free VRAM in the inference headroom monitor is
9.636/11.191 GiB.
The startup 7 GiB available-RAM and 21 GiB/card admission rules were retained.

The full-run thermal recorder has 158 samples at 1 s, zero errors and no dropped
records. Sampled GPU0/GPU1 hotspot peaks are 59/59°C; memory peaks 44/54°C;
CPU package peak 72°C. Fan peaks 2418/1928 RPM, power-average peaks 417/330W and
graphics-clock peaks 2886/2467 MHz are retained in the numeric record. Reported
SMU thermal/hotspot flags occur in 94/105 samples; those flags are not measured
time throttled and do not quantify speed loss. Sensors include whole-card work
and sampling can miss brief peaks.

Two earlier harness attempts are retained privately: an incompatible thermal
decorator signature stopped before model loading, and a process-proof filter
selected the native router after arithmetic. Both cleaned up owned workers;
neither produced benchmark timings or a valid inference window. The corrected
complete run above supplies the published results.

The model/placement/runtime configuration fingerprints are unchanged. All owned
workers stopped, both GPUs returned to baseline, and GPU-LOCK was released.
No engine/model promotion, ComfyUI experiment or nightly updater activation
was performed. [Curated numeric evidence](results/flint-reasoning128-2026-10-27.json).
