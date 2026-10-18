# Strata preparation after RAM expansion — October 16, 2026

**October 18 plan update:** CPU expert backing plus GPU expert caching is now the
requested MoE policy. The inactive generator uses **both RX 7900 XTX cards**,
HIP, automatic layer split, one slot and no single-card fallback. Its CPU-resident
expert mode is supported with layer split by the retained source; older forum
warnings describe an earlier implementation. The 64 GB/available-RAM gate still
blocks this approximately 40 GiB expert pack on the current 32 GB installation.
See [current MoE/cache plan](MOE-OFFLOAD-2026-10-18.md) and
[forum/primary-source trail](FORUM-OPTIMIZATION-SOURCES.md). No Strata inference
or maximum-context validation is claimed. The older single-card recipe below is
historical; do not use it as the current generated candidate.

Status: **inactive; no Strata inference attempted on the new GPU pair**.
The planned configuration has 64 GB system RAM; current OS memory is approximately
30.6 GiB. The approximately 40 GiB Strata expert pack remains capacity-gated.
The separately validated smaller MoE profiles fit the current memory budget.

## Current GPU policy

Both RX 7900 XTX cards are now installed. The user requests both for every model.
The old single-AMD candidate below is preserved only as a historical starting point;
it is not permitted as an automatic fallback. After RAM expansion, check this Strata
fork's dual-HIP inference, residency and cache behavior before enabling it.
The motherboard is now Z690 with both cards at CPU-connected PCIe4 x8; old
chipset-slot observations below describe the prior board. The other engines' RCCL workaround does not establish Strata compatibility.

## Preserved assets and inactive candidate

All 112.81 GiB under `/mnt/llm-models/Strata` remains intact:
IQ3_XXS GGUF shards, prepared dense/expert pack, tokenizer and MTP runtime files.
Windows retains its own Strata profile against these files; do not delete or
convert shared assets to satisfy a Linux-only experiment.

`python3 hardware/prepare-candidates.py` writes the ignored candidate
`hardware/generated/strata-7900xtx-candidate.json`. It is not registered in DSH,
Turnstone or the gateway and does not start a process. Initial settings:

- RX 7900 XTX alone, HIP gfx1100; confirm the actual HIP ordinal before use.
- 32,768 total context, INT8 KV, 32,768 resident KV, prefill chunk 512.
- Existing Q3 and MTP files (`--spec 4`), six CPU expert workers, 3 GiB VRAM reserve.
- Memory-mapped experts plus pageable CPU-resident expert storage; fixed cache
  (`--adapt-every 0`, `--pcie-frac 0`), conversation parking disabled initially.
- Loopback test port 18030; separate `strata/build-hip/strata` engine.

These are starting values, not validated performance or maximum-context claims.
Mixed AMD/NVIDIA execution is unsupported by this Strata source. The 4070 cannot
join a HIP/CUDA tensor-parallel group. Its historical 32/16 two-NVIDIA split and
256K context must not be reused as if validated on the new hardware.

## Readiness and build

Run the read-only check after the RAM expansion:

```bash
cd /opt/local-llm
python3 hardware/check-strata-ready.py
```

Exit 2 means a prerequisite is missing. It checks at least 60 GiB OS-visible RAM
(the planned 64 GB installation), at least 48 GiB currently available RAM, AMD
24 GB/KFD access, retained assets, tokenizer, candidate and HIP executable.
The available-RAM threshold is a conservative entry gate, not a measured memory
requirement. Passing does not authorize automatic activation or prove model fit.
The check never reads full weight contents, loads a model or stops another job.

`hardware/build-strata-hip.sh` uses the existing isolated ROCm 7.2.3 SDK and
GCC 14.4 toolchain, gfx1100 and HIP MMQ. It reuses Strata's bundled ggml source,
keeps compilation separate from CUDA and does not overwrite `strata/engine/strata`.
Pinned Strata source: `296b59d2f73c8f04a805df29c2fa97655adace78` (0.1.44.1).
Bundled ggml provenance: `3cf03257f219afbe7334045ff7c6a06ac68c627d`.
Build command: `BUILD_JOBS=1 bash hardware/build-strata-hip.sh`.

## Preparation result

The separate HIP build completed on October 16. `strata-device --list-devices`
identified **AMD Radeon RX 7900 XTX, device 0, gfx1100, 24.0 GiB, wave32**.
The 64 MiB allocator self-test passed, including allocation alignment and refusal
of over-allocation. This tests basic HIP device/memory operation, not model
inference, expert kernels or MTP correctness.

The read-only readiness check found all retained assets, tokenizer, candidate,
HIP executable and KFD access. It remains blocked by RAM: 30.60 GiB OS-visible,
about 19.96 GiB available at the check. No Strata model was loaded. Build logs,
device/self-test output, readiness details and binary checksums are ignored under
`hardware/generated/strata-prepare-2026-10-16/`.

## Work remaining after expansion

1. Confirm the installed RAM capacity and pass the read-only readiness check. Recheck
   upstream changes before selecting a new runtime revision; retain exact pins.
2. Source `hardware/rocm-env.sh`, supply the private host-toolchain library path,
   then verify `strata/build-hip/strata-device --list-devices` and `--selftest`.
   Resolve device identity and shared-library paths before any model load.
3. Extend the owned-process classifier for the exact HIP engine path and add AMD
   memory-release checks before wiring the candidate into ordinary launchers.
   The old wrapper forces CUDA 0,1 and must be migrated. Keep exclusive handover;
   never stop DSH, the gateway, unrelated training or other GPU applications.
4. Test 32K manually with host-RAM, AMD VRAM/residency and disk-I/O monitoring.
   Validate readable output, structured tools, streaming, long-prompt retrieval
   and MTP on/off correctness/acceptance. Leave room for the desktop and OS.
5. Compare prefill/decode/TTFT and CPU worker/cache settings; increase context
   32K → 64K → 128K only after each actual long-prompt test succeeds. Do not infer
   a usable context from cache allocation or the old two-NVIDIA benchmark.
6. Only then migrate the Strata guard/router/wrapper, enable the tested profile,
   refresh DSH/Turnstone/gateway, and validate authenticated LAN/Tailscale access.
   Update benchmarks, shared Windows handoff, and both private/public Git repos.

Keep assets on Shared SATA initially. Unlike fully resident models, SSD paging
and PLE reads can affect Strata speed; reconsider storage only with I/O evidence.
