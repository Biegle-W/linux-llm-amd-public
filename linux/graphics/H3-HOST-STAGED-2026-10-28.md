# H3 host-staged transport and comparison — October 28, 2026

Follow-up: [fresh true-one-card versus two-card tests](H3-ONE-VS-TWO-2026-10-28.md) now establish a fresh cold-workflow comparison. The original repeated-request failures below remain historical evidence for their different lifecycle.

The isolated host-staged H3 candidate passed its five-frame canary and all four 39-frame requests, with a 121.332 s timed median and 56.762 s sampler median. Both fresh one-card attempts completed only their excluded warmups, then stopped at the unchanged 3 GiB RAM floor during the first timed DiT load, including a standard-cleanup retry. No fresh three-trial control median or matched speedup is established. Loading-swap-v3 and all independent RAM, VRAM and ownership guards remained active. This is an isolated experiment; no production profile was promoted.

## Implementation and admission

Both live Torch peer queries remain false. The earlier [unmodified source admission failure](H3-DAVODDINO-2026-10-28.md) is preserved. This follow-up implements explicit GPU-to-pinned-host-to-GPU copies throughout an isolated davoddino-derived snapshot. One 64 MiB pinned buffer is serialized across copies; each leg receives a completion-event acknowledgement before reuse. Enqueue, event-construction and completion failures retain referenced storage and poison the owner until process teardown. Source reads use bounded preadv/H2D batches with retained file-identity checks.

The four original payload hashes match the frozen model manifest. The generated rank shards and pair manifest match upstream hashes. Local inode identities are sealed only after full-file equality, preserving header, manifest, marker and identity admission. The retained Torch/kitchen versions are admitted explicitly; the native Kilo48 backend and the author's exact environment are not reproduced. Source snapshots and trial entry points stay isolated from production.

Eleven GPU fixtures pass again after the retention repair, including both directions, five dtypes, 64 MiB boundaries, bit-exact roundtrips, reduction and source reads on both owners. Twelve CPU fault-injection cases pass, including poisoned-owner refusal, lock ownership, event timeout/construction/enqueue errors, RAM admission, changed files and symlinks. These fixtures are distinct from whole-model quality validation.

## Requested workload and measured results

608×352, 39 frames, 24 fps, 20 steps, seed 42, res_multistep/simple, CFG 1 and the same text prompt. Each benchmark arm requests one excluded warmup and three timed generations, using cache-none and the same loading-swap-v3 guards. The original control completed its warmup then stopped at the 3 GiB physical-RAM floor during the first timed DiT load. Its retry uses the standard owned-server /free unload_models+free_memory endpoint after every request; cleanup is separately measured outside server execution time. This changes between-request lifecycle and remains explicit in the comparison. Candidate DiT is split across both cards; the saved control has one-card DiT on GPU0 and encoder/VAEs on GPU1.

| Arm | Completed requests | Full server median s | Sampler median s |
|---|---:|---:|---:|
| Fresh one-card DiT control, standard cleanup | 1 | not available | not available |
| Explicit host-staged two-card DiT, 1 warmup + 3 timed | 4 | 121.332 | 56.762 |
| Saved October28 reference | 1 timed + warmup | 210.098 (single timed sample) | 28.324 (single timed sample) |

| Full lifecycle | Minimum available RAM GiB | Peak used VRAM GPU0 / GPU1 GiB | Peak worker swap GiB |
|---|---:|---:|---:|
| benchmark-control-r2 | 2.990 | 20.618 / 17.081 | 6.368 |
| benchmark-candidate | 18.660 | 17.020 / 10.078 | 0.000 |

No control server-plus-cleanup median exists because neither timed control request completed. Cleanup remains subject to all guards. These lifecycle peaks include encoder/loading/decoding phases, not only DiT sampling. Both one-card attempts produced only excluded warmups: 188.829 s initially and 216.083 s on the standard-cleanup retry. Neither completed a timed control generation. The retry cleanup after its warmup took 1.255 s and left 21.493 GiB available RAM, but the next request still hit the floor. The numeric record retains individual warmup/timed requests, guarded failures, phase spans, memory, swap and lifecycle thermals. A failed lifecycle duration is not a generation latency. The saved reference is historical v2 evidence, not a fresh matched median.

This is an end-to-end comparison of two execution paths. The candidate creates noise on GPU and explicitly destroys/reloads owners between phases; the saved path creates CPU noise and uses the standard model-loading lifecycle. Same seed does not imply identical input noise or pixels. Different Comfy source snapshots also limit attribution: any timing change cannot be assigned solely to host transport. The candidate ran first, followed by the control; only the candidate completed three timed samples. Those support its latency estimate; there is no fresh matched control median or broad performance guarantee. Cache-none forces computation for every request; these numbers do not characterize cached production reruns.

