# Linux LAN and Tailscale client access

The [consolidated handoff](LINUX-LLM-RUNTIME-HANDOFF.md) is the single current
reference for Linux-host access, Windows/phone clients, exact model IDs,
contexts, storage, runtime pins, backend launching and troubleshooting.
It replaces the separate Shared client, Windows-network and upgrade guides;
the original nine files are preserved in the dated Shared archive described there.

The authenticated gateway uses TCP **10000** and OpenAI-compatible Chat
Completions. Start the chosen GPU backend separately with its Desktop launcher
or `llm-*` PATH command; starting the gateway alone does not load a model.
Eight profiles are enabled. Strata is deferred pending RAM expansion/dual-AMD
validation; HyperQwen and old CUDA setups are retired locally.

Credentials and live addresses stay in ignored `dsh/data/` configuration.
Public documentation uses example paths and addresses. Never place an actual
API key in a handoff, source file or chat. Keep the selected backend's terminal
open and obtain exact IDs/readiness from authenticated `/v1/models` and `/health`.

Historical `network/check.py` assertions describe the old 12-model Strata
catalog and are not a current readiness check. Current connection examples and
validated limits are in the consolidated guide. This documentation change
restarts no service and changes no model, address, firewall or authentication.
