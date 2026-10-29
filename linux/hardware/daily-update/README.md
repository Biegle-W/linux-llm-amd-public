# Daily engine update

## Live status — October 29

The configured 03:00 timer is absent/inactive and the service inactive. A read-only check found newer llama.cpp, vLLM, Strata Qwen, Maya and Strata DeepSeek sources; the selected SGLang AMD fork is current. The registry includes six components; graphics/ComfyUI/H3 are not included. Manual vLLM runtime pins remain excluded from global comparisons. [Audit and exact selected/upstream references](../ENGINE-UPDATE-AUDIT-2026-10-29.md). No update or schedule activation occurred.

## Current user swap policy — October28

Use [loading-swap-v3](../SWAP-TASK-CONTINUITY-2026-10-28.md). Loading/parked swap and reads are allowed. Rates and PSI are advisory by default. An optional swap stop requires an explicit write budget plus matched measured slowdown; legacy validation needs its second opt-in. Do not copy older fixed-rate or zero-swap harness rules into a new test. Existing performance/quality, physical-RAM/VRAM and ownership gates remain, and this documentation does not resume the paused updater.

October27: VRAM-only llama profiles can carry separately qualified source_overrides. A full-catalog provisional install clears them so candidate gates use the new global source; rollback restores the saved JSON/pins. The timer remains paused. [Manual qualification](../VRAM-ENGINE-UPDATE-2026-10-27.md).


**Current status (October 26):** scheduled updates are disabled. Reduced-RAM
GPU-resident baseline qualification is separate and does not resume this updater.

User request (October 23): keep every inference engine on its newest upstream version and
check every day. `llm-daily-update.timer` runs `daily_update.py` at 03:00. A newer version
replaces production **only after it passes the standard promotion gates**; anything else is
rolled back and reported.

| Engine | Upstream it follows | Production location | How a new version is installed |
|---|---|---|---|
| llama.cpp | `ggml-org/llama.cpp` master | `llama.cpp/` (HIP build) | Compile check in an isolated clone, then checkout + rebuild at the production path (its binaries hard-code their build folder) |
| vLLM | ROCm nightly wheels, same ROCm line (`rocm72`) | `vllm/.venv-rocm` | Copy of the production environment + new wheel, private ROCm Torch stack held by constraints, local patches re-applied (they refuse changed upstream code); environment folders swapped |
| SGLang | `StevenChenSE/sglang` `gfx1100-support` | `sglang/rocm-src` + `sglang/.venv-rocm` | New fork commit swapped in with a copied environment; `sglang/apply-rocm-fixes.py` (refuses changed code), editable install and AOT kernels rebuilt at the production paths |
| Strata | `Niko1221/Strata` | `strata/` + `strata/build-hip` | Isolated clone and HIP build; the tracked source tree (the managed UI server runs it) and both binaries replaced together |
| Maya | `mw00/project-maya` | `maya/upstream` + `build-hip` | Isolated clone and HIP build with tests; 18 kernel parity tests on **each** GPU before install; source checkout, binaries, `maya/runtime.json` and the retained profiles' validation records updated |
| Strata DeepSeek | `Niko1221/Strata` (separate DeepSeek component) | `strata-dsv41/` | Isolated build and tests of the separate DeepSeek component; its profile validation, runtime pin and normal-launcher gates remain separate from Qwen |

## Each night

1. Compare each engine's production version with upstream. A revision rejected before is
   not retried until upstream moves again (`--retry-rejected` overrides).
2. Build every newer version in isolation. This needs no GPU and changes nothing in
   production; a build failure is reported and production stays.
3. Wait for an idle machine: no `GPU-LOCK`, no chat request through the hub or gateway for
   20 minutes and no open backend connection. Give up at 06:30 and try again the next night.
4. Take `hardware/generated/GPU-LOCK` (the hub refuses to load models while it exists),
   log in `AGENT-COORDINATION.md`, stop the loaded backend.
5. Per engine: benchmark **production** with `hardware/benchmark-current-amd.py` through the
   normal launcher (every enabled model of that engine). If production itself fails, the
   engine is skipped.
6. Engine-specific correctness tests on the isolated build (Maya kernel parity on each GPU).
7. Install the new build at the production paths after saving a rollback copy, then run the
   same benchmark through the normal launcher.
8. Keep it only if `hardware/compare-runtime-candidate.py` passes for every model:
   prefill and code/prose decode at least 95% of production; short time to first token at
   most max(1.25 × production, production + 0.05 s); no fewer retrieval markers;
   the default low-churn swap limits below and zero VRAM spill, with complete
   worker/host swap-activity evidence. Settled swap alone cannot establish a pass.
   Missing/invalid readings, sampling errors, no worker samples or incomplete
   model coverage also block promotion. Otherwise roll back and check that the
   restored build answers.
9. Release the lock, write `hardware/generated/daily-update/<date>/report.md`, append to
   `hardware/DAILY-UPDATES.md`, update the version block in the handoff and its Shared copy,
   commit only those files and the engine pin files in both repositories and push, and show
   a desktop notification.

If the job is stopped while a build is provisionally installed (shutdown, timeout), it
rolls back before releasing the lock. If the machine loses power instead,
`llm-daily-update-recover.service` rolls back at the next login, before the model hub starts.

## Memory promotion policy

### Default loading-swap policy — October 27

**Loading swap is allowed. Parked swap pages are allowed.** Use
`loading-swap-v2`; fixed resident-byte and cumulative-loading-write caps no
longer reject the default. Enforce sustained active-inference churn, pressure
and performance/quality gates. Physical-RAM admission, RAM caps, VRAM reserves,
zero dedicated-VRAM spill, ownership/telemetry checks and updater holds remain.
[Current policy, thresholds, evidence and historical harness limitations](../LOADING-SWAP-POLICY-2026-10-27.md).

