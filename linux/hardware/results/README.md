# Current benchmark results

- [Maya1.1.24 update — October23](maya-update-2026-10-23.json): four matched source19/24 arms, all trials/native PP/SSE TTFT+decode, near31.5K/history, guards/thermals/known kernel failures and normal integration; [report](../MAYA-UPDATE-2026-10-23.md).

- [Ornith122B metadata/tensor inspection](ornith-122b-assessment-2026-10-21.json), [assessment](../ORNITH-122B-ASSESSMENT-2026-10-21.md): research-only memory/quant candidates, **no inference or throughput measurements**.

- [llama.cpp batch sweep](llama-batch-sweep-2026-10-22.json), [report](../LLAMA-BATCH-SWEEP-2026-10-22.md): all five llama.cpp profiles: Ornith/Qwen3.6/Empero/Sage 4096/4096, Super 2048/1024; prefill 4.6–13.6×, decode within 2%; Ornith 8192 and Super ≥2048 break the 3 GiB/card guard.
- [Slow-model optimization research](../SLOW-MODEL-OPTIMIZATION-RESEARCH-2026-10-22.md): community sources only; top lead is llama.cpp ubatch (128 today) × op-offload threshold for CPU-expert MoE prefill.
- [Model hub live validation](model-hub-2026-10-22.json), [report](../MODEL-HUB-2026-10-22.md): any model via 127.0.0.1:30100 or the gateway starts/switches its backend on demand; waits for in-flight replies; refuses under GPU-LOCK.
- [ROCm 7.2.4 / 7.14.1 vs 7.2.3](rocm-724-7141-2026-10-22.json), [report](../ROCM-724-7141-2026-10-22.md): vLLM Qwen, llama Qwen3.6/Sage, Ornith; all within ±3% (Sage 7.14.1 seed-confirmation −0.05%); retain 7.2.3.
- [Bolt vLLM vs llama.cpp](bolt-vllm-2026-10-21.json), [report](../BOLT-VLLM-2026-10-21.md): AutoRound W4A16 on vLLM TP2 38.0/37.9 decode (+3%), 2,910 t/s prefill vs 224 (13×), 262K window with 255K retrieval pass; **promoted** as `nemotron-3.5-bolt-vllm` (router checks and production benchmark 37.32/37.21, 2,959 PP).
- [vLLM alternatives for Bolt/Sage](../VLLM-ALTERNATIVES-BOLT-SAGE-2026-10-21.md): research only; Bolt AutoRound W4A16 is the one test candidate, Sage has no ready 4-bit vLLM build, FP8 not recommended on RDNA3.
- [Ornith122B Q4 test](ornith-122b-test-2026-10-21.json), [report](../ORNITH-122B-TEST-2026-10-21.md): test-only, both GPUs/32K; MTP off 11.43/13.34/52.68, MTP3 rejected (−27.3%); 31K retrieval/history/vision pass.
- [Sage-A1.5 three-arm tests](sage-a15-2026-10-21.json), [report](../SAGE-A15-2026-10-21.md): test-only Q4/MTP/SDK7-vs-10.1, 64K retrieval/history, vision and full thermal coverage; ten production profiles unchanged.

- [ROCm10.1 six-engine trials](rocm101-2026-10-21.json), [decision and methods](../ROCM101-2026-10-21.md): fresh exact-stack controls, reverse-order/seed confirmation, normal graphics and all failed/partial arms.

- [Maya web switching and DSH reuse](maya-web-switching-2026-10-21.json), [report](../MAYA-WEB-SWITCHING-2026-10-21.md): functional-only UI/SSE/reload/security checks; no new throughput rates.
- [Other-engine ROCm10/table comparison](rocm10-other-engines-2026-10-20.json), [method and decision](../ROCM10-OTHER-ENGINES-2026-10-20.md): fresh exact-production SDK7 controls plus isolated SDK10/Strata-table candidates, all trials/temperatures; production unchanged.

- [Maya v1.1.19/ROCm comparison](maya-rocm10-2026-10-20.json), [decision](../MAYA-ROCM10-2026-10-20.md): SDK7 retained, both NVMe Maya-S packs tested; six GLM /three DeepSeek trials, near32K and normal UI/API/switchback pass. SDK10 negative/stalled arms retained.

