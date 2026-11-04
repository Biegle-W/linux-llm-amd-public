# Latest Maya/Strata, Unsloth Q1 and pinned tasks — November 3, 2026

**November 4 timing correction:** the agent-added 20-second TTFT cutoff was unsuitable for these large models. Past first-output deadline stops are **inconclusive inference attempts**, not proof the models cannot work. Raw outcomes remain. Corrected diagnostics measure prefill and use existing enclosing budgets while preserving physical safety and cleanup guards. [Corrected policy and verification](PREFILL-TIMING-CORRECTION-2026-11-04.md).


**Partial qualification complete; remaining downloads/checks continue.** Latest official Maya 1.1.52 (`6c9a27b44fa1`) and Strata 0.2.10 (`ffa80d73133e`, DeepSeek native 0.1.56) are built in isolation. This record separates passing short checks from failed qualifications and candidates that have not run. Strata Qwen 0.2.10 is now installed with the passing MTP settings: 12 GiB resident expert budget, native reserve 1024 MiB, prefill 256, spec 2/p=0.7, USERPTR off, direct-I/O loading and the tested GPU order. Source/binary hashes, installed server environment, resource admission, assets and unchanged catalog hold were verified. A complete rollback copy is retained. Maya remains 1.1.40 and Strata DeepSeek remains 0.2.4 after their candidate request failures. All catalog holds remain. No new GPU reset, bus-loss or OOM fault has been recorded in this no-switch boot.

## Completed short checks

| Candidate | Outcome |
| --- | --- |
| Latest Strata Qwen, Off | Reused the completed exact-source/configuration no-switch short pass; no duplicate run. |
| Qwen MTP, 128 MiB native reserve | Free-VRAM floor stopped startup. Native cache-sizing reserve is distinct from the independent 128 MiB free-VRAM guard. |
| Qwen MTP, 1024 MiB native reserve | **Passed:** load 75.334 s; actual MTP active; one read tool, two model steps, correct marker and matching IDs, 86 output tokens. Draft acceptance 41/41 across these requests. Verified owned unload. |
| Initial DFlash2 selection | **Does not qualify DFlash2.** An inactive pipeline-window argument triggered upstream fallback; actual native argv loaded no neural drafter. The initial interface label was wrong. |
| Explicit DFlash2, pipeline auto off | Actual DFlash2 active, MTP absent; load 133.287 s, strict tool/marker correct, 85 output tokens, 38/45 draft acceptance. Raw runner failed a proxy-thread completion race; final proxy rows both completed. Independent audit establishes inference success with that harness defect. Raw failure retained; no rerun for a clean log. |
| Latest Strata Unsloth Q1, 128 MiB native reserve | Startup free-VRAM floor block. |
| Strata Q1, 1024 MiB reserve | Loaded 157.049 s; actual DSH request missed 20 s first output. No tool pass. Owned unload verified. |
| Maya Q1 | Loaded 153.573 s; actual DSH request missed 20 s first output. Owned unload verified. |
| Strata Q1, community-informed RAM store | Supported 36 GB RAM store, gfx1100 kernel opt-in, 14 physical CPU threads; load 51.042 s. Actual tool request still missed 20 s first output. Zero sampled swap/spill; owned unload verified. This was a changed memory/kernel configuration, not a repeat of the same failed settings. |
| Maya GLM, initial adapter | Native model loaded, but old health-field expectation prevented readiness recognition. Invalid readiness wait; no inference claim. |
| Maya GLM, corrected adapter, 8 GiB expert RAM cache | Loaded 112.914 s; actual DSH first output exceeded 20 s. Clean owned unload. |
| Maya GLM, restored 40 GiB expert RAM cache | Supervisor heartbeat stopped while reading process arguments during large host-memory registration. This is a monitor-read blockage, not a GPU-fault result. |
| Maya GLM, same 40 GiB cache after monitor correction | Monitor remained responsive; native loading missed the unchanged 210 s deadline. Owned scopes and KFD clients emptied. No inference pass. |

The DSH prompts include the real tool schema (roughly 5.5–5.9K input tokens), rather than a minimal greeting. First-output stops cannot be relabeled as working inference. Prepared basic-prompt and long benchmark scripts remain unrun and unqueued. The short-check policy does not authorize retrying failures with easier prompts or extending progress deadlines.

## Numerical and CPU verification

