# AMD working setup and recovery runbook — November 7, 2026

[Investigation and test log](SAPPHIRE-POST-CRASH-LINK-TRAINING-2026-11-06.md). This page records the hardware and software layout that passed every test on November 7, how to check it, and what to do if a GPU crash happens again. Owner rule: "if it works, don't fix it". Keep this layout unless a new test says otherwise.

## Layout

| Item | Setting |
|---|---|
| Switch | Broadcom PEX88096 Gen4 switch on its own PSU, synced with the PC; switch PSU on first at power-up |
| PowerColor RX 7900 XTX (`148c:2422`) | switch branch `02:04.0`, port `08:00.0`, endpoint `0b:00.0`, Gen4 x8 |
| Sapphire RX 7900 XTX (`1da2:471e`) | switch branch `02:08.0`, port `10:00.0`, endpoint `13:00.0`, Gen4 x8 |
| Monitor | DisplayPort on the Sapphire |
| ROCm device order | `ROCR_VISIBLE_DEVICES=0,1`: ROCm 0 = PowerColor (rank 0, embeddings), ROCm 1 = Sapphire (rank 1) |
| BIOS | Native ASPM disabled; AER/DPC OS-controlled |
| Kernel | `7.0.14-42-vmpt1`, ACS `0x0011` on the six switch bridges, identity IOMMU |
| Driver P2P | `amdgpu pcie_p2p=Y`; KFD exposes a direct peer link between the two GPUs |

The device-order pin was `1,0` for the earlier layout, in which the PowerColor was `13:00.0`. With the cards in the positions above, `0,1` keeps the PowerColor as ROCm 0, the role every qualified dual-card route uses.

The Sapphire comes up in its high idle-power state (about 50–90 W reported, no heat) in this layout. It passed every test in that state.

## Where each setting lives

| Setting | File |
|---|---|
| ACS override on the six switch bridges | `/etc/default/grub.d/zz-local-llm-amd-p2p.cfg` (kernel `pci=config_acs=...`); `iommu=pt` and `amdgpu.ppfeaturemask=0xfff7ffff` are also on the command line |
| Default kernel `7.0.14-42-vmpt1` (stock kernel stays installed as a manual fallback) | `/etc/default/grub.d/zzz-vmpt-trial.cfg` |
| ROCm SDK 7.2.3, device order `0,1`, `NCCL_P2P_DISABLE=0`, `HSA_ENABLE_SDMA=0`, isolated RCCL 2.27.7 (`llm-tools/rccl-nohostcall`) | `hardware/rocm-env.sh` |
| llama.cpp peer copies (only for qualified IDs: Empero, Flint, Ornith) | `dsh/llama-runtime.json` `p2p_models` |
| Strata/Maya qualified profiles (config fingerprint and backing identity, including `st_dev`) | `dsh/qualified-strata-qwen-profiles.json`, `dsh/qualified-native-profiles.json` |
| ComfyUI production mode (H3 two-card TP over P2P) | `graphics/start-comfyui` (default `COMFY_MODE=tp2`), `graphics/h3-tp2/`, `graphics/runtime-versions.json` (`h3_tp2_production`), [report](../graphics/H3-TP2-PRODUCTION-2026-11-07.md) |
| Hub (`127.0.0.1:30100`, 10-minute idle unload) | user unit `local-llm-hub.service` |
| Daily engine updater (03:00) | user timer `llm-daily-update.timer` |
| GPU fault hold | `hardware/generated/GPU-LOCK` (absent = no hold; released holds are archived as `GPU-LOCK.released-*.private.json`) |

## Health check after any boot

Run these before loading models. All must match.

```bash
uname -r                                                  # 7.0.14-42-vmpt1
for p in 08:00.0 10:00.0; do d=/sys/bus/pci/devices/0000:$p; echo "$p $(cat $d/current_link_speed) x$(cat $d/current_link_width)"; done
                                                          # both "16.0 GT/s PCIe x8" (switch port to card; the
                                                          # endpoints 0b/13 read x16 at the card's internal bridge)
cat /sys/bus/pci/devices/0000:{0b,13}:00.0/aer_dev_fatal | grep TOTAL   # TOTAL_ERR_FATAL 0 on both
cat /sys/module/amdgpu/parameters/pcie_p2p                # Y
ls /sys/class/kfd/kfd/topology/nodes/{1,2}/p2p_links      # each GPU node lists peer link "0"
journalctl -k -b | grep -i -E "amdgpu.*(error|fault|timeout|reset)"   # empty
ls ~/Desktop/local-llm/hardware/generated/GPU-LOCK        # "No such file" = no hold
```

