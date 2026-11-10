# H3 two-card P2P is the production ComfyUI — November 7, 2026

Owner request: "Replace current production with p2p set up."

`graphics/start-comfyui` now starts **P2P mode by default** on `http://127.0.0.1:8188`. H3 text-to-video with the default projected-8B encoder runs fcys `tp2-comfy` tensor parallelism across both cards, over RCCL direct P2P/IPC ([qualification](DIFFUSION-P2P-RADIANCE-2026-11-07.md)). Every other workflow keeps the earlier staged two-card placement on the same server: FLUX, Qwen-Image, and H3 with the native 32B encoder.

To roll back: `COMFY_MODE=staged graphics/start-comfyui` starts the previous single-process server, unchanged.

## How it works

| Piece | Role |
|---|---|
| Rank 0, port 8188 | The production server. Both cards are visible; the PowerColor is device 0. It is launched through `h3-tp2/tp_boot.py` with `--use-ck-attention` instead of `--use-pytorch-cross-attention`. All other production flags, the input/user/output directories and the swap guard are unchanged. |
| Rank 1, `127.0.0.1:18189` | A headless follower that sees only the Sapphire. Its output goes to `graphics/generated/tp2-follower-output` and is never saved. |
| `h3-tp2/tp2_pair.py` | Starts rank 1, then rank 0, inside `guarded_comfy.py`'s owned scope. If either rank exits it stops both and restarts the pair, at most 3 times in 10 minutes. |
| `h3-tp2/custom_nodes/h3_tp2` | Rank 0 rewrites each H3 prompt that uses the projected encoder into the qualified form. The loader becomes the INT8-Fast loader with the qualified settings, and every component device becomes the rank's own card. The follower graph (encoder, conditioning, noise and sampler, ending in a sink) is queued on rank 1, immediately if rank 0 is idle, otherwise when the H3 loader runs. The sink frees rank 1's VRAM after sampling. H3 prompts with the native encoder get `H3StagedUNetLoader` and stay staged. Non-H3 prompts are not touched. |
| `h3-tp2/tp_boot.py` | fcys bootstrap, adapted. The load hook acts only on the H3 checkpoint. RCCL has a 300 s timeout. Cancels are decided jointly (below). |
| Pre-sliced halves | `make_halves.py` wrote the two half-width checkpoints once, 10.56 GB each, to `Graphics-Models/experimental/h3-tp2-halves-20261107/`, with a manifest of the source's size, mtime and SHA-256. Each rank loads only its own half; if the manifest does not match the source, the glue falls back to splitting per job. |
| Vendored code | fcys `core.py`/`tp_linear.py` and the INT8-Fast-ROCM plugin (with its updater disabled) live under `runtime/h3-tp2/`, which is git-ignored. `verify_vendor.py` checks them against `h3-tp2/vendor-sha256.txt` before every start. |

RCCL settings, the qualified November 7 transport: `HSA_ENABLE_SDMA=0`, `NCCL_PROTO=Simple`, 1 channel and 1 MiB buffers. P2P is not disabled. `NCCL_DEBUG=WARN` by default, because INFO prints about 12,000 tuning lines per job; set `H3_TP2_NCCL_DEBUG=INFO` to see `via P2P/IPC`.

## Problems found and fixed during validation

1. **`--enable-triton-backend` breaks the native-32B NVFP4 encoder.** That flag came from fcys's launcher. With it, the native-32B workflow rendered a sunset instead of the teapot, and the staged server reproduced this when only that flag was added. The flag was removed from both ranks; the INT8 plugin's Triton kernels do not need it.
2. **A cancel could deadlock the pair.** ComfyUI checks for cancels in every layer and every step, so the two ranks stopped at different steps, and rank 0 waited in an all-reduce until RCCL's watchdog aborted it. The supervisor then restarted the pair, which confirmed the recovery path. The fix: during a P2P sampling run, local cancel checks do not raise. At the start of every DiT forward both ranks read and clear their cancel flag and combine it with `all_reduce(MAX)`, so they stop at the same step. Retest: both ranks logged "interrupt agreed" at step 6, and the next H3 job succeeded.
3. **Rank 1 used to wait for rank 0's encoder.** Cold H3 after Qwen-Image took 178.8 s. Starting rank 1 when the prompt arrives brought this to 122.4 s.
4. **Each job split the 21 GB DiT on the CPU** (17 s on rank 0). The pre-sliced halves removed this: warm H3 went from 113.6 s to 56.4 s.
5. **The native-32B encoder is too large to run twice.** Each rank loading its own 15 GB copy took 246 s against 93 s staged, so these prompts stay staged on the same server (114 s, correct output).