Latest Maya exercised 38 per-GPU cases across both gfx1100 cards: 36 required cases passed, including selected exact-Q1 format combinations on both cards. Two known fused-prefill cases still fail; `MAYA_GLM_PREFILL_FUSED=0` remains required. Five CPU tests pass after explicitly building the two CPU-prepare targets excluded from the default build. Earlier selected Strata format tests remain tied to the identical staged build; no redundant GPU math sweep was run. Unselected mixed-format failures are retained; this is not universal quant-format qualification.

The Q1 files remain the previously full-hash-verified five-shard Unsloth revision `2688c0c3c2c3b052ec4f6d10a8417b0ef7ee4eba`, 232,979,608,420 bytes. Stat identities and pack metadata were checked; no repeat full download/hash pass was needed.

A focused monitor fix reads kernel process identity for already owned cgroup members, preserving same-UID, start-time, zombie, cgroup-membership and pidfd-signal checks. It avoids reading argument/cwd pages that can block behind host-memory registration. Global process classification is unchanged. Fourteen current-policy CPU checks pass in each repository. Nine existing ownership/containment checks pass with their explicit CPU-only historical fixture opt-ins; three historical expectations fail under the current owner policy because they expect superseded limits. Those legacy limits were never applied to GPU work. Private readiness, proxy-commit and owned-scope helpers pass 5, 4 and 4 checks respectively.

## Other pinned tasks

- **Super INT4/vLLM:** retained full checkpoint and exact runtime used. Plain TP2 failed before model readiness: expert width 1344 per rank is not divisible by quantization group 128. The supported EP2 alternative keeps each expert's full 2688 width; actual meta-allocation and AMD parallel-selector checks pass. Its full load reached the existing 900-second startup deadline before readiness (40/64 shards in the last progress record); no tool result exists. Maximum sampled worker swap was 7.28 GiB and spill zero; minimum available RAM was 1.71 GiB. The kernel recorded host-memory workqueue and memory-pressure warnings, without GPU reset/bus-loss/OOM. A second graceful stop interrupted the controller while saving cleanup records. Independent postmortem verification found all three owned scopes inactive and removed, KFD empty and no new kernel GPU fault. The original interrupted record and added verification are retained separately. Context is 8192, one request, BF16, eager, 2 GiB KV/rank and 18 GiB CPU offload/rank. P2P remains disabled. The copied harness advertises an overlarge window; no request beyond the actual backend cap is permitted or qualified.
- **DeepSeek Coder:** exact ISTA revision `54229d38d588a66d1c6cff08af7b281b9326c656`, 182,718,891,848 bytes, now fully downloaded and SHA-verified on the designated streaming SSD. Both metadata-only packs are created against that one backing. The nominal IQ2_XXS pack actually contains IQ1_M, IQ2_XXS and IQ2_XS routed experts, with 192 experts in each of 40 layers. The earlier Q1-only test matrix is insufficient for this mixed layout; seven newly needed role pairs and the two new dense formats receive selected tests on each card and engine before its short model check.
- **Checkpoint-backed ROCm PLE:** exact-hash AMD source overlay reproduced against retained vLLM. The actual quantization validator admits the Intel and FP8-PLE AutoRound configs as INC. Upstream `disk_offload` remains CUDA-only; it is separate from this opt-in AMD port. The compatible FP8-PLE checkpoint download has started; only the index-referenced files are selected (approximately 124.825 GB including metadata), with per-file hashes. A short TP2/EP2, 8K, no-MTP candidate is staged; no device or full-model pass exists. The explicit native AMD overlay remains isolated from the installed wheel.

## Remaining owned work

Coder backing verification and both metadata conversions are complete; the PLE download continues on the designated streaming SSD. A single one-off continuation waits for complete verification, converts the Coder metadata packs, then runs only the two Coder engine checks and the PLE check. Each uses one strict DSH read-tool round trip followed by owned unload. It checks the same boot, refuses an existing active stage, and stops the GPU queue on temperature/GPU/monitor faults or unverified cleanup. Five CPU boundary checks pass. The interrupted-cleanup signal race is corrected only in future private controllers; four real-signal/persistence/deadline CPU checks pass, retaining the 6/15-second watchdog limits. No recurring schedule or automatic production promotion was added.

The remaining weight transfers are an external wait, not completed qualification. A later checkpoint must inspect their saved results; do not launch duplicate stages or repeat completed tests.


