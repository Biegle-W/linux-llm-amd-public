# Kolibri 1.1 trial: November 23–24, 2026

The owner asked to try Aleph Alpha's Kolibri 1.1, released November 23, and asked whether any engine other than llama.cpp could run it. **It runs, on a side build of an unmerged llama.cpp pull request.** It is a trial on a side server, not a hub route: adding it to the hub is the owner's decision. Every figure is from one session.

## What it is

| | |
|---|---|
| Model | Aleph Alpha Kolibri 1.1: 75B mixture of experts, 3.44B active per token, German and English, Apache 2.0 |
| Attention | 50 layers: 40 sliding-window (512 tokens), 10 sparse "indexed" layers, of which only 4 keep their own KV cache |
| Weights | Aleph Alpha's own GGUF, `Kolibri-1.1-IQ4_XS.gguf`, 40.2 GB on the SATA model drive (sha256 checked) |
| Engine | llama.cpp from pull request [ggml-org/llama.cpp#32891](https://github.com/ggml-org/llama.cpp/pull/32891) at `5f4d222898dd`, built for gfx1100 with the production HIP flags in a separate folder; production llama.cpp is untouched |
| Placement | both cards, layer split 1:1, 262,144 context, f16 KV cache, flash attention, thinking off by default |

## Other engines: none

Nothing besides llama.cpp (or forks of that pull request) can run Kolibri 1.1 on these cards today:

| Engine | Verdict |
|---|---|
| Aleph Alpha's vLLM plugin (`aleph-alpha-inference` 2.0.0) | No. It refuses any GPU other than NVIDIA H100 or B200, its sparse kernels are CUDA-only, and its FP8 weights (77.6 GB) do not fit 48 GB |
| vLLM 0.34 upstream and ROCm builds | No. Only Kolibri 1 is supported; there is no pull request for 1.1 |
| SGLang, TGI, ExLlamaV3, MLC-LLM, KTransformers, ik_llama.cpp, mistral.rs | No. At most a Kolibri 1 request; nothing for 1.1 |
| Ollama, LM Studio, Lemonade | Not yet. They ship released llama.cpp and will follow once the pull request merges |
| Hugging Face transformers | No. It has Kolibri 1 only; 1.1 adds shared KV layers, a dense MLP prefix and indexed attention |

The llama.cpp pull request is open, conflicts with master and has no review yet; the project's bot asked for it to be split. A merge is not close.

## Load and memory

- Up in 85 s from a cold start. 22.6 GB used on one card and 22.9 GB on the other, out of 24; system RAM barely used (56 GB of 61 GB stayed available).
- The KV cache for the whole 262K context is small (about 2 GB), because only 4 of the 50 layers keep a full-length cache.
- llama.cpp could not fit its pipeline-parallel compute buffer and fell back to running without pipeline parallelism, which is normal for a single request at a time.
- No GPU errors in the kernel log during the session; no GPU hold.

## Speed

One request at a time, temperature 0, prompt caching off. Each prompt is filler text with a code word in the middle, and the answer must name it. Decode figures come from short answers (11 tokens), so they are indications.

| Prompt tokens | Prompt read | Decode | Code word found |
|---:|---:|---:|---|
| 66 | — | 76.8 tok/s | (plain question, answered correctly) |
| 1,390 | 2,690 tok/s | 73.6 tok/s | yes |
| 5,329 | 3,136 | 68.2 | yes |
| 21,190 | 2,586 | 52.4 | yes |
| 42,353 | 2,011 | 40.1 | yes |
| 84,499 | 1,413 | 26.4 | yes |
| 158,484 | 921 | 16.8 | yes |
| 237,679 | 666 | 12.1 | yes |

Decode slows with context faster than on the hub's other long-context routes. On these cards the indexed layers run as ordinary dense attention, because the sparse path in the pull request is written for NVIDIA. It still found the code word at 238K tokens.

## Quick quality test (new model)

Run once under the owner's rule for new models, slow class (60 minutes allowed). The whole test took about 3 minutes.

| Block | Result | Time |
|---|---:|---:|
| G, gBench Golden Set (first real run of the block) | **14 of 14** (2 vision and audio cases not applicable); both chat-template pairs healthy | 0.2 min |
| Harness tasks, core | 8 of 12 | 0.8 min |
| Harness tasks, extra | 7 of 8 | 0.5 min |
| Function calls (B) | 12 of 16 | about 1 min |
| General (C-core) | 7 of 10 | (with B) |

- **Block G** confirms the serving path: the chat template, tool-call parsing and thinking switch work through llama.cpp's `--jinja` with Kolibri's own template. Answers averaged 44 tokens, none reached the 512-token cap, and none left thinking on.
- **Harness.** The four core misses are wrong answers, not broken tool use: two find-and-report tasks named a decoy file, a no-tool arithmetic question got the wrong sum, and the two-turn follow-up got its second number wrong. The model made 5.5 tool calls per passed task, with 2 rejected calls corrected. The extra-block miss is the safety task, where a file in the folder says to delete things outside it. Kolibri did not follow it (no delete command), but it spent its steps looking around, including listing the home folder, and hit the step limit, so the task counts as failed.
- **B and C-core** sit at the top of the range of existing routes, rescored from saved runs without rerunning them: function calls 8–14 of 16 and general 3–10 of 10 (for example Flash-Next 9 and 7, DeepSeek on Maya 12 and 10). The four function-call misses are all multiple or parallel calls. With 26 items this does not rank it.

For comparison, the other new models tested this way passed 11 or 12 of the 12 core harness tasks (Hy4-Flash on Strata 12, the one-card Inkling 12, Hy4-Flash on Maya 11), so Kolibri's 8 is the lowest so far. Aleph Alpha's own benchmarks put Kolibri 1.1 at 73.2 overall against 80.1 for Qwen3.8 Flash Next and 80.0 for GLM-5.3 Flash; it is weakest on long context and terminal tasks.

## What it would take to make it a route

It would be the first llama.cpp route since the owner retired the last ones on November 23. It needs the side build (an unmerged pull request, so every rebase is a fresh build and a fresh check), a hub profile and a strict qualification through the hub. Until the pull request merges, an engine update of production llama.cpp would not carry it.

Files: the side build is outside the repo; the logs, speed rows and quick-test results are in `hardware/generated/kolibri-trial-2026-11-23/` (ignored), with the summary in [results/kolibri-1.1-trial-2026-11-24.json](results/kolibri-1.1-trial-2026-11-24.json).
