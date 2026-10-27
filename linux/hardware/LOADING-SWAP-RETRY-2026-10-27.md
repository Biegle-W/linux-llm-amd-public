# Current-RAM retry with loading swap allowed — October 27, 2026

User-authorized retry of the previously blocked vLLM/SGLang and native INT4 tests on **14.83 GiB OS-visible RAM**, both **RX 7900 XTX 24 GB** cards, Intel i9-13900KS and retained ROCm 7.2.3. No physical RAM upgrade is assumed.

**13 attempts; 6 complete benchmark/memory passes.** Loading swap and parked pages were allowed under `loading-swap-v2`, with no default cumulative-loading-write or resident-swap-byte cap. Sustained active-workload swap churn, host-RAM floors, zero dedicated-VRAM spill, GPU admission, owned scopes and lifecycle telemetry remained. [Policy](LOADING-SWAP-POLICY-2026-10-27.md).

One complete pass is a disabled-thinking Flint diagnostic; the matched reasoning128 run remains partial. Observed partial timings are retained with actual trial counts. They do not qualify a guarded/incomplete run or establish a valid candidate speedup. No selected engine version, model quantization, context, default profile or updater schedule changed. The systemd swap-property syntax was corrected without changing swap permission or RAM caps. The experimental Flint attention/norm patch remains isolated and unqualified.

[Curated numeric results, trial counts, memory and thermals](results/loading-swap-retry-2026-10-27.json).

## VRAM only models

Prefill below is **engine-phase throughput**, not native kernel-only throughput. vLLM uses scheduled-to-first-engine-token time; SGLang uses prefill-forward time for the slowest rank, so the phases are not identical across engines. TTFT is fresh-probe request submission to first emitted content/reasoning token; it differs from short-prompt TTFT and first visible-answer timing. Decode uses the retained SSE method and the code/prose medians. Parentheses show completed fresh/short probes out of three; short values use the median of completed observations, including explicitly partial single trials; all observed values from an incomplete run remain partial. Context is configured capacity, not a new maximum-window validation. Storage is decimal allocated GB; shared checkpoints count once. System-root paths are sanitized shareable examples; drive-relative checkpoint locations are retained.

| Tested profile | Prefill t/s (fresh probes) | Fresh TTFT s | Fresh input tokens | Decode code/prose t/s | Context limit | GB | Drive/path | Outcome |
|---|---:|---:|---:|---:|---:|---:|---|---|
| Qwen27B · vLLM dev435 | 1334.4 (1/3) | 6.179 | 8,189 | 141.03 (3/3)/76.01 (3/3) | 163,840 | 20.05 | System `/opt/local-llm/models/Qwen3.8-27B-W4A16-AutoRound-GPTQ` | partial; inference swap-I/O stop |
| Bolt W4A16 · vLLM dev435 | 2642.4 (3/3) | 3.026 | 7,924–7,926 | 37.88 (3/3)/37.98 (3/3) | 262,144 | 43.65 | SATA1 `vLLM-Models/Nemotron-3.5-Bolt-74B-A9B-AutoRound-W4A16` | full benchmark pass |
| Qwen27B · vLLM dev602 | 1372.5 (3/3) | 6.008 | 8,187–8,189 | 140.97 (3/3)/77.73 (3/3) | 163,840 | 20.05 | System `/opt/local-llm/models/Qwen3.8-27B-W4A16-AutoRound-GPTQ` | full benchmark pass |
| Bolt W4A16 · vLLM dev602 | 2777.4 (3/3) | 2.892 | 7,924–7,926 | 37.97 (3/3)/38.04 (3/3) | 262,144 | 43.65 | SATA1 `vLLM-Models/Nemotron-3.5-Bolt-74B-A9B-AutoRound-W4A16` | full benchmark pass |
| Qwen27B · SGLang f84475cc DFlash2 | not measured (0/3) | not measured | not measured | not measured/not measured | 163,840 | 21.34 | System `/opt/local-llm/models/Qwen3.8-27B-W4A16-AutoRound-GPTQ` +`models/drafts/Qwen3.8-27B-DFlash2-W4A16` | VRAM-spill guard during init |
| Qwen27B · vLLM dev435 confirmation | 1384.3 (3/3) | 6.469 | 8,187–8,189 | 141.08 (3/3)/76.71 (3/3) | 163,840 | 20.05 | System `/opt/local-llm/models/Qwen3.8-27B-W4A16-AutoRound-GPTQ` | full benchmark pass (confirmation) |
| Sage native W4A16 · vLLM dev602 | 5091.7 (3/3) | 1.619 | 8,187–8,189 | 148.64 (3/3)/139.62 (3/3) | 65,536 | 20.33 | SATA1 `vLLM-Models/Sage-A1.5-W4A16-AutoRound` (shared between trials) | full text benchmark pass |
| Sage native W4A16 · SGLang AutoRound/Marlin | not measured (0/3) | not measured | not measured | not measured/not measured | 65,536 | 20.33 | SATA1 `vLLM-Models/Sage-A1.5-W4A16-AutoRound` (shared between trials) | incomplete; sampler error |
| Flint AWQ · vLLM dev602 ROCm pilot | not measured (0/3) | not measured | not measured | not measured/not measured | 32,768 | 22.42 | SATA1 `vLLM-Models/Flint-AWQ` | Triton BF16 accumulation compile error |
| Sage native W4A16 · SGLang plain GPTQ | not measured (0/3) | not measured | not measured | not measured/not measured | 65,536 | 20.33 | SATA1 `vLLM-Models/Sage-A1.5-W4A16-AutoRound` (shared between trials) | Triton TF32 precision compile error |
| Sage native W4A16 · SGLang AutoRound/Marlin confirmation | not measured (0/3) | not measured | not measured | not measured/not measured | 65,536 | 20.33 | SATA1 `vLLM-Models/Sage-A1.5-W4A16-AutoRound` (shared between trials) | Marlin HIP compilation error |
| Flint AWQ · vLLM dev602 BF16 fix, thinking off | 5547.8 (3/3) | 1.129 | 6,021–6,025 | 43.22 (3/3)/42.53 (3/3) | 32,768 | 22.42 | SATA1 `vLLM-Models/Flint-AWQ` | full diagnostic pass; thinking off |
| Flint AWQ · vLLM dev602 BF16 fix, reasoning128 | not measured (0/3) | not measured | not measured | 43.25 (3/3)/41.60 (1/3) | 32,768 | 22.42 | SATA1 `vLLM-Models/Flint-AWQ` | reasoning128 partial; swap-write stop |

