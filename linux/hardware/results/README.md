# Current benchmark results

Current hardware: i9-13900KS,64 GB RAM, two RX 7900 XTX 24 GB. Thirteen selectable
profiles are covered: eleven shared-method rows and two fixed-8K Super workloads.

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
for its tokenizer dependency. Muse alone permits `--allow-marker-failure`, with
the failed marker trials retained. Raw logs and generated answers remain private.
Functional normal-launcher proofs are validation only, not throughput results.
Configured context is separate from actual tested input; phase PP is separate
from external SSE TTFT and input/TTFT proxies.
