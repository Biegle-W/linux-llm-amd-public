# Shared models and benchmarks (AMD and NVIDIA servers)

Owner, November 26, 2026: both LLM servers run the same models and the same benchmarks. Different weights are fine; the model set has to match. This folder is byte-identical in `linux-llm-amd` (`benchmarks/shared/`) and `linux-llm-nvidia` (`benchmarks/shared/`), and is exported unchanged to both public repos (`linux/benchmarks/shared/` on AMD's). Change it in both private repos in the same way, then export.

| File | What it defines |
|---|---|
| [models.json](models.json) | The shared API names, the shared model set with each server's routes and weights, and the routes only one server runs |
| [benchmarks.json](benchmarks.json) | The quality ranking test, the engine-update check and the speed report fields |
| [tooluse-short-manifest.json](tooluse-short-manifest.json) | The 55 frozen items of the short tool-use test (ids and hashes only, no item text) |
| [check_shared.py](check_shared.py) | Checks one server against all of the above; reads files only |

Hardware-specific parts stay in each repo: engines and their launch settings, quants, context, placement, guards, load caps and GPU holds.

## Models

Seven models run on both servers, on the same engines: Qwen3.8-27B (vLLM and SGLang), Qwen3.8-Flash-Next (Strata), DeepSeek-V4.1-Flash-1017 (Maya and Strata DeepSeek), GLM-5.3-Flash (Maya), Inkling 2 Mini (Strata), Kolibri 1.1 (llama.cpp) and Hy4-Flash (Strata). Each server picks the quant that fits it, so Inkling, Hy4-Flash, Kolibri and GLM use different weights on each side.

Server-specific extra routes, kept as they are: `ripple-65b-vllm` on AMD and `hy4-flash-maya` on NVIDIA (a second engine for Hy4-Flash). They are listed under `extra` in `models.json`.

When a model is added on one server, list it in `models.json`: under `models` if both servers run it, under `extra` if only one does.

## API names

The model names clients see through each server's OpenAI-compatible API are the same on both servers (owner, November 26). `api_names` in `models.json` maps each shared name to the internal route that serves it on AMD and on NVIDIA. `/v1/models` lists the shared names, and requests may use either the shared name or the old internal route id, so saved client selections keep working. A response carries the name the request used. The two extra routes keep their names: `ripple-65b-vllm` and `hy4-flash-maya`.

| API name | AMD route | NVIDIA route |
|---|---|---|
| `qwen3.8-27b-vllm` | `qwen3.8-27b-vllm` | `qwen27b-hyperqwen` |
| `qwen3.8-27b-sglang` | `qwen3.8-27b-sglang-dflash2` | `qwen27b-sglang` |
| `qwen3.8-flash-next-strata` | `qwen3.8-flash-next-iq3_xxs` | `flash-next-strata` |
| `deepseek-v4.1-flash-maya` | `deepseek-v4.1-flash-1017-maya-unsloth-q1` | `deepseek-maya` |
| `deepseek-v4.1-flash-strata` | `deepseek-v4.1-flash-1017-strata-unsloth-q1` | `deepseek-unsloth-strata` |
| `glm-5.3-flash-maya` | `glm-5.3-flash-maya` | `glm-maya` |
| `inkling-2-mini-strata` | `inkling-2-mini-sq-20-strata-2gpu` | `inkling-strata` |
| `kolibri-1.1-llamacpp` | `kolibri-1.1-iq4_xs` | `kolibri-llamacpp` |
| `hy4-flash-strata` | `hy4-flash-sq-64-strata` | `hy4-flash-strata` |

## Benchmarks

1. **Quality ranking: the short tool-use test.** BFCL v4, 55 frozen items, seed 20261122, temperature 0.6, top-p 0.95, 2,048 output tokens, thinking as served, one request at a time. 120 s per single-turn item and 480 s per episode; item budget 690 s (small group, 49 items) or 3,360 s (large group, 55 items). Score = 50 × single-turn correct / 40 + 50 × core episodes passed / 9. Both groups are ranked on the same 49 items. The item list is NVIDIA's frozen `fast-1` list; until November 26 AMD used its own draw of other items, so AMD scores from before then are not on these items.
2. **Engine-update check.** One strict DSH read-tool round trip with an owned unload, then the six gBench 0.5.0.post1 Golden Set cases for chat templates and tool calls. AMD: `hardware/quant-eval/quick/run_golden.py --engine-check`. NVIDIA: `scripts/gbench_template_check.py`.
3. **Speed report.** Measured on that round trip from a cold start. Report the model and quant, the engine and version, prompt tokens, prompt read tok/s, time to first token, decode tok/s, answer tokens, context, and weights size and drive. Say whether the prompt cache was reused, and that one run is one run.

Not shared yet: AMD's rank tier (`hardware/quant-eval/rank`), NVIDIA's mix quality test (`docs/QUALITY-MIX-TEST-PLAN.md`; neither is the ranking) and the archived deep suites (AMD 216 items, NVIDIA 390 items).

## Check

```sh
python3 benchmarks/shared/check_shared.py --server amd      # on the AMD server, from the repo root
python3 benchmarks/shared/check_shared.py --server nvidia   # on the NVIDIA server; reads ~/quality-eval-build/quality/fast/manifest.json
```

It exits 1 if a shared model has no enabled route, an enabled route is not listed, the tool-use items differ or the gBench cases differ. Routes listed under `extra` are reported as notes, not failures.
