# Current-RAM retest after compiler-temp cleanup — October 27, 2026

## Loading-swap framework/INT4 retry — October27

Recorded 13 model/kernel attempts on 14.83 GiB RAM with loading swap allowed;
6 completed benchmark/memory checks, including a no-thinking Flint diagnostic.
Qwen/Bolt vLLM and Sage native INT4 text tests completed; the original Qwen
paging stop and its successful unchanged-setting confirmation are both retained.
SGLang hit VRAM/telemetry/kernel blockers; matched reasoning128 Flint remained
partial at the inference swap-write guard. Three earlier systemd-syntax setup
failures are separate. Selected versions/profiles and the paused updater remain;
no models were retired and H3 was not retried.
[All attempts, benchmark fields and thermals](LOADING-SWAP-RETRY-2026-10-27.md).


**October27 policy correction:** these attempts used earlier strict loading
swap rules. The current policy allows loading swap and parked pages; a 4 GiB
loading-swapout stop does not prove the model cannot run under that policy.
Results remain historical; no new performance is inferred. Independent RAM/
VRAM failures and the Sage Marlin compile error retain their actual causes.
[Current loading-swap policy](LOADING-SWAP-POLICY-2026-10-27.md).


**No models, model files, engines or workflows were retired during this retry.** Existing production settings and selected pins remain. The user authorized both H3 and the blocked LLM tests on the current RAM, with other apps closable. No large ordinary apps or open browser tabs were found to close; the controlling app/runtime were retained.

Linux still exposes **14.83 GiB RAM**. Ten inactive HIP compiler temporary directories occupied **3.63 GiB** of allocated tmpfs storage. Their creators were gone and there were no live user-process file/mapping references. Every file was copied to the system disk, SHA-256 checked against its source, and retained before redundant RAM-backed copies were removed. No user data was discarded and no pre-existing user app was stopped.

Both groups were retried after reclamation. The actual framework/native trials used a short disk-backed TMPDIR; the first LLM retry's overly long path hit Linux's 107-byte Unix-socket limit before weight loading. That setup error is retained separately and corrected; it is not RAM, compatibility or performance evidence. There was no global/production temp-path, swap, swappiness, precision, context or memory-policy change.

Reclaimed tmpfs storage is not newly installed RAM. MemTotal stayed unchanged; sampled available memory rose and then settled further as disk copy/writeback and owned-worker cleanup completed. Initial available RAM differed across arms, so failed setup durations are not a matched speed comparison.

[Full numeric records and thermal summaries](results/current-ram-retest-2026-10-27.json) · [H3 detail](../graphics/H3-SP2-2026-10-27.md)

## H3 current workflow and SP2 pilot

Same 608×352,39-frame,24fps,20-step,seed42,INT8 FL2VA/audio graph, both 7900XTX cards configured, current component placement versus the isolated ComfyUI 0.42 SP2 pilot. One excluded full warmup plus three measured requests per arm was planned. All original RAM/VRAM guards, zero owned swap/spill, cgroups and 8 GiB SP2 activation reserve remained.

Both arms now passed video VAE loading and reached the 32B text encoder. Both then crossed the unchanged 3 GiB available-RAM floor. Neither completed a warmup, began denoising, or started the SP2 rank-1 model worker. Video/audio validation found zero completed media outputs. Full-request, denoising, decoding latency and speed ratio remain unmeasured.

| Arm | Available before GiB | Lowest available GiB | Completed generations |
|---|---:|---:|---:|
| control | 9.991 | 2.796 | 0 |
| sp2 | 12.013 | 2.894 | 0 |

## VRAM only models

All token throughput/TTFT entries below are **not measured**: no serving trial completed initialization and generated the requested benchmark outputs. Context values are requested/configured limits, not new full-window validation. Decimal GB is retained allocated storage. Selected working GGUF profiles were not replaced.

