# vLLM desktop startup recovery — October 18, 2026

The desktop terminal closed because the launcher exited before starting vLLM.
Its default 21 GiB-per-card VRAM admission check rejected approximately
20.78 GiB free on the display GPU; the other card had 23.61 GiB free.
The existing runtime probe passed. Recent kernel logs showed no new GPU reset
or system OOM, and the previous model log ended with an intentional SIGTERM.
This reproduces a startup refusal, not evidence of an inference kernel crash.

## Fix

- The saved Qwen profile and direct launcher now use GPU memory utilization
  **0.82 instead of 0.88**, with **20 GiB free required per GPU**. The shared
  backend launcher reads the profile admission threshold; SGLang retains 21 GiB.
- Keep the same Qwen3.8-27B GPTQ INT4 model, two RX 7900 XTX cards/TP2,
  **65,536 context**, **3.5 GiB fixed KV per GPU**, BF16 KV, compiled MTP3,
  graphs, tuned prefill and prefix caching. No CPU weight offload or new model.
- The desktop vLLM entry uses `dsh/start-backend-terminal vllm`. It records
  launcher output in ignored `dsh/logs/vllm-launcher.log` and, on failure in an
  interactive terminal, waits for Enter before closing. CLI/SSH launch commands do not wait for Enter on failure. Admission errors now report free VRAM on each GPU.

The installed vLLM initialization checks the utilization budget against free
memory before loading. Its explicit `kv_cache_memory_bytes` path retains the
specified cache size independently of automatic cache sizing. Lowering the
admission budget here does not reduce the fixed context/cache allocation.
This is a local launcher/memory-budget correction, not a forum kernel tweak.
[Upstream worker admission code](https://github.com/vllm-project/vllm/blob/3f1bcfd82/vllm/v1/worker/utils.py),
[fixed-cache worker code](https://github.com/vllm-project/vllm/blob/3f1bcfd82/vllm/v1/worker/gpu_worker.py),
[existing profile tuning](VLLM-TUNING-2026-10-17.md).

## Validation

The real saved profile/router passed arithmetic, ordered JSON,
a tool-call/result round trip, and the 1-through-100 JSON check using the
existing runtime Python. The actual worker arguments confirmed utilization
0.82, TP2, 65,536 context and 3,758,096,384 KV bytes per GPU.

The long marker test passed with **64,033 input tokens**.
An identical 8K marker prompt produced prefix-cache hits. This is allocation,
retrieval and integration validation, not a new sustained throughput benchmark.
Historical benchmark figures are unchanged.

Sampled total VRAM peaks, including other desktop applications, were
**16.88 / 14.64 GiB**.
Backend-owned nonresident VRAM remained zero in 132 samples.
Backend-owned host swap peaked at 3.66 GiB
during this startup/test session; this does not establish swap-free startup
with 32 GB system RAM. GPU residency checks establish that model VRAM remained
resident, not that all Python/runtime host pages stayed in RAM. Minimum available host RAM was 16.18 GiB.
Sampling can miss brief events; the check does not guarantee loading while
other applications continue allocating GPU memory. Unrelated applications were
preserved.

To repeat the integration check using the existing runtime dependencies:

```bash
source hardware/rocm-env.sh
vllm/.venv-rocm/bin/python hardware/test-vllm-production.py --long --cache
```

The installed desktop entry was reopened. Its router and the existing authenticated
API passed a fresh arithmetic request, and the model was left running in its
visible terminal. LAN/Tailscale binding and credentials were preserved; a separate
remote client was not tested.

The desktop-wrapper failure path was also checked with a synthetic failing
child: interactive execution waited for Enter, noninteractive execution returned
the original exit code, and both attempts were logged.

[Sanitized validation](vllm-startup-2026-10-18.json).