The first Coder test gate was stopped after the older Strata synthetic IQ1_M generator produced NaNs in both CPU and GPU comparisons. Its scale lives in the high nibbles of four words at bytes 48–55; the old fixture wrote a half at byte zero. A CPU encoding audit found 305 nonfinite scales among 10,000 old random samples and none with the legal encoding, preserving the low 12 code bits. The corrected test copies only the legal scale case already in upstream Maya; engine arithmetic, reference comparisons and tolerances are unchanged. The raw failed fixture and verified owned unload remain recorded. This is not a claim of a GPU-kernel failure.

The one-off continuation also initially refused an ownership check as the completed download scope exited, before any GPU model launch. Its freeze helper now waits for a terminal unit state and refuses root, wrong or unrelated populated cgroups; four CPU checks pass. No model attempt was repeated for that pre-launch refusal.


The corrected legal combined batch reached its 210-second process limit after both new dense formats and the first three role pairs completed on Strata GPU0, with all recorded comparisons finite and matching. Its raw timeout remains a failure. An independent output audit reuses only those completed checks (11 successful comparisons for each of the small and model shapes). Remaining pairs now run as independent processes with the same 210-second limit, grouped into per-card stages with the existing 900/990-second caps. Each model check still waits for its engine to pass both cards. No completed pair is repeated for a clean log, and model first-output/request/cleanup thresholds are unchanged.

## November 4 completed Coder follow-up

All four engine/card selected-format stages passed. The audited Strata GPU0 prefix was reused; the remaining independent cases completed without changing reference math, tolerances or numeric guards. The earlier invalid fixture and combined-batch timeout remain recorded as failures, rather than being overwritten.

- **Maya 1.1.52 / ISTA Coder:** passed the actual installed DSH headless read-tool round trip. Load **31.961 s**; first output **15.694 s**, then **1.398 s** for the tool-result reply; exactly one read, two model steps, **98 generated tokens**, matching IDs and exact final marker. Both proxy requests completed. Guard passed and owned scopes/KFD emptied.
- **Strata 0.2.10 / same Coder backing:** loaded **20.950 s**, then the first DSH request hit the unchanged **20-second first-output deadline**. No tool round trip passed. Owned scopes/KFD emptied; no new GPU fault was recorded.
- **PLE:** download still in progress; no device/model test yet. The same one-off continuation is waiting for full file verification. No production promotion is automatic.

The Maya Coder result qualifies this isolated model/configuration for a short tool request. It does not qualify GLM or Unsloth Q1, establish sustained stability, or enable a normal catalog route. Installed Maya and Strata DeepSeek pins and all existing catalog holds remain.

## Guards and interpretation

P2P remains off on both direct x16/chipset x4 cards. Free RAM 1 GiB, free VRAM 128 MiB per card, current RAM hard limit, unrestricted soft limit, loading-swap-v5 SSD health/temperature checks, first output 20 s, request 30 s, decode stall 3 s, supervisor heartbeat 6 s and cleanup 15 s are unchanged. Existing 33.53 GiB swap capacity is unchanged. Q1/Super/PLE use their existing 900 s startup allowance; GLM/Qwen use 210 s. Edge/junction-memory/CPU limits remain 75/90/85°C. No driver, kernel, PCIe, PSU-wiring or schedule change was made.

An engine passing a short tool check does not establish sustained stability, full-window quality or a PSU/switch diagnosis. Failed source/model combinations are not promoted. Preserve the no-switch historical successes and thermal stop without repeating them.

[Community configurations and source links](DUAL-XTX-64GB-COMMUNITY-RECIPES-2026-11-03.md). [Structured progress and corrections](results/maya-strata-q1-upgrade-2026-11-03.json). [Short-test policy](SHORT-HARNESS-TEST-POLICY-2026-11-01.md).

<!-- pinned-followup:begin -->
## Follow-up checkpoint

2026-11-04T05:29:13.683863+00:00 UTC: waiting for verified downloads: ple. Completed records are reused.

| Check | Saved status |
| --- | --- |
| coder-format-parity-legal | testprocess-timeout |
| coder-formats-strata-0 | passed-selected-formats |
| coder-formats-strata-1 | passed-selected-formats |
| coder-formats-maya-0 | passed-selected-formats |
| coder-formats-maya-1 | passed-selected-formats |
| strata-coder | failed — first output deadline |
| maya-coder | passed-one-short-DSH-check |
| vllm-ple-file-gather | prepared; not run |
<!-- pinned-followup:end -->
