# Strata: current 32 GB profile and 64 GB preparation

The existing IQ3_XXS model now runs at **262,144 native context** on both AMD
cards with 32 GB RAM. The old 32K cap was a validated conservative choice, not a
hardware maximum. See [the current settings and measured limits](STRATA-CONTEXT-2026-10-19.md).

INT8 KV retains 32K on the GPUs and uses about 3.352 GiB host backing. The expert
budget is13.5 GiB; startup requires29 GiB physical /22.852 GiB available RAM.
Reserves are7/8 GiB. Both GPUs, overlapped split 26, stage trimming, MTP3,2048
prefill, worker-only no-swap scope and continuous guard remain enabled.

Start **Strata Q3** or `llm-strata`; DSH is separate. Keep other large graphics
workloads separate. GPU headroom belongs to the whole desktop, not just Strata.

## Additional 32 GB

The inactive `dsh/strata-iq3-64gb-candidate.json` retains native 256K and the same
KV/placement/MTP, with 20 GiB expert budget. It requires60 GiB physical and29.352 GiB
available RAM. More memory does not automatically activate or validate it.

After installing RAM, boot Linux and run:

```bash
free -h
python3 hardware/check-strata-ready.py --ram 64
```

Validate actual long-context retrieval/code, tools, streaming and memory on both
cards before changing the active profile. Retain the validated256K profile
until then. `hardware/prepare-candidates.py` writes inactive candidates only;
it now preserves the current context/placement/reserves. Beyond256K uses
experimental RoPE extension and is not enabled by either retained profile.
