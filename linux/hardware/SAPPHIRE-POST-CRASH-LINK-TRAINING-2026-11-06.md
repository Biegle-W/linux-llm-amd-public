# Sapphire post-crash link training — November 6, 2026

**After the November 5 23:01 headless failure, the Sapphire switch port failed to train its PCIe link normally at power-on in two consecutive boots: the card was absent from enumeration in one boot and trained at x2 instead of x8 in the next.** Link training completes before amdgpu, ROCm, RCCL/P2P or any model process runs, so these two boots implicate the Sapphire-to-switch link or its power rather than driver or workload software. The following boot trained at the normal x8. This is read-only journal evidence; no GPU work, reboot, hold release or runtime change was made. [Structured assessment](results/SAPPHIRE-POST-CRASH-LINK-TRAINING-2026-11-06.json).

## Post-crash boot sequence

Times are America/Toronto (EST). All boots used patched `7.0.14-42-vmpt1` with unchanged boot arguments.

| Boot | Start | Sapphire path (port `08:00.0`) | PowerColor path (port `10:00.0`) | How the boot ended |
|---|---|---|---|---|
| Failure boot | Nov 5 21:41 | x8 | x8 | SGLang Qwen DFlash2 startup: `0b:00.0` lost from bus at 23:01:30 ([campaign](AMD-HEADLESS-KNOWN-PASSED-MODELS-2026-11-05.md)) |
| Recovery boot | Nov 5 23:29 | x8 | x8 | Interactive terminal `sudo reboot` at Nov 6 01:18:02 |
| Short boot | Nov 6 01:20:29 | x8 | x8 | Journal stops at 01:20:35 during early userspace with no shutdown sequence: hard reset or power loss |
| Degraded boot A | 01:21:50 | **Absent**: no endpoint under switch port `02:04.0` (bus range `07-0c` instead of `07-0e`); one KFD device | x8 (renumbered under `0e:00.0`) | Desktop-session reboot at 01:23:23 |
| Degraded boot B | 01:28:00 | **x2** at `08:00.0` (31.5 Gb/s available); amdgpu and SMU still initialized | x8 | Interactive terminal `sudo systemctl poweroff` at 01:32:15 |
| Current boot | 12:59:55 | x8 | x8 | Running; both cards enumerated, all exposed AER counters zero at inspection |

The NVMe address changes in degraded boot A (`1c/1d` to `1a/1b`) follow from the two missing bus numbers, not from a storage change. No AER, DPC or hotplug error was logged in any of these boots; the persistent `00:1d.0 retraining failed` message is an empty chipset root port and appears in every boot.

## Prior boots for comparison

Every earlier saved boot that logged switch-port widths (November 3 02:34 through November 6 01:20, 24 boots) trained both GPU paths at x8 and enumerated both cards. Degraded boots A and B are the only absent or narrowed GPU link in the retained journal.

| Bus-loss boot | Lost device | Board identity |
|---|---|---|
| Nov 3 04:25 | `13:00.0` | Not individually reidentified (see [P2P audit](SAPPHIRE-SWITCH-P2P-EVIDENCE-AUDIT-2026-11-06.md)) |
| Nov 3 15:38 | `13:00.0` | Not individually reidentified |
| Nov 4 14:57 | `13:00.0` | Sapphire, before the recorded slot swap ([kernel comparison](AMD-CRASH-KERNEL-COMPARISON-2026-11-05.md)) |
| Nov 5 23:01 | `0b:00.0` | Sapphire, after the slot swap |

The PowerColor path has no recorded bus loss or degraded training.

## Identity limits

Both boards report the same VBIOS part `113-3E4710U-O54`, so the journal alone cannot name the board in a given boot. The current boot shows subsystem `1da2:471e` (Sapphire) at `0b:00.0` and `148c:2422` (PowerColor) at `13:00.0`, matching the placement recorded before the failure. Degraded boots A and B are attributed to Sapphire on the assumption that no board was moved between the failure boot and the current boot; the unexplained hard stop at 01:20:35 means physical intervention during that window cannot be excluded from logs.