## Actual outcomes and memory

Host swap I/O is system-wide and conservatively monitored; it is not attributed exclusively to model workers. The inference limits remain 1 MiB/s swapout and 8 MiB/s combined swap I/O over sampled continuous active-workload windows of at least 30 seconds. A rate-guard stop is not a measurement of SSD damage or remaining endurance. Loading/idle PSI does not trigger the inference pressure rule.

| Attempt | Available before /minimum GiB | Load/readiness host swapout GiB | Lifecycle host swapout /swapin GiB | Owned swap peak GiB | Max inference out /total MiB/s | Root outcome |
|---|---:|---:|---:|---:|---:|---|
| Qwen27B · vLLM dev435 | 9.788 / 4.371 | 6.369 | 6.370 / 3.501 | 4.438 | 0.021 / 10.331 | partial; inference swap-I/O stop |
| Bolt W4A16 · vLLM dev435 | 10.284 / 4.860 | 6.606 | 6.606 / 4.446 | 4.835 | 0.004 / 0.415 | full benchmark pass |
| Qwen27B · vLLM dev602 | 10.656 / 4.197 | 5.569 | 5.571 / 3.204 | 4.173 | 0.081 / 1.434 | full benchmark pass |
| Bolt W4A16 · vLLM dev602 | 10.654 / 4.721 | 6.885 | 6.885 / 4.498 | 4.757 | 0.000 / 0.560 | full benchmark pass |
| Qwen27B · SGLang f84475cc DFlash2 | 10.939 / 4.166 | not measured | 5.949 / 2.138 | 4.540 | not measured / not measured | VRAM-spill guard during init |
| Qwen27B · vLLM dev435 confirmation | 10.959 / 5.230 | 5.131 | 5.131 / 2.587 | 3.623 | 0.000 / 2.634 | full benchmark pass (confirmation) |
| Sage native W4A16 · vLLM dev602 | 10.868 / 4.984 | 5.390 | 5.406 / 2.862 | 4.146 | 0.565 / 2.751 | full text benchmark pass |
| Sage native W4A16 · SGLang AutoRound/Marlin | 10.928 / 5.078 | not measured | 6.092 / 0.949 | 4.953 | not measured / not measured | incomplete; sampler error |
| Flint AWQ · vLLM dev602 ROCm pilot | 11.347 / 5.826 | not measured | 3.860 / 4.045 | 2.995 | not measured / not measured | Triton BF16 accumulation compile error |
| Sage native W4A16 · SGLang plain GPTQ | 11.003 / 5.156 | not measured | 6.252 / 2.446 | 4.938 | not measured / not measured | Triton TF32 precision compile error |
| Sage native W4A16 · SGLang AutoRound/Marlin confirmation | 10.978 / 4.656 | not measured | 3.426 / 0.373 | 3.228 | not measured / not measured | Marlin HIP compilation error |
| Flint AWQ · vLLM dev602 BF16 fix, thinking off | 10.946 / 5.748 | 5.105 | 5.105 / 2.855 | 4.297 | 0.000 / 3.833 | full diagnostic pass; thinking off |
| Flint AWQ · vLLM dev602 BF16 fix, reasoning128 | 10.782 / 5.588 | 4.501 | 4.568 / 2.307 | 3.637 | 2.274 / 3.628 | reasoning128 partial; swap-write stop |

