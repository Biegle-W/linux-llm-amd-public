# RCCL explicit P2P-control audit — November 3, 2026

**Confirmed source-order defect; isolated candidate built and statically audited. Not installed or GPU-qualified, and not established as a remedy for the held SGLang failure.** Existing production libraries, model pins and guards remain unchanged. The SGLang route stays held; no further model retry has been run.

The pinned build recipe for the retained no-hostcall RCCL 2.27.7 identifies source commit **bf3ebf549fec376521b7d35f09a67f67071c96d3**. In that exact source's `ncclTopoCheckP2p`, the function obtains the explicit user P2P level first, then assigns the Intel default `PATH_PXB` afterward. Thus the platform-default assignment can overwrite the level obtained from `NCCL_P2P_DISABLE=1` or an explicit P2P-level setting.

This source finding matches the observed isolated collective controls: logs acknowledged the disable flag but still selected P2P/IPC, including with the explicit level variable removed. It explains why a configuration flag cannot be used as proof of host transport here. The source-order defect is independently established; equivalence of every source line to the released binary has not been rebuilt and verified yet. It is not proof that this defect caused the SGLang interruption.

## Offline candidate

The minimal source change applies user overrides **after** the platform defaults. No platform default changes when the user supplies no override. The patch applies to the exact pinned source with zero fuzz and passes the source-order validation. This is a source-level check, not a passing GPU transport test.

An isolated gfx1100-only build uses the same no-hostcall recipe's NDEBUG requirement on device compilation, the existing ROCm 7.2.3 SDK and an official matching HIPIFY helper. It is bounded to three build jobs, a 24 GiB memory maximum and 400% CPU quota, with reduced scheduling priority. Dependencies and generated artifacts stay outside the installed runtime. No source/binary selection has changed in a launcher.

Static verification now passes: the candidate’s extracted gfx1100 device images contain zero hidden hostcall buffers, and all 37 exports required by the installed PyTorch and SGLang wrapper are present. The same audit passes on the retained library as a control. The prior instruction to require `ncclCommDump` was overly broad: it is absent from the retained library and is not required by these installed consumers. Installed library/configuration and AMD-SMI compatibility files retain their recorded fingerprints.

The raw candidate links the real ROCm-SMI library, unlike the retained library’s `librsmi_stub.so.1` dependency. A separate isolated copy now uses the retained SMI shim, which supplies all nine required SMI exports. Its extracted device images are unchanged by that dependency adjustment, and it passes the same static audit. Neither library has been loaded; runtime dependency resolution and ABI behavior remain untested.

A separately authorized bounded communicator check must prove the actual selected host channel and tensor correctness with P2P disabled. Flag parsing or a successful process exit is insufficient. Candidate P2P-on behavior needs its own matched bounded check.

Only after a reliable fallback is demonstrated should a controlled SGLang initialization comparison be considered: change one factor at a time, retain the prior profile and original failures, use a small isolated admission rather than restoring all production settings, and unload each owned attempt. Stop at the first new GPU/bus fault; do not replay the failed full DFlash2 setup as an automatic retry. The prepared MES workaround remains separate and is not installed by this work.

Sources: [exact RCCL paths.cc](https://github.com/ROCm/rccl/blob/bf3ebf549fec376521b7d35f09a67f67071c96d3/src/graph/paths.cc), [pinned no-hostcall build recipe](https://github.com/cadamcat/dual-radeon-vllm/blob/23c2beb2e200353fda84afa216c2cea2f7c579e9/build/build-rccl-nohostcall.sh). [Curated audit state](results/rccl-p2p-control-audit-2026-11-03.json).

Exact source correction: [pinned-source patch](patches/rccl-p2p-user-override-bf3ebf5.patch).

## Completed offline build

All 258 build steps completed. The source archive comparison identifies only the P2P precedence correction and the CMake NDEBUG definition used by the retained no-hostcall recipe. Isolated shim-compatible candidate SHA-256: `45847d2f61a504746867a1beef08be1041999682b00a7abf19cdc07b11f1d118`. These static checks establish build completion and the inspected properties; they do not demonstrate host-channel selection, collective correctness, or a SGLang crash remedy. No candidate installation, kernel/firmware replacement, GPU communicator, or model retry was performed. The SGLang fault hold, RAM/weight holds, runtime pins and updater pause remain.
