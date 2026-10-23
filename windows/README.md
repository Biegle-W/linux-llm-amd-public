# Windows local LLM — RTX 3060

Current Windows reference, validated 23 October 2026. This is a separate machine from the Linux dual-RX-7900-XTX build. Linux profiles, runtimes and benchmarks remain independent.

| Component | Validated Windows configuration |
|---|---|
| Hardware | i5-13600KF, 16 GB DDR5 at 6000 MT/s, RTX 3060 12 GB |
| Runtime | llama.cpp b11630 (`6868a52cb`), CUDA 13.4, NVIDIA 610.88 |
| Model | Ornith 1.5 35B-A3B IQ2_S MoE, text only |
| Profile | 32,768 allocated context, GPU + RAM weights, Q8 K/V, Flash Attention |
| Short decode samples | 48.24 / 44.29 tokens/s (two 128-token-limit samples) |

Chat, streaming, tool round trip and 8,080-token input retrieval passed. Allocation is not a full-32K quality or stress test. Measurements describe this complete profile and are not a controlled comparison with Linux or archived dual-NVIDIA results. See [curated evidence](reports/WINDOWS-MOE-MODELS-20261023.md) and [numeric record](reports/windows-moe-summary-20261023.json).

## Prepare and launch

This directory is a reference distribution: install the runtime and download weights separately. Binaries, models and private app data are excluded.

1. Put the matching CUDA runtime at `runtimes/llama.cpp-b11630-cuda-13.4/` under this directory. The launcher expects Python at `runtimes/python/cpython-3.11.15-windows-x86_64-none/python.exe`; install that runtime, a compatible NVIDIA driver and Windows Terminal.
2. Download [Ornith-1.5-35B-A3B-IQ2_S.gguf](https://huggingface.co/bartowski/Ornith-1.5-35B-A3B-GGUF/tree/64b0493d34a5ca4c1b4ad67bb99b41d74b4f07d6). The example profile uses `C:\Models`. Update its path in `config/selected-profiles.json` if different, preserving all options/admission fields; run `python scripts/build_configuration.py` to regenerate. Do not use `--full-gpu` for this mixed profile.

3. Open `Start Local LLM.cmd`. The owned backend opens in the visible Local-LLM terminal. The authenticated OpenAI-compatible API is `http://127.0.0.1:10000/v1`, model ID `Ornith-1.5-35B-A3B-IQ2_S`.

The launcher discovers the RTX 3060 UUID and exposes it as CUDA0. It refuses missing/wrong hardware or weights. This mixed profile requires at least **4 GiB available RAM,16 GiB commit headroom and9,728 MiB actual free VRAM** before fresh start. Keep one model loaded; stop the owned backend with `scripts/Start.ps1 -Mode Stop` before benchmarking.

Selected options: fit on, GPU layers auto, **fit-target2816**, **no-host true**, split none, batch/microbatch512/128, Q8 KV, thinking off, no speculation. Measured normal model buffers:7,840.74 MiB GPU /2,643.67 MiB host; after streaming:1,571MiB actual free VRAM /1.19GiB available RAM. One short-generation sample reached1,336MiB free VRAM, so fitter target is not guaranteed headroom.

Both newer community MoEs passed functional tests: September's Empero Qwen3.8 distillation and August's Ornith1.5. Empero's IQ2_M and earlier Qwen3.5 weights remain downloaded but outside the active catalog. Empero is distilled into Qwen3.6 architecture; do not mistake its name for an official small Qwen3.8 release. Early faster trials used much less desktop VRAM headroom. Low-bit quantization and these functional checks do not establish answer-quality superiority. [All trials, hashes and limitations](reports/WINDOWS-MOE-MODELS-20261023.md).

## Clients and maintenance

The private key is generated/stored in `data/credentials/.local-api-key`. Do not commit it. DSH uses the `LLAMA_CPP_API_KEY` credential route; configure that variable or the app's credential service locally. The saved Windows DSH catalog/default was updated, but its Desktop executable was unavailable, so GUI/SDK use was not validated. Native authenticated API streaming passed.

Tailscale forwarding selects only port 10000 while Windows Strata is disabled. Use `http://<TAILSCALE_HOST>:10000/v1` with the same real key. IPv4/MagicDNS host self-checks passed; a remote peer was not tested. No Funnel or Linux network policy was changed. LAN forwarding was not reconfigured/revalidated during this restoration.

`config/selected-profiles.json` and `config/stack.json` are the sources; `scripts/build_configuration.py` regenerates catalogs. The stale Windows dual-AMD draft is retired. Strata is disabled for this single-3060/16-GB reference; its historical source/settings remain, with setup/launch/verification refusing while disabled. Do not enable Linux AMD profiles here.

Keep Windows changes under `windows/`, preserve all Linux settings and historical measurement attribution, publish example paths and curated results only. Never commit runtime binaries, weights, keys, addresses, raw logs or private histories. This restoration reuses a validated runtime and does not claim a latest-version upgrade.
