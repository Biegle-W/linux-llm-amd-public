# Strata: current 32 GB profile and 64 GB preparation

The retained **Qwen3.8-Flash-Next GSQ-RCO IQ3_XXS** uses both RX 7900 XTX
cards through HIP layer splitting. Weights, prepared pack, tokenizer and MTP
runtime remain on Shared SATA. No new quant or conversion is needed.

The earlier blanket 64 GB requirement was a conservative local gate, not an
engine minimum. See [community evidence](STRATA-LOW-RAM-COMMUNITY-2026-10-18.md)
and [upstream resident split support](https://github.com/Niko1221/Strata/pull/848).
The [local validation report](STRATA-DUAL-AMD-2026-10-18.md) distinguishes actual
measurements from proposed settings.

## Current 32 GB settings

- Source 0.1.44.1, commit `296b59d2f73c8f04a805df29c2fa97655adace78`.
- Separate `strata/build-hip/strata`, gfx1100, private ROCm 7.2.3 SDK.
- Both GPUs, automatic layer split, one session, no single-card fallback.
- 32,768 context; INT8 KV fully resident at this length; prefill chunk 512.
- Automatic GPU expert cache; up to **8 GiB** CPU-resident expert complement;
  mmap fallback for anything outside that budget. PLE uses bounded mmap reads.
- MTP `--spec 3 --spec-min-p 0.7`; six CPU expert workers.
- 3 GiB VRAM reserve per card; fixed expert placement, PCIe expert alias off.
- Conversation parking disabled to preserve RAM. Thinking defaults off.
- Preflight requires 29 GiB physical RAM, retained assets/KFD and both GPUs.
  After managed handover releases the old worker, require 14 GiB available RAM
  and at least 16 GiB free VRAM on each card. These are admission gates, not measured peaks.
- The worker runs in its own systemd scope with `MemorySwapMax=0`; global swap
  and other applications are unchanged. A monitor unloads only the owned Strata worker after sustained less than
  2 GiB available RAM or over 1 GiB worker swap. Other applications stay running.

Start the Desktop **Strata Q3** launcher or run `llm-strata`; logs remain in its
terminal. DSH has a separate launcher: select **Local Strata**, model
`qwen3.8-flash-next-iq3_xxs`. Router API: `http://127.0.0.1:30020/v1`; its private
worker is on 30021. The existing authenticated gateway exposes the enabled ID.
Managed launches stop only configured LLM inference, including detached HIP
Strata workers, before loading another backend.

## When the additional 32 GB arrives

`dsh/strata-iq3-64gb-candidate.json` is prepared but **not an enabled model**.
It retains both GPUs and the same files/MTP, proposes 131,072 context with INT8
KV streaming (32,768 resident positions), a 2,048-token prefill chunk, and
caps CPU experts at 20 GiB.
It requires at least 60 GiB OS-visible RAM and 26 GiB available before loading.
No 128K inference or speed result is claimed on the present 32 GB installation.
Installing more RAM does not silently switch the live profile.

After installing RAM and booting Linux:

```bash
free -h
cd /opt/local-llm
python3 hardware/check-strata-ready.py --ram 64
```

Then validate the candidate on both cards: actual long-prompt retrieval, tools,
streaming, MTP acceptance, RAM/VRAM residency and storage activity, before promoting
its context into the active catalog. A readiness pass alone does not validate it.
Use 64K first if 128K leaves insufficient memory or slows the intended workload.
The 32K profile remains the usable default until that validation is complete.

`python3 hardware/prepare-candidates.py` regenerates ignored 32/64 GB candidates;
it does not activate either. `hardware/validate-strata.py --long` checks an already
running 32K production router and writes ignored synthetic test evidence.

No direct GPU P2P is required: Strata uses layer hand-offs through pinned host
memory. This is not tensor parallelism. Preserve the Shared pack's compatibility
with Windows; the historical 4070/3060 CUDA split and its 256K measurements do
not establish current Linux/Windows AMD capacity or performance.