- [Strata user-selected 5 GiB startup floor](../STRATA-STARTUP5-2026-10-20.md): 0.1.46.1 promoted; all candidate/near256K and actualDesktop/nativeUI/API gates pass. Fresh912.2PP,9.015s freshTTFT,75.28/50.31decode; [all trials](strata-startup5-2026-10-20.json). Former6GiB failures remain historical.

Current hardware: i9-13900KS,64 GB RAM, two RX 7900 XTX 24 GB. Ten selectable
profiles remain after Muse Q4 and Super Q4 retirement: nine shared-method profiles and Super IQ3 with its separate fixed-8K workload. Historical batches keep all original results.

- [Strata Linux app/update admission evidence](strata-linux-update-2026-10-20.json), [scope and limits](../STRATA-LINUX-UPDATE-2026-10-20.md): app0.2.1 installed; Intel primary rendering verified after login; former6GiB startup rule failed twice (exact loaded5.388/6.269GiB free). These historical failures are superseded by the passed5GiB rollout above; old0.1.45 measurements remain dated.

- [Normal launchers and native frontend checks](launcher-validation-2026-10-20.json): functional-only proofs for SGLang/vLLM160K, Strata Q3 and both Maya models, original UI assets and managed runtime controls.
- [GLM Maya-S/S24 ABBA results](maya-s-vs-s24-2026-10-20.json), [decision and method](../MAYA-S-VS-S24-2026-10-20.md): six samples/task/quant at32K; selected Maya-S. DeepSeek measurements are unchanged.
- [DeepSeek DSpark production retest](deepseek-dspark-production-2026-10-20.json), [decision](../DEEPSEEK-DSPARK-2026-10-20.md):
  32K, 24 threads; DSpark −20.4% geometric mean (code −33%, prose −22%) despite 85% draft acceptance. Rejected.
- [Super IQ3 NVMe load and SSD-streaming trial](super-nvme-load-2026-10-20.json), [decision](../SUPER-NVME-LOAD-2026-10-20.md):
  NVMe load 42.2 s vs 112.1 s, with identical inference (−0.12% geometric mean); mmap streaming rejected (forced tool-call failure).
- [Requested model retirement](model-retirement-2026-10-20.json): four exact GGUF files, 95.726 GiB, retained dependency checks.
- [Qwen INT4 context candidates and selected trials](qwen-int4-context-2026-10-20.json), [selection report](../QWEN-INT4-CONTEXT-2026-10-20.md): actual long inputs, full-history follow-ups, three-trial short/8K timings and rejected guard case.
- [Current report](../CURRENT-AMD-BENCHMARKS.md) and [CPU/RAM/pool validation](../CPU-RAM-PROFILES-2026-10-20.md).
- [Original eleven-profile numeric batch](dual-amd-i9-64gb-2026-10-20.json): all trials, exact measured source revisions, actual counts, timing definitions, memory, both Strata pools and normal functional proofs.
- [Maya added two-profile batch](maya-dual-amd-2026-10-20.json) and [Maya report](../MAYA-2026-10-20.md): final RAM/GPU reserves, exact inputs/outputs, all trials, screening controls, numerical limits and normal API/switchback proofs.
- [Earlier i9 baseline/selection evidence](dual-amd-i9-baseline-2026-10-20.json):31288c9, old SATA Strata pack; separate from corrected-NVMe tests.
- [Verified model storage](streaming-storage-2026-10-20.json): checksums and asset scope, no model weights.
- [October 19 i5/32 GB report](../AMD-BENCHMARKS-2026-10-19.md), [nine-profile numeric batch](current-amd-2026-10-19.json) and [Super IQ3 batch](nemotron-super-2026-10-19.json).
- [Complete dated history](../BENCHMARK-HISTORY.md), including NVIDIA/Windows and older capacity tests.

Use [benchmark-current-amd.py](../benchmark-current-amd.py) against one already
running normal backend at a time. It does not launch models or disable guards.
Use `--kind llama|sglang|vllm|strata|maya`, `--model API_ID` for one profile, and an
output beneath ignored `hardware/generated/`. Run with the existing vLLM Python
for its tokenizer dependency. The legacy Muse `--allow-marker-failure` option is for historical replay only;
it does not restore the retired profile. Raw logs and generated answers remain private.
Functional normal-launcher proofs are validation only, not throughput results.
Configured context is separate from actual tested input; phase PP is separate
from external SSE TTFT and input/TTFT proxies.
