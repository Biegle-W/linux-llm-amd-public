# ROCm source integration for checkpoint-backed PLE — November 1, 2026

The owner requested resolving the ROCm prerequisite before the queued RAM-upgrade
trial. An isolated candidate now connects checkpoint-file row gathering to the
AMD Qwen4Exp backend on the exact reviewed vLLM wheel. **Source integration is
prepared; device execution and model correctness remain unverified.** No active
runtime, enabled model, context cap, guard or schedule changed.

## What was missing and what changed

The reviewed upstream [host-file proposal #58815](https://github.com/vllm-project/vllm/pull/58815)
remains a CUDA-only path at `a7ebbe5fa1fe`. Its reader and staging integration
lived in the NVIDIA backend. The AMD backend already has resident/pinned-host
PLE lookup, but did not consume file-backed staged rows. Removing the platform
check alone would not connect those paths.

The candidate adds a separate `rocm_host_file_gather` opt-in, a shared readonly
file reader, AMD eager n-gram-ID/input staging, and loader binding after all
shards and scales arrive. Captured forwards only read fixed-address staging
buffers. The full PLE table receives no allocated tensor storage. Every TP rank
gathers complete rows; TP2 sequence sharding does not sum the same rows twice.
Request-history tails and padded token rows are cleared; dummy/profile paths
perform no checkpoint reads. Reload is rejected, malformed/truncated inputs
fail closed, and file descriptors close with the model.

## Verification and practical limits

- **38 CPU tests pass** in 4.32 seconds through a reproduced zero-fuzz overlay.
  BF16, FP32 and stored FP8 rows preserve bytes and duplicate/order semantics.
  Tests cover actual safetensors offsets and symlinks, readonly handles, missing
  shards, reload, bad IDs, truncation without partial staging, bounds, cleanup,
  zero-only dummy inputs, the AMD forward, TP2 duplicate prevention, scale-before-
  bind ordering, stale request tails and configuration/MTP rejection.
- Real candidate modules import against the installed dependencies. Most storage
  tests isolate distributed allocation; two tests also use the real embedding
  base constructor at the two TP2 ranks. All tests assert no CUDA/HIP context
  initialization. This is not a GPU kernel, graph-replay or full-model test.
- The preparer verifies exact base hashes, applies with zero fuzz and verifies
  every candidate hash. It refuses unknown wheel contents or existing output.
  Installed Python files still match their original hashes after the checks.
- Initial scope is ROCm Qwen4Exp, explicit V2 runner, TP1/2, DP1, PP1 and MTP off.
  NVFP4 remains rejected by the AMD backend. Compatible BF16/FP8 PLE safetensors
  are needed; existing Strata GGUF files cannot be substituted.

The exact wheel is `0.33.0rc1.dev229+g3966924d5.rocm72`, PyTorch
`2.13.0+git733fca1`, HIP `7.2.53211`. The older local source checkout is a
different revision and is not this patch's base. The manifest pins code hashes
rather than assuming wheel version strings prove identical contents.

## Next action after RAM installation

Keep the candidate isolated. Recheck actual available RAM/VRAM, compatible
checkpoint layout/quantization and gfx1100 kernel admission. Calculate context
and staging/KV allocations conservatively, retaining all existing guards. Then,
only on the owner's request, run one short DSH tool-call round trip through the
candidate and unload. Record a device/kernel/tool failure without retrying it
into a pass. Do not run full-context qualification or promote this CPU-only
result as working ROCm inference. Daily updates and existing model holds remain.

[Patch, exact-hash preparer, CPU tests and license](experiments/ple-rocm-host-file-gather/README.md).
[Structured verification](results/ple-rocm-source-port-2026-11-01.json).
[Owner's short-test policy](SHORT-HARNESS-TEST-POLICY-2026-11-01.md).
