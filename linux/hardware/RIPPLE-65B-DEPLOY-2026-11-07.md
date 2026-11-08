# Ripple-65B-Preview deploy, November 7

> **Removed November 7, 2026 (owner request):** "keep the vllm, remove the llama.cpp setup and its weights". The `ripple-65b` llama.cpp route (`dsh/models.json`, `dsh/models-hip.ini`, `dsh/llama-runtime.json`), the `llama.cpp-b12189` worktree and the 38 GB GGUF are deleted. Ripple now runs only as `ripple-65b-vllm`; see [Ripple-65B on vLLM](RIPPLE-65B-VLLM-2026-11-07.md). This page is kept as history.

The owner released the GPU fault hold on November 7 and approved this deployment.

- **Route:** `ripple-65b` in `dsh/models.json`, `dsh/models-hip.ini` and `dsh/llama-runtime.json`. The hub (127.0.0.1:30100) and the authenticated API (:10000) load it on demand.
- **Model:** `AtomicChat/Ripple-65B-Preview-GGUF`, file `Ripple-65B-Preview-AD-Q4_K_M.gguf` (40.4 GB, ~96% top-token match vs BF16), stored at `<model drive>/GGUF-Models/Ripple-65B-Preview-GGUF/`.
- **Runtime:** Ripple needs llama.cpp b12167 or later (PR #31692). The global source predates it, so the route uses a `source_overrides` pin to `llama.cpp-b12189` (a git worktree, commit `80d2c0c2c56e4a1bbf74be98f64b99927bf230bc`), built with HIP for gfx1100 by `llama.cpp-b12189/build-ripple.sh`. Other routes keep their binaries.
- **Build note:** `rocm-env.sh` puts the conda toolchain first on PATH, and it fails to link this release against glibc 2.43 (`sqrtf@GLIBC_2.43`, GOMP). The build script uses `/usr/bin/gcc` and `g++` instead.
- **Placement:** both cards, layer split 1,1, 32k context, q8_0 KV (the `[*]` defaults), ~22 GB VRAM per card.
- **Measured:** ~77 tok/s prompt processing and 16–17 tok/s generation. Short chats through the hub returned correct answers, and the kernel log showed no amdgpu errors.
- **Not done:** no guarded qualification run (tool calls, long context, memory guards) and no P2P. `llama.cpp-b12189/serve-ripple.sh` starts the same model standalone on :30110 for manual tests. Do not run it while the hub has Ripple loaded.
- **Leftover:** the empty download folder `<model drive>/models/` (only `download.log`) can be deleted.
- **Rollback:** restore the three dsh files from `hardware/generated/backup-ripple-route-20261107T163436/`.