**Qwen27B · vLLM dev435:** Completed three code/prose trials and one fresh8K marker probe; the next fresh request stopped at the active-workload combined host-swap-I/O guard (about10.33MiB/s versus8). Swapout write rate was only about0.021MiB/s; the guard includes reads and system-wide activity, so this is not proof of SSD damage or worker-only I/O. Retained as partial despite available timings; no inference speedup is inferred from it.

**Bolt W4A16 · vLLM dev435:** All three code, prose and fresh marker trials plus sustained-inference and lifecycle memory checks passed. Loading swap was permitted; no observed dedicated-VRAM spill or memory-guard violation. This is benchmark evidence, not a runtime-promotion decision.

**Qwen27B · vLLM dev602:** All three code, prose and fresh marker trials plus sustained-inference and lifecycle memory checks passed. Loading swap was permitted; no observed dedicated-VRAM spill or memory-guard violation. This is benchmark evidence, not a runtime-promotion decision.

**Bolt W4A16 · vLLM dev602:** All three code, prose and fresh marker trials plus sustained-inference and lifecycle memory checks passed. Loading swap was permitted; no observed dedicated-VRAM spill or memory-guard violation. This is benchmark evidence, not a runtime-promotion decision.

**Qwen27B · SGLang f84475cc DFlash2:** The normal router latched vram_spill after main/draft loading and returned HTTP503 before generation. Its exact spill size was not logged; the independent lifecycle sampler peaked at zero at a different cadence. The primary guard fault remains a failure. Loading swapout exceeded the former 4GiB cap without rejection; the host-RAM floor was not the stopping cause.

**Qwen27B · vLLM dev435 confirmation:** An unchanged-setting fresh-worker confirmation completed all trials and lifecycle gates. The original paging stop is retained separately. Normal OS/compiler cache state and available RAM differed; this confirmation does not erase the first failure or prove uniform behavior for every cold start.

**Sage native W4A16 · vLLM dev602:** Completed all text/code/prose, fresh-marker, sustained-inference and lifecycle checks on both GPUs, with loading swap allowed. Sage remains an isolated text-only native candidate; vision, full-window quality and GGUF-equivalent quality were not newly validated, so its selected GGUF profile remains.

**Sage native W4A16 · SGLang AutoRound/Marlin:** Loaded the checkpoint, then the independent lifecycle collector recorded a KeyError sampling failure and stopped the owned worker. The primary parent-exit telemetry fault followed. No inference output or conclusive backend result was obtained in this attempt. The separate logging-only confirmation below captures the actual AutoRound/Marlin HIP compile failure; do not relabel this first sample failure as a RAM-floor or measured Marlin failure.

**Flint AWQ · vLLM dev602 ROCm pilot:** Loaded the checkpoint but GPU graph-memory profiling failed in AWQ Triton GEMM: BF16 out_dtype is unsupported by tl.dot. The later parent-exit telemetry error is secondary. This was a software-kernel error, not a loading-swap cap or RAM-floor stop. A separately recorded isolated compatibility pilot follows; the selected GGUF remains unchanged.

**Sage native W4A16 · SGLang plain GPTQ:** With the full retained quantization dictionary overridden to backend=gptq, loading progressed to a Triton compile error: input_precision=tf32 is unsupported on this AMD target (allowed ieee,bf16x3,bf16x6). Child/parent exit then latched the guard. This attempt produced no qualified inference timing; it is a software compatibility result, not a RAM-cap failure.

