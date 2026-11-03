# RCCL explicit P2P-control audit — November 3, 2026

**Confirmed source-order defect; isolated candidate build in progress. Not installed or GPU-qualified, and not established as a remedy for the held SGLang failure.** Existing production libraries, model pins and guards remain unchanged. The SGLang route stays held; no further model retry has been run.

The pinned build recipe for the retained no-hostcall RCCL 2.27.7 identifies source commit **bf3ebf549fec376521b7d35f09a67f67071c96d3**. In that exact source's `ncclTopoCheckP2p`, the function obtains the explicit user P2P level first, then assigns the Intel default `PATH_PXB` afterward. Thus the platform-default assignment can overwrite the level obtained from `NCCL_P2P_DISABLE=1` or an explicit P2P-level setting.

This source finding matches the observed isolated collective controls: logs acknowledged the disable flag but still selected P2P/IPC, including with the explicit level variable removed. It explains why a configuration flag cannot be used as proof of host transport here. The source-order defect is independently established; equivalence of every source line to the released binary has not been rebuilt and verified yet. It is not proof that this defect caused the SGLang interruption.

## Offline candidate

The minimal source change applies user overrides **after** the platform defaults. No platform default changes when the user supplies no override. The patch applies to the exact pinned source with zero fuzz and passes the source-order validation. This is a source-level check, not a passing GPU transport test.

An isolated gfx1100-only build uses the same no-hostcall recipe's NDEBUG requirement on device compilation, the existing ROCm 7.2.3 SDK and an official matching HIPIFY helper. It is bounded to three build jobs, a 24 GiB memory maximum and 400% CPU quota, with reduced scheduling priority. Dependencies and generated artifacts stay outside the installed runtime. No source/binary selection has changed in a launcher.

Before any candidate deployment, verify zero hidden hostcall buffers in the extracted device image, the required PyTorch/RCCL exported symbols including ncclCommDump, and preservation of the AMD-SMI compatibility setup. Then a separately authorized bounded communicator check must prove the actual selected host channel and tensor correctness with P2P disabled. Flag parsing or a successful process exit is insufficient. Candidate P2P-on behavior needs its own matched bounded check.

Only after a reliable fallback is demonstrated should a controlled SGLang initialization comparison be considered: change one factor at a time, retain the prior profile and original failures, use a small isolated admission rather than restoring all production settings, and unload each owned attempt. Stop at the first new GPU/bus fault; do not replay the failed full DFlash2 setup as an automatic retry. The prepared MES workaround remains separate and is not installed by this work.

Sources: [exact RCCL paths.cc](https://github.com/ROCm/rccl/blob/bf3ebf549fec376521b7d35f09a67f67071c96d3/src/graph/paths.cc), [pinned no-hostcall build recipe](https://github.com/cadamcat/dual-radeon-vllm/blob/23c2beb2e200353fda84afa216c2cea2f7c579e9/build/build-rccl-nohostcall.sh). [Curated audit state](results/rccl-p2p-control-audit-2026-11-03.json).
