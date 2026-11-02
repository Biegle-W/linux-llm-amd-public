# DSH desktop backend logs — November 2, 2026

Superseded by [headless defaults](HEADLESS-INFERENCE-2026-11-02.md): GUI logs now require explicit opt-in.

On-demand requests now open a Ptyxis log window for the selected backend when
the hub has a desktop display and Ptyxis is installed. The window follows the
persistent launcher log, including startup failures and replacement log files.
An open viewer is reused per backend during the hub process's lifetime; a closed
viewer is reopened on the next backend launch. Each viewer shows the last 30
lines before following new output. Cairo matches the normal desktop launchers.

The hub still supervises the guarded backend launcher directly. Closing a log
window leaves inference running. Headless sessions and installations without
Ptyxis retain background launch behavior. A terminal spawn failure does not
block inference. Queueing, startup-failure detection, model arguments, ownership,
GPU reservations, memory guards and inference-aware idle unloading are preserved.

Existing DSH and server log windows were preserved. An additional viewer was
opened for the already-running backend without loading a model or restarting
DSH. Activated after an idle hub restart; the existing backend and DSH were preserved.

[Machine-readable verification](../hardware/results/dsh-terminal-visibility-2026-11-02.json).

Validation: 61 focused CPU tests pass across terminal logs, model-hub behavior
and router admission. Coverage includes X11/Wayland selection, safe argv/path
handling, viewer reuse/reopen, missing desktop/terminal fallback, spawn errors,
the directly tracked guarded child, GPU reservations, admission and routing.
The existing HTTP fixtures emit socket ResourceWarnings; the suite passes.
Desktop window enumeration is restricted, so process survival verifies launch,
not visual placement or focus. No model was loaded for this change or validation.

No engine/profile/context or throughput result changes. RAM holds and the paused
daily updater remain. Future GPU qualification still requires the owner request
and RAM prerequisite; use only the short DSH tool-call check followed by unload.
