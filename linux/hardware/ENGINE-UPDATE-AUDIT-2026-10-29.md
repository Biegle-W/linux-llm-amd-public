# Backend update audit — October 29, 2026

> Historical snapshot before restoration: the owner subsequently restored the nightly timer and completed a guarded update run (vLLM promoted; other outcomes recorded in the restoration report). See [restoration status](ENGINE-UPDATER-RESTORED-2026-10-29.md). The version comparison below retains its original observation time.

Read-only upstream check completed at 2026-10-29T12:14:45.128616-04:00. At that snapshot, `llm-daily-update.timer` was absent/inactive; its service was loaded but inactive. The configured 03:00 policy was not running. No engine build, install, promotion or schedule activation was performed.

| Component | Selected | Configured upstream | Result |
|---|---|---|---|
| llama.cpp | `2280f0fd163b` | `0893ec98f5ea` | update available |
| vLLM | `0.32.1rc1.dev602` | `0.33.0rc1.dev229` | update available |
| SGLang | `f84475ccf593` | `f84475ccf593` | current |
| Strata | `7dd5cf18e68c` | `46c152a1310f` | update available |
| Maya | `f26d8bab43f9` | `cf6472cc8448` | update available |
| Strata DeepSeek | `8183c6b67162` | `46c152a1310f` | update available |

llama.cpp has separately selected source overrides for its VRAM-only profiles; the global selected pin above does not replace them. Bolt retains its explicit older vLLM runtime pin. Manually pinned vLLM profiles are excluded from global candidate comparisons. The configured engine registry has six components: llama.cpp, vLLM ROCm nightly, the SGLang gfx1100-support fork, Strata Qwen, Maya and Strata DeepSeek. Graphics/ComfyUI/H3 and unrelated auxiliary stacks are outside that registry.

Newer upstream availability is not promotion qualification. The existing isolated build, functionality, memory and performance gates still apply, with rollback on failure. Reduced-RAM holds remain; the historical schedule pause was subsequently superseded by the authorized restoration.

Configured sources: [llama.cpp master](https://github.com/ggml-org/llama.cpp), [vLLM ROCm nightly index](https://wheels.vllm.ai/rocm/nightly/rocm72/vllm/), [SGLang AMD fork](https://github.com/StevenChenSE/sglang/tree/gfx1100-support), [Strata](https://github.com/Niko1221/Strata), [Maya](https://github.com/mw00/project-maya).