## What this changes

Read with the prior topology history:

- [No-switch validation](NO-SWITCH-VALIDATION-2026-11-03.md): with the Broadcom switch removed, both boards on motherboard paths and driver P2P off, eight LLM paths and six graphics workflows passed with no bus loss. The owner also reports Sapphire stable directly on the motherboard.
- Every bus loss in the retained journal occurred with the switch installed, including the November 3 15:38 failure with driver P2P disabled ([P2P-off retry](STRATA-P2P-OFF-LOAD-RETRY-FAILURE-2026-11-03.md)). Owner single-PSU rewiring and dedicated cables preceded the November 4 recurrence.
- PowerColor behind the same switch has no bus loss or degraded training, and the owner's NVIDIA pair previously worked on this switch with P2P.
- Failures followed Sapphire across both switch branches, so a single switch port is unlikely.

The fault is therefore specific to **Sapphire behind the switch**: neither the card alone nor the switch alone reproduces it. Power-on training failure on Sapphire's switch path adds evidence that the problem exists at the link/electrical level and is not only a P2P, driver-queue or workload effect. It does not distinguish Sapphire-to-switch link margin from slot power delivered through the switch board or a Sapphire-specific power-transition interaction.

Read-only checks on November 6 exclude two software mechanisms for the current boot: both cards hold a single 16 GT/s x8 PCIe DPM level (no runtime link-speed switching), and both are at stock clocks, voltage offset 0 mV and the default 303 W cap. BACO runtime power management is configured, but neither card had suspended at inspection; its activity before earlier failures is not recorded.

## Candidate Sapphire-behind-switch mechanisms

1. Individual-unit link margin between this Sapphire and the switch at Gen4 (leading candidate). Both boards report the same VBIOS part, which suggests similar designs, so a unit-level PCIe margin difference fits better than a design-level one; not confirmed.
2. Load-start power transients on the Sapphire. Its switch-side power arrangement matches PowerColor's, so this would need to be unit-specific.
3. A Sapphire-specific power-state or reset interaction with the switch, now with ASPM and root-port clock gating disabled in firmware.

## Sapphire idle-power state (Prometheus history, November 6)

Owner report: the setup worked through the early part of November 5 and began crashing in the afternoon. Kernel, BIOS 1836, microcode `0x133`, GPU VBIOS/SMU firmware (`0x004e8300`), kernel command line, packages, CoolerControl profiles and motherboard voltage rails are identical between the working boot (Nov 4 17:02 to Nov 5 16:50) and the crashing boots. One measured difference was found:

| Boot period (EST) | Sapphire idle power, median | PowerColor idle | Outcome |
|---|---|---|---|
| Nov 3 01:00–17:00, switch, Sapphire at `13:00.0` | 50–57 W | 4–12 W | Bus losses 04:25, 15:38 |
| Nov 4 13:00–17:01, switch, across the slot swap | 50–54 W (followed Sapphire `13:00.0` → `0b:00.0`) | 5–13 W | Bus loss 14:57 |
| **Nov 4 17:02 – Nov 5 16:50, switch** | **10–12 W** | 7–9 W | **~24 h of dual-GPU work, no bus loss** |
| Nov 5 16:53 onward, every boot, switch | 53–61 W | 4–14 W | Crashes 18:45, 23:01; degraded link training Nov 6 |

The step is exact: 10–13 W in every sample to 16:50, 53 W in the first sample after the 16:53 power-loss restart, retained through warm reboots, a full power-off and the BIOS change. In the high state the Sapphire is idle (0 % utilization, core clock 0, memory clock 96 MHz, `vddgfx` ≈ 0.05 V), fan PWM/RPM match the normal state, and edge temperature does not rise, so the extra ~45 W reported by the card is not dissipated as package heat. Behind the switch, every bus-loss boot was a high-state boot and the only long high-workload boot in the normal state had none.

