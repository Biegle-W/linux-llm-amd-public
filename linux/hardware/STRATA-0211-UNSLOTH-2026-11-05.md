# Strata 0.2.11 with existing Unsloth V3.1 — November 5, 2026

The official Linux RX7900 engine and matching Control 0.1.57 from Strata 0.2.11 completed this isolated dual-RX7900XTX test. The strict two-step DSH read-tool round trip passed. Six fixed quality fixtures scored **5/6**, with the same arithmetic/JSON fixture missed in the November4 run. Three 128-token speed prompts had median native decode **52.895 tokens/s** and median client TTFT **0.536s**. Existing production GSQ/source selections remain unchanged.

| Measurement | Result |
|---|---:|
| Model load, separate from request latency | 102.297s |
| First tool request TTFT / elapsed | 11.952s / 12.970s |
| Second tool request TTFT / elapsed | 9.832s / 10.157s |
| Strict tool call/result IDs and final marker | Pass |
| Fixed quality fixtures | 5/6 |
| Median native decode, three short prompts | 52.895 tokens/s |
| Median client TTFT, three short prompts | 0.536s |
| Maximum recorded owned swap / VRAM spill | 0 / 0bytes |
| Final owned cgroups / KFD clients | Empty / 0 |

The downloaded Unsloth UD-IQ3_XXS Dynamicv3.1 set at revision `d96201194f103c906994f283f504209dc8d2a10c` was reused. All four existing GGUF SHA-256 values were freshly verified against the pinned download manifest. The new package's packer is byte-identical to the prior packer, and prepared-pack metadata hashes matched; no weight download, repack or relocation occurred. Package checksums and signed feed sequence121 were verified using the pre-existing trusted publisher keys. [Official release](https://github.com/Niko1221/Strata/releases/tag/v0.2.11).

The current normal profile was retained: two cards in 26/26 layer groups, one session, MTP2, int8 KV with32,768 resident tokens,256K allocation, 256-token prefill chunks, bounded CPU expert backing and the existing GPU reserve. This is layer splitting, with no new tensor-parallel or transport-performance claim. The current `MemoryHigh=max`, hard RAM bound, phase-aware swap, 100°C thermal policy, zero-spill protection, six-second heartbeat and 15-second owned cleanup stayed active. Loading/prefill/generation had 1800-second budgets inside a 10800-second enclosure; the removed three-second decode cutoff was not restored.

A controller-only GPU-order assertion failed before the engine/model started because its visibility environment had not yet matched the profile. That record and its freshly reviewed hold were retained intact; applying the profile's existing ROCR/HIP visibility to the controller fixed the preflight before the first actual model run. No model case was repeated. The actual run passed the final guard, emptied owned scopes/KFD, preserved all pinned input-file identities and produced no new kernel fault. Original installed runtimes, models, user state, schedules, boot settings and unrelated work were preserved. Nothing was deleted or promoted.

These are six small local quality fixtures and three short timing prompts, not a vendor benchmark, general model-quality ranking, sustained-stability test or full256K retrieval test. Native decode uses the engine's generated-token count divided by engine-reported decode duration; client TTFT is measured separately. Prior Unsloth52.481tokens/s and GSQ55.944/56.042tokens/s are different-day historical results; no same-day control bracket was rerun. Cache residency, packaged runtime/Control and the current resource policy limit attribution. The result supplies no evidence to replace the retained GSQ selection. [Prior comparison](UNSLOTH-FLINT-COMPARISONS-2026-11-04.md).

[Numeric evidence](results/STRATA-0211-UNSLOTH-2026-11-05.json) · [Current runtime handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md)
