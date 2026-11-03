# RCCL explicit P2P-control audit — November 3, 2026

**Confirmed source-order defect; isolated candidate passes static, host-transport and reduced initialization checks. Not installed or production-profile qualified, and not established as a remedy for the held SGLang failure.** Existing production libraries, model pins and guards remain unchanged. The production SGLang route stays held; only the explicitly scoped reduced target initialization below has run.

The pinned build recipe for the retained no-hostcall RCCL 2.27.7 identifies source commit **bf3ebf549fec376521b7d35f09a67f67071c96d3**. In that exact source's `ncclTopoCheckP2p`, the function obtains the explicit user P2P level first, then assigns the Intel default `PATH_PXB` afterward. Thus the platform-default assignment can overwrite the level obtained from `NCCL_P2P_DISABLE=1` or an explicit P2P-level setting.

This source finding matches the observed isolated collective controls: logs acknowledged the disable flag but still selected P2P/IPC, including with the explicit level variable removed. It explains why a configuration flag cannot be used as proof of host transport here. The source-order defect is independently established; equivalence of every source line to the released binary has not been rebuilt and verified yet. It is not proof that this defect caused the SGLang interruption.

## Offline candidate

The minimal source change applies user overrides **after** the platform defaults. No platform default changes when the user supplies no override. The patch applies to the exact pinned source with zero fuzz and passes the source-order validation. This source-level check is separate from the bounded host-transport result below.

An isolated gfx1100-only build uses the same no-hostcall recipe's NDEBUG requirement on device compilation, the existing ROCm 7.2.3 SDK and an official matching HIPIFY helper. It is bounded to three build jobs, a 24 GiB memory maximum and 400% CPU quota, with reduced scheduling priority. Dependencies and generated artifacts stay outside the installed runtime. No source/binary selection has changed in a launcher.

Static verification now passes: the candidate’s extracted gfx1100 device images contain zero hidden hostcall buffers, and all 37 exports required by the installed PyTorch and SGLang wrapper are present. The same audit passes on the retained library as a control. The prior instruction to require `ncclCommDump` was overly broad: it is absent from the retained library and is not required by these installed consumers. Installed library/configuration and AMD-SMI compatibility files retain their recorded fingerprints.

The raw candidate links the real ROCm-SMI library, unlike the retained library’s `librsmi_stub.so.1` dependency. A separate isolated copy now uses the retained SMI shim, which supplies all nine required SMI exports. Its extracted device images are unchanged by that dependency adjustment, and it passes the same static audit. At the offline-build checkpoint neither candidate had been loaded. The later owner-authorized bounded check below exercised the isolated shim-compatible copy in the retained SGLang Python environment.

The owner-authorized bounded communicator check below verifies the actual selected host channel and tensor correctness with P2P disabled. Flag parsing or a successful process exit is insufficient. Candidate P2P-on behavior needs its own matched bounded check.

Only after a reliable fallback is demonstrated should a controlled SGLang initialization comparison be considered: change one factor at a time, retain the prior profile and original failures, use a small isolated admission rather than restoring all production settings, and unload each owned attempt. Stop at the first new GPU/bus fault; do not replay the failed full DFlash2 setup as an automatic retry. The prepared MES workaround remains separate and is not installed by this work.

