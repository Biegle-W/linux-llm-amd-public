# Current Strata Q3 — October 19, 2026

Use **Strata Q3** / `llm-strata` for a visible backend terminal. Launch **dsh**
separately and select **Local Strata** / `qwen3.8-flash-next-iq3_xxs`.
Context: **262,144 total tokens**, INT8 KV with 32K GPU residency and RAM backing.
DSH replies remain capped at4096; history/tools/input/output share the total.

HIP 0.1.45, both RX 7900 XTX, split 26/stage trimming and overlapped handoff,
2048 prefill,13.5 GiB CPU expert budget, MTP3. Startup reserve7/8 GiB; scoped
RAM/VRAM guard and no-swap scope remain. A guard stop requires explicit reload
or restart after freeing resources. This is layer splitting, not TP.

Near-full retrieval/code: **258,044 input / 256 output**, native PP **775.1**,
decode **39.9 t/s** in one sample. Short three-run medians: **72.2/48.0**
code/prose. See [configuration, limits and results](../../hardware/STRATA-CONTEXT-2026-10-19.md)
and [current handoff](../../network/LINUX-LLM-RUNTIME-HANDOFF.md).
The 64 GB candidate is inactive and retains native 256K; it never activates itself.
