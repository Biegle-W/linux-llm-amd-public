# DeepSeek GSQ-RCO on dual 7900 XTX / 32 GB RAM — test plan

Date: November 1, 2026. **Status: research and plan only.** No model download, compilation, GPU probe/trial, runtime deployment, service change or new schedule was performed. This plan evaluates the current host; it does not require waiting for the planned RAM upgrade. Existing production selections, RAM holds and guards remain.

The question is whether Strata can use both 24 GB GPUs, a bounded host expert cache and SSD-backed weights/Engram to run a useful full-routing DeepSeek configuration on approximately 30.56 GiB visible host RAM. Nominal 48 GB VRAM + 32 GB RAM exceeds the cited 12 GB + 64 GB example. Those pools have different uses and overhead, so only measured placement can settle fit. A retained profile's 60 GiB physical-RAM check is not a universal engine minimum.

## What the forums establish

| Evidence | What it establishes | Limit for this test |
|---|---|---|
| [First-hand dual-XTX report, Strata issue 4136](https://github.com/Niko1221/Strata/issues/4136) | DeepSeek 2.00 bpw ran on two gfx1100 cards and an AVX2 Intel CPU using a source-built DeepSeek engine. | Host had 64 GiB RAM; its cache sizes and split tuning do not qualify this 32 GB host. |
| [Single-XTX benchmark, PR 4800](https://github.com/Niko1221/Strata/pull/4800) | IQ1_M 1.75 bpw, engine 0.1.54, 64K context: about 10 tok/s short decode and 14.3 tok/s agent follow-ups; 36 measured requests completed. | 62.6 GiB RAM, newer isolated TheRock SDK, only about 568 MiB free GPU memory, and explicitly no correctness check. Preserve our larger reserves. PR 4796 is an earlier submission of the same evidence, not a second reproduction. |
| [Conversation-switch failure, issue 4350](https://github.com/Niko1221/Strata/issues/4350) | A→A→A→B→A can fault on gfx1100 even when many same-conversation requests pass. | The maintainer's October 31 comment describes fatal-error recovery, not a demonstrated root-cause fix. Some comments concern Qwen and must not be counted as DeepSeek reproductions. |
| [Mixed R9700/XTX placement report, issue 3933](https://github.com/Niko1221/Strata/issues/3933) | Actual PCIe bandwidth, layer placement and host-cache size can change the bottleneck substantially. | Its XTX was behind a PCIe 3 x1 link, unlike our two CPU-connected PCIe 4 x8 links. Copy the measurement method, not its split. |
| [DeepSeek memory guide](https://github.com/Niko1221/Strata/blob/main/docs/MODELS.md) and [0.2.4 release](https://github.com/Niko1221/Strata/releases/tag/v0.2.4) | Expert streaming is intentional; the author reports a 12 GB RTX 3060 with 46 GB RAM. Full backbone residency is not a prerequisite. | NVIDIA results do not establish Radeon kernel correctness or speed. |
| [Reddit hardware discussion](https://www.reddit.com/r/LocalLLM/comments/1xe7r2g/for_those_running_deepseek_41_what_are_you_using/) | Useful leads for configurations and user workloads. | Anecdotes without matching model, version, memory and raw logs are discovery leads, not acceptance evidence. Several other low-RAM Strata threads concern Qwen rather than DeepSeek. |

No reviewed report establishes this exact pair of GPUs with 32 GB host RAM and the AtomicChat checkpoint. The reports justify an isolated test, not an assumed pass or failure. They also make clear why a successful short answer is insufficient.

## Freeze the candidate and control

Use [Strata v0.2.9](https://github.com/Niko1221/Strata/releases/tag/v0.2.9), source `c62d5e3a15b40ea51c96aae9e8d36928965f53ab`, engine/Control package version 0.1.55, as the candidate source. The packaged Linux DeepSeek HIP artifact is `rx9070`; do not install that gfx1201 build on gfx1100. Build a separate gfx1100 executable and retain its exact source, compiler, linked libraries and binary hash. The single-XTX report used 0.1.54 / `870aedd9e` and a newer SDK; its speed is context, not a current baseline.

Keep the working source/build paths untouched. Retained DeepSeek is `8183c6b67162340c09b67360860177c577a65f2e`, ROCm 7.2.3; retained Qwen is `7dd5cf18e68c`. Reuse completed local trials as evidence; do not repeat the prior Qwen trials as part of this DeepSeek plan.

Start with **stock ISTA GSQ-RCO IQ1_M / 1.75 bpw** as the compatibility control. Once it passes, test **AtomicChat's corresponding IQ1_M** on the same engine, cache budget, context, prompt set and seed. This separates low-bit/kernel/resource feasibility from the behavior modification. Do not silently substitute Unsloth UD-IQ1_M, Maya-XS IQ1_S, or a pruned/routing-reduced pack; their names and layouts are different.

AtomicChat's backbone is 120,721,120,256 bytes. The shared ISTA IQ4_NL Engram is approximately 110.6 GB: about 231.3 GB total per active model. A retained stock control plus AtomicChat backbone plus one shared Engram is about **352 GB of source weights**, before preparation, caches and temporary files. The local shared NVMe had approximately 432 GB available when checked, leaving only about 80 GB before those additions. Inventory actual preparation requirements first; do not assume zero-copy preparation. Do not delete retained models to make room. The existing Q6_K Engram is not interchangeable with IQ4_NL merely because both are lookup tables.

Pin model revisions, all shard SHA-256 values, Engram and metadata hashes before acquisition. AtomicChat identifies its stock source as ISTA revision `cb02422c900d`; resolve it to a full immutable revision and verify the matching files. [AtomicChat card and modification details](https://huggingface.co/AtomicChat/DeepSeek-V4.1-Flash-1017-Uncensored-GSQ-RCO-GGUF).

## Stage 0 — preparation without GPU work

1. Inventory source pins, existing packs, free disk, RAM, PCIe placement, current backend ownership and relevant services. Record a restoration manifest; preserve all unrelated work and the current held profiles.
2. Read pinned source/build instructions and CLI help before choosing flags. Use a checkout path without spaces. [PR 4801](https://github.com/Niko1221/Strata/pull/4801) fixes force-include quoting for paths with spaces; it is not a kernel fix and need not be applied to a path without spaces.
3. Attempt a separate source build against the retained ROCm 7.2.3 toolchain and AVX2 CPU baseline. No AVX-512 assumptions. If incompatible, record the exact compiler/API blocker. A different isolated SDK is a separate candidate; never replace global ROCm, Torch, drivers, firmware or kernel to match a forum benchmark.
4. Inspect GGUF headers/pack metadata for tensor types, real expert shapes, supported dimensions, tokenizer, full routing and separate Engram references. The file's quant label is not a substitute for a type inventory. Ensure the source's CPU/GPU tests cover every selected type and actual shape. No skipping a failing selected type or loosening tolerances.
5. Prepare new pack/cache/session directories. Verify whether preparation copies payloads, and seal the initial expert-profile seed. Do not reuse writable production slot caches or overwrite user histories.

Stage 0 passes only with a reproducible build, valid files, enough disk for the real preparation path, and a reviewed launch manifest. It creates no inference result.

## Starting resource envelope

| Setting | Initial proposal |
|---|---|
| GPUs | Both gfx1100 cards explicitly selected; record actual loaded placement and expert counts. No silent single-card fallback. |
| Routing | Full six routed experts per token; no pruning, route-prior shortcuts, YOCO or prompt skipping. Verify effective logs rather than relying on defaults. |
| Context / requests | 8,192 total tokens initially; one request at a time. Leave space for generated tokens. |
| Expert RAM store | Explicit 8 GiB target initially, using the pinned CLI's verified units and option. Avoid host-wide auto-sizing. Only consider 12 GiB after 8 GiB passes with headroom. |
| Worker RAM scope | Existing bounded 32 GB envelope: MemoryHigh 18 GiB / MemoryMax 20 GiB, swap allowed under the current phase-aware policy. No automatic increase. |
| Host admission / floor | At least 29 GiB physical visible; at least worker cap + 3 GiB available before loading; retain the 3 GiB running host floor. |
| VRAM | Keep 8,192 MiB reserve per card and at least 6 GiB actual free per card at readiness, with existing continuous soft/hard headroom protections. Zero dedicated spill is an acceptance condition. |
| CPU / features | 24 threads initially, AVX2; DSpark and vision off; text-only, one slot. Add features only in separately recorded later steps. |
| Transport | Current validated placement and transport. No P2P/ACS/IOMMU, SDMA, firmware, clock or fan changes based on forum posts. |

This is a new isolated candidate configuration, not an edit to the sealed 64 GB profile or a waiver of its validator. Use the existing bounded-profile/ownership/telemetry framework with candidate-specific resource validation. Confirm that the new source accepts each setting. DeepSeek uses `--reserve-mib`, not Qwen's `--vram-reserve-mib`; some Qwen options are ignored or rejected by this engine. Record native KV format and its validation; do not invent a generic `kv=` option.

## Stage 1 — kernels and measured fit

Acquire the normal exclusive GPU reservation only when inference and other compute are idle. Never evict another owner. Launch only the owned candidate in its unique scope; all telemetry and ownership checks must fail closed.

- Run the existing CPU-reference, finite-value and actual-shape quantization tests on each GPU, then the dual-card path. Retain existing numerical tolerances and cross-card requirements. Record unsupported types as a blocker for this pack.
- Load stock IQ1_M at the initial envelope. Capture CPU anonymous/file-backed/page-cache attribution, scope current/peak/swap, per-card free/resident/shared/evicted VRAM, expert cache placement and allocation sizes. RSS alone is insufficient.
- Check a handful of short factual, arithmetic, JSON and ordinary coding requests. Record full load and request wall time, first-token time, input/output token counts and decoded output. A load, a warm model or high GPU utilization alone is not a pass.
- If fit fails at 8 GiB store, preserve evidence and stop. Do not lower desktop reserves or host floors, switch off telemetry, count swap as guaranteed capacity, or silently abandon one GPU. An accepted smaller cache requires a fresh reviewed envelope; it is not an automatic retry.

## Stage 2 — correctness, history and failure reproduction

Stay serial. First run A→A→A→B→A with distinct system prompts and explicit facts, checking that A's facts survive and B's do not leak. Repeat on three fresh owned starts. Record proof of actual cache reuse/restore; a path not reached is not covered. Do not enable experimental persistent slots to manufacture coverage. Also test a fresh unrelated prefix and a restart after saved-session use. A 503/restart, illegal access or hang is a failure, not a successful recovery.

Use controlled context growth: about 1K, 4K and 6K actual input at 8K context; then increase the candidate context to 16K for approximately 8K input, and to 32K for approximately 16K input plus follow-ups toward 24K. Check tokenizer counts and reserve output space. Do not jump to 64K/256K because a forum author did. At each level test:

- Multi-needle retrieval plus explicit unanswerable facts; exact expected markers and no fabricated missing facts.
- Multi-turn fact retention, corrections, two unrelated conversations and A→B→A cache restoration.
- JSON/schema compliance and declared tool calls with deterministic local stubs; tool execution, if later included, is limited to a temporary test directory.
- At least four small coding tasks with independent semantic checks, not string similarity to a preferred answer.

Stop progression on any wrong answer, malformed output, false retrieval, tool-schema failure, non-finite result, native watchdog stop or lost session state. Record sampling and fixed seeds; expert-cache CPU/GPU rounding means temperature zero is not proof of bitwise repeatability. Restore the sealed cache/profile seed for controlled comparisons, and record the OS page-cache state. Never flush the machine's global cache just to manufacture a cold run.

## Stage 3 — AtomicChat comparison and performance

Only after the stock control passes, repeat the same functional and history cases with AtomicChat IQ1_M. Preserve routed expert counts, KV format, context, cache budgets, session isolation and source. Report any behavior/quality changes separately from kernel stability and resource fit. Routed experts being byte-identical does not prove all output quality unchanged.

After both arms pass correctness, run one excluded warmup plus three alternating matched pairs for 4K and 8K fresh prompts and the same growing-history workload, using modest 128–256-token output limits. Report medians/ranges for end-to-end TTFT, engine prefill/decode, complete wall time, expert-cache hit rate, disk bytes/read bandwidth, RAM/VRAM and swap I/O. Record load time separately. A new 32 GB result must not be compared as a speedup against old 64 GB measurements or unrelated NVIDIA results.

Finish with a 30-minute serial mixed-workload soak that includes session switching and context growth, and verify clean owned shutdown. Concurrency is outside this initial qualification: reported multi-request gains are often NVIDIA-only, and separate dual-card cache faults exist.

## Stop conditions and decision

Keep `loading-swap-v4`: loading/parked swap allowed; inference swap writes limited to 128 MiB/s and combined swap I/O to 160 MiB/s over complete 30-second windows. Report how many complete windows were observed. Maintain the native no-progress watchdog, physical/scope caps, host/VRAM floors, zero-spill acceptance and telemetry fail-closed rules. Stop the campaign on a GPU fault/reset, OOM/kill, numerical failure or native watchdog failure. No unattended crash/restart retry loop. Capture relevant kernel messages and terminate only owned workers; retain the reservation if owned cleanup cannot be established.

Classify outcomes as **build/layout blocked**, **kernel/numerics blocked**, **resource blocked under retained guards**, **functional/history failed**, or **qualified within the measured context/features**. A resource failure does not prove that 32 GB can never work; it identifies the failed allocation/envelope. Fit alone does not qualify quality. No throughput win should be claimed until matched evidence exists.

A successful isolated candidate still needs the normal guarded authenticated API, JSON/SSE/tools/history, ownership and idle-release checks before any later activation. Preserve the old source/build/profile/weights as rollback. No production pin, RAM hold, default model or schedule is changed by this plan.

[Machine-readable envelope, stages, exact functional/session fixtures and coding checks](results/deepseek-gsq-32gb-test-plan-2026-11-01.json).