**Sage native W4A16 · SGLang AutoRound/Marlin confirmation:** The one unchanged-setting confirmation with logging-only sampler diagnostics loaded the checkpoint and reproduced18 HIP compile errors in Marlin repacking, including CUDA-only identifiers and kernel-function-pointer conversion to const void*. No sampler-read errors were recorded in this confirmation; parent-exit telemetry is secondary. No generation timing is available.

**Flint AWQ · vLLM dev602 BF16 fix, thinking off:** The transient BF16 AWQ accumulation fix passed18 dual-GPU numerical cases, then all short, fresh-marker and sustained-inference/lifecycle checks. However the generic text template disabled thinking (observed reasoning_tokens0) and the Qwen-tokenized corpus became only about6K actual Flint input tokens. Retained as a diagnostic, not the matched128-reasoning comparison. Candidate AWQ kernel bytes were restored before GPU-lock release.

**Flint AWQ · vLLM dev602 BF16 fix, reasoning128:** Explicit thinking=True with budget128 reported exactly128 reasoning tokens in all four completed timed short trials. All three code trials and one prose trial completed; before any fresh model-tokenized8K probe or full sustained test, both guard views latched inference_swapout_rate (peak2.274MiB/s, above1MiB/s; combined3.628MiB/s, below8MiB/s). The host-RAM floor and zero-VRAM-spill guard did not cause this stop. Keep timings partial; this does not establish SSD damage or a stable native replacement. The18-case numerical precheck passed and candidate kernel bytes were restored.

## Setup correction

Three initial native launches were rejected before payload execution because the new wrapper used `MemorySwapMax=max`, which systemd does not accept. They are retained separately as setup failures in the numeric record, not model incompatibility or memory evidence. Fresh corrected runs use `MemorySwapMax=infinity`; the cgroup readback remains `memory.swap.max=max`. The same syntax correction is applied to the three normal launchers, current policy docs and H3 follow-up. A real CPU cgroup regression verifies unlimited swap with unchanged RAM high/max caps.

## Method and limits

Five initial framework attempts and one unchanged-setting Qwen baseline confirmation used the normal selected launchers, with only the existing isolated vLLM environment override for dev602. Four initial native alternatives plus diagnostic/compatibility confirmations retained their TP2, BF16 activation/KV, context and speculation settings: Sage 64K/MTP3 on vLLM and SGLang, and Flint 32K/AWQ with the requested 128-token reasoning budget on the retained isolated ROCm pilot. Sage native tests are language-only; they cannot replace the selected GGUF vision profile without separate validation.

Same named models, prompts and context are compared, but native INT4 checkpoints and GGUFs differ in quantization and kernels. No equal-quality or numerical-parity claim is inferred. Native Sage plain-GPTQ uses the existing full quantization-config override, without changing checkpoint files.

The existing numerical performance, marker and full-lifecycle memory comparator passes dev602 against both complete dev435 references, using the Qwen confirmation. This is benchmark-gate evidence; normal API/tool/vision and full-window integration were not freshly qualified for a runtime promotion. The original Qwen baseline failure is retained alongside its unchanged-setting confirmation; normal compiler/OS cache state may differ. The planned measurement was one excluded short warmup per task, three 256-output code trials, three 256-output prose trials, three unique salted ~8K marker requests, and at least 35 seconds of back-to-back compute for the inference rate window. Initial model loading/arithmetic readiness were excluded; measured TTFT does not include an unloaded cold start. The load/readiness sampling span and full elapsed lifecycle seconds are retained separately in the numeric record. Raw timings distinguish first output and first visible answer. Complete marker/cache/usage evidence and exact short trial counts remain in the numeric record; absent/incomplete evidence is never a pass.

A short disk-backed TMPDIR avoids the earlier Unix-socket path-length failure. No apps were force-closed, no global swap/swappiness setting changed, no weights downloaded/removed, and recorded model/profile fingerprints and selected engine pins stayed unchanged; the launcher syntax correction is recorded separately. GPU-LOCK covered device probing, startup, generation and shutdown. All owned workers were cleaned up before lock release.

## Isolated Flint AWQ compatibility pilot

