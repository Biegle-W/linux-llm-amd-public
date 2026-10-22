# Optimizing the large, slow models — community research, October 22, 2026

The user asked for optimizations for the large, slower models from forums, Reddit, X and
YouTube. **Research only:** nothing was changed or measured locally. The models in scope:

| Model (engine) | Decode t/s code/prose | Fresh ~8K prefill t/s | Where the time goes |
|---|---:|---:|---|
| Ornith-1.5-122B (llama.cpp, 30 CPU expert layers) | 11.4 / 13.3 | 52.7 | CPU experts (~41 GiB in RAM) |
| Nemotron-3.5-Super-VL 120B IQ3 (llama.cpp) | 15.9 / 16.9 | 98.5 | CPU experts (~19 GiB in RAM) |
| DeepSeek-V4.1-Flash Maya-S (Maya) | 6.9 / 7.1 | 187 | RAM-resident experts |
| GLM-5.3-Flash Maya-S (Maya) | 18.0 / 16.1 | 533 | RAM-resident experts |
| Nemotron-3.5-Bolt (vLLM) | 37.3 / 37.2 | 2,959 | Triton int4 MoE kernel |

The llama.cpp MoE profiles that keep some experts in RAM (Qwen3.6, Empero, Sage) share most of
the llama.cpp findings below.

## 1. Physical batch size: the largest lever (llama.cpp CPU-expert profiles)

Every llama.cpp profile here inherits `batch-size = 512` and `ubatch-size = 128` from the
October 16 GPU-resident Bolt setup. That value was never tuned for CPU-resident experts.

When a prompt batch exceeds `GGML_OP_OFFLOAD_MIN_BATCH` (default 32, present in our build),
llama.cpp copies the CPU-resident expert weights to the GPU to process that micro-batch.
- **Ornith:** copying ~41 GiB over PCIe 4.0 x8 takes roughly 3 s. With 128-token micro-batches
  that caps prefill near ~40–50 tok/s, consistent with the measured 52.7. A 4096-token
  micro-batch spreads the same copy over 32× as many tokens.
