# Previous dual-NVIDIA Linux setup

**Archive status, October 18:** this tree remains the historical configuration
snapshot. Offline NVIDIA rollback files and research were separately archived
before the user-approved AMD workspace cleanup. Original rollback environments
and unused source were removed after checksum verification; this reference tree
and all tracked setup files are retained. No installed runtime or model is
included in this public tree. See [archive scope and version boundaries](../../linux/hardware/NVIDIA-ARCHIVE-2026-10-18.md).

Historical reference from October 15, 2026, before the AMD migration:
RTX 4070 12 GB + RTX 3060 12 GB, Intel i5-13600KF, 64 GB RAM and approximately
33 GB swap. GPU order is PCI order: 4070 = CUDA0; 3060 = CUDA1. Both cards were
used. There was no CUDA peer-to-peer/NVLink connection; custom all-reduce was
disabled for the TP2 engines.

This directory contains the previous launchers, profiles and compatibility
patches, with personal paths and storage identity replaced by examples. It does
not contain compiled binaries, installed Python environments, model weights,
credentials or private Git history. It is a configuration snapshot, not a new
validation on the current AMD hardware.

The historical [Flash-MTP patch and setup provenance](research/flash-mtp-2026-09-18/README.md)
are retained separately as text for future reference.

## Placement and launch

Use this tree **instead of** the current `linux/` tree in a runtime workspace
such as `/opt/local-llm`. Both trees use that example path and the same service
ports; they are alternative installations, not two stacks to start together.
Changing these reference files does not change the active workstation setup.

1. Read [BUILD.md](BUILD.md), obtain the pinned upstream runtimes and install
   their dependencies. Supply a CUDA-capable driver and the expected toolchain.
2. Set actual checkpoint paths in `dsh/models.json`, `dsh/models.ini`, the backend
   wrappers, HyperQwen wrappers and Strata profile. Historical checkpoint paths
   use `/mnt/llm-models`; the current AMD tree uses Linux NVMe for HF checkpoints.
   Models retired from the active machine are not restored or downloaded here.
3. Configure the real Shared mount and UUID in `dsh/shared_storage.py`, replacing
   `CONFIGURE_SHARED_DRIVE_UUID`. These historical launchers require that mount.
4. Create `dsh/logs`, install the Node runtime/dependencies expected by `dsh/run`,
   and run `dsh/configure_local.py` with PyYAML available to generate private state.
   Configure API credentials locally; do not commit generated state.
5. Start one backend using `bin/llm-llama`, `bin/llm-sglang`, `bin/llm-vllm`,
   `bin/llm-hyperqwen` or `bin/llm-strata`. Start `bin/dsh` separately. Desktop
   examples are in `launchers/`; `bin/install.py` installs SSH/PATH wrappers.

The launcher stops the previous configured inference backend and its owned
workers. DSH, the gateway and unrelated applications are not shutdown targets.
Backend ports and the authenticated gateway remain the same as the current tree.
The historical launchers predate the mixed-vendor hardware guard: do not install
these profiles over a working AMD setup or assume a single 12 GB card can fit them.

## Historical profiles

| Engine | Model/profile | Context tokens | Placement/strategy |
|---|---|---:|---|
| SGLang | Qwen 27B INT4 MTP | 40,960 | CUDA TP2, MTP, 0.98 static memory fraction |
| vLLM | Qwen 27B INT4 MTP | 49,152 | CUDA TP2, 768 MiB KV per GPU |
| HyperQwen | Qwen 27B AWQ DFlash2 | 65,536 | CUDA TP2, 7 draft tokens, 1 GiB Q4 KV per GPU |
| HyperQwen | Qwen 27B AWQ MTP | 65,536 | CUDA TP2, 3 draft tokens, 1.5 GiB Q4 KV per GPU |
| Strata | Flash-Next IQ3_XXS + MTP | 262,144 | 32/16 GPU layer split, expert paging, INT8 KV |
| llama.cpp | Qwen 27B Q4 + MTP | 65,536 | CUDA layer split 9:8, Q4 KV |
| llama.cpp | Muse Glimmer 30B | 131,072 | CUDA layer split 1:1, Q4 KV |
| llama.cpp | Qwen 35B A3B + MTP | 262,144 | CUDA layer split + partial CPU expert offload |
| llama.cpp | Empero 35B A3B + MTP | 262,144 | CUDA layer split + partial CPU expert offload |
| llama.cpp | Nemotron Lightning + MTP | 1,048,576 | CUDA layer split + partial CPU expert offload |
| llama.cpp | GPT-OSS-20B | 131,072 | CUDA layer split, GPU weights |
| llama.cpp | GPT-OSS-120B | 131,072 | Historical file/profile only; not live validated |

Configured context budgets are not measured full-window decode rates or proof
that every advertised context can be filled. Large CPU-offload profiles were
configured for 64 GB RAM; they are unsuitable defaults for the temporary 32 GB
AMD system. GPT-OSS and Lightning entries are historical and remain retired in
the current setup. llama.cpp layer splitting and Strata's split are not TP2.

HyperQwen uses explicit prefix caching, boundary-only retention and INT8
activations in MLP layers. INT8 activations are a quality/performance tradeoff;
target weights remain INT4. The DFlash KV pool was reduced to 1 GiB/rank after a
larger pool caused a long-prompt CUDA OOM. Strata retains the process-local
`STRATA_NO_ARENA_THP=1` loading workaround and bounded conversation parking.

## Saved benchmarks

See the [public README NVIDIA result set](../documentation/ubuntu-readme-before-organization-2026-10-24.md#nvidia-archived-setup-and-results)
for per-model prefill/decode, the direct HyperQwen comparison, and longer-input
results, plus the October 15 INT8-MLP TTFT comparison. Measurements retain their
original dates, runtime versions and settings; earlier decode results predate
the October 14 runtime update and must not be attributed to this archived build. Brief smoke-test outputs are labeled separately.

## Validation scope

The saved October 14 update record reports functional checks on all five engines,
including streaming/tools, 32,843-token retrieval on SGLang/vLLM/HyperQwen and
DFlash2 → MTP → DFlash2 switching. Six llama.cpp profiles generated with their
configured context budgets allocated. GPT-OSS-120B was checked only as a retained
file/profile and was not loaded. The October 15 optimization record adds focused
HyperQwen prefix/INT8 and Strata cache checks; these were not broad quality tests.

This publication checks syntax, JSON, the retained shutdown/mount unit tests,
model/private-state exclusions, and secrets/identity patterns. It does not rerun
historical GPU benchmarks or install old runtimes on the current machine.
Raw original reports, logs and personal connection settings are excluded.
