# Headless known-passed model campaign — November 5, 2026

[Sapphire switch/P2P evidence audit](SAPPHIRE-SWITCH-P2P-EVIDENCE-AUDIT-2026-11-06.md): completed direct HIP/IPC and RCCL P2P transfers passed before the headless failure. The model faulting operation and transport remain unlogged. An older driver-P2P-disabled Strata qualification also failed; its workload/software state differs and site-specific failure evidence remains private. Recent Sapphire/logical-GPU1 identity correction and all guard failures remain preserved. [Qwen backend comparison](QWEN-VLLM-SGLANG-TRIGGER-COMPARISON-2026-11-05.md). Read-only audit; no retry or runtime change.

**The headless campaign reproduced Sapphire PCI/SMU failure during SGLang Qwen DFlash2 startup.** Four model tool checks completed first; three had clean guard passes and Qwen vLLM had a separately preserved harness result-path guard failure after its successful tool check and clean cleanup. SGLang was the fifth route attempted. Nine routes were never run. The campaign is stopped, the new fault hold remains, and no model was retried. [Structured result](results/AMD-HEADLESS-KNOWN-PASSED-MODELS-2026-11-05.json).

## Scope and completed work

The owner disconnected the physical monitor and requested all models previously tested successfully. The plan covered the14 enabled selected routes across11 weight sets, retaining normal source/weight/profile/context/math/reserve settings and excluding failed or retired candidates. Read-only admission verified patched kernel `7.0.14-42-vmpt1`, its AMDGPU module, board identities, identity IOMMU domains, six-bridge ACS `0x0011`, storage/temperature health, ownership and empty KFD. Every physical output was disconnected and disabled; disabled virtual writeback connectors were not treated as monitors. The headless condition was checked before each executed stage.

All four fresh same-boot peer prerequisites passed: capability, local correctness, direct/IPC integrity, and RCCL P2P/IPC all-reduce/all-gather. Normal managed short DSH read-tool checks then ran sequentially. Context allocations stayed configured as shown; these are short functional checks, not full-window or sustained-stability validation.

| # | Selected route | Configured context | Outcome | Load s |
|---|---|---:|---|---:|
| 1 | `empero-qwen3.8-35b-a3b` | 262,144 | Tool + guard passed | 48.053 |
| 2 | `flint-40b-a2.5b` | 32,768 | Tool + guard passed | 51.794 |
| 3 | `ornith-1.5-122b` | 32,768 | Tool + guard passed | 150.043 |
| 4 | `qwen3.8-27b-vllm` | 163,840 | Tool passed; guard administrative failure | 93.535 |
| 5 | `qwen3.8-27b-sglang-dflash2` | 163,840 | GPU/SMU startup failure | — |
| 6 | `nemotron-3.5-bolt-vllm` | 262,144 | Unrun; blocked | — |
| 7 | `sage-a1.5` | 65,536 | Unrun; blocked | — |
| 8 | `qwen3.8-flash-next-iq3_xxs` | 262,144 | Unrun; blocked | — |
| 9 | `qwen3.8-flash-next-unsloth-iq1_m` | 262,144 | Unrun; blocked | — |
| 10 | `glm-5.3-flash-maya` | 32,768 | Unrun; blocked | — |
| 11 | `deepseek-v4.1-flash-1017-maya-coder-iq2-xxs` | 32,768 | Unrun; blocked | — |
| 12 | `deepseek-v4.1-flash-1017-strata-coder-iq2-xxs` | 32,768 | Unrun; blocked | — |
| 13 | `deepseek-v4.1-flash-1017-strata-unsloth-q1` | 32,768 | Unrun; blocked | — |
| 14 | `deepseek-v4.1-flash-1017-maya-unsloth-q1` | 32,768 | Unrun; blocked | — |

**The Maya DeepSeek no-store headless case was last in the plan and was not reached.** No Maya or Strata model case ran in this campaign.

Qwen vLLM completed its strict two-step read-tool roundtrip with the correct marker, two completed requests and clean owned cleanup. The surrounding guard nevertheless failed because the newly prepared nested case omitted the standard `active-terminal.private.json` result pointer. That administrative failure remains failed. After read-only review established empty cgroups/KFD, unchanged inputs and no GPU/watchdog fault, the pointer was added only to the10 then-unrun stages. Only those stages continued under the existing all-models request, with the administrative hold preserved through owned handover. The original four model checks were never repeated. Canonical guard code and limits were unchanged.

## Headless GPU failure

Times are America/Toronto (EST).

| Event | Evidence |
|---|---|
| 23:00:57 | SGLang Qwen DFlash2 case started. |
| 23:01:29–30 | Worker log reports weights/cache/graph initialization and API startup. Outer readiness attestation was not reached. |
| 23:01:30.761818 | `amdgpu 0000:0b:00.0: device lost from bus!` — Sapphire, the retained logical GPU1 role. |
| Immediately afterward | SMU `TransferTableSmu2Dram(18)` bus error, response `0xFFFFFFFF`, then hanged-state messages. |
| 23:01:33–44 | Five MES messages requested a GPU reset. These messages do not establish that a reset completed. |
| Guard completion | Failed GPU/bus guard and failed owned cleanup; four KFD clients remained. Zero requests were sent. No heartbeat-watchdog fault was recorded for this case. |
| 23:02:05 | Last persisted kernel faults remain SMU/metrics failures. |
| Later reboot | Patched kernel again; KFD empty. The original failed cleanup result remains failed. No further model work started. |

The112 complete telemetry samples recorded minimum available host RAM46.997GiB, per-card free VRAM minima5.346/5.339GiB, CPU package peak68°C, GPU sensor peak46°C, and zero maximum recorded owned swap/spill. There was no recorded OOM or thermal-limit event. The15-second cleanup limit and all existing six-second heartbeat,100°C,1GiBhost/128MiBper-card live floors, startup reserves, spill/swap and ownership protections remained.

The saved kernel journal contains repeated SMU errors and MES reset requests, but no recorded DMCUB, vblank timeout or CPU hard/soft-lockup sequence for this headless case. Initial AER-enabled boot messages are not PCIe errors; no separate AER/DPC/PCIe error report was found in the saved trial window. The journal ending shortly after the failure limits conclusions about the later host interruption.

## What this changes

A **currently connected physical monitor is not required** for the observed Sapphire lost-bus/SMU failure. A Maya-specific36GBRAM-store option is also not required: a different engine/model route failed headless. This test does not rule out Display Core or retained boot/hotplug/power state: the monitor was disconnected within an existing boot, not followed by a cold headless boot, and Display Core remained loaded.

The repeating failure point is Sapphire PCI/SMU access, across workloads while the physical card and logical-GPU1 role remain correlated. The evidence still does not distinguish physical-card, runtime-role, PCIe/power-state/firmware or driver cause. Four preceding successful short checks and passed peers demonstrate intermittent/workload-sensitive behavior, not sustained stability.

All managed input/source pins and older immutable failure artifacts remain unchanged. Exact pre-campaign and administrative holds were archived before owned handovers; the latest hardware fault hold is retained. Full kernel/system journals, worker log and273 evidence files are content-pinned privately. All14 catalog entries and prior pins remain; nine planned checks are blocked, with no retry, promotion, queue restart or new recurring schedule. The current post-crash boot has no fresh peer/model qualification.
