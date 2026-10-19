# Current Strata Q3 — October 19, 2026

Use **Strata Q3** / `llm-strata` for a visible backend terminal, then launch
**dsh** separately and choose **Local Strata** / `qwen3.8-flash-next-iq3_xxs`.
Existing chats retain their own model selections. Context: **32,768 total tokens**.

HIP0.1.45, both RX7900XTX, explicit split26/stage trimming and overlapping handoff,
2048 prefill, 14 GiB CPU expert budget, INT8 KV and MTP3. Each card reserves
7 GiB; the scoped RAM/VRAM watchdog unloads only Strata when headroom is unsafe.
A guard stop requires explicit `/models/load` or restart after freeing resources.
This is layer splitting, not TP. The 64 GB /128K candidate remains inactive.

[Exact measurements, protection thresholds and source links](../../hardware/STRATA-OPTIMIZATION-2026-10-19.md).
[Current client/runtime handoff](../../network/LINUX-LLM-RUNTIME-HANDOFF.md).
