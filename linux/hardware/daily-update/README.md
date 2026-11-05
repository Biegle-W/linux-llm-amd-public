# Daily engine updater

The existing `llm-daily-update.timer` targets **03:00 local time**, with `Persistent=false`: a missed night does not start a daytime catch-up run. The owner requested its restoration on November 5. Check actual timer state; the current runtime handoff records completed restoration and qualification outcomes. Other paused schedules are separate.

The scheduled CLI is `daily_update.py`; it dispatches to `nightly.py`. The older builder APIs remain available to isolated preparation tools. The scheduled path uses **one strict two-step DSH read-tool round trip per enabled qualified profile**, then owned unload. It does not run the former same-night baseline, routine full-window tests or throughput promotion gates.

## Scope and selection

- Six existing components: llama.cpp, the global ROCm vLLM wheel, the gfx1100 SGLang fork, Strata Qwen, Maya and separately qualified Strata DeepSeek.
- Maya/Strata DeepSeek selection comes from the enabled qualified native registry. Their retired legacy source pins are separate. No blanket validation or enablement of disabled profiles occurs.
- Manual source/runtime holds remain excluded from automatic global replacement. A manual unpin requires actual qualification of that profile.
- ComfyUI and the separate RDNA3 vLLM checkout remain distinct manual qualification components. The RDNA3 checkout tracks `perf/rdna3_full_stack`; the repository's default branch is not a substitute.
- Weights, quantization, context, selected profile settings, custom-all-reduce exclusions and Torch/ROCm pins remain unchanged by a routine engine update.

## Guarded update and rollback

1. Skip builds/recovery over any GPU lock, STOP, recent/in-progress client request, inference process or KFD owner. A serialization mutex and the owned GPU lock cover preparation, qualification and promotion. Never stop another owner's work.
2. Prepare an isolated source/build or environment. Retain resource, storage-health and 100°C monitoring during CPU work as well as GPU work. Run required per-card parity before native candidates.
3. Snapshot selected runtime files before provisional changes. Provisional native records require a matching ephemeral updater token and a live updater lock owner; ordinary clients reject them.
4. Run the exact current normal profiles through isolated ports, retaining startup capacity checks, RAM/VRAM/spill/phase-aware swap, independent heartbeat and cleanup safeguards. Loading, prefill and generation have finite generous budgets; no three-second inter-token cutoff is enforced.
5. Promote only complete strict tool results for every selected profile. Restore original files/environment/source on failure or interruption. Keep a hardware/watchdog fault hold for review; never retry a rejected revision until upstream changes.
6. Publish only files actually changed by that component plus the current ledger/handoff. Public native records require independent local validation and omit machine-specific backing seals. Publication failures remain queued; a normal push is retried only for an owned publication commit. Remote refs and the exact Shared handoff are verified. Unrelated edits are not staged, and no force push, automatic rebase or model deletion occurs.

`--check` audits versions without building, inference, runtime changes or publication. `--engines` narrows the existing component set. `--no-publish` leaves publication for reviewed manual delivery. Normal scheduled runs do not replay unchanged passed checks. The current selected model/result inventory is in [the runtime handoff](../../network/LINUX-LLM-RUNTIME-HANDOFF.md) and [current results](../CURRENT-AMD-BENCHMARKS.md).
