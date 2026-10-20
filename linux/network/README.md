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

`python3 -B network/check.py` validates authentication, health, enabled IDs and
contexts, and retired-Q2 rejection without loading a model. It derives the
catalog from local configuration; `--output PATH` optionally saves a report.
`--generate` is the additional Strata Q3 SDK streaming/tool test and requires
that backend. Maya's separate normal-launcher proofs cover both selected models.

Earlier October 20 authentication/catalog checks passed for the then-thirteen profiles on
loopback/LAN/Tailscale host-self routes. Maya generation, JSON, tool round trips
and model switching passed there too; a separate remote client was not tested.
The Maya addition refreshed only the gateway; credentials and access controls
are unchanged. See the canonical handoff and [Maya report](../hardware/MAYA-2026-10-20.md).
