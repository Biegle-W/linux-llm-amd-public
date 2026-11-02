# DSH on the AMD server

All enabled local models appear under **AMD server**. The loopback model hub
starts the correct backend on the first message; selecting a model does not
require choosing a separate engine provider.

Inference launches headlessly by default, including during desktop sessions.
GUI log viewers require explicit `LOCAL_LLM_GUI_LOGS=1` opt-in; manual desktop
launchers remain available on demand. See the
[headless server setup](../network/HEADLESS-INFERENCE-2026-11-02.md).

Eight routes are currently enabled: Empero, Super IQ3, Flint, Qwen 27B SGLang
DFlash2, Qwen 27B vLLM MTP, Nemotron Bolt, Sage and GLM. Qwen's two routes keep
their engine labels so the choices remain distinguishable. Ornith, Qwen Flash
Next/Strata and both DeepSeek XS routes retain their existing RAM holds.

`configure_local.py` migrates former local engine providers to `amd-server`,
preserves an available selected model and unrelated providers/settings, and
retains per-model wire compatibility and configured context limits. A paused or
retired selection falls back to an enabled model; it does not clear a hold.
Both the web and headless profile overrides support the same catalog. Existing
conversations and credentials remain private and are not exported.

The harness remains `@deepseek-ai/dsh@0.2.1-rc.2` with Node.js 24.21.0. Its web
settings are in ignored `data/profiles/web/cordis.patch.yml`. Refresh the browser
model selector after a configuration reload. Engine launch commands remain
available for maintenance; they do not create separate visible providers.

Follow the [short harness testing policy](../hardware/SHORT-HARNESS-TEST-POLICY-2026-11-01.md):
calculate context from RAM/VRAM and engine allocations, run one short tool-call
round trip through the harness, then unload. No routine full-context tests.
Daily engine updates remain paused until explicitly resumed by the owner.
