# Diffusion re-validation, H3 P2P and Radiance on RDNA3 — November 7, 2026

Layout: [AMD working setup](../hardware/AMD-WORKING-SETUP-2026-11-07.md): PowerColor GPU 0 at `0b:00.0`, Sapphire GPU 1 at `13:00.0`, both behind the switch. Owner request: "What about diffusion models? What about P2P for minimax H3? What about AMD radiance for RDNA3 7900XTX? Research on forums and set them up."

## Device order for graphics

`graphics/runtime_selection.py` previously hard-coded and enforced device order `1,0`. In this layout that would place the H3 denoiser on the Sapphire. It now returns the recorded `qualified_device_order`, accepting `1,0` for the earlier layout and `0,1` for this one. `graphics/runtime-versions.json` records `0,1`, so the PowerColor stays GPU 0 (denoiser) and the Sapphire GPU 1 (encoders and VAEs). The unit tests were updated and pass.

## Production workflows re-validated (ComfyUI 0.44.0, guarded launcher)

| Workflow | Output | Request s | Earlier reference s |
|---|---|---:|---:|
| Qwen-Image 2.1 BF16 (`qwen-image-2.1-base-api.json`) | 512×512 PNG, coherent red teapot and cup | 90.4 | 100.9 (Oct 18) |
| FLUX 3 Image Klein (`flux3-klein-t2i-api.json`) | 1024×1024 PNG, lighthouse with legible "LOCAL LLM" text | 92.7 | — |
| MiniMax H3 INT8 with the projected 8B encoder (`minimax-h3-base-api.json`) | 608×352, 39 frames H.264 plus stereo 32 kHz AAC; frames 1, 20 and 39 show a coherent steaming teapot | 126.3 | 232.4 (Oct 18, earlier encoder) |

One request each, staged placement (DiT on GPU 0, encoder and VAEs on GPU 1), not tensor parallel. No amdgpu kernel errors. Results are in `graphics/results/validation-2026-11-07-*.json`.

## Radiance on RDNA3

- **Radiance H3 (video) has a working RDNA3 path: fcys's `tp2-comfy`.** *Correction: an earlier draft of this report said there was no 7900 XTX path. That was wrong.* Only Bunsei's native `libr4d` kernels are RDNA4-only (they need FP8 WMMA; see the [October 28 preflight](RADIANCE-H3-PREFLIGHT-2026-10-28.md)). The community RDNA3 port runs H3 as two-card tensor parallelism. It uses two ComfyUI processes, one per card, joined by RCCL: the DiT heads are split 56→28 and the FFN 14336→7168, with a bf16 all-reduce after `out_proj` and `fc2` and CK attention. lcz.me threads:
  - topic 2826: terry's write-up;
  - topic 2705: fcys, 1.65–1.87× per step on 2×7900 XTX;
  - topic 2803: setup notes;
  - topic 2866: Goitex, with RCCL `isAllDirectP2p 1`, P2P/IPC at 12–13.5 GB/s and 24.6 s per step at 1344×768.

  The local copy (`fcys-rccl-ck-20261028`, [qualification](H3-FCYS-QUALIFICATION-2026-10-28.md)) produced correct 39-frame clips here on October 28. At that time P2P was forced off, because peer access did not work before the switch. The P2P comparison is below.
