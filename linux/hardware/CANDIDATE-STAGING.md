# Staging engine and profile candidates

These opt-in switches let a candidate build or configuration run through the
normal guarded launchers and validators **without changing production**. Each is
unset by default, and an empty value also means production, so normal launches
are unaffected. Take `hardware/generated/GPU-LOCK` before any GPU test
(`hardware/generated/AGENT-COORDINATION.md`).

| Switch | Read by | Effect |
|---|---|---|
| `LLAMA_SRC=<checkout>` | `hardware/build-llama-hip.sh`, `hardware/build-vulkan.sh` | Build llama.cpp from an isolated checkout (for example a `git worktree` under `hardware/generated/`) into its own `build-hip`/`build-vulkan` |
| `LLAMA_CPP_DIR=<checkout>` | `dsh/llama_runtime.py`, `hardware/nemotron_super.py`, `hardware/validate-llama-launcher.py`, `hardware/validate-nemotron-super.py` | Run the llama.cpp router, Super validator and integration check against that checkout's binaries; the validator records its commit |
| `VLLM_ENV_PATH=<venv>` | `vllm/run-rocm`, `vllm/apply-*.py` | Run vLLM from a candidate environment (existing) |
| `STRATA_PROFILE_CONFIG=<file in dsh/>` | `dsh/strata-router.py`, `dsh/strata_runtime.py` | Start managed Strata with a candidate config; its own RAM gate, reserves, watchdog and no-swap scope still apply |
| `--max-gpu-busy N` | `hardware/validate-nemotron-super.py` | Raise the idle precheck (default 10%) for one run with a known desktop load; the value is recorded in the result |
| `--model-path`, `--load-mode` | `hardware/validate-nemotron-super.py` | Test a model copy or `mmap` loading in isolation (see `SUPER-NVME-LOAD-2026-10-20.md`) |

Compare a candidate against a **same-hardware** baseline from
`hardware/benchmark-current-amd.py` with:

```sh
python3 hardware/compare-runtime-candidate.py --baseline BASELINE.json CANDIDATE.json [...]
```

The comparison applies the standard thresholds:
- prefill and code/prose decode medians at least 95% of baseline;
- short TTFT at most max(1.25 × baseline, baseline + 0.05 s);
- marker checks no fewer than baseline;
- zero VRAM spill.

It exits non-zero on any miss. Write the promotion criteria before timing, and keep failed
and rejected trials. Promote only by rebuilding or replaying the validated steps at the
production paths, keep a rollback copy, then rerun the normal-launcher proof. The
October 20 llama.cpp `4c3c5810`, vLLM dev36 and Strata 20 GiB evaluations used these switches.
