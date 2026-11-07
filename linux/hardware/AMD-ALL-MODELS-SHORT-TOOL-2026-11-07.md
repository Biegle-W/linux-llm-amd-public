# All-models short tool-call benchmark — November 7, 2026

Owner request: "if it works, don't fix it. document the working solution, and test all downloaded models and show benchmark for short toll call in harness". Layout: [AMD working setup](AMD-WORKING-SETUP-2026-11-07.md) (PowerColor ROCm 0 at `0b:00.0`, Sapphire ROCm 1 at `13:00.0`, both behind the switch; Sapphire in its high idle state). Guarded campaign 49, boot `d81d1623`, patched kernel `7.0.14-42-vmpt1`. [Structured result](results/AMD-ALL-MODELS-SHORT-TOOL-2026-11-07.json).

**All 14 enabled routes passed** one normal short DSH read-tool round trip (tool call, then answer from the tool result) under the guarded stage harness, after four fresh same-boot peer checks (capability, local, direct/IPC integrity, RCCL P2P/IPC). Every guard passed with owned cgroups empty, no remaining KFD clients, no kernel faults and no watchdog fault. No amdgpu kernel errors; AER 0/0/0 on both GPUs. A monitor was connected to the Sapphire (recorded, not headless).

| Route | Engine | Load s | Tool prompt tokens | Tool TTFT s | Prefill tok/s | Decode tok/s | Tool step s | Answer step s | Max owned swap |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `empero-qwen3.8-35b-a3b` | llama.cpp | 46.7 | 7,082 | 2.46 | 2,874 | 174.5 | 2.92 | 0.33 | 0 |
| `flint-40b-a2.5b` | llama.cpp | 50.7 | 6,502 | 1.31 | 4,980 | 64.8 | 4.1 | 1.68 | 0 |
| `ornith-1.5-122b` | llama.cpp | 151.9 | 7,073 | 10.87 | 651 | 11.3 | 18.5 | 4.19 | 9.4 MiB |
| `qwen3.8-27b-vllm` | vLLM TP2 | 89.5 | 7,074 | 4.11 | 1,723 | 153.7 | 4.61 | 0.4 | 0 |
| `qwen3.8-27b-sglang-dflash2` | SGLang TP2 | 34.4 | 7,359 | 4.23 | 1,741 | 218.6 | 4.59 | 0.44 | 0 |
| `nemotron-3.5-bolt-vllm` | vLLM | 224.4 | 7,668 | 3.67 | 2,092 | 29.6 | 6.41 | 1.59 | 0 |
| `sage-a1.5` | vLLM | 113.0 | 7,049 | 1.24 | 5,698 | 136.5 | 1.76 | 0.38 | 0 |
| `qwen3.8-flash-next-iq3_xxs` | Strata | 107.5 | 6,847 | 9.21 | 744 | 66.5 | 10.37 | 8.78 | 0 |
| `qwen3.8-flash-next-unsloth-iq1_m` | Strata | 59.0 | 6,855 | 9.43 | 727 | 70.1 | 10.55 | 9.21 | 0 |
| `glm-5.3-flash-maya` | Maya | 64.2 | 6,600 | 188.92 | 35 | 2.1 | 214.68 | 34.3 | 0 |
| `deepseek-v4.1-flash-1017-maya-coder-iq2-xxs` | Maya | 317.8 | 6,980 | 92.42 | 76 | 17.3 | 98.59 | 3.47 | 0 |
| `deepseek-v4.1-flash-1017-strata-coder-iq2-xxs` | Strata | 687.8 | 6,980 | 34.23 | 204 | 5.6 | 53.46 | 6.25 | 0 |
| `deepseek-v4.1-flash-1017-strata-unsloth-q1` | Strata | 62.2 | 6,968 | 87.06 | 80 | 3.3 | 118.78 | 15.87 | 0 |
| `deepseek-v4.1-flash-1017-maya-unsloth-q1` | Maya | 50.2 | 6,968 | 180.57 | 39 | 1.2 | 267.73 | 18.21 | 635.0 MiB |

Columns: *Tool* = first request (about 7K prompt tokens with 25 tool definitions; the model emits the read-tool call, 71–107 tokens). *Prefill tok/s* = prompt tokens / time to first token. *Decode tok/s* = output tokens / (step time − TTFT), short sample. *Answer step* = second request with the tool result (about 7.2K tokens, mostly a cached prefix; 14–20 output tokens). Load includes model start-up and, for qualified native routes, the backing-file content checks.

Notes:

- Speed classes: Empero, Qwen 27B (vLLM/SGLang), Sage and Flint answer the whole tool round trip in under 5 s; Flash Next (Strata) in about 20 s; Ornith 122B in about 23 s; DeepSeek and GLM (Maya/Strata with CPU/RAM expert stores) take 1–5 minutes on a cold first request.
- Ornith peaked at 9.4 MiB and Maya DeepSeek Unsloth Q1 at 635 MiB of owned swap; both within the existing swap policy, which passed.
- These are single short functional checks, not sustained or full-context qualification.

## Setup changes needed in this layout (all committed)

1. Device order `ROCR_VISIBLE_DEVICES=0,1` in `hardware/rocm-env.sh` and the two Strata Qwen profiles, keeping PowerColor as ROCm 0.
2. `qualified-strata-qwen-profiles.json`: the IQ1_M profile fingerprint refreshed for that device-order-only change (verified: the old order reproduces the old fingerprint exactly), and 69 file identities refreshed for `st_dev` only. The new PCIe numbering renumbered both NVMe drives; 67 files were re-hashed against their recorded sha256 and 2 large GGUF shards matched exact size and nanosecond mtime.
3. Campaign tooling (outside the repo): PCI roles, expected peer logical map and the fault-check hold owner updated for this layout.

## Stops during the campaign (none were GPU faults)

| Stop | Cause | Resolution |
|---|---|---|
| Peer runner, three times before any model | Campaign preparation: missing preflight copy, hard-coded old logical map, a leftover log, and an RCCL script left out of the archive | Fixed tooling; peers then passed twice |
| Route 9 (Flash Next IQ1_M), twice | Registry refused the device-order fingerprint, then the `st_dev` identities | Items 1–2 above; passed in 59 s |
| Route 12 (Strata DeepSeek Coder) | `Qualified native backing content changed` after about 9 minutes of hashing ~170 GB on `sharedNVME1` (`nvme1n1`, chipset root port `00:1a.0`, not behind the switch) | All six files were re-hashed afterwards and matched; both registries agree; no NVMe, exFAT, I/O or machine-check errors; non-ECC RAM. One fresh attempt passed (687.8 s load). A one-time host-side read or memory integrity miss; consider a memory test if it recurs. |

Each stopped attempt's files are archived next to its stage (`*.attempt*`, `*.part*`). Routes 1–8 ran in part 1, 9–11 in part 2 and 12–14 in part 3.

## Hold

The guard latched `GPU-LOCK` at the route 9 registry refusal, and the campaign kept it in place. **The owner released it on November 7 at 03:56** ("Stop the hold since it's fixed"); the hold file is archived untracked as `hardware/generated/GPU-LOCK.released-20261107T035653.private.json`. A request through the model hub then auto-started Empero and answered correctly in 49 s including load, with no amdgpu errors. The hub and nightly update are no longer blocked.
