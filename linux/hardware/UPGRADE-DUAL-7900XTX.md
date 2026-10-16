# Planned migration to two RX 7900 XTX cards

Recorded October 16, 2026. The user plans to retire the RTX 4070 and install a
second RX 7900 XTX 24 GB. Installation has not been reported or validated.
Current profiles and measurements still refer to one RX 7900 XTX for inference.

## Placement policy

Prefer one AMD card when the model fits with a usable context and enough room
for desktop and runtime allocations. Use both AMD cards when that capacity is
insufficient, after validating the relevant engine. Two 24 GB devices provide
48 GB aggregate VRAM; this is not one automatically pooled allocation. Do not
promise twice the speed, a specific context increase, or working TP2 before tests.
Keep the existing single-card profiles as the comparison and fallback.

## Work after installation

1. Inventory PCI addresses, GPU enumeration, VRAM available after desktop startup,
   link width/speed and ROCm device visibility. Check the actual second-slot link;
   replacing a GPU does not establish a new motherboard lane layout.
2. Update device selection before loading models. `dsh/llama_runtime.py` currently
   requires a unique AMD model name, which can fail with two identical cards.
   Use stable device identity and validate the selected device for each engine.
   `hardware/rocm-env.sh` currently exposes device 0 only, and the ROCm probe
   validates the single-card setup; adapt visibility and checks per profile.
3. Review backend-switch GPU guards and obsolete NVIDIA assumptions. Keep shutdown
   restricted to configured inference workers. Leave DSH, gateways, unrelated
   training and other applications running.
4. Test ROCm peer access and RCCL communication before trying SGLang/vLLM TP2.
   Start with the existing GPTQ checkpoint and validated single-card settings.
   Compare matching prompts, prefill, decode, output correctness and per-card
   memory; increase context only after these pass. Revalidate MTP and DFlash2.
5. Test supported llama.cpp HIP/Vulkan device splits for models or contexts that
   need both cards. Select the fastest validated configuration; do not assume a
   particular API or split improves speed. Retest desktop VRAM headroom when the
   RTX 4070 is no longer available for display use.
6. Keep Strata inactive until RAM expansion and model-level AMD validation. Its HIP
   device/allocator self-test is not a model benchmark or proof of dual-GPU
   support. Follow `STRATA-AFTER-RAM.md` and reassess against the installed hardware.
7. Publish measured results and actual active device assignments in both Git
   repositories and the shared Windows handoff. Preserve historical NVIDIA and
   Windows reference snapshots as historical, not validated on the new hardware.

## State preserved while waiting

- SGLang MTP: 40,960 tokens, BF16 KV, MTP2, one AMD card.
- SGLang DFlash2: 16,384 tokens, BF16 KV, one AMD card.
- vLLM: 65,536 tokens, Q4 KV, MTP3, one AMD card.
- llama.cpp: existing validated single-AMD profiles and contexts.
- RAM: last reported 32 GB, B1/B2; GPU-resident profiles only until repair.
- Model storage and retained Strata assets remain as documented in the README.

No runtime flags, drivers, model files, launchers or benchmark results were changed
for this planning update. No dual-AMD inference has been validated.