October26 `low-churn-v1` deployment, its fixed 4 GiB caps and stricter no-swap
precedence are superseded. [Historical deployment](../LOW-CHURN-DEFAULT-2026-10-26.md).
Only explicit legacy validation modes reproduce those caps. Old trial results
retain their original settings and are not automatically qualified under v2.

### Minor worker swap allowance — October 25

Historical default, superseded by the October26 low-churn policy above. The
explicit `bounded-64mib` override and these original acceptance results remain.

User instruction supersedes the October24 exact-zero worker-swap promotion rule:
allow at most **64 MiB (67,108,864 bytes)** of sampled aggregate managed inference
worker swap. More than that fails. Apply the same inclusive cap to every model's
memory record and the full launch/load/warmup/benchmark/shutdown lifecycle, for
both production baseline eligibility and candidate promotion. The cap is for the
owned process total, not a separate allowance for each PID. Gate tables print it.
Dedicated VRAM spill must still be exactly zero. Missing/invalid counters,
sampling errors, absent workers, incomplete coverage and all performance/quality
gates still fail closed. Background system swap is outside this check.

The three October25 skipped production baselines pass replay of the new memory
gate: llama.cpp lifecycle peak 12,468,224 bytes, Maya 34,598,912 bytes and Strata
DeepSeek 25,956,352 bytes. vLLM dev466 still fails: lifecycle swap 4,041,416,704
bytes, Qwen27B swap 2,535,796,736 bytes and prose decode down 6.7%. Bolt's
8,265,728-byte reading alone is now acceptable. These are saved-record replays,
not fresh GPU tests or promotions; original nightly results stay unchanged.
Skipped candidates require fresh normal tests before installation/promotion.

Validation: 18 CPU-only accounting/comparator/updater tests, including the exact
64 MiB boundary, one byte over, lifecycle-only violations, missing telemetry,
small-swap promotion and large-swap rollback/smoke. Existing worker cgroup limits,
RAM/VRAM admission, continuous latched watchdogs, model profiles, runtime pins,
ROCm and global swap are unchanged. No inference or new throughput measurement
was run. The next scheduled updater invocation reads this rule without restart.

### Zero-swap gate correction — October 24

The October25 allowance above supersedes this section's exact-zero swap threshold.

The original comparator checked dedicated VRAM spill but omitted worker swap.
It now checks both the shared benchmark's per-model memory record and a separate
0.5-second lifecycle monitor, started before the normal launcher and stopped
after worker shutdown. This includes loading, prewarm, benchmark and teardown;
loading still does not count as measured TTFT. Peaks and sampling errors latch
throughout that lifecycle. A swapping or unverifiable production baseline skips
installation; a swapping or unverifiable candidate triggers the existing rollback
and restored-build smoke check. Gate tables include the recorded byte counts.

The read-only collector identifies only configured inference servers/routers and
their descendants, counts each PID once, and de-duplicates shared AMD DRM clients.
It excludes compilers, environment preparation, DSH and unrelated applications.
The zero-swap rule applies only to the active managed inference task and owned
workers. System swap used by unrelated/background tasks is explicitly allowed;
system-wide swap totals are not a promotion gate and global swap stays enabled.
No global swap setting, worker guard, runtime version or model profile changes.
The timer uses this code on its next invocation; no service restart is required.
Sampling cannot prove the absence of transients between observations.

The separately authorized ten-minute idle unloader defers whenever this updater
or an agent holds GPU-LOCK. It therefore cannot interrupt update benchmarks,
parity tests, provisional installation or rollback checks.

Validation: CPU-only comparator/accounting/orchestrator rollback regressions and
replay of the saved October24 vLLM records. That replay rejects their nonzero
swap fields. The old collector could double-count descendants, so those original
byte values remain historical reported values, not exact unique-process totals.
No fresh throughput, full-window inference or real runtime rollback was run for
this fix; the previously installed versions remain unchanged. Earlier promotion
records retain the gates that existed when they were produced.

### Retained limits

It never relaxes a gate, edits upstream source beyond the existing local patch scripts,
changes model settings, quantizations, contexts or memory guards, or upgrades ROCm,
PyTorch or drivers. When a local patch no longer applies, a test fails or a version needs a
settings change (as Maya 1.1.24 needed `MAYA_GLM_PREFILL_FUSED=0`), the version is rejected
and the report says why; an agent or the user then ports it by hand.

## Commands

```sh
python3 hardware/daily-update/daily_update.py --check                 # versions only
python3 hardware/daily-update/daily_update.py --engines llama,maya    # a subset now
systemctl --user list-timers llm-daily-update.timer                   # next run
systemctl --user disable --now llm-daily-update.timer                 # stop the daily runs
journalctl --user -u llm-daily-update -e                              # last run
```

State (last tested and rejected revisions, a provisional install) is in
`hardware/generated/daily-update/state.json`; logs, benchmark records, gate tables and
rollback copies are in `hardware/generated/daily-update/<date>/<engine>/`. Rollback copies
of large environments are deleted after 14 days by the job's cleanup step.

Strata DeepSeek is a separate `strata-dsv41` component beside Strata Qwen. The same03:00 job tests its retained XS profile through the normal Strata launcher, checks selected-format parity on both GPUs, seals source/binary/config fingerprints and rolls back only that component. Model quants/contexts/guards and the existing timer are unchanged. Unselected mixed Q2_K/Q3_K and Q4_K/IQ4_XS expert formats are not admitted.
