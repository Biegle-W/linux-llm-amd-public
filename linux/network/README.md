# Linux LAN and Tailscale client access

The [consolidated handoff](LINUX-LLM-RUNTIME-HANDOFF.md) is the single current
reference for Linux-host access, Windows/phone clients, exact model IDs,
contexts, storage, runtime pins, backend launching and troubleshooting.
It replaces the separate Shared client, Windows-network and upgrade guides;
the original nine files are preserved in the dated Shared archive described there.

The authenticated gateway uses TCP **10000** and OpenAI-compatible Chat
Completions. Start the chosen GPU backend separately with its Desktop launcher
or `llm-*` PATH command; starting the gateway alone does not load a model.
Ten profiles are enabled, including the validated managed Strata Q3 backend.
HyperQwen and old CUDA setups are retired locally.

Credentials and live addresses stay in ignored `dsh/data/` configuration.
Public documentation uses example paths and addresses. Never place an actual
API key in a handoff, source file or chat. Keep the selected backend's terminal
open and obtain exact IDs/readiness from authenticated `/v1/models` and `/health`.

`python3 -B network/check.py` validates authentication, health, the exact enabled
profile IDs and contexts, and retired-Q2 rejection without loading a model.
It derives the catalog from local profile configuration and writes no report
unless `--output PATH` is supplied. Generation requires the explicit
`--generate` option; it was not used for the October 19 maintenance check.
Loopback/LAN/Tailscale host self-access passed for all ten profiles; a remote
client still needs its own connectivity test. No service restart or production
inference setting change was made.
