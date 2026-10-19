# Current benchmark results

Start with [the current AMD benchmark report](../CURRENT-AMD-BENCHMARKS.md).
Its [October 19 numeric record](current-amd-2026-10-19.json) contains each
profile's exact measured build, production context, all timed trials, actual
input/output token counts, TTFT, prefill source, decode, output hashes and memory
summaries. It contains no generated answer text or private connection settings.

Reproduce with [benchmark-current-amd.py](../benchmark-current-amd.py) against
one already-running production backend at a time. Start it with its normal
visible-terminal launcher first; the helper does not launch engines, change
profiles or disable guards. Run using the existing vLLM environment for the
`tokenizers` dependency, for example from the runtime workspace:

```sh
vllm/.venv-rocm/bin/python hardware/benchmark-current-amd.py --kind llama --output hardware/generated/my-benchmark/llama.json
```

Repeat for `sglang`, `vllm` and `strata` after switching with the normal launcher.
SGLang tests both configured strategies; llama.cpp tests all five models. Use
`--model API_ID` to select one configured profile. For the complete Muse batch
that retains retrieval failures explicitly, run:

```sh
vllm/.venv-rocm/bin/python hardware/benchmark-current-amd.py --kind llama --model muse-glimmer-30b --allow-marker-failure --output hardware/generated/my-benchmark/muse-final.json
```

That flag changes benchmark result acceptance only; it cannot disable production
memory guards and is restricted to Muse. Marker outcomes remain in the data.
Raw per-backend output stays
under ignored `hardware/generated/`; publish only reviewed numeric records.
The helper reads Prometheus timing metrics from the owned loopback worker for
SGLang/vLLM and native SSE timing fields for llama.cpp/Strata.

Older builds, hardware phases, near-window tests and retired profiles remain
in [BENCHMARK-HISTORY.md](../BENCHMARK-HISTORY.md) and their dated source reports.
They are historical evidence, not substitute measurements of the current build.
The public root README keeps the archived NVIDIA setup as its separate result set.
