# dsh with local inference backends

Current hardware is i9-13900KS, 64 GB RAM and two RX 7900 XTX cards.
Every active model uses both cards. The canonical catalog, contexts, measured
speeds and build versions are in the [current root README](../../README.md) and
[Linux/Windows handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md).

Backends have independent visible terminals. Start one backend, then start
`dsh` separately and select the corresponding Local provider. Switching managed
backends closes only configured inference and owned workers; DSH, the API
gateway, ComfyUI and unrelated jobs are preserved. The saved DSH default is
preserved by [configure_local.py](configure_local.py).

| Command | DSH provider | Models |
|---|---|---|
| `llm-llama` | Local llama.cpp | Five profiles, including Super IQ3 |
| `llm-sglang` | Local SGLang | Qwen 27B TP2 DFlash2 only |
| `llm-vllm` | Local vLLM | Qwen 27B compiled MTP |
| `llm-strata` | Local Strata | Flash-Next Q3, 13.5 GiB expert cap, native 256K |
| `llm-maya` | Local Maya | GLM-5.3-Flash and DeepSeek-V4.1-Flash-1017, each 32K |

The current catalog has ten active profiles. Maya passed context, memory,
normal API and model-switch checks on both cards. See [Maya setup](../maya/README.md)
and [its validation report](../hardware/MAYA-2026-10-20.md).

The harness remains `@deepseek-ai/dsh@0.2.1-rc.2` with private Node.js 24.21.0.
Its imported web settings live in ignored `data/profiles/web/cordis.patch.yml`;
refreshing model providers does not recreate legacy settings or remove sessions.
Model weights, app data, credentials and logs remain excluded from Git.

Older CUDA/single-card/pending-RAM instructions are historical. Their original
text is preserved in the [pre-Maya committed record](https://github.com/Biegle-W/linux-llm-amd-public/blob/95a052ad560b25d3559891d9b49c9779079ed504/linux/dsh/README.md)
and dated hardware reports. They do not override the current catalog or
[dual-AMD offload policy](../hardware/MOE-OFFLOAD-2026-10-18.md).

Strata Q3 and Maya now also open their own local Chat/Monitor page when ready.
DSH stays optional and separate; `--no-browser` suppresses browser opening.
[Native frontend behavior and controls](../hardware/NATIVE-FRONTENDS-2026-10-20.md).