State history: in the motherboard layout the Sapphire was `03:00.0` (recorded October 18). It idled at about 12 W until the October 29 18:07 EDT reboot series, then at 55–76 W on the motherboard (without bus loss) and behind the switch until November 4 17:01. The November 4 17:02 boot came up normal (10–12 W) and stayed normal for about 24 hours of switch work; the November 5 16:53 restart after the power loss came up high again. Every flip happened at a boot, never within one. No file in `/etc`, modprobe, udev, systemd or tmpfiles configuration changed at any flip, so the trigger is outside OS configuration. The high state is therefore a recurring Sapphire condition that was harmless directly on the motherboard; behind the switch, every bus loss occurred in it.

Owner-assisted reboot checks on November 6, all with no GPU work and `GPU-LOCK` retained:

| Boot | Type | Sapphire idle | PowerColor idle | Links / AER |
|---|---|---|---|---|
| 14:15 | After BIOS change | 43–57 W | 9 W | Gen4 x8 / 0 |
| 14:56 | Warm reboot | 44–53 W | 8–9 W | Gen4 x8 / 0 |
| 15:11 | Full power-off, both PSUs switched off about 10 minutes | 46–55 W | 11 W | Gen4 x8 / 0 |

Neither a warm reboot nor complete power removal restores the normal state.

**Practical gate:** before any GPU work, require the Sapphire to idle near the normal 10–13 W. A boot showing ~50 W should be treated as unqualified.

## Owner-requested known-good retest — November 6, 15:29–15:32

Owner request: "test know good models now". Campaign 48 reused campaign 47's pristine stage inputs and harness unchanged (all 20 managed inputs and 8 peer assets matched the November 5 pins), with the Sapphire in its high idle state (47–57 W at stage start) and a disabled monitor connected to PowerColor.

| Stage | Result |
|---|---|
| Read-only preflight (kernel, ACS 0x11 on six bridges, identity IOMMU, module hash, no faults, thermals, storage, memory) | Passed |
| Four fresh peers: capability, local, direct/IPC integrity, RCCL P2P/IPC | All passed |
| Route 1 `empero-qwen3.8-35b-a3b` | Loaded normally in 47.7 s (48.1 s on November 5); **Sapphire failed during the first prefill** |

Telemetry from the guarded stage (elapsed seconds from stage start, 15:31:08):

| Time | Sapphire | PowerColor |
|---|---|---|
| 46.7 s, prefill begins | 36 W, 23 % busy, 1339 MHz | 43 W, 29 % busy |
| 47.2 s | 86 W, 28 % busy, memory 1249 MHz | 72 W |
| 47.5–48.4 s | **0 % busy, core clock 0, memory stuck at 1249 MHz, 76–84 W** | returns to idle (waiting on Sapphire) |
| 51.5 s | no telemetry | 11 W, idle |

Kernel: `0b:00.0` device lost from bus at 15:31:58.396, SMU `TransferTableSmu2Dram` bus error, about 23,700 SMU hang messages, MES REMOVE_QUEUE and reset requests, CPU workqueue stalls and an NMI backtrace; the journal ends at 15:32:28 and the host froze (no SSH or ping) until a forced power-off. No AER/DPC report. The guard detected the fault and latched a new fault hold (`daily-update-fault-qualification`, boot `226ffa28`) before the freeze. Thirteen routes were not run. PowerColor stayed healthy throughout.

The Sapphire stopped executing about one second into the first heavy compute burst, then lost its PCIe link about three seconds later. The host freeze follows from the driver's recovery against a device that is no longer reachable.

## Motherboard idle check — November 6, 20:31 boot

Owner powered off, removed the switch path and booted with only the Sapphire, directly in the CPU x16 slot (`03:00.0`, root port `00:01.0`). No GPU work; `GPU-LOCK` retained; one HDMI monitor connected.

