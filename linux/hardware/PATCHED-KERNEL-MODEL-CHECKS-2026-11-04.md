# Patched-kernel original-plan model checks

The six prepared checks are complete. The conditional queue is at **stopped; review required**. Tests are isolated on `7.0.14-42-vmpt1`, after the four guarded peer/IPC/RCCL checks passed.

| Model stage | Outcome so far | Load seconds |
|---|---|---:|
| strata-qwen-mtp | passed-one-short-DSH-check | 117.724 |
| maya-coder | passed-one-short-DSH-check | 33.25 |
| strata-coder | passed-one-short-DSH-check | 17.451 |
| strata-q1 | decode progress stalled | 41.532 |
| maya-q1 | decode progress stalled | 53.3 |
| maya-glm | decode progress stalled | 69.574 |

All recorded stages have verified owned cleanup. Decode-stall stops retain the three-second guard and do not qualify a complete tool check. Conditional stages continue only after safe boundaries; hardware, thermal, monitor or cleanup faults stop the queue.

PLE and Super INT4 EP2 were explicitly included after admission. Their metadata/source checks pass; fresh idle admission passed before launch, and capacity is checked again in each worker. The original 900-second loading/990-second stage limits still apply. Prior PLE/Super loading-budget exhaustion remains inconclusive, and no blind retry or budget extension is authorized. The isolated vLLM wrapper applies P2P and device-order overrides after the production ROCm environment; global configuration is unchanged.

Original math, source/weight pins and custom all-reduce exclusions remain. Actual transport must be established from each engine log. These short tests do not establish sustained stability or isolate the effect of the concurrent slot/kernel changes.