| Profile / tested engine | Prefill t/s | TTFT s | Decode code/prose t/s | Context limit | GB | Drive/path |
|---|---|---|---|---:|---:|---|
| Qwen27B · vLLM dev435 /dev602 | not measured | not measured | not measured | 163,840 | 20.05 shared base | System `/opt/local-llm/models/Qwen3.8-27B-W4A16-AutoRound-GPTQ` |
| Bolt W4A16 · vLLM dev435 /dev602 | not measured | not measured | not measured | 262,144 | 43.65 | SATA1 `vLLM-Models/Nemotron-3.5-Bolt-74B-A9B-AutoRound-W4A16` |
| Qwen27B · SGLang DFlash2/f84475cc | not measured | not measured | not measured | 163,840 | 21.34 incl shared base +draft | System model above +`models/drafts/Qwen3.8-27B-DFlash2-W4A16` |
| Sage native W4A16 · vLLM dev602 | not measured | not measured | not measured | 65,536 | 20.33 | SATA1 `vLLM-Models/Sage-A1.5-W4A16-AutoRound` |
| Sage native W4A16 · SGLang auto /explicit GPTQ | not measured | not measured | not measured | 65,536 | 20.33 same files | SATA1 same Sage candidate directory |
| Flint AWQ · vLLM dev602 isolated ROCm pilot | not measured | not measured | not measured | 32,768 | 22.42 | SATA1 `vLLM-Models/Flint-AWQ` |

All five corrected normal-launcher framework cases reached actual initialization/loading and stopped at the unchanged 4 GiB cumulative system swapout budget. Both baseline profiles and both new-vLLM candidates failed that gate; current SGLang did too. No source performance regression is inferred. Framework/INT4 workers retained the existing low-churn policy, including 4 GiB aggregate worker-swap cap, sampled host-memory/PSI and continuous-inference requirements, and zero dedicated VRAM spill. These are distinct from graphics' stricter zero-worker-swap policy.

Native Sage/vLLM and Flint/vLLM also stopped at the swapout budget. Flint retained the earlier isolated ROCm attention/norm experiment and 128-token reasoning budget; no output correctness or speed is established.

Native Sage/SGLang progressed through checkpoint loading to a **Marlin HIP compilation failure** on its automatic AutoRound backend route. Its child exit later appeared to the watchdog as `telemetry_error:RuntimeError`; this case is a backend compile failure, not a RAM-floor measurement. An additional isolated trial selected the source's existing plain-GPTQ route through `quantization_config.backend=gptq`, retaining the full original quantization dictionary, weights, BF16 activations/KV, TP2,64K,MTP3 and guards. That changed trial stopped during loading at the swapout budget, before proving that alternate backend works. Production SGLang source/model files were not patched.

The native Sage trials remain language-only and do not qualify a replacement for the current GGUF's vision capability. The downloaded Sage/Flint candidates are retained as unqualified assets; shared files count once. [Storage inventory](MODEL-STORAGE-INVENTORY.md). Earlier qualified llama.cpp Empero/Sage/Flint profiles remain selected at 19cce691; their separately dated rates are in the [engine qualification](VRAM-ENGINE-UPDATE-2026-10-27.md).

### Actual loading guard outcomes

| Trial | Available before GiB | Host swapout GiB | Owned swap peak MiB | Root outcome |
|---|---:|---:|---:|---|
| `qwen3.8-27b-vllm /baseline` | 10.952 | 4.018 | 3219.17 | system swapout budget |
| `nemotron-3.5-bolt-vllm /baseline` | 11.672 | 4.201 | 3911.52 | system swapout budget |
| `qwen3.8-27b-vllm /candidate` | 11.644 | 4.010 | 3254.74 | system swapout budget |
| `nemotron-3.5-bolt-vllm /candidate` | 11.799 | 4.006 | 3469.61 | system swapout budget |
| `qwen3.8-27b-sglang-dflash2 /baseline` | 11.741 | 4.109 | 3030.20 | system swapout budget |
| `sage-a1.5-int4-vllm /native` | 11.726 | 4.064 | 4028.25 | system swapout budget |
| `sage-a1.5-int4-sglang /native` | 11.323 | 3.885 | 3312.19 | Marlin HIP compile; child exit |
| `flint-40b-a2.5b-awq-vllm /native` | 11.175 | 4.106 | 3474.36 | system swapout budget |
| `sage-a1.5-int4-sglang /explicit GPTQ` | 11.104 | 4.079 | 4073.87 | system swapout budget |

