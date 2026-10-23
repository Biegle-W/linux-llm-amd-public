# Windows local LLM — RTX 3060

Current Windows reference, validated 23 October 2026. This is a separate machine from the Linux dual-RX-7900-XTX build. Linux profiles, runtimes and benchmarks remain independent.

| Component | Validated Windows configuration |
|---|---|
| Hardware | i5-13600KF, 16 GB DDR5 at 6000 MT/s, RTX 3060 12 GB |
| Runtime | llama.cpp b11630 (`6868a52cb`), CUDA 13.4, NVIDIA 610.88 |
| Model | Qwen3.5 9B UD-Q4_K_XL, text only |
| Profile | 32,768 allocated context, all 33 layers on CUDA0, Q8 K/V, Flash Attention |
| Short decode samples | 50.74 / 50.90 tokens/s (two 128-token-limit samples) |

Chat, streaming, tool round trip and 8,080-token input retrieval passed. Allocation is not a full-32K quality or stress test. Measurements describe this complete profile and are not a controlled comparison with Linux or archived dual-NVIDIA results. See [curated evidence](reports/WINDOWS-RTX3060-20261023.md) and [numeric record](reports/windows-rtx3060-summary-20261023.json).

## Prepare and launch

This directory is a reference distribution: install the runtime and download weights separately. Binaries, models and private app data are excluded.

1. Put the matching CUDA runtime at `runtimes/llama.cpp-b11630-cuda-13.4/` under this directory. The launcher expects Python at `runtimes/python/cpython-3.11.15-windows-x86_64-none/python.exe`; install that runtime, a compatible NVIDIA driver and Windows Terminal.
2. Download [Qwen3.5-9B-UD-Q4_K_XL.gguf](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF/tree/3885219b6810b007914f3a7950a8d1b469d598a5). The example profile uses `C:\Models`; another local location, including Downloads, can be registered:

```powershell
python scripts/register_model.py 'C:\Models\Qwen3.5-9B-UD-Q4_K_XL.gguf' --id Qwen3.5-9B-UD-Q4_K_XL --name 'Qwen3.5 9B (UD-Q4_K_XL)' --context 32768 --full-gpu --default
```

3. Open `Start Local LLM.cmd`. The owned backend opens in the visible Local-LLM terminal. The authenticated OpenAI-compatible API is `http://127.0.0.1:10000/v1`, model ID `Qwen3.5-9B-UD-Q4_K_XL`.

The launcher discovers the RTX 3060 UUID and exposes it as CUDA0. It refuses a missing/wrong GPU or model and requires at least 8 GiB actual free VRAM for this profile. One model runs at a time. Split mode is none, batch/microbatch 512/128, thinking off, no speculation, no CPU weight offload. Host RAM remains necessary; available host RAM after test load was 2.28 GiB. Do not run a benchmark worker beside a loaded production model. Stop the owned backend first with `scripts/Start.ps1 -Mode Stop`.

## Clients and maintenance

The private key is generated/stored in `data/credentials/.local-api-key`. Do not commit it. DSH uses the `LLAMA_CPP_API_KEY` credential route; configure that variable or the app's credential service locally. The saved Windows DSH catalog/default was updated, but its Desktop executable was unavailable, so GUI/SDK use was not validated. Native authenticated API streaming passed.

Tailscale forwarding selects only port 10000 while Windows Strata is disabled. Use `http://<TAILSCALE_HOST>:10000/v1` with the same real key. IPv4/MagicDNS host self-checks passed; a remote peer was not tested. No Funnel or Linux network policy was changed. LAN forwarding was not reconfigured/revalidated during this restoration.

`config/selected-profiles.json` and `config/stack.json` are the sources; `scripts/build_configuration.py` regenerates catalogs. The stale Windows dual-AMD draft is retired. Strata is disabled for this single-3060/16-GB reference; its historical source/settings remain, with setup/launch/verification refusing while disabled. Do not enable Linux AMD profiles here.

Keep Windows changes under `windows/`, preserve all Linux settings and historical measurement attribution, publish example paths and curated results only. Never commit runtime binaries, weights, keys, addresses, raw logs or private histories. This restoration reuses a validated runtime and does not claim a latest-version upgrade.