- **Community measurements:**
  - [r/LocalLLaMA, u/coder543](https://reddit.sentinel-team.org/posts/1tany5t/snapshots/2026-05-15T23%3A40%3A01.25497Z)
    (December 2025, RTX 3090, gpt-oss-120b): prefill **380 → 1,682 tok/s** going from `-ub 512` to
    `-ub 4096`, with generation 32.3 → 32.4. At `-ub 8192`, prefill was 2,091 tok/s and generation
    fell to 30.1. Commenters report 200 → 600 tok/s on other MoE models.
  - [Doctor-Shotgun's Hugging Face guide](https://huggingface.co/blog/Doctor-Shotgun/llamacpp-moe-offload-guide)
    (January 2026) recommends `-b 4096 -ub 4096` for CPU+GPU MoE. It notes the larger compute buffer
    needs VRAM, and that on slow PCIe a higher op-offload threshold avoids copying all CPU weights
    for small prompts.
  - [@analogalok on X](https://x.com/analogalok/status/2092697021790708148): `-b 4096 -ub 4096`
    roughly doubled prefill (≈150 → 360 tok/s) on a 125B MoE on one 4090.
- **Counterpoint:** [johnnybegood on lcz.me](https://lcz.me/topic/1929) (September 25, dual 3090,
  GLM-5.3-Flash with an expert cache) saw prefill rise 340 → 415 at `UBATCH=4096`, but decode drop
  19 → 14.6. Decode must be measured too.

**Proposed local test:** an isolated sweep for Ornith and Super of `ubatch` 128/512/2048/4096 (and
8192 for Ornith) × `GGML_OP_OFFLOAD_MIN_BATCH` 32/256/1024. Use matched decode, fresh-prefill and
short-prompt TTFT, and adjust GPU expert-cache MiB if compute buffers need room. Then repeat for
Qwen3.6, Empero and Sage.

## 2. CPU threads for CPU-bound decode

Our llama.cpp profiles use `threads = 6` on an i9-13900KS (8 P-cores + 16 E-cores).
- [Level1Techs: Optimal local AI on 12 GB VRAM](https://forum.level1techs.com/t/optimal-local-ai-on-12-gb-vram/251461):
  on a hybrid CPU, the default thread count on mixed cores halved speed.
- [Level1Techs: DeepSeek R1 at home](https://forum.level1techs.com/t/deepseek-deep-dive-r1-at-home/225826):
  the sweet spot was about one thread per physical core; extra SMT threads didn't help, because RAM
  bandwidth is the limit.
- [lcz.me #1929](https://lcz.me/topic/1929): GLM decode was CPU-bound (host 78%, GPU SM 10–18%,
  PCIe ~9%).

**Proposed local test:** `threads` 6/8/16, with and without pinning to the P-cores, on Ornith
and Super decode. Keep `threads-batch` separate. Expect gains of a few to tens of percent, not
multiples.

## 3. Speculative decoding that keeps the drafter on the GPU

- Our Ornith MTP3 test lost 27%: verifying draft tokens multiplies CPU expert work.
  [sxuff's DGX Spark Ornith repo](https://github.com/sxuff/ornith-1.5-122b-gb10) also notes only
  ~36% MTP acceptance on free-form prose.
  [irr's Strix Halo launcher](https://github.com/irr/ornith-1.5-122b) gets ~30 t/s with MTP, but
  with all weights in unified memory.
- [lcz.me #1929](https://lcz.me/topic/1929): a **DFlash2 drafter on the second GPU with only
  2 draft tokens** gave +21–25% decode on CPU-bound GLM. 3, 5 or 7 drafts were worse.
- Our llama.cpp build supports `draft-dflash`. The
  [Ornith DFlash2 drafter](https://huggingface.co/incoai/Ornith-1.5-122B-DFlash2) is published
  for SGLang. Its card says acceptance roughly halves on GGUF targets, and it would need conversion.
  Low priority; MTP with `spec-draft-n-max 1–2` is a cheaper retest.

## 4. Bolt on vLLM

- NVIDIA's [Bolt 24GB page](https://research.nvidia.com/labs/nemotron/Nemotron-3.5-Bolt-24GB/)
  reports 84 TPS with its LiLiCorr drafter on RTX Spark. A
  [Classmethod DGX Spark test](https://dev.classmethod.jp/en/articles/dgx-spark-nemotron-3-5-bolt-74b-a9b-first-touch/)
  measured 61.6 tok/s with speculation in llama.cpp. vLLM support for LiLiCorr is unverified.
- Locally, the gfx1100 MoE kernel that vLLM skipped needs a compressed-tensors checkpoint.
  Repacking the AutoRound GPTQ weights into that format could raise decode without changing quality.

## 5. Not actionable here

- **ik_llama.cpp:** strong CPU-MoE results on CUDA ([Level1Techs DeepSeek Q1 guide](https://forum.level1techs.com/t/full-deepseek-q1-with-the-ik-version-of-llama-cpp-on-am5-no-distills-just-a-quant/233530)),
  but its author says 7900 XTX/ROCm "isn't a nut we've cracked yet".
- **Strata-DSV4.1** ([lcz.me #2357](https://lcz.me/topic/2357), October 16): DeepSeek V4.1 Flash
  at ~26 tok/s (DSpark ~32–40) on a 4090. It needs a custom ternary/2-bit quant of an abliterated
  base with lossy default routing, about 600 GB of SSD, and CUDA. Its expert sizes are hardcoded, and
  a separate [attempt](https://lcz.me/topic/2153) to patch mainline Strata for DeepSeek was judged
  not viable.
- **KTransformers / Apple MLX / NVFP4 builds:** they need AMX/AVX-512, Apple silicon or NVIDIA
  Blackwell. The i9-13900KS has no AVX-512 or AMX.
- **YouTube:** expert-offload tutorials
  ([MoE offload on 8 GB](https://www.youtube.com/watch?v=Ypeu57aGJd8),
  [llama.cpp expert cache](https://www.youtube.com/watch?v=moppXgqNHcc)) cover techniques already in
  use here (`-ot` expert placement, GPU expert cache). None measured a matching dual-XTX setup.

## Recommended order

1. ubatch × op-offload-threshold sweep on Ornith and Super. Cheap and isolated; the likely payoff
   is several-fold prefill.
2. Thread-count and P-core pinning sweep on the same models.
3. Apply the winners to Qwen3.6, Empero and Sage, and re-benchmark.
4. Bolt: compressed-tensors repack for the gfx1100 MoE kernel; LiLiCorr if vLLM supports it.
5. Ornith speculative retest with a 1–2 token draft only after 1–2.

All community numbers are other people's hardware and are not local speed claims.