Full path for reference: PowerColor `00:01.0 → 01:00.0 → 02:04.0 → 07:00.0 → 08:00.0 → card 0b:00.0`; Sapphire `00:01.0 → 01:00.0 → 02:08.0 → 0f:00.0 → 10:00.0 → card 13:00.0`. The uplink and both branches run at Gen4 x16.

The full peer qualification (capability, local, integrity over HIP IPC in both directions, two-rank RCCL all-reduce and all-gather over P2P/IPC) is the campaign peer runner `hardware/generated/all-models-2026-11-07-49/peers/run-once.private.py`. It is untracked; it runs once per directory and refuses to repeat a run. Copy the directory to a new dated name to run it again.

## If a GPU crash happens again

1. **Stop and hold.** Do not retry the workload. Stop the hub and ComfyUI. Create `hardware/generated/GPU-LOCK` with owner, boot ID, purpose and last failed stage, in the same format as the archived `GPU-LOCK.released-20261107T035653.private.json`. Every guarded launcher (`start-comfyui`, the campaign runners, the daily updater) refuses to start while it exists.
2. **Capture before rebooting.** Save `journalctl -k -b`, and `lspci -vv` for both endpoints, ports `08:00.0`/`10:00.0` and branches `02:04.0`/`02:08.0`. Record the workload, the engine, which card (bus `0b` or `13`), the monitor port and the idle state of each card. Earlier failures were all the Sapphire losing PCIe/SMU access, in both switch branches.
3. **Full power cycle.** Power off, turn off both PSUs, then power on with the switch PSU first. Check that both cards train at Gen4 x8; a card missing or at x2 means another full power cycle, not a software fix.
4. **Requalify in the order that worked on November 7**, stopping at the first failure:
   1. Sapphire alone (one model, about 30 minutes sustained).
   2. Both cards running independent models at once (10 synchronized ~16K prefills).
   3. Empero layer split with P2P off, then with P2P on (10 rounds each).
   4. 27B vLLM TP2 over RCCL (10 rounds).
   5. The guarded all-models short tool-call campaign ([November 7 results](AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.md)).
   6. ComfyUI: the production H3, FLUX and Qwen-Image workflows (`graphics/run-workflow.py`).
5. **Release the hold** only after the owner reviews the results. Move `GPU-LOCK` to `GPU-LOCK.released-<UTC>.private.json`.

## Fallbacks (in order of least change)

| Problem | Fallback |
|---|---|
| ComfyUI H3 P2P mode misbehaves | `COMFY_MODE=staged graphics/start-comfyui`: the previous single-process server, unchanged |
| A ComfyUI H3 cancel or peer loss | Built in: both ranks agree on a cancel at the next step; an RCCL timeout (300 s) aborts the rank and `tp2_pair.py` restarts the pair, at most 3 times in 10 minutes |
| Suspect P2P in general | RCCL 2.27.7 ignores `NCCL_P2P_DISABLE=1` and `NCCL_P2P_LEVEL=LOC` once KFD reports a peer link (tested November 7). To really disable peer access, use the boot-time tool `sudo python3 hardware/amd_p2p_disable.py plan`, then `install`, then reboot. `verify` checks it and `rollback` removes it. It only stages kernel parameters (`amdgpu.pcie_p2p=0 amdgpu.use_xgmi_p2p=0`) and never touches live GPUs |
| A card is unreliable | Single-card settings measured November 6–7 ([log](SAPPHIRE-POST-CRASH-LINK-TRAINING-2026-11-06.md)): vLLM 27B TP1 (fp8 KV, 128K), SGLang 27B TP1 (no DFlash2), Strata Flash Next on one card (`--prefill auto`), Empero on one card |
| Kernel suspected | Stock kernel is installed; choose it from the GRUB menu (the default is set in `zzz-vmpt-trial.cfg`) |

## Tests passed in this layout (boot `d81d1623`)