## Results (all on the production server, all outputs checked by eye)

| Workflow | P2P mode s | Staged s (same conditions) | Notes |
|---|---:|---:|---|
| H3 projected-8B, 608×352×39, warm | 56.4 | 54.1 | sampler 1.06 vs 1.40 s/step; the gain is spent on two ranks each loading the encoder |
| H3 projected-8B, cold (after Qwen-Image) | 122.4 | 126.3 (morning) | loading from SATA dominates |
| H3 projected-8B, 960×544×39 | 132.3 | 148.3 | sampler 2.67 vs 3.65 s/step (27% faster) |
| H3 queued behind a FLUX job | 155.9 | — | rank 1 starts when the H3 loader runs |
| H3 after a cancel | 119.6 | — | joint cancel at step 6, then a clean run |
| H3 native-32B encoder (kept staged) | 114.3 | 92.6 | correct teapot; CK attention instead of PyTorch attention |
| FLUX 3 Klein t2i | 96.5–98.7 | 92.7 | legible "LOCAL LLM" text |
| FLUX 3 Klein i2i | 42.1 | — | correct edit |
| Qwen-Image 2.1 BF16 512×512 | 90.3 | 90.4 | coherent |

Health: no guard faults, no amdgpu or AER kernel errors, and the RCCL transport was P2P/IPC (checked with INFO on the first runs). The PowerColor (bus 0b) is rank 0 and the Sapphire (bus 13) is rank 1.

**Where P2P helps:** H3 sampling is 25–27% faster per step, and each card holds only half the DiT (10 GB instead of 20 GB). That leaves more room for larger frames and longer clips. For small, warm 608×352 jobs end-to-end time is about the same as staged; the gain grows with resolution.

**Image-to-video:** the projected-8B encoder is text-only by design (its node refuses an image and points to the native-32B workflow), so H3 image-to-video always uses the native-32B encoder, which production keeps staged. Tested November 7: the FLUX lighthouse image as first frame, 608×352×39, 175.5 s, the first frame matches the input and the beam and waves move coherently. A P2P image-to-video path would need the native-32B encoder on both ranks, measured slower (246 s vs 93 s for text-to-video).

**Known cost: idle CPU (November 9).** While the pair is resident, each rank has one thread busy-looping at 100% of a core, mostly in kernel time, so about 1.7–2 cores of system CPU at idle (about 0.05 with ComfyUI stopped). It starts about 5.5 s into startup and is present on both ranks. Swapping PyTorch's bundled HSA runtime (ROCr 7.2 build 81) for the system ROCm 7.2.4 runtime (build 93) did not change it (1.75 cores, both threads still at 100%), so the bundled runtime is not the cause; the original library was restored. Finding the looping code needs a stack sample, which the host's ptrace restrictions block. Rendering is unaffected. Since the idle stop below, the cost lasts at most 10 minutes after the last use.

**Idle stop (November 9).** `graphics/guarded_comfy.py` stops the pair after 600 s with an empty queue and no client connected to :8188 (an open browser tab counts as use; anything it cannot read counts as busy). `COMFY_IDLE_TIMEOUT_S` changes the limit, 0 disables it. It exits through the normal guard shutdown, so both ranks stop, the GPUs are released and the start lock is freed; restarting takes about 10 s to HTTP 200. Tested with a 60 s limit: it stayed up while a client was connected and stopped 58 s after the client left, leaving no processes or GPU clients.

**Not covered:** sustained load and concurrent users. The Desktop ComfyUI app still uses its own staged installation.

Numbers: `results/h3-tp2-production-2026-11-07.json` and the raw runs in `results/h3-tp2-production-2026-11-07/`.
