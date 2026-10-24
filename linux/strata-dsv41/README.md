# Strata DeepSeek component

The DeepSeek engine is isolated from the retained Strata Qwen installation.
Source, build products and local preparation records are ignored by Git. The
runtime pin and guarded model profiles describe the validated configuration;
public profiles contain example paths and require fresh local validation.

The October 24 setup uses source `8183c6b67162340c09b67360860177c577a65f2e`,
Terminal 0.2.4.1 / release DeepSeek package 0.1.49. The local engine reports
`0.1.49.1 build 8183c6b67`, built for gfx1100 with ROCm 7.2.3.
Official release AMD binaries target gfx1200/1201, so they are not substituted
for the source-built RX 7900 XTX executable.

The maintained build helper is `hardware/build-strata-dsv41-hip.sh`. Set
`STRATA_DSV41_SOURCE_DIR`, `STRATA_DSV41_BUILD_DIR` and `STRATA_GGML_DIR` for an
isolated candidate. It uses the existing GNU 14.4/sysroot toolchain and records
the source, ggml archive pin and binary fingerprint. Selected-format test
executables use the same engine objects; only test-source selection changes.
Numerical tolerances and engine source remain unchanged. Unselected mixed
Q2_K/Q3_K and Q4_K/IQ4_XS expert formats are not admitted by this setup.

With the pinned source and existing verified Maya assets available,
`hardware/prepare-strata-deepseek.py` creates separate Strata packs on the
mounted shared NVMe. It never downloads, copies or requantizes model weights,
never overwrites an existing pack, checks tensor bounds and preserves Maya
metadata. XS references the existing S Engram shards 5/6; both engines depend
on those files. Strata keeps independent expert-routing seeds.

The two model IDs are `deepseek-v4.1-flash-1017-strata-s` and
`deepseek-v4.1-flash-1017-strata-xs`. Both use 32K, 24 CPU threads, both GPUs,
CPU expert access and GPU hot caching. S has no drafter; XS uses the matching
xs2 drafter. Prompt skipping, expert omission and persistent slots are disabled.
The engine's nominal TP2 falls back to layer groups for this model's dimensions;
both cards participate, but this is not true tensor parallelism.

`dsh/strata_ds41_runtime.py` checks the source/binary/config/pack seals before
handover. The normal router retains its scoped 52G/no-swap worker, startup VRAM
admission and continuous latched guards. The existing daily updater tests and
rolls back this component independently of Qwen; it does not alter model settings.

[Measured selection, failure evidence and validation limits](../hardware/STRATA-DEEPSEEK-2026-10-24.md).
