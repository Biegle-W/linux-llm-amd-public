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

- **Radiance H3 (video)** is still not usable on gfx1100. Its accelerated `libr4d` kernels need FP8 WMMA, which only RDNA4 (gfx12) has; see the [October 28 preflight](RADIANCE-H3-PREFLIGHT-2026-10-28.md). The only gfx1100 port effort found, [bigcherry PR #109](https://github.com/audiagentic/bigcherry/pull/109), is closed and unmerged: 28 of 66 units compiled unchanged, with operator checks only, LLM targets only, no end-to-end run and nothing for H3.
- **Radiance vLLM for gfx1100** ([mkadrlik/vllm-radiance-p2p](https://github.com/mkadrlik/vllm-radiance-p2p)) is a Docker image based on Radiance 0.5.7 and vLLM 0.26.0. Its own Qwen3.8-27B AWQ TP2 + MTP figure on 2×7900 XTX is 23.8–28.9 tok/s single-stream. It states that one-shot custom all-reduce is not viable on RDNA3 consumer PCIe, and its fast-reduce path hangs (`RADIANCE_FAST_REDUCE=0` by default). The qualified local vLLM TP2 route measured 80–87 tok/s on November 7. Not deployed.
- **P2P on this host.** The vLLM RDNA3 tracking branch ([PR #57925](https://github.com/vllm-project/vllm/pull/57925)) reports peer reads returning zeros on a Z790 chipset host but working behind a PCIe switch. On November 7 this host's peer integrity check (direct and IPC, both directions, read and write) passed through the switch.

## H3 two-card P2P

Every earlier two-card H3 path used host-staged transport because peer access was unavailable. The October 28 [one-vs-two comparison](H3-ONE-VS-TWO-2026-10-28.md) shows the cost: the two-card sampler took about 60 s against about 30 s on one card, and the two-card request was faster only because it avoided loading swap. With working P2P, the transport can move device-to-device instead. The code investigation and the P2P candidate are recorded below when complete. No P2P H3 generation has been run yet.
