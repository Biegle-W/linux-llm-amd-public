# MES source compatibility and offline preparation — October 30, 2026

The experimental MES workaround is **absent from the exact installed kernel source**, and the six-file forum patch applies cleanly to it with no fuzz. Both GPUs expose loaded MES scheduler firmware **0x86**, above the patch's **0x70** minimum. A separate offline source candidate is prepared. **It has not been compiled, installed or booted. No GPU trial was run.** This establishes source applicability, not a fix for the retained Strata watchdog failure.

## Exact source and applicability

| Check | Result |
|---|---|
| Running kernel / source package | `7.0.0-42-generic` / Ubuntu `linux-source-7.0.0` `7.0.0-42.42` |
| Source Makefile version | `7.0.14`; Ubuntu's ABI/package version is a separate identifier |
| Download verification | Exact source package SHA-256 `3da06804a13cbc18974a61f78ff73dbbbfe476dc9b775e99102aee15aabe55a7`, matching APT metadata; package downloaded only, never installed |
| Original attachment | Targets `7.0.0-38.38`; SHA-256 `afcd71e5904bc66ee6139535ba2ff20a9d3bb9bc52a32e805d0a19854275a3fe` |
| Forward applicability on `42.42` | All six files pass `patch --dry-run --force --forward --fuzz=0`; three KFD hunks move by +36 lines |
| Inclusion check | Notify API, software work items, queue hooks and user-queue reset guard absent; reverse dry run fails on the original source |
| Installed/loaded module cross-check | Module `srcversion` agrees with loaded sysfs; new notify symbols absent from the installed module's symbol table |
| Offline candidate | Patch applied only to a separate extracted-source copy; forward reapplication rejected and reverse dry run passes |
| Firmware prerequisite | Loaded driver sysfs reports scheduler `0x86` on both cards; the generic firmware-file header is not the live scheduler version |
| Existing configuration | `sched_policy=0`; `CONFIG_HZ=1000`, AMDGPU module and KFD enabled; unchanged |

Exact original and candidate file fingerprints, feature checks and applicability output are in the [curated evidence](results/mes-source-audit-2026-10-30.json). The extracted sources and rebased candidate diff remain in the private audit workspace. The raw forum attachment is not redistributed by this report.

## What the candidate contains

The inspected [AMD-maintainer branch](https://kernel.googlesource.com/pub/scm/linux/kernel/git/superm1/linux/+/refs/heads/superm1/amdgpu-100-7.2.y) was pinned at `d1ec743e945d7d5f514489d525bfcbc48cdf057f`. It supplies the notify misc operation, GFX11 KFD and user-queue software timers, microsecond-to-jiffies conversion and SR-IOV exception. The forum backport also adds the [user-queue reset-domain protection](https://www.mail-archive.com/amd-gfx@lists.freedesktop.org/msg153442.html), which is absent from that inspected branch tip. Five inspected helper bodies match the branch after comment/whitespace normalization; the sixth differs by this reset guard. This is a focused source comparison, not complete semantic or build validation.

The bare-metal firmware oversubscription timer is replaced with software notification while queues are oversubscribed; SR-IOV retains the firmware timer. This is a coordinated multi-file change: disabling the firmware timer alone is not the prepared candidate. With this kernel's 1000 Hz tick, `usecs_to_jiffies(50)` rounds to one jiffy; it does not promise a notification every 50 microseconds.

The [upstream issue discussion](https://github.com/ROCm/TheRock/issues/9141#issuecomment-6211587609) distinguishes oversubscription preventing idle from forward-progress failures. The [forum reporter](https://lcz.me/post/29572) still recorded one watchdog failure among 27 requests after patching. Neither its idle improvement nor this source audit establishes that our completed 8K/history stall is fixed.

## Offline preparation delivered

- [MES audit utility](experiments/mes-preparation/audit_mes_source.py): validates the six expected file pairs, records hashes/features and performs forward/reverse dry runs without editing the supplied source. It has no build/install mode.
- [H3 readiness inspector](experiments/mes-preparation/inspect_h3_readiness.py): parses Python ASTs and bounded safetensors headers without importing Torch/Comfy, executing candidate source or reading weight tensors. File presence never enables a launch.
- [P2P qualification plan](experiments/mes-preparation/p2p-qualification-plan.json): topology, bidirectional copy correctness, RCCL transport proof and matched application comparisons, all separated by explicit gates. No schedule, GPU launcher or runtime environment override was installed.
- [Eleven CPU-only checks](experiments/mes-preparation/test_offline_preparation.py): pristine/applied/partial patch distinction, unexpected-path rejection, source non-execution and bounded metadata parsing. All pass in both maintained checkouts.

Example offline commands, using source/asset paths selected by the operator:

```bash
python3 hardware/experiments/mes-preparation/audit_mes_source.py \
  --source "$AUDIT_SOURCE" --patch "$REVIEWED_PATCH"
python3 hardware/experiments/mes-preparation/inspect_h3_readiness.py \
  --comfy-root "$SAVED_COMFY" --tp-root "$SAVED_TP" --models-root "$MODEL_ROOT"
```

In the public repository, prefix these script paths with `linux/`.

## H3 integration boundary

The saved matched Comfy snapshot's INT4 loader explicitly selects **ConvRot W4A4**. Its published TP2 `core.py` and row-parallel code use **INT8** operations; the three TP Python hashes still match the retained matched-comparison pins. A filename containing W4A8 or an available INT4 LoRA class does not qualify the requested W4A8 diffusion path.

The exact forum diffusion checkpoint `Minimax-h3_Singularity_ref2va_v2_pruned_w4a8.safetensors` and Turbo LoRA `minimax_h3_turbo_v4_step600_ema_pruned_comfyui.safetensors` were absent at the audited model-root locations. No verified custom W4A8/sparse TP2 runner bundle was available in the reviewed topic. This inventory is scoped to those paths and reviewed sources, not a machine-wide claim. The already-prepared W4A8 text encoder and retained INT8 diffusion result remain separate evidence.

Next integration work needs an inspectable runner and correctly identified/licensed weights, packed-weight and scale sharding review, ConvRot/LoRA semantics and sparse-attention integration. Source inspection can continue offline when those assets are available. GPU correctness, transport proof, guarded admission and full media validation remain pending; the 1080p/10-second target is still only a candidate, and the near-23-GiB/card 12-second setting does not meet our existing VRAM reserve unchanged.

## Preserved runtime and next action

The seven selected launcher/guard/config hashes match the pre-audit snapshot. Kernel, scheduler policy, selected model settings, RAM holds and schedules were not edited. The API and hub remain running, authenticated `/health` passes, and the normal update timer remains active. Health reads the hub's existing snapshot; no inference request was sent. No service restart, GPU reservation, kernel build/install or recurring task was created.

No audit job or lock remains active. The next kernel step, only after separate authorization, is an isolated build against the exact generic config with a unique kernel identity and preserved original boot path, followed by a planned controlled qualification. No ready-to-install kernel is claimed. P2P tests wait for switch installation and authorization; RAM restoration waits for actual visible capacity and idle admission. All existing guards remain mandatory.
