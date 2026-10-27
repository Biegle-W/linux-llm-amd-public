# Sage INT4 replacement and GGUF retirement — October 27, 2026

User requested the new benchmark results in three categories and removal of the slower Sage llama.cpp GGUF. Hardware: two RX 7900 XTX 24 GB, i9-13900KS, ROCm7.2.3, 14.83GiB OS-visible RAM. Loading swap and parked pages remain allowed. Existing active-compute churn, physical-RAM/VRAM admission, owned-worker and thermal safeguards remain.

## VRAM only models

The preceding [loading-swap retry](LOADING-SWAP-RETRY-2026-10-27.md) contains every framework/INT4 attempt. The comparison below uses complete October27 text results; the GGUF is a retained historical measurement after removal. Fresh~8K TTFT excludes cold loading. Decode is code/prose median of three256-output trials after excluded warmups. Native GGUF prefill and vLLM scheduled-to-first-token engine-phase prefill measure different phases and must not be used for a direct prefill speedup claim. Context is configured capacity; actual tested lengths are recorded separately.

| Sage profile | Prefill t/s | Fresh TTFT s | Decode code/prose t/s | Context tokens | Allocated GB | Storage location |
|---|---:|---:|---:|---:|---:|---|
| W4A16 AutoRound · vLLM dev435 selected (text-only) | 4142.6 engine phase | 2.001 | 148.04/138.33 | 65,536 | 20.33 | SATA1 `vLLM-Models/Sage-A1.5-W4A16-AutoRound` |
| W4A16 AutoRound · vLLM dev602 text candidate | 5091.7 engine phase | 1.619 | 148.64/139.62 | 65,536 | 20.33 | SATA1 `vLLM-Models/Sage-A1.5-W4A16-AutoRound` |
| Q4_K_M · llama.cpp19cce691, retired reference | 4618.1 native | 1.779 | 86.26/71.41 | 65,536 | 22.61 including projector | SATA1 `GGUF-Models/Sage-A1.5-GGUF` (removed) |

Native dev602 code/prose decode is72.3%/95.5% faster, fresh TTFT9.0% lower, with2.28GB less allocated model storage (10.1%). Quantization, KV formats and kernels differ; these measurements do not establish equal model quality. The selected native-runtime qualification below is separate from the dev602 text-only result.

The existing **vLLMdev435** runtime now serves `sage-a1.5` at64K/MTP3 with BF16 KV on both cards. Qwen/Bolt engine versions remain unchanged. The selected profile measured **4142.6 engine-phase prefill**, **2.001s fresh TTFT**, **148.04/138.33t/s code/prose**, with actual fresh input8,187–8,189tokens. Authenticated API, JSON, forced-tool round trip, SSE, history and **62,009-token** three-marker input passed. This is a near-window smoke check, not exhaustive full-context quality validation.

**The replacement is text-only.** Both dev435 and dev602 produced repetitive, incorrect synthetic image descriptions; vision is disabled in the selected profile and language-only loading is explicit. The old GGUF vision path and its projector are removed as requested; image support is not qualified in the native replacement.

The first dev435 image attempt stopped before timed text benchmarks; its missing active-inference window is retained as incomplete evidence. The repeat and dev602 attempts record text timing separately from failed image quality. No equal-quantization/quality claim follows. [All trials, memory/thermal summaries and attempts](results/sage-int4-replacement-2026-10-27.json).

Selected dev435 code/prose decode improves by71.6%/93.7% versus the retired GGUF. Fresh TTFT changes from1.779s to2.001s (12.5% higher). No direct prefill-phase percentage comparison is made.

## MoE models with CPU RAM offload

No new benchmarks. Super IQ3 and Ornith retain their existing placements, contexts, physical-RAM requirements and results.

## MoE models with SSD streaming

No new benchmarks. Strata Qwen Q3, GLM Maya and shared DeepSeek XS profiles retain their existing placements, contexts and results. H3 is outside this LLM comparison and its RAM-upgrade follow-up remains active.

## Storage removal and validation

Removed exactly `Sage-A1.5-Q4_K_M.gguf` and its exclusive `Sage-A1.5-mmproj.gguf` after successful native text/API/context validation and owned-worker shutdown. Reclaimed **22.61GB allocated** (22,613,065,728bytes); the20.33GB native checkpoint was already stored. The2.28GB format-size difference is distinct from the22.61GB physically reclaimed. File identity/size/link count and absence of active use were checked before deletion; unrelated weights, client settings and project files remain.

Removed Sage only from llama.cpp models, HIP preset, memory plan and model-specific source override. Registered the same API ID in vLLM; DSH migrates an old llama-local/Sage selection to vllm-local/Sage while preserving unrelated providers and saved Strata default. Catalog remains12profiles/10weight sets: four llama.cpp, one SGLang, three vLLM, two Strata and two Maya. Existing framework memory guards remain; the retired llama-specific4/5GiB scope no longer describes Sage. Remaining llama worker RAM caps are unchanged. Loading/parked swap is permitted, active churn and zero-VRAM-spill enforcement remain, and the updater stays paused.

**45focused CPU regressions per checkout passed.** They cover routing, settings migration/repeatability, llama source selection, retained GPU defaults and offload admission. Lifecycle sample/thermal summaries are retained numerically; sampled peaks are not guaranteed transient maxima and SMU flag counts do not measure time throttled.

Historical Sage GGUF measurements and source references remain for comparison. Flint's GGUF remains: its selected reasoning128 measurement46.73/46.82t/s is faster than the native no-thinking diagnostic43.22/42.53t/s, while the matched native reasoning128 attempt remained partial. Empero and all CPU/SSD profiles remain.
