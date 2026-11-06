# DeepSeek no-store loading failure — November 5, 2026

The owner-requested single Maya DeepSeek UD-IQ1_S baseline **failed during loading without `--ssd-cache36`**. It never became ready and recorded zero requests. A later reboot returned to the owner-selected patched kernel. The latest watchdog fault hold remains; no retry or promotion occurred. [Structured result](results/MAYA-DEEPSEEK-NO-STORE-2026-11-05.json).

## What ran

The installed `7.0.14-42-vmpt1` kernel is now the persistent inference default, with stock retained as an installed manual fallback. The privileged boot operation verified all 6,901 installed modules, boot hashes and existing unrelated boot configuration before selecting it. Inference admission now requires that release and loaded AMDGPU source version `140B8E9A04991D891F18CD3` before handover/loading; the updater defers other kernels. This kernel selection is an owner preference, not a proved crash fix.

Read-only admission on the trial boot verified the module, six-bridge ACS `0x0011`, both board identities, identity IOMMU domains, empty KFD, health and ownership. Four fresh same-boot prerequisites passed: peer capability, local correctness, direct/IPC integrity, and RCCL P2P/IPC all-reduce/all-gather on both ranks.

An initial RCCL launcher failed before RCCL executed because the new case omitted `run_rccl.sh`. That failed guard and administrative fault hold were preserved. The owner explicitly approved a distinct corrected case, which passed; the three already-passed prerequisites were not repeated. The original stopped queue remains unchanged; a separate reviewed queue records the four actual passes.

The model case retained Maya source `c1670044bbc09310f35f9d00f7596c50ae8a38f1`, the same weights, PowerColor-then-Sapphire logical placement, 32,768 context and reserves. Its argument, environment and qualification-record append/update maps were empty. The previously cleared Lt tuning file was absent before loading, so this was a cold-cache trial rather than an exact replay of the morning pass. All prepared case hashes matched before binding only the verified boot and fresh peer queue. All 100°C, 1 GiB host/128 MiB per-card live floors, startup reserves, dedicated-VRAM spill, owned swap, six-second heartbeat and 15-second owned cleanup protections remained.

## Recorded sequence

Times below are America/Toronto (EST).

| Event | Recorded outcome |
|---|---|
| 21:33:24 | Guarded no-store case started loading. |
| 21:33:39.831128 | Driver reported `amdgpu 0000:0b:00.0: device lost from bus!`. |
| Immediately afterward | SMU `TransferTableSmu2Dram(18)` bus error, response `0xFFFFFFFF`, then SMU hanged-state errors. |
| About 6.666 seconds after the first fault | Independent supervisor latched `supervisor heartbeat missing`. |
| Owned cleanup | Failed: worker cgroup remained populated and one KFD client remained at the original cleanup deadline. |
| Later reboot | KFD became empty; the failed cleanup result remains failed. Patched kernel booted again, confirming continued persistent selection. |

The first fault identifies **Sapphire at `0b:00.0`, logical model GPU1**. PowerColor was logical GPU0 at `13:00.0`. Telemetry enumeration order differs from model logical order; do not identify the card from a telemetry array index alone.

Recorded minimum available host RAM was 57.256 GiB; per-card free VRAM minima were 20.346 GiB at `0b:00.0` and 20.439 GiB at `13:00.0`. Maximum recorded owned swap and spill were both zero. The 48 complete telemetry samples recorded CPU package peak 48°C and GPU sensor peak 42°C; one trailing sample is incomplete. These samples show no recorded resource exhaustion or thermal limit, but cannot exclude an unobserved transient.

## Interpretation and evidence limits

This reproduces the failure without the 36 GB RAM store: that option is not necessary for the observed failure. The patched kernel and passed short peer checks did not prevent this model-loading failure. Same Sapphire/logical-GPU1 correlation remains; these symptoms do not establish a defective physical card, fixed bad slot, power fault or driver root cause. The first recorded fault precedes the watchdog, so the watchdog is a later response in the saved sequence.

The persisted kernel journal ends at the initial SMU fault. This boot does not provide a saved CPU hard/soft-lockup trace; do not copy that conclusion from the earlier crash. The guard retained additional repeated faults. Several trial-local engine/profile/wrapper/rollback files are zero length after the abrupt reboot and remain untouched; readiness and exact last engine phase cannot be reconstructed from those files. The prepared input seal and empty append maps are retained, and the live original model profile and registry record both match their exact pretrial hashes after reboot, with no candidate owner.

Full kernel/system journals, original and latest fault holds, failed guards and incomplete artifacts are preserved operationally with content hashes. The earlier 36 GB failure remains unchanged. The new current boot has no fresh peer/model qualification. All 14 routes and prior pins remain; RAM40, Radiance and other trials remain unrun/blocked. No recurring schedule was created. Keep the new fault hold and require owner review before further GPU work.

Kernel-admission CPU verification: six focused tests plus 41 existing native admission tests passed; no GPU workload was used for these tests.
