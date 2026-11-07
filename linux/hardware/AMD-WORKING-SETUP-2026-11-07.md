# AMD working setup — November 7, 2026

[Investigation and test log](SAPPHIRE-POST-CRASH-LINK-TRAINING-2026-11-06.md). This page records the hardware and software layout that passed every test on November 7. Keep it unchanged unless a new test says otherwise.

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

The device-order pin was `1,0` for the earlier layout, in which the PowerColor was `13:00.0`. With the cards in the positions above, `0,1` keeps the PowerColor as ROCm 0, the role every qualified dual-card route uses. It is set in `hardware/rocm-env.sh` and in the two Strata Qwen profiles.

The Sapphire comes up in its high idle-power state (about 50–90 W reported, no heat) in this layout. It passed every test in that state.

## Tests passed in this layout (boot `d81d1623`)

| Test | Result |
|---|---|
| Both cards, independent models (Empero on Sapphire, 27B vLLM on PowerColor), 10 synchronized ~16K prefills + 15 min sustained | Pass; 628 W combined peak |
| Empero layer split across both, P2P off, 10 rounds | Pass |
| Empero layer split across both, P2P on, 10 rounds | Pass |
| 27B vLLM TP2 over RCCL (P2P on), 10 rounds | Pass; 80–87 tok/s |

Earlier in the same night the Sapphire alone passed on the motherboard (2.5 h, all engines) and alone behind the switch in port `10:00.0` (44 min sustained).

## All models in this layout

[All 14 enabled routes passed the guarded short tool-call check](AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.md), with per-route load, prefill and decode times.

## Hold

The GPU fault hold was released by the owner on November 7 at 03:56; the hub serves all routes in this layout.

## Not used

The Sapphire in branch `02:04.0` (its position during the November 6 15:31 bus loss) has not been retested. The cause of that failure was not identified; see the investigation log.