- **bigcherry gfx1100 LLM port** ([PR #109](https://github.com/audiagentic/bigcherry/pull/109)) is closed and unmerged: 28 of 66 units compiled unchanged, with operator checks only and LLM targets only. It is not needed for H3.
- **Radiance vLLM for gfx1100** ([mkadrlik/vllm-radiance-p2p](https://github.com/mkadrlik/vllm-radiance-p2p)) is a Docker image based on Radiance 0.5.7 and vLLM 0.26.0. Its own Qwen3.8-27B AWQ TP2 + MTP figure on 2×7900 XTX is 23.8–28.9 tok/s single-stream. It states that one-shot custom all-reduce is not viable on RDNA3 consumer PCIe, and its fast-reduce path hangs (`RADIANCE_FAST_REDUCE=0` by default). The qualified local vLLM TP2 route measured 80–87 tok/s on November 7. Not deployed.
- **P2P on this host.** The vLLM RDNA3 tracking branch ([PR #57925](https://github.com/vllm-project/vllm/pull/57925)) reports peer reads returning zeros on a Z790 chipset host but working behind a PCIe switch. On November 7 this host's peer integrity check (direct and IPC, both directions, read and write) passed through the switch.

## H3 two-card P2P

Every earlier two-card H3 path used host-staged transport because peer access was unavailable. The October 28 [one-vs-two comparison](H3-ONE-VS-TWO-2026-10-28.md) shows the cost: the host-staged sampler took about 60 s against about 30 s on one card. The two-card request was faster only because it avoided loading swap.

**Result: fcys `tp2-comfy` runs over direct P2P on this host, with correct output.**

Method:
- Workload: the October 28 quality diagnostic, unchanged. MiniMax H3 INT8 (`plugin-tp`), CK attention, 608×352, 39 frames, 20 steps, seed 42.
- Inputs: the same hash-pinned teapot conditioning.
- Ranks: two ComfyUI processes. Rank 0 is the PowerColor (`0b:00.0`), rank 1 the Sapphire (`13:00.0`).
- RCCL: 2.27.7, 1 channel, 1 MiB buffers, `NCCL_PROTO=Simple`.
- Guards: the guarded runner with a 3 GiB host floor and the VRAM floors. A thermal log was kept for each run, and every run was taken under the GPU lock and released.

| Run (Nov 7 unless noted) | RCCL transport | Lifecycle s | Sampler (20 steps) | Steady step s | Latent vs Oct 28 |
|---|---|---:|---:|---:|---|
| Oct 28, before the switch (`canary-tequality-w4a8-hip-teapot-39-s1`) | SHM/direct (no peer access) | 146.2 | 94 s (68 s to step 1, loading under swap) | 1.33 | reference (passed visual review) |
| `NCCL_P2P_DISABLE=0` | **P2P/IPC**, `isAllDirectP2p 1` | 42.2 | 27 s | 1.05 | bit-identical (cos 1.00000) |
| `NCCL_P2P_DISABLE=1` | P2P/IPC (flag ignored) | 57.2 (cold) | 27 s | 1.05 | cos 0.99979, rel L2 0.021 |
| `NCCL_P2P_DISABLE=1` + `NCCL_P2P_LEVEL=LOC` | P2P/IPC (flags ignored) | 41.7 | 27 s | 1.06 | cos 0.99979, rel L2 0.021 |

Findings:
- **P2P is now used automatically.** RCCL 2.27.7 logs both disable settings and still selects P2P/IPC once KFD reports a direct peer link. This is the same RCCL build that fell back to SHM on October 28, when no peer link existed. A same-day SHM control was therefore not possible through the environment. The October 28 SHM run is the comparison.
- **Per-step speed: 1.05 s against 1.33 s, about 21% faster.** The step after warm-up is the cleanest comparison. The step makes 104 all-reduces, enough to bound it by transport latency at this size, so the gain is modest. Goitex's 12–13.5 GB/s matters more at 1344×768 and above.
- **End-to-end: 42 s against 146 s.** Most of that gain comes from loading without swap (61 GiB RAM, warm page cache), not from the transport.
- **Quality.** All latents are finite. The `P2P_DISABLE=0` latent is bit-identical to the October 28 reference, which passed visual review. The two `P2P_DISABLE=1` runs match each other exactly and differ from the reference by cos 0.9998. That difference is the flag changing RCCL's reduction schedule, not a transport error.
- **Health.** There were no guard faults, swap or amdgpu errors. Minimum free VRAM was 7.0 GiB on GPU 0 and 12.5 GiB on GPU 1.

The working config is fcys `tp2-comfy` with `NCCL_P2P_DISABLE=0` (or unset). It runs on the current [working layout](../hardware/AMD-WORKING-SETUP-2026-11-07.md) with `ROCR_VISIBLE_DEVICES` set to the rank. It remains a guarded experimental route; the production ComfyUI workflow above still uses staged placement. Numbers: `results/h3-p2p-2026-11-07.json`.
