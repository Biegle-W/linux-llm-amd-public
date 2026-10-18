# NVIDIA recovery archive — October 18, 2026

The retired NVIDIA setup has been archived separately from the active dual-AMD
workspace. **No original files have been deleted.** Their proposed removal remains
subject to explicit user confirmation in the [cleanup review](CLEANUP-REVIEW-2026-10-18.md).

Archive directory: `/mnt/shared/LLM-ARCHIVE/NVIDIA/2026-10-18` (example Shared mount).
It contains `nvidia-recovery.tar.zst`, `MANIFEST.json`, `SHA256SUMS` and `README.md`.
The compressed archive is **10,913,993,973 bytes (10.16 GiB)** on Shared SATA.
GNU tar compared every archived member's content/metadata against the original
sources successfully. The compressed archive also has a recorded SHA-256.
The exact checksum and source locations are recorded privately in the archive manifest.

## Contents and version boundaries

- `.private-backups/runtime-upgrade-2026-10-14/`: old CUDA SGLang, vLLM and
  HyperQwen virtual environments, native llama.cpp/Strata rollback binaries and
  moved package files. These are **pre-upgrade rollback copies**, not the latest
  NVIDIA versions configured on October 14–15. Saved package metadata reports
  SGLang 0.5.21/Torch 2.13.0, vLLM 0.30.0/Torch 2.13.0+cu130, and HyperQwen's
  patched vLLM 0.30.0/Torch 2.13.0+cu130.
- `llm-tools/llama-flash-mtp-src/`: historical isolated Flash-MTP source,
  normalization-shape patch and small upstream vocabulary/test fixtures.
- `hyperqwen/` and `BENCHMARKS-HYPERQWEN.md`: historical research and measurements.
- `dsh/research/upgrade-2026-10-14/`: source pins, compatibility fixes and reports
  documenting the later CUDA nightly/development setup.
- `linux-nvidia/`: sanitized configuration/build-guide snapshot of the former
  RTX 4070 + RTX 3060 installation. It remains in the public repository in place.

The sanitized configuration snapshot came from public commit `2048b70`, before
adding this cleanup documentation. Private archive metadata retains its own
provenance. This is a historical recovery collection, not one newly tested or
self-contained installation. Some old model
checkpoints were already removed in earlier authorized cleanups; no model
checkpoint is restored or downloaded here. Current model/draft files, chat state
and credential directories were not selected for archival.

## Recovery and retained dependencies

Keep this binary archive private and outside Git. To inspect it, run
`tar -I zstd -tf nvidia-recovery.tar.zst`. To recover files, first verify
`sha256sum -c SHA256SUMS`, then extract into a new empty directory on a Linux
filesystem; do not extract over the active AMD workspace. Tar preserves Linux
symlinks, hardlinks and permissions inside the exFAT-hosted archive.

Historical environments contain absolute paths and external toolchain references;
restore only with compatible CUDA hardware/driver, dependencies and the intended
paths, or rebuild from the recorded pins. This cleanup did not validate NVIDIA
inference or rerun old benchmarks. Earlier benchmark dates/results are preserved.

Keep the current `llm-tools/cuda-build` directory: AMD build scripts and SGLang
JIT still use its C++ compiler, sysroot and libraries. Current ROCm environments,
SDK, RCCL, active kernel caches, Vulkan builds, models and Strata preparation
stay in place. Historical tracked configuration paths and reports also stay.
