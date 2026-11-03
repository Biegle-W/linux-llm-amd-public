# No-switch validation — November 3, 2026

**In progress.** The Broadcom PCIe switch is absent; both 24 GB RX 7900 XTX cards remain. The two actual upstream paths are Gen4 x16 and Gen4 x4. Driver P2P stays off. Logical placement for the repeated Strata/llama checks retains PowerColor first and Sapphire second despite changed bus/device order. No production profile, source pin, recurring schedule or resource guard is changed by these isolated tests.

The guarded basic stage passed: SSD SMART/live-temperature admission, three address-dependent patterns over a 2 GiB host-RAM subset, three fresh bidirectional HIP P2P-off checks, and three checked local kernel/read/write patterns on each GPU. This is bounded smoke coverage, not full DIMM or sustained hardware certification.

| Stage | Current result | Load seconds | DSH output tokens |
| --- | --- | ---: | ---: |
| hardware-smoke | passed | — | — |
| llama-empero | passed-one-short-DSH-check | 47.957 | 76 |
| llama-flint | passed-one-short-DSH-check | 51.954 | 159 |
| strata-short | passed-one-short-DSH-check-with-direct-IO | 77.855 | 77 |
| vllm-bolt | starting | — | — |
| vllm-qwen | failed | — | — |
| vllm-sage | passed-one-short-DSH-check | 83.463 | 75 |

Successful DSH stages require exactly one read tool call, matching tool-result IDs, two model steps and the exact fixture marker in the final answer. They use retained models/runtime pins and existing memory, VRAM, SSD, thermal, progress and owned-cleanup protections. The short loading budget is 210 s with 240 s total caps; first-output/request limits remain 20/30 s. Graphics use their separately retained fixed workflow request protocol, one run per graph. No GPU workloads run concurrently, and a new GPU fault or incomplete owned cleanup stops later stages.

Removed Super IQ3 and the old DeepSeek XS backing are unavailable; no replacement download/conversion is automatic. Held profiles with existing assets are assessed only in isolated qualification views, leaving production flags unchanged. Current owner-policy (8), P2P (40), llama (18) and shared-storage (26) CPU checks pass. Historical memory/swap suites require both explicit legacy-validation opt-ins; a few stale fixture/default expectations remain and are recorded rather than changing live guards to satisfy them.

Initial positive results do not identify the earlier failure cause or establish sustained stability. Remaining model/graphics stages continue under the same serial ownership discipline. [Machine-readable status](results/no-switch-validation-2026-11-03.json).