The initial Flint attempt failed because AWQ Triton GEMM requested unsupported BF16 dot accumulation. The isolated fix retained BF16 model inputs/outputs, used FP32 dot accumulation and IEEE precision, and retained the final output cast. Both GPUs were checked against unchanged AWQ dequantization followed by PyTorch FP32 matmul rounded to BF16, with fixed rtol/atol 0.01. These are tolerance checks, not bit-exact or full-model quality tests. The temporary AWQ file was restored before each GPU-lock release; no kernel fix was installed in production.

| Variant | Numerical checks | Maximum absolute error | Kernel restored |
|---|---:|---:|---|
| Thinking off diagnostic | 18/18 | 0.015625 | True |
| Reasoning enabled, budget128 | 18/18 | 0.015625 | True |

The first BF16-fix Flint run used the generic disabled-thinking text template and only about6K actual Flint input tokens from the Qwen-tokenized corpus. It is a diagnostic, not the matched128-budget comparison. The final variant explicitly enabled thinking and requested budget128; all four completed timed short trials reported exactly128 reasoning tokens. It prepared model-tokenized~8K prompts, but the inference swap-write guard stopped the run before those probes.


## Full-lifecycle thermals

GPU triples are edge /junction /memory °C. CPU is package peak. Samples cover load, compute (when reached), failure and shutdown. Sensor/SMU flags are sampled observations, not measured slowdown or proof of SSD wear; raw private logs are excluded.

| Attempt | Samples/errors | GPU0 °C | GPU1 °C | CPU °C |
|---|---:|---|---|---:|
| Qwen27B · vLLM dev435 | 133/0 | 50.0 / 73.0 / 50.0 | 43.0 / 68.0 / 59.0 | 100.0 |
| Bolt W4A16 · vLLM dev435 | 360/0 | 57.0 / 78.0 / 62.0 | 44.0 / 69.0 / 61.0 | 100.0 |
| Qwen27B · vLLM dev602 | 306/0 | 63.0 / 82.0 / 74.0 | 48.0 / 77.0 / 68.0 | 100.0 |
| Bolt W4A16 · vLLM dev602 | 351/0 | 59.0 / 79.0 / 66.0 | 45.0 / 71.0 / 66.0 | 100.0 |
| Qwen27B · SGLang f84475cc DFlash2 | 185/0 | 55.0 / 62.0 / 61.0 | 38.0 / 49.0 / 62.0 | 87.0 |
| Qwen27B · vLLM dev435 confirmation | 161/0 | 61.0 / 78.0 / 70.0 | 47.0 / 72.0 / 68.0 | 100.0 |
| Sage native W4A16 · vLLM dev602 | 278/0 | 56.0 / 71.0 / 60.0 | 44.0 / 65.0 / 62.0 | 100.0 |
| Sage native W4A16 · SGLang AutoRound/Marlin | 78/0 | 53.0 / 61.0 / 58.0 | 39.0 / 52.0 / 60.0 | 84.0 |
| Flint AWQ · vLLM dev602 ROCm pilot | 177/0 | 39.0 / 45.0 / 42.0 | 27.0 / 37.0 / 50.0 | 88.0 |
| Sage native W4A16 · SGLang plain GPTQ | 114/0 | 32.0 / 39.0 / 36.0 | 24.0 / 36.0 / 48.0 | 84.0 |
| Sage native W4A16 · SGLang AutoRound/Marlin confirmation | 76/0 | 30.0 / 36.0 / 34.0 | 24.0 / 35.0 / 46.0 | 81.0 |
| Flint AWQ · vLLM dev602 BF16 fix, thinking off | 231/0 | 53.0 / 74.0 / 56.0 | 43.0 / 69.0 / 60.0 | 100.0 |
| Flint AWQ · vLLM dev602 BF16 fix, reasoning128 | 147/0 | 47.0 / 57.0 / 48.0 | 37.0 / 50.0 / 55.0 | 100.0 |

## Verification

**170 CPU regression tests passed in each checkout**, including a real scope with `MemorySwapMax=infinity` reading back as kernel `max` while retaining RAM caps. Result validation checks observed medians, trial counts, complete-pass requirements, policy versions, dual-GPU evidence, cleanup and sanitized publication fields. Both transient AWQ kernel edits were independently verified restored byte-for-byte.

## MoE models with CPU RAM offload

No models in this category were retested. Existing selected profiles and physical-RAM requirements remain.

## MoE models with SSD streaming

No models in this category were retested. Existing profiles remain. The separate H3 follow-up still waits for a real OS-visible RAM upgrade; no H3 generation was retried in this work.
