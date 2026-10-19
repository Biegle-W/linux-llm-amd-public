# Strata native 256K context on dual AMD / 32 GB RAM — October 19, 2026

The retained IQ3_XXS profile now has **262,144 total tokens**, the model's
native trained window, on both RX 7900 XTX cards with 32 GB system RAM.
The previous 32K setting was a conservative validated choice, not a demonstrated
hardware maximum. This profile reuses existing weights and the installed runtime. It retains
INT8 KV and the native context, without RoPE extrapolation.

## Retained configuration

- Strata HIP 0.1.45, source `477ac13cbe8e582c20484871ce459d20d82df09d`.
- i5-13600KF, Z690 CPU PCIe4 x8/x8, 32 GB installed / about 30.6 GiB visible.
- Both GPUs, explicit layer boundary 26, trimmed stage weights,
  `STRATA_SPLIT_OVERLAP=1`; this is layer splitting, not TP.
- **INT8 KV, 32,768 resident positions per attention layer, full host backing**
  for the larger context. The conservative host-KV estimate includes twelve
  target QSA layers and the draft layer: **3.352 GiB at 256K**.
- Automatic GPU expert caches, **13.5 GiB CPU expert budget**; actual startup
  backing 13.23 GiB with GPU expert caches approximately 14.43/12.31 GiB.
  These are expert bytes; dense/MTP weights, KV and buffers are additional.
- MTP `--spec 3 --spec-min-p 0.7`, six pool workers, prefill 2048, one session.
- Startup reserve targets **7 GiB on GPU0 / 8 GiB on the display GPU1**.
  The watchdog and worker-only no-swap scope remain enabled. Other apps are
  never reclaimed by killing their processes.
- Same Shared SATA weights/pack/tokenizer/MTP. PLE remains mmap; expert
  complement is pinned in RAM. Adaptive expert swapping and conversation
  parking stay disabled. Thinking defaults off.

## Measured context and speed

Fresh synthetic inventory prompts place three access codes near the beginning,
middle and end. Every probe returned all three; cache hits were zero.

| Context allocation | Actual input / output | Native prefill t/s | Native decode t/s | Minimum available RAM GiB | Minimum free VRAM0 /1 GiB |
|---|---:|---:|---:|---:|---|
| 65,536 | 61,405 / 22 | 1006.2 | 52.1 | 11.52 | 5.486 / 3.703 |
| 131,072 | 126,955 / 22 | 970.4 | 46.8 | 9.73 | 5.408 / 4.57 |
| 262,144 | 258,044 / 256 | 775.1 | 39.9 | 6.99 | 5.28 / 4.427 |

The 64K/128K answers are only 22 tokens, so their decode figures are capacity checks,
not sustained generation benchmarks. The 256K request first retrieves the codes
and then generates code, capped at 256 tokens. It is one long-output sample,
not a repeated performance median or a broad accuracy evaluation.

On the selected 256K profile, short code/prose medians are **72.2/48.0 t/s**,
three warm samples per task plus excluded warm-up, greedy, 512-token output cap.
An initial batch overlapped the separate Strata app setup, measured 30.2/24.6 t/s
and was highly variable;
it is preserved separately. The reported later medians were sampled after that
setup ended. This does not isolate the cause of the initial variation.
The earlier 32K profile measured 77.6/52.3; reserve, expert budget, desktop load and
potential output rounding differ, so this is a complete-profile comparison,
not an isolated measurement of context-size cost. All individual timings,
counts, hashes and memory summaries are in [the curated JSON](strata-context-2026-10-19.json).

A separate normal-checkpoint conversation test used **258,025 fresh input tokens**,
then a follow-up containing the full conversation. It passed marker retrieval on
both turns. The follow-up reused **258,048 tokens**
and took **0.84 seconds** wall time.
Minimum available RAM over both turns was **7.53 GiB**.
This test uses production checkpoint defaults, unlike the uncached speed probes.

All probes and production functional checks recorded **zero worker swap and
zero sampled dedicated-VRAM spill**. Arithmetic, streaming and a complete
function-call/tool-result round trip passed after the larger-context test.
Authenticated gateway streaming also passed through the existing host-loopback
entry point; remote LAN/Tailscale clients were not independently retested.
No deliberate OOM or desktop-crash test was performed. Sampled guards cannot
prevent every sudden allocation or driver failure.

## Admission, DSH and future RAM

The single existing **Strata Q3 / `llm-strata`** option now advertises 256K in
DSH and the authenticated gateway, under unchanged model ID
`qwen3.8-flash-next-iq3_xxs`. DSH's maximum reply remains 4096; instructions,
conversation, tools, input and output share the 262144-token budget.

Startup counts the full host KV copy alongside the expert budget and 6 GiB of
headroom: **22.852 GiB available RAM** for the active profile, with at least
29 GiB physical total and both 24 GB GPUs. Swap does not satisfy admission.
The readiness tool uses the same arithmetic. The guard still unloads only the
owned Strata worker below its RAM/VRAM thresholds and latches the failure until
explicit reload/restart. Keep large graphics workloads separate.

The inactive 64 GB candidate retains this same native 256K context and placement,
with a 20 GiB expert budget. Its 60 GiB physical / 29.352 GiB available-RAM gate and
fresh validation still apply. Installing RAM never changes the active profile
automatically. The candidate generator preserves current placement/reserves/
context rather than recreating the obsolete 32K/128K recipes.

This establishes a usable native 256K profile, **not the largest possible
experimental allocation**. Beyond 262144 Strata uses RoPE extrapolation; such
windows need separate quality and memory testing and are not enabled here.
The old NVIDIA 256K timing remains a different 64 GB/CUDA configuration.

## Sources and reproduction

- [Pinned upstream multi-GPU/KV implementation](https://github.com/Niko1221/Strata/blob/477ac13cbe8e582c20484871ce459d20d82df09d/docs/MULTI_GPU.md)
  and [setup/context accounting](https://github.com/Niko1221/Strata/blob/477ac13cbe8e582c20484871ce459d20d82df09d/setup.py):
  resident CPU complement, streamed KV and native 262144 boundary.
- [lcz.me topic 2163](https://lcz.me/topic/2163), reviewed October 19: two RTX 5060 Ti 16 GB cards,
  IQ3_S,196K/256K reports. Different hardware; source of the earlier retained
  NVIDIA tuning approach, not evidence of local AMD speed.
- [Level1Techs local-server discussion](https://forum.level1techs.com/t/advice-on-a-local-ai-server-before-buying/258001),
  October 8: RAM/offload and PCIe considerations, but no matching dual-XTX 32 GB
  context A/B. Its different-engine/card speeds are not used as local targets.

With the managed backend already loaded, use its existing tokenizer environment:

```bash
strata/.venv/bin/python hardware/probe-strata-context.py --tokens 258048 --decode --output hardware/generated/context-check.json
python3 hardware/validate-strata.py --output hardware/generated/functional-check.json
```

The tools never launch a backend or stop other apps. Generated raw evidence is
ignored by Git; the curated numeric record contains no credentials or chat logs.