A sampled guard-crossing value can exceed its threshold before shutdown completes. Cumulative host swapout is a conservative system-wide counter, not solely worker-attributed I/O; all actual counters remain inspectable. No inference window qualified and no new engine or quantized model was promoted.

## MoE models with CPU RAM offload

Super IQ3 and Ornith retain their profiles, source pins and physical-RAM admission. They were not retested or retired.

## MoE models with SSD streaming

Strata Qwen Q3, GLM Maya and DeepSeek XS on Maya/Strata retain their profiles, weights, guards and pins. They were not retested or retired. DSH's default and the paused updater remain unchanged.

## Full-lifecycle thermal summaries

Each GPU triple is edge /junction /memory °C, covering startup/loading/failure/shutdown. CPU is package peak. Raw SMU flags do not quantify lost performance; sampled peaks cannot exclude between-sample transients. The numeric record also retains fan RPM, clocks, power, utilization, flag availability and sampling coverage.

| Trial | Samples/errors | GPU0 °C | GPU1 °C | CPU °C |
|---|---:|---|---|---:|
| control H3 | 36/0 | 24.0/29.0/24.0 | 20.0/31.0/44.0 | 60.0 |
| sp2 H3 | 35/0 | 24.0/29.0/24.0 | 20.0/31.0/44.0 | 59.0 |
| qwen3.8-27b-vllm/baseline | 34/0 | 25.0/31.0/28.0 | 21.0/32.0/44.0 | 76.0 |
| nemotron-3.5-bolt-vllm/baseline | 60/0 | 26.0/33.0/30.0 | 22.0/33.0/46.0 | 85.0 |
| qwen3.8-27b-vllm/candidate | 42/0 | 28.0/34.0/30.0 | 22.0/34.0/46.0 | 74.0 |
| nemotron-3.5-bolt-vllm/candidate | 52/0 | 28.0/34.0/30.0 | 22.0/33.0/46.0 | 87.0 |
| qwen3.8-27b-sglang-dflash2/baseline | 34/0 | 28.0/35.0/30.0 | 23.0/34.0/46.0 | 72.0 |
| sage-a1.5-int4-vllm/native | 50/0 | 27.0/33.0/30.0 | 22.0/33.0/46.0 | 70.0 |
| sage-a1.5-int4-sglang/native | 75/0 | 28.0/34.0/32.0 | 23.0/33.0/45.0 | 70.0 |
| flint-40b-a2.5b-awq-vllm/native | 78/0 | 28.0/34.0/32.0 | 23.0/34.0/46.0 | 75.0 |
| sage-a1.5-int4-sglang/gptq | 50/0 | 28.0/34.0/30.0 | 22.0/32.0/45.0 | 69.0 |

## Decision and follow-up

Retain every selected model/profile/pin and working workflow. All owned scopes report cleanup; both GPU/server locks were released by their respective tests. Original production-profile fingerprints match. No pre-existing user apps were force-closed and the compiler-temp data remains archived on disk. No new model files were downloaded or removed.

The existing hourly H3 follow-up remains active for an actual OS-visible RAM increase, with short disk-backed temp-path guidance. It stays quiet while RAM is unchanged or the host is busy, preserves all guards, performs no automatic promotion, and stops after recording/publishing the post-upgrade comparison or substantive guarded attempt.
