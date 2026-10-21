# vLLM/SGLang alternatives for Bolt and Sage — research, October 21, 2026

**Question:** the user asked whether the slower llama.cpp profiles have SGLang or vLLM builds
that could run much faster on the two RX 7900 XTX cards.

**Scope:** research only. Nothing was downloaded, loaded or benchmarked, and no
profile changed. Super-VL 120B is excluded: even at 4 bits its weights exceed the 48 GiB
of VRAM, and SGLang/vLLM keep weights on the GPUs. Qwen3.8-27B already has faster active
SGLang and vLLM profiles.

## Nemotron-3.5-Bolt 74B-A9B

Bolt's architecture is `NemotronH_Omni_Reasoning_V3`. Its text model is
`nemotron_h_puzzle`: a pruned Super-VL with a hybrid Mamba-2/attention backbone, a
latent MoE, and RADIO vision plus audio towers. It has no MTP layer.

| Candidate (pinned revision) | Format | Size | Fits 2×24 GiB? |
|---|---|---:|---|
| [SergiioB AutoRound W4A16](https://huggingface.co/SergiioB/Nemotron-3.5-Bolt-74B-A9B-AutoRound-W4A16-G128-sym/tree/b9f381d20cbd4cede9f729c2647d2542c4a35997) | GPTQ int4, group 128, symmetric (vLLM) | 43.6 GB / 40.6 GiB | **Probably, with little room left** |
| [cyankiwi AWQ-INT4](https://huggingface.co/cyankiwi/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-AWQ-INT4/tree/3df8bd99af5d58abe5f052ef81127dff092f26b4) | compressed-tensors | 55.4 GB | No |
| NVIDIA 24GB / NVFP4 / MLX / EXL3 builds | NVFP4 with ggml packing, Apple MLX, ExLlamaV3 | — | Not usable by ROCm vLLM/SGLang |

The AutoRound card reports **60.5 t/s decode and 2,925 t/s prefill** (886-token prompt, one
request) on two Intel Arc Pro B70 cards with vLLM 0.31.0 XPU, TP2. It also says the
model's 262,144-token maximum context loads. These are self-reported results, not
independently reproduced.

**Local engine support (vLLM 0.32.1rc1.dev36 ROCm):**
- It registers `NemotronH_Omni_Reasoning_V3` and `NemotronHPuzzleForCausalLM`.
- GPTQ is in its ROCm quantization list.
- Its MoE oracle prefers a native **gfx1100 W4A16 MoE HIP kernel**
  (`moe_gptq_gemm_rdna3`, built into the installed `_rocm_C`). That kernel accepts
  symmetric int4 and non-gated activations such as Bolt's `relu2`.
- The local SGLang fork (f84475cc) has `nemotron_h` and a `nemotron_h_puzzle` config, but
  its ROCm int4 MoE path on gfx1100 is unverified. vLLM is the better candidate.

**Risks**
- *Memory:* 40.6 GiB of weights leaves about 7 GiB across both cards before
  runtime overhead. Context will be limited, though the hybrid design keeps the KV cache small.
- *Mamba-2 kernels on gfx1100:* untested here.
- *Quantization:* a single uploader made it, with locally patched calibration code.

**Rough expectation:** the 7900 XTX has about 1.6× the B70's memory bandwidth. Decode might
reach roughly 60–90 t/s, against 36.9/36.6 now. Prefill could be about 10× faster, against
224 t/s now. This is an estimate to test, not a measurement.

## Sage-A1.5 (Qwen3.5-MoE, 256 experts, 3B active)

| Candidate (pinned revision) | Format | Size | Assessment |
|---|---|---:|---|
| [InternScience FP8 (official)](https://huggingface.co/InternScience/Sage-A1.5-FP8/tree/193ce46fd184f486f9e2413f194cd5f560da9108) | compressed-tensors, FP8 per-channel weights **and dynamic FP8 activations** | 39.4 GB | Fits, but RDNA3 has no FP8 matrix hardware. W8A8 FP8 is likely unavailable or emulated on gfx1100. **Not recommended.** |
| Community builds published today | GGUF, MLX "oQ4e" | — | Not vLLM/SGLang formats |
| *Self-made AutoRound W4A16* from [official BF16](https://huggingface.co/InternScience/Sage-A1.5/tree/3e6b02c5e6afbc481fd4556baca8e6009f26d696) | GPTQ int4, the same method as the active Qwen3.8 vLLM model | about 20 GB (estimate) | Would fit with a large cache and use the gfx1100 MoE kernel. Needs the 71.9 GB BF16 download and hours of calibration. |

vLLM dev36 registers `Qwen3_5MoeForConditionalGeneration` and Qwen3.5 MTP. The active
Qwen3.8-27B vLLM profile already runs the same family's hybrid linear attention on these
cards. **No ready 4-bit vLLM/SGLang build of Sage exists yet;** the model was released
today, so one may appear. Sage is not slow now (83/67 decode t/s), but its llama.cpp prefill
(387 t/s) is the part vLLM could improve most.

## Forum evidence (required sources)

- No lcz.me or Level1Techs report covers Bolt or Sage on vLLM/ROCm.
- [Level1Techs: R9700 TP2/TP4 guide](https://forum.level1techs.com/t/amd-radeon-r9700-linux-tp2-and-tp4-the-definitive-guide/250504)
  runs Qwen3.5-122B-A10B GPTQ-Int4 on RDNA4 with AITER MoE kernels. It is RDNA4-specific,
  not gfx1100.
- [Level1Techs: vLLM/ROCm 7.14 on 4× R9700](https://forum.level1techs.com/t/vllm-0-23-x-rocm-7-14-upgrade-on-4x-radeon-ai-pro-r9700-50-regression-on-one-model-unaffected-on-another-but-a-free-9-via-kernel-tuning/253460)
  reports about a 50% regression for an FP8 MoE model after an upgrade. That is RDNA4 again, but it
  warns that FP8 MoE paths on Radeon are fragile.
- [Level1Techs: "I need help with ROCm"](https://forum.level1techs.com/t/i-need-help-with-rocm/242075)
  (Froz04, December 6, 2025) reports about a week of failed vLLM setup on two 7900 XTX cards.
  This workstation already runs TP2 vLLM successfully.
- [Level1Techs: 7900 XTX inference notes](https://forum.level1techs.com/t/7900xtx-llm-inference-notes/250869)
  (ivgranite, May 31, 2026) and the
  [lcz.me 7900 XTX Qwen3.6-27B ROCm/Vulkan notes](https://lcz.me/topic/353) both use
  llama.cpp on a single card. Neither tests vLLM MoE.

## Follow-up

The Bolt test ran the same day ([results](BOLT-VLLM-2026-10-21.md)). Decode was unchanged
(38 vs 37 t/s), prefill was about 13× faster, and the 262K window held. The earlier decode
estimate was too optimistic, because the MoE ran on the generic Triton kernel.

## Recommendation

1. **Bolt AutoRound W4A16 on vLLM** is the one candidate worth testing. It needs a
   43.6 GB download (sharedSATA2 has 932 GB free) and an isolated vLLM test under the GPU lock.
   Start at 32K context, then raise it if memory allows. Keep the llama.cpp Bolt profile unless
   the test passes the usual checks and is clearly faster.
2. **Sage:** wait for a community GPTQ/AWQ build, or make one with AutoRound if the user wants
   it. Do not use the FP8 build on RDNA3.
3. **Super-VL 120B:** no vLLM/SGLang path fits the 48 GiB of VRAM. Keep llama.cpp.
