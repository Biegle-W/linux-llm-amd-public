# Current benchmark results

Current hardware: i9-13900KS,64 GB RAM, two RX 7900 XTX 24 GB. Ten selectable
profiles remain after Muse Q4 and Super Q4 retirement: nine shared-method profiles and Super IQ3 with its separate fixed-8K workload. Historical batches keep all original results.

- [Normal launchers and native frontend checks](launcher-validation-2026-10-20.json): functional-only proofs for SGLang/vLLM160K, Strata Q3 and both Maya models, original UI assets and managed runtime controls.
- [GLM Maya-S/S24 ABBA results](maya-s-vs-s24-2026-10-20.json), [decision and method](../MAYA-S-VS-S24-2026-10-20.md): six samples/task/quant at32K; selected Maya-S. DeepSeek measurements are unchanged.
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
