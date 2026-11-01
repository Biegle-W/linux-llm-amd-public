# Experimental ROCm checkpoint-backed PLE candidate

This package prepares an isolated Python overlay for the exact reviewed vLLM
`0.33.0rc1.dev229+g3966924d5.rocm72` wheel. It is a source candidate, not an
installed or GPU-qualified runtime. The installed wheel and selected profiles
remain unchanged.

The host reader derives from [Trosfy's PR #58815](https://github.com/vllm-project/vllm/pull/58815),
head `a7ebbe5fa1fe5984e4d0f1f2d65ab3501d6ba9ac`, under Apache-2.0. This candidate
adds a separate opt-in `rocm_host_file_gather` flag and wires the reader to the
AMD backend. It does not remove the upstream CUDA-only gate or import the
NVIDIA model implementation into ROCm.

## Prepare and check without a GPU

`prepare_candidate.py` verifies every base hash before writing, refuses an
existing output, applies the patch with zero fuzz, verifies the result hashes,
and creates an isolated import overlay. It never overwrites site-packages.
Use the Python interpreter from the reviewed wheel environment.

```bash
python prepare_candidate.py --wheel-root /path/to/site-packages --output /path/to/new-candidate
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/path/to/new-candidate/overlay \
ROCR_VISIBLE_DEVICES='' HIP_VISIBLE_DEVICES='' CUDA_VISIBLE_DEVICES='' \
VLLM_TARGET_DEVICE=cpu VLLM_PLUGINS='' \
python -m pytest test_file_gather_cpu.py -q
```

Recorded verification: 38 CPU tests passed in the reproduced overlay. Every test
asserts that PyTorch's CUDA/HIP context remains uninitialized. Tests use tiny
safetensors fixtures; no model weights are downloaded or loaded. Most host-reader
checks isolate distributed allocation; separate tests exercise the real base
constructor at both TP2 ranks. GPU kernels, HIP transfers, graph replay, model
outputs and performance are outside this CPU result.

## Deliberate initial limits

- Qwen4Exp on ROCm, explicit `VLLM_USE_V2_MODEL_RUNNER=1`.
- TP1 or TP2, DP1, PP1; no elastic expert parallelism.
- MTP/speculative decoding off. Compatible BF16 or FP8 PLE checkpoint; existing
  ROCm NVFP4 rejection remains. Strata GGUF files are not this loader's input.
- Existing startup RAM/VRAM, ownership, spill and thermal guards remain required.
- First device check uses one request, conservative calculated context and a
  small input. On this workstation use TP2 on both AMD cards; no automatic
  single-card fallback. Run only one short DSH tool-call round trip, then unload.

The new flag for that later isolated candidate is
`--engram-config '{"rocm_host_file_gather": true}'`.
The checkpoint files must remain unchanged while the candidate serves requests.
It must not be added to the current installed wheel, which does not contain it.
The preparer creates no launcher or enabled profile and starts no GPU job.
After the owner reports the RAM upgrade and requests testing, verify compatible
weights, actual capacity and gfx1100 kernel support before that short check.
No full-context test, soak, automatic retry, timer or production promotion is
included. Daily updates remain paused.
