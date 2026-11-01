# Enabled AMD models: short DSH tool checks — November 1, 2026

The owner requested the same short tool-call check on the other seven enabled
routes. Each used its normal guarded backend; when startup was admitted, one
fresh installed DSH headless session ran through **AMD server**, the model hub
and the selected backend. Startup failures are recorded before tool execution. Empero's earlier
same-day pass is retained without a repeat. Paused profiles were not tested.

The request includes DSH's normal system prompt/tool catalog and a tiny one-line fixture; it is not padded toward the configured context limit.

The fixture requires exactly one `read` tool call, a completed matching tool
result and the exact marker in the final reply. Each response is capped at 256
tokens; the check stops at its two-step/one-tool-call boundary. Router readiness
has a 90-second deadline; the harness has a 240-second deadline including any
on-demand model startup. A deadline failure is not proof of unsupported tools.
There is no padded input, full-context
request, context-growth test, repeated trial, performance comparison or soak.
Loading retains the normal runtime/RAM/VRAM guards. Failures are recorded without
retrying or changing model settings to obtain a pass. Every tested managed
backend is stopped after its attempt, including failed admission.

**Results: 4 passed; 4 did not pass. All eight entries include verified cleanup.**

## VRAM only models

| Model / route | Short DSH result | Tool calls | Exact final marker | Unloaded |
|---|---|---:|---|---|
| Empero Qwen3.8 35B A3B | passed | 1 | yes | yes |
| Qwen 27B / vLLM MTP | passed | 1 | yes | yes |
| Flint 40B A2.5B | stopped: extra tool call | 2 | not reached | yes |
| Qwen 27B / SGLang DFlash2 | passed | 1 | yes | yes |
| Nemotron 3.5 Bolt / vLLM | failed: timeout | 0 | not reached | yes |
| Sage A1.5 / vLLM | passed | 1 | yes | yes |

## MoE models with CPU RAM offload

| Model / route | Short DSH result | Tool calls | Exact final marker | Unloaded |
|---|---|---:|---|---|
| Nemotron 3.5 Super IQ3 | blocked: RAM admission | 0 | not reached | yes |

## MoE models with SSD streaming

| Model / route | Short DSH result | Tool calls | Exact final marker | Unloaded |
|---|---|---:|---|---|
| GLM 5.3 Flash / Maya | failed: timeout | 0 | not reached | yes |

## Recorded failures

- **Nemotron 3.5 Super IQ3:** The existing CPU-expert RAM admission guard refused startup (about 23.1 GiB available RAM required). No model tool call ran. The original message rounds required and available RAM to the same decimal.
- **Flint 40B A2.5B:** The model called glob before read. Both tools completed, but the extra tool call reached the short-test boundary; the final reply was not tested. No retry.
- **Nemotron 3.5 Bolt / vLLM:** Short harness deadline (includes cold loading); no retry
- **GLM 5.3 Flash / Maya:** Router readiness deadline; no retry

## Selected runtime revisions

- llama.cpp: `eb4e244be77a`.
- Qwen/Sage vLLM: `0.33.0rc1.dev229+g3966924d5.rocm72`.
- Bolt vLLM: its retained `0.32.1rc1.dev435+gc50aca144.rocm72` manual pin.
- SGLang: `f84475ccf593`.
- Maya: `cbaaec5d70fd`.

## Meaning of these results

These are current harness compatibility checks, not new throughput benchmarks.
Historical prefill, TTFT, code/prose decode rates and prior context evidence stay
unchanged with their original dates and hardware attribution. A pass certifies
only this one short DSH tool round trip; it does not establish an intermittent
failure rate or certify other tools, harnesses or full-window quality. A blocked
startup is not a passed tool test or proof of bad model output.

Existing context caps, selected runtimes, RAM holds and guards are retained.
Daily updates remain paused. No failed route was silently disabled, promoted,
retuned or replaced during this request. A follow-up fix needs its own scoped
work and exact failure reproduction under the owner's short-test policy.

[Structured results](results/dsh-enabled-tool-checks-2026-11-01.json).
[Current short-test policy](SHORT-HARNESS-TEST-POLICY-2026-11-01.md).