Sources: [exact RCCL paths.cc](https://github.com/ROCm/rccl/blob/bf3ebf549fec376521b7d35f09a67f67071c96d3/src/graph/paths.cc), [pinned no-hostcall build recipe](https://github.com/cadamcat/dual-radeon-vllm/blob/23c2beb2e200353fda84afa216c2cea2f7c579e9/build/build-rccl-nohostcall.sh). [Curated audit state](results/rccl-p2p-control-audit-2026-11-03.json).

Exact source correction: [pinned-source patch](patches/rccl-p2p-user-override-bf3ebf5.patch).

## Completed offline build

All 258 build steps completed. The source archive comparison identifies only the P2P precedence correction and the CMake NDEBUG definition used by the retained no-hostcall recipe. Isolated shim-compatible candidate SHA-256: `45847d2f61a504746867a1beef08be1041999682b00a7abf19cdc07b11f1d118`. These static checks establish build completion and the inspected properties; they do not demonstrate host-channel selection, collective correctness, or a SGLang crash remedy. At that offline-build checkpoint no candidate installation, kernel/firmware replacement, GPU communicator, or model retry had been performed. The SGLang fault hold, RAM/weight holds, runtime pins and updater pause remain.

## Authorized P2P-disabled communicator result

The isolated shim-compatible candidate passed a guarded two-rank check in **8.47 seconds** using the retained SGLang Python environment. Before GPU initialization, the parent and both rank processes verified that the mapped RCCL was the isolated candidate and no real ROCm-SMI library was mapped. Production launchers and the installed library were unchanged.

With `NCCL_P2P_DISABLE=1`, P2P level unset and Simple protocol, **both channel directions selected `SHM/direct/direct`**; no channel selected P2P/IPC. This is logged shared-memory transport evidence, beyond acknowledgement of the disable flag. FP32 and BF16 all-reduce and rank-distinct all-gather passed at 1, 4,096 and 1,048,576 elements on both ranks: 12 rank cases, each checking both collectives.

The guard sampled zero owned swap/spill, a minimum of about 51.98 GiB available host RAM and 22.71/23.30 GiB free VRAM. No new GPU/bus/OOM fault appeared through final cleanup. Both communicators were destroyed; owned processes and the scope exited, KFD clients were absent, and the owned GPU reservation was released. The existing AMD-SMI warning (error 32) remained; device count was two and independent sysfs guard telemetry was valid. This does not claim that AMD-SMI was repaired.

This establishes a working disabled-P2P shared-memory path for the tested candidate and small collective workload. It does not qualify candidate P2P-on behavior, CUDA graphs, full SGLang initialization, model inference, or the original crash remedy. SGLang stays fault-held; RAM/weight holds, pins, guards and updater pause remain. No candidate was installed and no model retry ran. Any further GPU workload requires its own authorized scope.

[Curated communicator result](results/rccl-candidate-host-2026-11-03.json).

## Guarded reduced SGLang initialization

The owner authorized one isolated initialization using the candidate and P2P disabled, keeping production unchanged. It reached readiness in **64.74 seconds**, then the owned server and all ranks were unloaded. Both `/health` and `/server_info` returned HTTP 200 after the ready marker. Health generation was disabled; no generation request was sent.

This was a deliberately reduced **target-only TP2 / 4,096-token** test: GPTQ weights and BF16 compute/KV, memory fraction 0.65, Mamba cache limit eight, no DFlash draft, both graph backends disabled, and server warmup skipped. Actual KV capacity was 4,096 tokens. The 32 GiB transient memory limit and ten-minute deadline supplemented the retained owned-worker loading/swap guard, RAM/VRAM/spill checks, thermal limits and new-kernel-fault stop. Generated kernel caches stayed in the isolated workspace. Production profiles, launchers, selected library, holds and updater state were unchanged.

Target weights loaded in 45.83 seconds (8.68 GB per rank as logged), and Mamba/KV cache initialization completed. Both rank channel logs acknowledged the disable flag and selected `SHM/direct/direct` in both directions; no P2P channel appeared. The guard verified candidate mappings in owned processes. There were 249 guard samples, zero owned swap/spill, about 49.00 GiB minimum available host RAM and 13.51/14.10 GiB minimum free VRAM. Sampled sensor maxima were 48/33°C. No new GPU/bus/OOM fault appeared through final cleanup. The owned cgroup was empty, all observed owned processes exited, KFD clients were absent, the reservation was released and the isolated server port closed.

A **nonfatal `post-warmup freeze_gc` callback warning** reported connection refused before readiness. The retained source catches that request exception and logs it; the ready marker and both read-only endpoint checks subsequently succeeded. The AMD-SMI warning 32 seen in the earlier communicator check was not seen in this initialization log; no AMD-SMI repair is claimed. Independent sysfs guard telemetry remained valid. No startup code was changed to suppress or fix warnings.

This establishes reduced target initialization and clean unload for this candidate. It does not reproduce the failed full DFlash setup, exercise generation or graphs, qualify the production profile, or establish that RCCL caused or cured the original bus loss. Production SGLang stays fault-held and the candidate remains uninstalled. Further workload changes need an explicitly scoped follow-up.

[Curated initialization result](results/sglang-candidate-init-2026-11-03.json).
