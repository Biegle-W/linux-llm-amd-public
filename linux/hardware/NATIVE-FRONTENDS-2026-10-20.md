# Native Strata and Maya frontends — October 20, 2026

The managed **Strata Q3** and **Maya** launchers now open each engine's original
Chat/Monitor page in the default browser after its worker is ready. Terminal
logs remain visible. The frontend is served by that same worker: no second
engine, environment or model-weight copy is created. DSH remains optional and
separate. SGLang, vLLM and llama.cpp launch behavior remains backend-only.

| Launcher / PATH command | Native frontend | Managed OpenAI router |
|---|---|---|
| Strata Q3 / `llm-strata` | `http://127.0.0.1:30021/` | `http://127.0.0.1:30020/v1` |
| Maya / `llm-maya` | `http://127.0.0.1:30031/` | `http://127.0.0.1:30030/v1` |

The pages stay local to the Linux host. LAN/Tailscale clients keep using the
existing authenticated port 10000 `/v1` gateway; no web/admin ports are exposed.
Headless SSH launches print the frontend URL and do not open a browser on the
server. `llm-strata --no-browser` and `llm-maya --no-browser` also suppress opening
it. This does not stop backend serving. Closing a browser tab does not stop the
worker; closing its terminal or switching managed backends stops owned inference.

Maya loads GLM by default. `llm-maya --model deepseek-v4.1-flash-1017-maya` selects
DeepSeek initially; DSH/API model selection can still switch the one worker.
The web page follows the currently loaded model. Existing browser chat state and
private frontend sampling preferences are preserved; `*.shared-settings.json`
is ignored by Git. Images on DeepSeek remain outside the validated quality scope.
The separate standalone Strata AppImage entry is preserved and is not launched
by the managed Q3 command.

## Runtime protection

The upstream source trees remain at their pinned clean commits. A small local
[HTTP adapter](../dsh/native-ui-server.py) imports the original server and serves
its original HTML/CSS/JS/fonts. Native chat, monitoring, cancellation, token
counts, shared sampling and existing authentication/origin checks are retained.
Context/config writes, load/unload controls and self-updates return a managed-
profile error; Maya's context slider is restricted to its configured value.
Model/context/runtime changes must keep the existing admission and validation
workflow. This prevents a frontend action from silently bypassing the measured
budgets, source pins, both-GPU placement and memory watchdogs.

[Browser opening](../dsh/native_frontend.py) waits for a loaded healthy worker,
opens only its local URL once, and cancels if that owned backend exits. It never
launches a second inference process or terminates a browser. Backend switching
recognizes only the exact configured adapter path and its `strata`/`maya`
project argument; arbitrary Python and unrelated apps remain excluded.

## Evidence and limits

Five CPU tests check the runtime-write boundary, fixed context, exact process
ownership, headless/disabled behavior, a ready-page open and cancellation after
backend exit. [Normal worker/frontend proofs](results/launcher-validation-2026-10-20.json)
cover Strata Q3, Maya GLM and Maya DeepSeek, plus the selected SGLang/vLLM160K
launchers. They include original page/assets, monitoring, JSON/tools/SSE, both
GPUs, source/config/binary pins and zero owned swap/spill. Browser-open dispatch
is logged; automated control of the default desktop browser is unavailable.
Frontend wiring is not a throughput update. Current hardware and
runtime fingerprints remain in the [handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md).
All original reserve/no-swap/latched-failure rules remain. When other desktop
applications consume the required headroom, launchers block instead of closing
those applications or lowering the guard.

Upstream UI/server implementations:
[Strata 477ac13c](https://github.com/Niko1221/Strata/tree/477ac13cbe8e582c20484871ce459d20d82df09d/serve)
and [Maya 8d9a9b5d](https://github.com/mw00/project-maya/tree/8d9a9b5d705049a87da853717cdc59440252de30/serve).
