# H3 davoddino trial and linked forum review — October 28, 2026

Follow-up: [explicit host-staged implementation and tested comparison](H3-HOST-STAGED-2026-10-28.md) supersedes the current-status interpretation below. The original unmodified-source failure remains valid historical evidence; later fcys reply 17 now provides source.

The requested davoddino candidate cannot reach generation on this host unchanged.
Its real H3 coordinator admission constructor raises **`H3 TP requires bidirectional P2P`**.
Both physical RX 7900 XTX cards enumerate as gfx1100, but live Torch/HIP peer queries
return false in both directions. No RAM, VRAM or swap guard fired. No existing task
was stopped or restarted; OS swap remains enabled under loading-swap-v3.

## What was actually tried

Pinned [davoddino source](https://github.com/davoddino/minimax-h3-rocm-dual-gpu/tree/b1454c54410fe990640928183a04329944c75784)
at `b1454c54410fe990640928183a04329944c75784`; cloned a disposable ComfyUI at
`344b43989e8c56b5bb4a66cf028c834192ab59dd`, applied the frozen patch and verified
all **19 resulting SHA-256 hashes**. Bundle-integrity and SeedVR2 CPU self-checks pass
with Python optimization enabled. The first patch-verifier attempt hit EXDEV while
hardlinking a temporary Git clone; a same-filesystem temporary directory corrected
the verification setup without modifying the frozen source or patch.

On an idle, reserved GPU pair, a unique owned systemd scope ran the exact unmodified
`H3TPExecution` class extracted by AST, using real Torch and 50 empty Module owners
per rank. This executes its source prerequisite checks without importing the
monolithic Kilo48 backend or loading model weights. The constructor and the direct
loader both require bidirectional P2P. The constructor rejected the live peer
capability. This is a **prerequisite attempt**, not full H3 inference validation.

The probe used the retained Torch `2.15.0.dev20260827+rocm7.2` / HIP `7.2.53211`.
The author's Torch2.12/ROCm7.14 environment and native DSO were **not rebuilt or
reproduced**. No shards or weights were downloaded, no workflow was submitted,
and no candidate video, denoising timing or end-to-end speedup exists. A full build
would not remove the explicit peer requirement. This agrees with the host's
[existing topology diagnosis](../hardware/PCIE-P2P-2026-10-17.md); no boot, BIOS,
IOMMU, ACS, kernel, driver or hardware change was made.

## Comparison with the saved one-card result

| Arm | Full server request s | Sampler span s | Evidence |
|---|---:|---:|---|
| Saved one-card DiT, October28 | 210.098 | 28.324 | One timed completed generation after a 196.228 s excluded warmup |
| Davoddino two-card DiT | not measured | not measured | Rejected at bidirectional-P2P admission; zero generations |

The saved control uses FL2VA INT8 ConvRot,608×352,39frames,24fps,20steps,seed42,
res_multistep/simple. Its DiT runs on GPU0 while GPU1 handles encoder/VAEs.
It is one-card denoising with component placement. There is no matched candidate
timing and no speedup ratio. No control generation was repeated after the candidate
prerequisite failed. [Original record](H3-POST-UPGRADE-2026-10-28.md) retains its
hardware, policy and sample-count attribution. LLM prefill/TTFT/token decode/context
metrics do not apply to this diffusion prerequisite check.

## Memory and task continuity

Linux exposed 30.56GiB RAM. During admission, minimum available RAM was 22.10GiB;
minimum free VRAM was 23.93/23.96GiB. The child scope verified a host-sized RAM cap
and **`memory.swap.max=max`**. Current **loading-swap-v3**, with no optional write
budget configured, observed swap without rate-based termination. Loading/parked
swap, reads, rates and PSI alone cannot stop work. No swap I/O, owned worker swap
or owned dedicated-VRAM spill was observed in this short probe; it does not qualify
sustained-inference memory behavior because inference never began.

The 3GiB physical-RAM floor,2GiB free-VRAM/four-sample protection,hard1.5GiB VRAM
floor, zero dedicated-VRAM spill and thermal recording remained. The Kaihui8GiB
activation reserve is not part of this candidate. GPU hotspot peaks were 36/35°C,
CPU package peak62°C; reported SMU flags remain sampled telemetry, not measured
thermal throttling. No thermal or memory performance conclusion follows from
idle admission checks. [Current swap policy](../hardware/SWAP-TASK-CONTINUITY-2026-10-28.md).

## Earlier linked lcz.me posts, rechecked in the browser

- [2582/50 and later replies](https://lcz.me/topic/2582/50): Bunsei's native Radiance
  H3 work remains a gfx12/RDNA4 path. Later replies lead to fcys's separate RDNA3 work.
- [2594](https://lcz.me/topic/2594), [J I's direct reply](https://lcz.me/post/28082):
  firsthand dual-XTX ComfyUI SP2 success at480p/8–10s; roughly1.8× is recalled,
  without a pinned implementation or saved matched timing log. This is separate
  from native Radiance and from the davoddino design.
- [1532](https://lcz.me/topic/1532): SGLang gfx1100 text-model kernels.
- [2626](https://lcz.me/topic/2626): Strata0.1.45/96GB/IQ3_S text prefill and layer split.
- [2550/16](https://lcz.me/topic/2550/16): Strata text-model single/dual-card tuning
  caveats. These three are not H3 kernel implementations; no LLM settings changed.

### New RDNA3 lead missed by the earlier search

[fcys, topic2643](https://lcz.me/topic/2643), followed from topic2582's later
replies, reports an independent **ComfyUI INT8/RCCL TP2** implementation on two
**W7900 gfx1100 48GB cards**. The author explicitly says this is not Radiance and
that XTX applicability is inferred, not tested. At832×480/124frames/8steps/seed145,
the reported SDPA per-step time is18.6→8.3s and end-to-end201.3→134.1s; per-card
sampling VRAM drops from23.5GiB to12.9/13.2GiB. CK attention reports12.8→7.7s/step
and128s TP2 end-to-end. These are external claims, not local results or matched
comparators for our39-frame20-step task. The two rank outputs reportedly match
each other, but differ from single-card output (reported PSNR25.5dB).

The post describes shared activation scales and FP32 accumulation for row-parallel
INT8 reductions. **No source repository is linked in the nine replies reviewed**;
the last reply asks for GitHub. It is a useful implementation lead, not presently
a reproducible local checkout. No message was posted to the forum. Attention
kernel suggestions in the replies likewise require a separate H3 port and validation.

## Cleanup and next step

The owned probe exited naturally; its scope is inactive, no KFD compute client
remains, GPU-LOCK was released, server lock was closed and production configuration
fingerprints match. No production runtime, workflow, precision, model, engine pin,
default or paused schedule changed. No full H3 build or inference job is active.

An unchanged davoddino run needs a validated bidirectional P2P host. On this host,
the next engineering step is an explicit host-staged transport with numerical and
lifecycle qualification, or an inspectable fcys INT8/RCCL implementation. Do not
bypass the peer check or assume its event/copy semantics work without P2P. The
one-card versus davoddino performance comparison remains **unavailable**.

[Numeric record](../hardware/results/h3-davoddino-2026-10-28.json).
