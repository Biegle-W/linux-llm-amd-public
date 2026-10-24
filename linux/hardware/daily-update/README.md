# Daily engine update

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
| Maya | `mw00/project-maya` | `maya/upstream` + `build-hip` | Isolated clone and HIP build with tests; 18 kernel parity tests on **each** GPU before install; source checkout, binaries, `maya/runtime.json` and the three profiles' validation records updated |

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
   most max(1.25 × production, production + 0.05 s); no fewer retrieval markers; zero
   VRAM spill. Otherwise roll back and check that the restored build answers.
9. Release the lock, write `hardware/generated/daily-update/<date>/report.md`, append to
   `hardware/DAILY-UPDATES.md`, update the version block in the handoff and its Shared copy,
   commit only those files and the engine pin files in both repositories and push, and show
   a desktop notification.

If the job is stopped while a build is provisionally installed (shutdown, timeout), it
rolls back before releasing the lock. If the machine loses power instead,
`llm-daily-update-recover.service` rolls back at the next login, before the model hub starts.

## What it does not decide

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