| Check | Value |
|---|---|
| Link | Gen4 x16, AER 0/0/0, no kernel errors |
| Idle power (15 samples, 2 s apart) | **61–67 W** — high state persists |
| Clocks | sclk 0 MHz, mclk 96 MHz (lowest level), busy 0 % |
| Heat and voltage | edge 26 °C, junction 31 °C, memory 24 °C, fan 0 rpm, VDDGFX 55 mV |

The high idle state is not caused by the switch: it survives removing the switch, the PowerColor and the switch PSU. The reported 61–67 W again produces no heat, which matches every earlier high-state boot. Whether the card fails under load here (it did not in the October 29 – November 3 motherboard period) is the owner's next test.

## Single-card Qwen3.8-27B on the motherboard — November 6, 20:51

Owner request: "test models that would run on one card, qwen 3.8 27B". Same boot as the motherboard idle check (Sapphire alone, Gen4 x16, high idle state 61–67 W). `GPU-LOCK` was left in place so the hub and updater stayed blocked; vLLM was started by hand from `~/Documents/Codex/2026-11-06/single-card-27b/` with the qualified 27B W4A16 weights and the qualified launcher flags except: TP=1, 32K context (was 160K), 2.5 GiB BF16 KV (was 6 GiB), memory fraction 0.95, no MTP, port 30091. Single-card configuration is not a qualified route.

A first start with a 2 GiB KV cache stopped at configuration (32K needs 2.15 GiB); no request was sent and the card was unaffected.

| Step | Result |
|---|---|
| Load (weights 17.25 GiB, cached graphs) | ready in 26 s |
| Short arithmetic | `391`, correct, 1.1 s |
| Tool call | `read_file {"path": "/etc/hostname"}`, correct, 1.0 s |
| Long prefill, 15,859 tokens | `3584`, correct, 15.4 s |
| Decode, 1,022 tokens | 25.4 s, 40.3 tok/s |

Telemetry (140 samples at 0.5 s, 105 busy): peak 326 W, 100 % busy, sclk to 2871 MHz, mclk 1249 MHz, junction 73 °C, memory 64 °C, fan to 968 rpm, VDDGFX to 1029 mV, VRAM 21.1 GiB. Device present in every sample; no amdgpu kernel warnings or errors; AER 0/0/0; KFD empty after shutdown; idle afterwards 67–71 W (still the high state).

Directly on the motherboard, in the high idle state, the Sapphire sustained about 70 s of full load, including a 15.9K-token prefill, the operation during which it was lost behind the switch. This is a short functional check, not sustained-stability evidence, and it uses vLLM TP=1 rather than the llama.cpp route that failed.

## Single-card Empero and long-context runs on the motherboard — November 6–7

Same boot (Sapphire alone in the CPU x16 slot, Gen4 x16, high idle state). `GPU-LOCK` retained throughout; every engine was started by hand from `~/Documents/Codex/2026-11-06/single-card-27b/` with per-run telemetry at 0.5 s. All single-card configurations below are unqualified owner-requested tests, not catalog routes.

**Empero (owner: "Yes, run Empero").** llama.cpp HIP, same pinned build and route flags (MTP draft, q8_0 KV, batch 512/512, threads 6, `load-mode dio`), minus the dual-card split and P2P; 32K context. Loaded in 52 s; short `391` correct; tool call correct; 15,859-token prefill correct in 4.5 s; 1,113 tokens decoded at 148.6 tok/s. Peak 307 W, junction 65 °C. This is the route that lost the Sapphire about one second into its first prefill behind the switch the same afternoon.

**Long full-context runs (owner: "run a long test with fully context with qwen 3.8 27b llm and sglang and flash next with strata, adjust setting that can be run on one card").** Each run: two near-full-context prompts with three hidden codes at 10/50/90 % depth, a follow-up turn on the first, and a ~2K-token decode.

