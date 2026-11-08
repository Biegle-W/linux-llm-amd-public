# Ripple-65B on vLLM INT4, two-card TP over P2P — November 7, 2026

Owner request: "Why so slow? Can is run int4 in vllam or sglang?", then "Yes. Run the daily updater first. Then set up the int4 in vllm".

New hub route **`ripple-65b-vllm`**, which passed the guarded short tool-call check. It is now the only Ripple route: on the owner's request the llama.cpp route `ripple-65b` (from a separate session, [deploy notes](RIPPLE-65B-DEPLOY-2026-11-07.md)), its `llama.cpp-b12189` worktree and its 38 GB AD-Q4_K_M GGUF were removed the same evening. The llama.cpp column below is the comparison measured before removal.

## Why llama.cpp was slow

Ripple-65B is dense: every generated token reads all of its weights. llama.cpp's layer split runs half the layers on one card, then the other half on the second card, so only one card's memory bandwidth (about 960 GB/s) is used at a time. With 40.4 GB of weights the ceiling is about 24 tok/s, and llama.cpp reached 14–17. vLLM tensor parallelism makes both cards read half the weights at the same time.

## Daily updater (run first, 18:13–19:12)

| Engine | Result |
|---|---|
| llama.cpp `9c9074e` → `818ac6b` | promoted |
| Strata `ffa80d7` → `146df3c` | promoted |
| Maya `c167004` → `7bf15ac` | promoted |
| Strata DeepSeek `ffa80d7` → `146df3c` | rejected: IQ3_XXS matrix-core vs scalar 3.14e-3 against 3e-3 tolerance (the same known result as November 3); both cards bit-identical; production kept |
| vLLM, SGLang | current |

The updater follows the `rocm72` nightly vLLM line, which has not published since dev229 (October), so it cannot bring Ripple support. The idle hub llama router (no model loaded) had to be stopped first, because the updater refuses to run while any inference process exists.

## How Ripple runs on the installed vLLM dev229

vLLM added Ripple (`RicursiveForCausalLM`) on November 5 (PR #65745, commit `03bd3c6848`); dev229 predates it. Instead of a new ROCm 10 / Torch stack (the `rocm100` nightly line, never qualified here), the support is an out-of-tree plugin:

- **`vllm/ripple-plugin/vllm_ripple/`:** `ricursive.py` and `ricursive_config.py` from the PR, with only three import lines changed. `register()` adds the architecture and config to vLLM. A `vllm.general_plugins` entry point loads it only when the directory is on `PYTHONPATH`, which only `vllm/start-ripple-rocm` sets. The production vLLM environment is byte-for-byte unchanged, and a CPU check confirmed it has no Ripple entry.
- **`vllm_ripple/reasoning.py`:** an optional-think reasoning parser, `ripple_optional_think`. Ripple answers directly by default and only sometimes opens with `<think>…</think>`. dev229's `qwen3` and `olmo3` parsers treat output as reasoning until `</think>`, which moved plain answers into reasoning and broke streamed tool calls. Running with no parser leaked raw `<think>` text to clients. The new parser decides from the first text; it passed 5 streaming unit cases plus live checks. Tool calls use the existing `hermes` parser, since Ripple uses the Qwen-style `<tool_call>` JSON format.
- **Model:** `ModelCloud/Ripple-65B-Preview-GPTQ-W4A16-v2` (GPTQ 4-bit, group 128, symmetric), 35.2 GB in `sharedSATA1/vLLM-Models/Ripple-65B-Preview-GPTQ-W4A16-v2`. All 9 shards matched Hugging Face's SHA-256.
- **Settings (`vllm/start-ripple-rocm`, profile in `dsh/vllm-profiles.json`):**
  - TP2 with custom all-reduce off, so RCCL P2P/IPC carries the reductions (`isAllDirectP2p 1`, logged).
  - 64K context, BF16 KV with 3 GiB reserved per card (74,842 tokens), memory fraction 0.92.
  - TRITON_ATTN, compiled graphs with FULL_DECODE_ONLY CUDA graphs.
  - 2.5 GiB KV was too small for 64K (2.63 GiB needed).

## Results (same probes on both routes, temperature 0)

| | vLLM GPTQ W4A16, TP2 P2P | llama.cpp AD-Q4_K_M, layer split |
|---|---:|---:|
| VRAM per card | 17.03 GiB weights, 21.2 GiB with KV | ~22 GB with KV (deploy notes) |
| Decode (300–600 tokens) | **28–29 tok/s** | 14–17 tok/s |
| Prefill, 8K-token prompt | 755 tok/s (10.6 s) | 687 tok/s (11.6 s) |
| Tool call (`read_file`) | correct | correct |
| 12 known-answer questions | 12/12 | 12/12 |
| Guarded DSH short tool check | passed: 96.5 s load, 2 model steps, clean unload | not run |

There were no amdgpu or AER errors and no guard faults. The GPU lock was held for the test and released after it.

**Not done:** long-context and sustained runs, and the DFlash2 draft. The authors' 8.1 GB draft is supported upstream but would not fit next to 17 GiB of weights per card at 64K without cutting context, and needs further backported speculative-config changes.

When the daily updater's vLLM line moves to a release with native Ripple support, the plugin's `register()` skips anything vLLM already registers. The route then needs the guarded check again before the plugin is removed.