## Retained failures and repairs

- Initial server startup used an unsupported command-line flag; the frozen snapshot's supported API-node switch replaced it.
- The next attempt completed encoding but correctly rejected the author's stale shard inode pins. Full local shard hashes were reverified before local identity sealing.
- The next attempt completed all 20 DiT steps but audio staging updated a buffer from the wrong inference-mode thread. Staging now completes in the owning execution thread before concurrent AV decode.
- The next attempt completed generation and output audit but hit the older SaveVideo codec schema. Only the isolated graph was adapted. The subsequent complete five-frame workflow saved valid AV media.

The original control completed a 188.829 s warmup, then its first timed request stopped during DiT loading at 3,145,764,864 available bytes, below the unchanged 3 GiB floor. Worker swap occupancy was permitted, no swap-policy failure occurred and dedicated VRAM spill remained zero. The standard-cleanup retry also stopped on its first timed DiT load at 3,210,752,000 available bytes, again below 3 GiB. Normal cleanup released GPU owners in 1.255 s after its 216.083 s warmup, but did not make repeated requests fit. Both attempts had zero dedicated VRAM spill and no swap-policy failure. The allocation/retention root cause is not established.

All failed evidence remains private and separate from successful samples. Production configuration fingerprints match after owned-worker cleanup.

## Guards, media and operational status

Host available RAM floor 3 GiB; free VRAM soft floor 2 GiB for four samples and hard floor 1.5 GiB; source-reader floor 3 GiB; zero dedicated VRAM spill; scope RAM cap equals 32,811,163,648 physical bytes with unlimited swap occupancy. Loading, parked swap and reads remain allowed; rates and PSI are advisory, with no configured SSD-write budget. Whole-host swap I/O counters do not attribute every byte to the owned worker. Unique owned scopes, exclusive GPU/server locks and full-lifecycle telemetry contain the trial. Only owned work may be stopped for independent guard faults.

All seven saved files (five-frame canary, four candidate 39-frame outputs and two excluded one-card warmups) pass complete ffmpeg AV decoding. Each file passes 608×352, 24 fps, expected-frame-count and finite stereo 32 kHz PCM checks. Sampled frames show the intended red teapot scene without obvious corruption. Final 39-frame media results and exact hashes appear in the numeric record. Audio semantics and exhaustive motion quality are not assessed. All four fixed-seed candidate videos have different decoded-frame digests and different decoded PCM digests. Whole-model bitwise determinism is therefore not established; the bit-exact transport fixtures do not imply model-output equality. Decoded frame and PCM digests are retained for within-arm inspection.

The next work is to profile the standard loader CPU/RAM peak during the second request after normal cleanup and make a concrete lifecycle repair before another matched retry, with every guard preserved. Candidate same-seed output variation also needs investigation before production qualification. No automatic production promotion is made. Selected LLM pins and paused schedules remain. Original model payloads, production environments and boot/hardware settings were unchanged; generated trial shards remain isolated. No existing task was unloaded or interrupted.

## Broader public forum research

Public searches covered H3 with 7900/P2P/RCCL, host-staged, CPU中转 and 多卡 terms, followed by linked source discussions. This is not an exhaustive audit of private or unindexed forum content.

- [fcys W7900 report](https://lcz.me/topic/2643) is a separate INT8/RCCL implementation. A later [reply 17](https://lcz.me/topic/2643/17) now includes four complete tp2-comfy v1.0.0 code blocks. This supersedes the earlier no-source snapshot. It uses two rank processes, shared activation scales and FP32 row-parallel accumulation. The author's W7900 result is not a local XTX measurement; the posted source was inspected privately, not deployed or republished under an assumed license.
- [X99 host fallback discussion](https://lcz.me/topic/1749/3) illustrates transport verification and explicit P2P disabling on different NVIDIA hardware. It does not validate this H3 implementation. [Dual-XTX discussion](https://lcz.me/topic/1839/18) also distinguishes missing P2P from inability to run RCCL tensor parallelism; its workload is an LLM.
- [H3 distributed sampling and separate decode](https://lcz.me/topic/2138/6) is another architecture, using different GPUs and xFuser/Raylight. The [project landing page](https://lcz.me/projects/local/h3-multigpu-pipeline) exposes no usable implementation through its public read-only shell. These do not replace local guarded validation.

[Sanitized numeric evidence](../hardware/results/h3-host-staged-2026-10-28.json) records the final measured scope. Native Radiance remains a separate gfx1100 kernel-compatibility issue.