| Engine and single-card settings | Context / prompt | Needles | Prefill | Follow-up | Decode | Load window, peaks |
|---|---|---|---|---|---|---|
| vLLM 27B W4A16, TP1, fp8 KV 4.4 GiB, util 0.97, no MTP | 131,072 / 122,218 | 2/2 correct | 96 tok/s (21 min each) | correct, 14 s (prefix reuse) | 39.4 tok/s | 46 min; 406 W, junction 93 °C, memory 82 °C, VRAM 23.97 GiB |
| SGLang 27B, TP1, fp8_e4m3 KV, mem 0.93, 4 mamba slots, **no DFlash2** | 131,072 / 122,218 | 2/2 correct | 64 tok/s (32 min each) | correct, 11.5 s (122,176 cached) | 34.7 tok/s | 66 min; 358 W, junction 88 °C, memory 78 °C |
| Strata Flash Next IQ3_XXS, `gpu` 0, no layer split, `--prefill auto`, int8 KV, 32K resident | 262,144 / 238,126 | 2/2 correct | 471–508 tok/s (8 min each) | correct, 7.4 min (prompt cache off) | 15.9 tok/s | 36 min; 358 W, junction 85 °C |

Setup findings:

- **27B in 24 GB.** Weights take 17.25 GiB; BF16 KV is 64 KiB/token (16 full-attention layers), so 160K needs about 10 GiB. fp8 KV fits 128K but runs through a software conversion on gfx1100 ([vLLM issue 56992](https://github.com/vllm-project/vllm/issues/56992)); long prefill is slow. BF16 KV would allow roughly 64K at higher speed (not measured here).
- **SGLang DFlash2 on one card.** The draft costs 1.48 GB of weights, 1.12 GB of intermediate SSM state for verifying 8 draft tokens, and its own KV; with it the pool held only 43,040 tokens. `--max-mamba-cache-size 2` fails (zero schedulable requests); 4 works. Running the draft on the CPU is not supported by SGLang or vLLM and would not free the verify state.
- **Strata on one card.** Only 16.76 GiB of experts fit in VRAM and the 75 GB model exceeds the page cache, so prefill is NVMe-bound (about 1.3 GB/s). The qualified `--prefill 256` read the prompt at about 34 tok/s (aborted); `--prefill auto` (8,192-token chunks, as in the [single-XTX lcz.me setup](https://lcz.me/topic/2059)) reached about 500 tok/s. Requests need `chat_template_kwargs.enable_thinking=false`, otherwise the model spends the reply budget thinking.

Across about 2.5 hours of mostly continuous full load: the device stayed present in every sample, no amdgpu kernel errors, AER 0/0/0, KFD empty after each run. Unrelated desktop processes (`gamemd-spawn.exe`, `explorer.exe`, `dotnet` under Wine) also used the card around 22:50–22:52 and exited with routine VM-statistics warnings. Idle after the runs: 86–91 W.

**What this changes.** In the high idle state, directly on the motherboard, the Sapphire sustains far heavier and longer load than the operations that lost it behind the switch, on the same driver, kernel, firmware and models. Behind the switch the failure is a GPU/SMU hang at the first load step followed about three seconds later by link loss, without prior AER. The open question is whether the switch path alone (slot power/ground through the switch board and its PSU, or the link) fails with this card, or whether it needs both cards (P2P traffic, simultaneous load steps). The owner-proposed next test is the Sapphire alone behind the switch, same port, with the same single-card checks.

## Sapphire alone behind the switch — November 7, 00:25 boot

Owner request: "should I test it on the switch alone?" — powered off (including the switch PSU), Sapphire alone on the switch, PowerColor removed. It enumerated at `11:00.0` under switch port `0e:00.0`, in the `02:08.0` branch normally used by PowerColor (the afternoon crash was in the `02:04.0` branch; earlier crashes occurred in both branches). Link Gen4 x8 at the switch port, Gen4 x16 inside the card, AER 0/0/0. Idle 51–56 W: **high state**. HDMI monitor connected. `GPU-LOCK` retained; same hand-started single-card engines and telemetry as the motherboard runs.

| Check | Result |
|---|---|
| Empero llama.cpp, 32K | loaded 48 s; short, tool, 15,859-token prefill (4.6 s) correct; 1,092 tokens at 145 tok/s; peak 314 W |
| 27B vLLM TP1, 32K | loaded 108 s; short, tool, prefill (14.6 s) correct; 40.2 tok/s; peak 317 W |
| 27B vLLM TP1, 128K fp8 KV, sustained | 2/2 needles at 122,218 tokens (95.7 tok/s, 21 min each), follow-up correct in 14 s, 1,576 tokens at 39.2 tok/s; 44 min; peak 399 W, junction 91 °C, memory 84 °C |

No amdgpu errors, AER 0/0/0 at the card and the switch port, device present in every sample.

**What this changes.** Alone behind the switch, in the high idle state, the Sapphire passed the Empero prefill that lost it about one second in on November 6 with both cards installed, and 44 minutes of sustained full load. Every recorded bus loss behind the switch had both cards installed and a dual-card workload. P2P is not sufficient as an explanation: the November 3 Strata dual-card crash had driver peer access disabled with HIP-negative proof (see the [P2P evidence audit](SAPPHIRE-SWITCH-P2P-EVIDENCE-AUDIT-2026-11-06.md)). The leading candidates are now two-card conditions behind the switch: simultaneous load steps on slot power through the switch board and its PSU, or inter-GPU traffic. Proposed discriminator: both cards behind the switch running two independent single-card models at the same moment (no inter-GPU traffic); a crash points to combined load, a pass points to P2P/multi-GPU traffic.

## Both cards behind the switch, independent simultaneous load — November 7, 01:30 boot

Owner request: "Yes, powering off" for the proposed two-card discriminator. PowerColor `0b:00.0` in the `02:04.0` branch (port `08:00.0`); Sapphire `13:00.0` in the `02:08.0` branch (port `10:00.0`), the port where it had just passed alone. Both Gen4 x8, AER 0/0/0. Idle: PowerColor 4 W, Sapphire 52–56 W (**high state**). Monitor on Sapphire DP. Driver `pcie_p2p=Y`, but each server was given only its own card (`ROCR_VISIBLE_DEVICES` 1 = Sapphire, 0 = PowerColor, verified by BDFID), so no inter-GPU access was possible. `GPU-LOCK` retained.

- Sapphire: Empero llama.cpp single-card (32K). PowerColor: 27B vLLM TP1 (32K).
- 10 synchronized rounds: a ~15.9K-token prefill fired on both at the same instant, then a 1K decode on both. All 20 prefills correct (Sapphire 4.6–4.8 s, PowerColor 14.7–14.8 s); all decodes completed (Sapphire 134–144 tok/s, PowerColor 40 tok/s).
- 15 minutes of independent back-to-back prefill+decode on both: Sapphire 76/76, PowerColor 23/23.
- Combined peak 628 W at one instant (Sapphire 326 W, PowerColor 302 W); both above 200 W together for about 2 minutes of the synchronized phase. Over 23.8 minutes: Sapphire peak 359 W, junction 80 °C; PowerColor peak 339 W, junction 78 °C. Both devices present in every sample; no amdgpu errors; AER 0/0/0 on both.

**What this changes.** Both cards behind the switch with simultaneous load steps, including the Sapphire in its high state running the Empero prefill that failed on November 6, did not reproduce the failure. Combined slot-power load on the switch is therefore not sufficient. Every recorded bus loss involved a single workload spanning both cards (llama.cpp layer split, vLLM/SGLang TP2, Strata layer split). That includes the November 3 Strata case with driver peer access disabled, where inter-GPU data was staged through host memory. The remaining discriminator is a cooperative dual-card run with P2P disabled versus enabled.

## Dual-card Empero layer split with P2P off — November 7, 01:59 (same boot)

Owner request: "Yes, P2P off first". Same layout as the independent-load test (PowerColor `0b:00.0` in `02:04.0`, Sapphire `13:00.0` in `02:08.0`, Sapphire in the high idle state). The qualified Empero hip-amd route (layer split 1:1, `token_embd` on ROCm0, 262,144 context, MTP draft, q8_0 KV, batch 512/512), with ROCm0 = PowerColor and ROCm1 = Sapphire as in the failing route, and **`GGML_CUDA_P2P` unset**. In the pinned llama.cpp source, peer access is enabled only by `GGML_CUDA_P2P`; the HIP build has `GGML_HIP_NO_VMM=ON` and `GGML_HIP_RCCL=OFF`, so no other path enables it. Driver `pcie_p2p` stayed `Y` (changing it needs root); this is process-level P2P off, and inter-card copies are staged through host memory.

| Step | Result |
|---|---|
| Load | 46 s |
| Short, tool | `391`, `read_file`, correct |
| 10 rounds of fresh 15,864-token prefill + 1K decode | 10/10 prefills correct (4.96–5.01 s), decodes 98–106 tok/s |

Peaks: Sapphire 214 W, 98 % busy, junction 61 °C; PowerColor 182 W, junction 50 °C. Both devices present in every sample; no amdgpu errors; AER 0/0/0 on both; KFD empty after shutdown. About three minutes of load: a short check, not sustained evidence.

**What this changes.** The same cooperative dual-card route that lost the Sapphire about one second into its first prefill on November 6 (with `GGML_CUDA_P2P=1`) ran ten heavy rounds with P2P off. Combined with the passes alone behind the switch and with independent simultaneous load, direct peer traffic through the switch is now the leading trigger. Two caveats keep it from being settled: the November 6 failure had the Sapphire in the other switch branch (`02:04.0`), and the November 3 Strata crash had driver-level P2P disabled. The confirming test is the same layout and route with `GGML_CUDA_P2P=1`.

## Dual-card Empero layer split with P2P on — November 7, 02:09 (same boot)

Owner request: "Yes, P2P on". Identical to the P2P-off run except `GGML_CUDA_P2P=1` (verified in the server's environment). KFD exposes a direct PCIe peer link between the two GPU nodes in both directions, so llama.cpp enabled peer access and inter-card copies went directly through the switch.

| Step | Result |
|---|---|
| Load | 46 s |
| Short, tool | correct |
| 10 rounds of fresh 15,864-token prefill + 1K decode | 10/10 prefills correct (4.96–5.02 s), decodes 93–105 tok/s |

Peaks: Sapphire 299 W, junction 61 °C; PowerColor 293 W, junction 54 °C. No amdgpu errors, AER 0/0/0 on both, KFD empty after shutdown. Speed matched P2P off because a layer split moves only small activations between cards.

**What this changes.** The route that failed on November 6 with P2P on did not fail in this boot and layout, with P2P on or off. P2P on its own is therefore not sufficient either. In this boot nothing reproduced the failure: Sapphire alone, independent simultaneous load (628 W), layer split with P2P off, and layer split with P2P on all passed, with the Sapphire in the high idle state throughout. Differences from the November 6 15:31 failure that remain untested:

1. Switch branch: on November 6 the Sapphire was in `02:04.0` (port `08:00.0`); tonight it was in `02:08.0` (port `10:00.0`). (Older crashes occurred in both branches.)
2. Sequence: the November 6 run started right after the four peer prerequisites (including RCCL P2P/IPC all-reduce and all-gather) in the same boot.
3. Display: a monitor was attached to PowerColor on November 6; tonight it is on Sapphire.
4. Heavy P2P traffic: layer split moves little data; the vLLM/SGLang TP2 failures move far more through RCCL.
5. Intermittency: the failure may need time or a particular boot condition not captured by the idle-state flag.

## vLLM 27B TP2 with RCCL P2P — November 7, 02:15 (same boot)

Owner request: "Yes, run TP2". The qualified `qwen3.8-27b-vllm` route as the router launches it (TP2, 163,840 context, MTP 3, BF16 KV 6 GiB, memory fraction 0.82, TRITON_ATTN, compiled graphs), RCCL 2.27.7 via PyNCCL with `NCCL_P2P_DISABLE=0` and `NCCL_PROTO=Simple`, rank 0 = PowerColor, rank 1 = Sapphire. Same layout and boot as the layer-split runs; Sapphire still in the high idle state.

| Step | Result |
|---|---|
| Load | 34 s (cached graphs), world size 2 confirmed |
| Short, tool | correct |
| 10 rounds of fresh 15,864-token prefill + 1K decode | 10/10 prefills correct (9.03–9.11 s), decodes 80–87 tok/s |

Both cards ran at 100 % busy and about 300 W during prefill. No amdgpu errors, AER 0/0/0 on both, KFD empty after shutdown.

**What this changes.** Heavy per-layer all-reduce traffic through the switch also did not reproduce the failure. In this boot and layout, every tested combination passed: one card, two independent cards, layer split with P2P off and on, and TP2 with RCCL. Remaining untested differences from the November 6 failure are the Sapphire's switch branch (`02:04.0` then, `02:08.0` now), the preceding RCCL peer checks in the guarded campaign, the monitor placement, and test duration. None of tonight's runs exceeded a few minutes of dual-card load.

## Switch power topology (owner report, November 6)

The PCIe switch board requires and uses its own dedicated PSU, switched on and off in sync with the PC; GPU auxiliary connectors and the rest of the system use the PC PSU. The owner reports this same power connection worked with the NVIDIA pair and previously with these AMD cards. Both switched GPUs receive power the same way, yet only Sapphire fails, so the split-supply arrangement is not by itself an explanation and is not a one-variable test target. It remains unexcluded only as part of a Sapphire-specific interaction.

## Next one-variable test

Set Sapphire's switch downstream port to a Gen3 target link speed from Linux (firmware speed settings affect only the CPU root port), retrain, confirm Gen3 x8 with zero AER, then repeat the unchanged SGLang Qwen DFlash2 startup three times. A pass at Gen3 where Gen4 failed indicates link margin; a failure at Gen3 moves the next comparison to a reduced Sapphire power cap. Both changes are reversible and require root; neither has been performed.

## BIOS ASPM change — boot of November 6, 14:15

The owner changed PCIe power-management settings in firmware between the 14:08:49 reboot and the 14:15:20 boot. Verified from this boot: the kernel now logs that ACPI FADT declares PCIe ASPM unsupported and uses the BIOS configuration, which has PEG, DMI and PCH ASPM disabled. This is the first retained boot with that message, so firmware Native ASPM is now disabled and Linux cannot enable link power states itself. `_OSC` still grants the OS PCIe hotplug, PME, AER, LTR and DPC control, so error reporting is retained. Bus numbering, endpoint addresses and subsystem identities are unchanged; both GPU paths trained at 16 GT/s x8 and all exposed AER counters were zero at inspection. The r8169 `can't disable ASPM` message is an expected side effect for the chipset NIC.

Also recommended: PCI Express Clock Gating disabled, SR-IOV disabled and the CPU root port forced to Gen4 at x16. Those firmware values are not observable from the OS and are not verified here. One clean boot at idle is not a link-stability or model qualification; the hold remains.

## Preserved state

Read-only journal and sysfs inspection, plus the owner-requested retest above; the BIOS change was made by the owner. The GPU fault hold, all 14 routes, guards, selected persistent kernel with stock fallback, prior failure records and paused schedules are unchanged. Apart from the owner-requested retest, no GPU trial, retry, hold release or runtime change occurred; the retest's new fault hold is retained.
