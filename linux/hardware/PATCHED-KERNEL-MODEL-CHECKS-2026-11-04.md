# Patched-kernel original-plan model checks

**Later authorized checks:** PLE/Super were subsequently tested in a separate 100°C queue; [latest outcomes](PLE-SUPER-100C-2026-11-04.md). Original outcomes below are unchanged.

**Subsequent policy change:** current software temperature ceilings are now 100°C; the results below retain their original guard thresholds. The hold/STOP remain and no model was rerun. [Current temperature policy](TEMPERATURE-GUARDS-2026-11-04.md).

The campaign stopped at PLE's retained **85°C CPU guard**, with a **sampled 87°C** maximum. PLE unloaded; **Super INT4 EP2 never started and remains blocked**. No further GPU work or automatic retry is queued. Tests used `7.0.14-42-vmpt1`, after four bounded peer/IPC/RCCL checks passed.

| Model stage | Final outcome | Load seconds |
|---|---|---:|
| strata-qwen-mtp | Strict short DSH tool check passed | 117.724 |
| maya-coder | Strict short DSH tool check passed | 33.250 |
| strata-coder | Strict short DSH tool check passed | 17.451 |
| strata-q1 | Three-second decode-stall guard; no complete tool pass | 41.532 |
| maya-q1 | Three-second decode-stall guard; no complete tool pass | 53.300 |
| maya-glm | Three-second decode-stall guard; no complete tool pass | 69.574 |
| vllm-ple-file-gather | CPU thermal guard; unloaded; no load/tool qualification | — |
| super-int4-ep2 | Blocked by preceding thermal stop; never started | — |

Three strict short tool checks passed, three stopped at the unchanged decode guard, PLE stopped at the CPU thermal boundary, and Super was blocked. A guard stop is not a complete tool pass. PLE did not establish loading readiness or complete inference. All attempted stages have verified owned cleanup. Raw queue/result labels still contain intermediate `starting`/`admission pending` values; this final summary reconciles them against the terminal guard record and independent cleanup audit, preserving the raw records.

PLE and Super passed fresh idle source/capacity admission before the conditional queue. Admission is not load qualification. Prior attempts that exhausted their 900-second loading budgets remain inconclusive. The original 900-second loading/990-second stage caps remain, along with the 30-second output budget from first output, six-second heartbeat, three-second decode-stall and 15-second cleanup guards. No first-token prefill cutoff was added or budget extended.

Final read-only verification at 2026-11-04T22:41:57.905016+00:00 found all 19 recorded owned scopes inactive and empty, both queue controllers exited, no KFD clients, and both GPUs at 0% busy. The current-boot journal scan found no GPU/reset/bus-loss/OOM or kernel-crash pattern. Expected AMDGPU source identity is loaded and its module taint field is empty. The global kernel taint value is **4**; its cause/onset was not established by this audit, so this is not a claim of a globally untainted kernel. CPU package temperature had returned to 36°C; cooling does not release the thermal stop.

The persistent fault hold and conditional STOP sentinel remain. Model profiles and pinned scoped inputs match the retained hashes. The final stock `7.0.0-42-generic` default override is unchanged and the one-shot entry is cleared. Current generated GRUB configuration could not be reread without interactive administrator authentication; retain the preboot privileged validation and current override evidence. Runtime services, guards, source/weight pins and paused schedules were not changed.

The isolated vLLM wrapper applies P2P and device-order overrides after the production ROCm environment. Global configuration, original math, hostcall settings and native custom all-reduce exclusions remain. System peer/IPC/RCCL transport passed separately; enabling P2P does not alone establish each model's actual transport. These short checks establish neither sustained stability nor a causal fix, especially with concurrent slot/kernel changes. No production promotion occurred.

Next action: retain the hold and STOP, review/address the CPU thermal boundary, and obtain separate authorization plus fresh admission before any later GPU check. Do not retry PLE or launch Super automatically.

[Machine-readable final outcomes](results/patched-kernel-model-checks-2026-11-04.json).