| Test | Result |
|---|---|
| Both cards, independent models (Empero on Sapphire, 27B vLLM on PowerColor), 10 synchronized ~16K prefills + 15 min sustained | Pass; 628 W combined peak |
| Empero layer split across both, P2P off, 10 rounds | Pass; decode 98–106 tok/s |
| Empero layer split across both, P2P on, 10 rounds | Pass; decode 93–105 tok/s |
| 27B vLLM TP2 over RCCL (P2P on), 10 rounds | Pass; 80–87 tok/s |
| All 14 enabled LLM routes, guarded short tool call | [All pass](AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.md) |
| H3 TP2 over RCCL P2P (fcys tp2-comfy) | [Pass, bit-identical output](../graphics/DIFFUSION-P2P-RADIANCE-2026-11-07.md) |
| Production ComfyUI in P2P mode: H3 projected-8B and native-32B, FLUX t2i/i2i, Qwen-Image, queued job, cancel | [Pass](../graphics/H3-TP2-PRODUCTION-2026-11-07.md) |

Earlier in the same night the Sapphire alone passed on the motherboard (2.5 h, all engines) and alone behind the switch in port `10:00.0` (44 min sustained).

**P2P against the earlier motherboard x8/x8 bifurcation (October 29, no peer access, RCCL over host shared memory):**
- **27B vLLM TP2:** prefill 1,472 → 1,723 tok/s and decode 142.5 → 153.7 tok/s.
- **27B SGLang TP2:** prefill 1,474 → 1,741 tok/s and decode 193.3 → 218.6 tok/s.
- **H3 per step:** 1.33 → 1.05 s.

The test methods and engine builds also differed between those dates, so these are direction, not a strict A/B.

## Model status (November 7)

**Qualified and enabled, all on two cards:**

| Group | Routes | How the two cards are used |
|---|---|---|
| vLLM / SGLang | `qwen3.8-27b-vllm`, `qwen3.8-27b-sglang-dflash2` | TP2 over RCCL P2P/IPC |
| vLLM | `nemotron-3.5-bolt-vllm`, `sage-a1.5` | two-card vLLM |
| llama.cpp | `empero-qwen3.8-35b-a3b`, `flint-40b-a2.5b`, `ornith-1.5-122b` | layer split, peer copies on |
| Strata | `qwen3.8-flash-next-iq3_xxs`, `qwen3.8-flash-next-unsloth-iq1_m`, `deepseek-v4.1-flash-1017-strata-coder-iq2-xxs`, `deepseek-v4.1-flash-1017-strata-unsloth-q1` | layer groups with NVMe expert streaming |
| Maya | `glm-5.3-flash-maya`, `deepseek-v4.1-flash-1017-maya-coder-iq2-xxs`, `deepseek-v4.1-flash-1017-maya-unsloth-q1` | layer groups with NVMe expert streaming |
| ComfyUI | H3 INT8 with projected-8B encoder (TP2 P2P); H3 with native-32B encoder, FLUX 3 Klein t2i/i2i, Qwen-Image 2.1 BF16 | staged component placement |

**Held or retired (no automatic retry; each needs a new owner decision):**

| Candidate | State |
|---|---|
| Nemotron 3.5 Super | IQ3 weights removed November 2. INT4 vLLM attempts (EP2, PLE host-file-gather) stopped on the loading heartbeat guard; no weights on disk now |
| Maya DeepSeek UD-IQ1_S with the 36 GB store | Loading failure followed by AMDGPU/CPU lockups (November 5). The same model without the store is the enabled `deepseek-v4.1-flash-1017-maya-unsloth-q1` route |
| RDNA3 full-stack fork2314 (vLLM) | Qwen startup warm-up failed (`_seq_lens_cpu`); final |
| H3 image-to-video through P2P | Not tested: there is no saved I2V workflow |

**Downloaded but not used by any route** (kept on purpose, nothing to qualify):
- Graphics experimental assets:
  - `h3-hoststage-20261028`: 20 GB of host-staged rank shards, superseded by the November 7 TP2 halves.
  - `h3-encoder-formats-20261028`: 16 GB, a W4A8 32B encoder trial.
  - `h3-8b-comparison-20261031`: 10 GB. This is the projected-8B encoder that production uses.
  - `h3-tp2-halves-20261107`: 20 GB, the TP2 halves that production uses.
- `Unsloth/hub/models--unsloth--MiniMax-H3-FP8`: an incomplete 1.9 GB Hugging Face download (`.incomplete` blob); nothing uses it.
- `LLM-ARCHIVE/NVIDIA/2026-10-18`: an 11 GB NVIDIA-host recovery archive, not a model.

No GPU hold is active. The owner released the fault hold on November 7 at 03:56. The daily updater is enabled (next run 03:00), and the hub serves all routes.

## Not used

The Sapphire in branch `02:04.0` (its position during the November 6 15:31 bus loss) has not been retested. The cause of that failure was not identified; see the investigation log.
