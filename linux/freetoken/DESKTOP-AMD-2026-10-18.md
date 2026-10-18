# FreeToken Desktop with the AMD engine — October 18, 2026

**Desktop Chat works with the isolated ROCm engine through an explicit engine
bridge. Native AMD discovery and engine installation remain incomplete.** This
was a real Desktop test: Start from the model card, enter prompts in Chat,
observe streamed text and the rendered reply, then use the model card's Stop.
The UI and its hardware results were not mocked or replaced.

## Released frontend and installed engine

- Frontend: [FreeToken Desktop v0.2.0-beta.23](https://github.com/FlashML-org/FreeToken-Web/releases/tag/v0.2.0-beta.23), Linux amd64 `.deb`.
- Package SHA256: `a10c342339e367350bcb54c8394a7d737f673f68eb86de64b26c4beeff9b9b82` (matches the GitHub release asset digest).
- Extracted executable SHA256: `c432b66a6a4667d1823282f9a8c26425822a46dc2c6c2d8a96e25e82a266a3bf`.
- Extracted with `dpkg-deb -x`; package maintainer scripts and bundled engine installer were not run. The retired system package and CUDA environment remain removed.
- Engine: existing source commit [`8f49e0af98ba444dd261af69e82d5a1841778c68`](https://github.com/FlashML-org/FreeToken/tree/8f49e0af98ba444dd261af69e82d5a1841778c68), isolated Torch `2.14.0+rocm10.1.0`.
- Observed worker mappings include `libamdhip64.so.7`, `libhipblas.so.3`, `libhipblaslt.so.1` and `librocblas.so.5`.

## Working configuration

Existing Shared-drive `Qwen3.8-27B-UD-Q4_K_M.gguf`; **GPU1 only**, TP1,
**8,192 context allocated**, 128-token prefill chunks, Triton attention, graphs
disabled, naive KV cache, memory ratio 0.75, one running request. Text only;
MTP disabled. No weights were copied or downloaded.

Set `FREETOKEN_FT_BIN` explicitly to a wrapper invoking `freetoken/run`.
`FREETOKEN_HOME` alone was insufficient in this environment, which retains a
legacy engine-path configuration. The bridge also supplies a sibling `python`
wrapper that sources `freetoken/env.sh` before invoking the ROCm environment's
Python. All wrappers, extracted binaries and test state are ignored under
`freetoken/generated/desktop-test/`.

Use isolated `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` for testing;
the user's retained Desktop settings/chat/cache directories were preserved.
The test's `config/freetoken/desktop.json` uses:

```json
{
  "version": 2,
  "enginePort": 1919,
  "serverHost": "127.0.0.1",
  "concurrency": 1,
  "memoryRatio": 0.75,
  "moeMode": "offload",
  "models_dir": "<Shared GGUF model root>",
  "extraArgs": "--gpu 1\n--tensor-parallel-size 1\n--disable-pynccl\n--cuda-graph-max-bs 0\n--max-prefill-length 128\n--attn triton\n--max-seq-len-override 8192\n--num-tokens 8192\n--text-model-only\n--cache-type naive"
}
```

Do not repeat `--max-running-requests` in extraArgs: Desktop already supplies it
from concurrency. The first trial was refused for that duplicate; the corrected
trial passed. `moeMode=offload` avoids Desktop's automatic bandwidth probe for a
GGUF whose MoE metadata is unknown; the dense worker correctly ignores MoE flags.
The initial auto mode ran a bandwidth probe before launch; it was not a model
throughput benchmark.

For the actual chat tests, thinking was set to **Off**, response budget to 256,
and streaming enabled. Temperature was 0 for the JSON/code samples (the model's
startup defaults reset the earlier temperature selection).

## Results

| Real Desktop Chat test | Result | Output tokens | Elapsed | Output t/s, end-to-end |
|---|---|---:|---:|---:|
| First arithmetic reply | Rendered `85` for `37 + 48` | 3 | 5.446 s | 0.6 |
| Warm JSON content | Correct numbers array inside a Markdown JSON fence | 38 | 1.062 s | 35.8 |
| Warm short Python code | Correct sum-of-squares function and explanation | 100 | 2.650 s | **37.7** |

The first reply includes cold first-request work; it is not representative
steady decode. These are one-run whole-response timings, including prefill,
streaming and frontend/API overhead. They do not establish a speed difference
against the earlier CLI probe (100 tokens / 2.584 s, 38.7 t/s).

Desktop Start loaded the real ROCm worker. Desktop Stop removed its worker PID
and released port 1919 before the frontend was closed. During model serving,
GPU0 stayed at about **0.026 GiB total VRAM**; GPU1 peaked at **19.009 GiB**.
Minimum available host RAM over the monitored test was **20.795 GiB**, with
**zero worker swap and zero VRAM spill**, and no memory-guard alerts. The earlier
automatic bandwidth probe briefly raised total GPU0 usage to 1.990 GiB.

## Remaining Desktop limitations

- `hardware_snapshot` reports `gpus=[]`. The UI displays “No NVIDIA GPU or driver detected” and no AMD VRAM gauges. Generation still works through the explicit `--gpu 1` argument. No GPU names, metrics or capability values were fabricated.
- Local GGUF cards show incomplete architecture/MoE metadata and context `0`. The worker's actual context was explicitly set to 8,192; the card's `0` is a frontend metadata limitation.
- The beta's engine installation/update flow is CUDA-oriented. **Do not use its Install/Reinstall/Update engine controls for this ROCm environment.** This test did not validate an official one-click AMD Desktop package or replace the isolated AMD build.
- GGUF TP2, Desktop tools/agent launching, MTP, MoE generation and filling the entire 8K window were not tested here. Existing CLI tool-call validation remains separate.

The test frontend and worker were closed afterward. The normal visible
llama.cpp terminal was restored for Nemotron Q4, and an authenticated gateway
generation returned `85` for `37 + 48`; restoration is recorded in the
[structured results](desktop-amd-2026-10-18.json). No FreeToken service was added
to DSH, the LAN/Tailscale gateway or other backends' automatic shutdown targets.
Use [the validated CLI workflow](README.md#desktop-frontend-and-api-clients) when
the Desktop's incomplete AMD integration is undesirable.

For reproduction, extract the pinned frontend, set the engine override and
isolated XDG directories above, configure the test JSON, then start the local
Qwen Q4 card. Close other inference first; the existing wrapper refuses occupied
inference ports and insufficient GPU headroom. Local test automation used
WebKit's inspector bound to loopback only and the actual UI controls; the
inspector endpoint is closed with the test frontend. Screenshots, UI bundles,
request traces and raw telemetry remain ignored and are not published.

[Upstream AMD installation guide](https://github.com/FlashML-org/FreeToken/blob/8f49e0af98ba444dd261af69e82d5a1841778c68/docs/install_amd.md)
and [source installer](https://github.com/FlashML-org/FreeToken/blob/8f49e0af98ba444dd261af69e82d5a1841778c68/install.sh)
provide background; the results above are local observations of the pinned
Desktop binary and installed engine, not a claim of official AMD Desktop support.
