# DSH on the AMD server

All enabled local models appear under **AMD server**. The loopback model hub
starts the correct backend on the first message; selecting a model does not
require choosing a separate engine provider.

Inference launches headlessly by default, including during desktop sessions.
GUI log viewers require explicit `LOCAL_LLM_GUI_LOGS=1` opt-in; manual desktop
launchers remain available on demand. See the
[headless server setup](../network/HEADLESS-INFERENCE-2026-11-02.md).

Nine qualified routes are enabled. Use the [current handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md#enabled-routes) and authenticated `/v1/models` for the exact catalog; older availability lists are historical.

`configure_local.py` migrates former local engine providers to `amd-server`,
preserves an available selected model and unrelated providers/settings, and
retains per-model wire compatibility and configured context limits. A paused or
retired selection falls back to an enabled model; it does not clear a hold.
Both the web and headless profile overrides support the same catalog. Existing
conversations and credentials remain private and are not exported.

The harness remains `@deepseek-ai/dsh@0.2.1-rc.2` with Node.js 24.21.0. Refresh the browser
model selector after a configuration reload. Engine launch commands remain
available for maintenance; they do not create separate visible providers.

Follow the [short harness testing policy](../hardware/SHORT-HARNESS-TEST-POLICY-2026-11-01.md):
calculate context from RAM/VRAM and engine allocations, run one short tool-call
round trip through the harness, then unload. No routine full-context tests.
The 03:00 daily engine updater was retired on November 9, 2026; engine updates are checked and installed by hand. See the [updater README](../hardware/daily-update/README.md).
