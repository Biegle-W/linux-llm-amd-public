# All eleven active profiles — October 23, 2026

All eleven active profiles were benchmarked with their production launchers and settings after
the cooling changes of the same day. **All eleven passed**: arithmetic smoke, three code and three prose
timed runs, three fresh ~8K marker prompts with every marker retrieved and no cache reuse, both GPUs
allocated, and zero VRAM spill.

**Method (unchanged shared method, `benchmark-current-amd.py`):** one backend at a time through
`dsh/launch-backend.py` while `GPU-LOCK` was held; the cold model load was excluded (an untimed
4-token warm-up, then the helper's own warm-ups). 256-output code/prose prompts, seed 42,
temperature 0.6 / top-p 0.95, thinking off; medians of three. Fresh prefill: three salted ~8,192-token
(Qwen tokenizer) marker prompts, greedy, 64-token cap. Decode = `(completion_tokens − 1) / (stream_end − first_output)`.
TTFT runs from request submission to the first streamed token.

**Build and system:** unchanged production stacks (llama.cpp 4c3c5810, SGLang f84475cc, vLLM
0.32.1rc1.dev36, Strata 9ae93f7b/0.1.46.1, Maya 25deec5/1.1.24; ROCm 7.2.3). i9-13900KS, 64 GB
(61.51 GiB visible), two RX 7900 XTX on CPU PCIe4 x8/x8, kernel 7.0.0-38. New since the earlier runs:
`amdgpu.ppfeaturemask=0xfff7ffff` (OverDrive, needed for GPU fan control), BIOS OS-controlled
ASPM (policy `default`, L1 enabled on both GPU links, links still 16 GT/s), and CoolerControl 5.1.1
max-cooling curves on every fan.

## Results

| Model · engine | Context | Code / prose decode t/s | Fresh PP t/s | Fresh TTFT s | Actual fresh input | vs previous: code / prose / PP |
|---|---:|---:|---:|---:|---:|---|
| Empero Qwen3.8-35B-A3B IQ4_XS · llama.cpp | 262,144 | 119.89 / 72.61 | 2,988.5 | 2.748 | 8,185–8,188 | -1.3% / -1.2% / +1.5% |
| Sage-A1.5 Q4_K_M · llama.cpp MTP3 | 65,536 | 80.42 / 64.93 | 2,839.2 | 2.892 | 8,186–8,188 | -0.5% / -0.4% / +1.6% |
| Nemotron Super IQ3_XXS · llama.cpp | 32,768 | 15.63 / 17.14 | 433.4 | 18.300 | 7,924–7,925 | -0.1% / -0.5% / +0.5% |
| Ornith-1.5-122B Q4_K_M · llama.cpp | 32,768 | 11.43 / 13.32 | 717.2 | 11.425 | 8,187–8,189 | -0.1% / -0.1% / +0.3% |
| Qwen3.8-27B INT4 · SGLang TP2 DFlash2 | 163,840 | 206.18 / 71.08 | 1,468.8ᵉ | 5.585 | 8,187–8,189 | -2.6% / -2.1% / +1.3% |
| Qwen3.8-27B INT4 · vLLM TP2 MTP3 | 163,840 | 134.82 / 71.73 | 1,511.0ᵉ | 5.435 | 8,186–8,191 | +0.7% / +1.2% / +2.4% |
| Nemotron Bolt W4A16 · vLLM TP2 | 262,144 | 38.12 / 38.08 | 2,950.4ᵉ | 2.699 | 7,923–7,927 | +2.1% / +2.3% / -0.3% |
| Qwen3.8-Flash-Next IQ3_XXS · Strata | 262,144 | 78.05 / 47.63 | 916.0 | 8.974 | 8,185–8,187 | +0.9% / -10.6% / +0.8% |
| GLM-5.3-Flash Maya-S · Maya | 32,768 | 18.64 / 16.28 | 539.1 | 13.289 | 6,310–6,312 | -5.5% / +3.8% / +0.7% |
| DeepSeek-V4.1 Maya-XS + DSpark · Maya | 32,768 | 27.60 / 13.67 | 448.1 | 14.074 | 6,299–6,300 | -11.8% / -11.0% / +0.6% |
| DeepSeek-V4.1 Maya-S · Maya | 32,768 | 6.73 / 6.78 | 301.2 | 20.919 | 6,296–6,300 | +4.8% / +0.0% / +0.7% |

ᵉ engine-phase prefill (SGLang/vLLM); others native. Previous values: llama.cpp from the October22 batch sweep; SGLang/vLLM Qwen and Strata from the October21 shared baseline; Bolt from its October21 production benchmark; GLM and DeepSeek-S from the October23 Maya1.1.24 update; DeepSeek-XS from the October23 isolated XS+DSpark test.

Nine of the eleven profiles are within ±5.5% of their previous published rates on every metric. Two outliers:

- **Strata prose −10.6%** (47.63 vs 53.25 t/s), consistent across all three trials (47.45–47.66). Code and
  prefill are unchanged. The generated prose differs from every earlier recorded run (content hash), so
  the MTP draft acceptance differs and this is not an isolated causal measurement. Not attributed to ASPM or cooling.
- **DeepSeek Maya-XS code/prose −11.8% / −11.0%** against the isolated XS+DSpark test, which used a
  separate test harness rather than the production launcher. Prefill matches (448.1 vs 445.5). This is the
  first production-launcher XS rate.

GLM and both DeepSeek profiles show one slow first fresh prompt (26–34 s) before two normal ones;
the medians exclude it by construction.

## Cooling and memory

| Profile | Peak hotspot °C GPU1 / GPU2 | Peak GPU fan RPM GPU1 / GPU2 | Peak GPU W | Peak CPU °C | Min available RAM GiB | Peak VRAM GiB | Owned swap |
|---|---:|---:|---:|---:|---:|---:|---:|
| `empero-qwen3.8-35b-a3b` | 52 / 40 | 2,231 / 1,681 | 238 / 157 | 55 | 44.49 | 14.3 / 17.7 | 0 |
| `sage-a1.5` | 62 / 42 | 2,446 / 1,738 | 337 / 209 | 66 | 46.22 | 14.1 / 13.9 | 0 |
| `nemotron-3.5-super-iq3` | 68 / 51 | 2,954 / 1,866 | 328 / 289 | 80 | 37.92 | 20.4 / 19.3 | 0 |
| `ornith-1.5-122b` | 70 / 45 | 3,209 / 1,927 | 371 / 242 | 67 | 15.39 | 19.9 / 18.9 | 0 |
| `qwen3.8-27b-sglang-dflash2` | 78 / 68 | 3,622 / 3,020 | 311 / 310 | 84 | 48.42 | 19.5 / 19.5 | 0 |
| `qwen3.8-27b-vllm` | 82 / 72 | 3,628 / 3,125 | 467 / 508 | 97 | 50.26 | 16.7 / 16.7 | 0 |
| `nemotron-3.5-bolt-vllm` | 78 / 69 | 3,549 / 3,023 | 309 / 303 | 100 | 47.96 | 22.8 / 22.8 | 0 |
| `qwen3.8-flash-next-iq3_xxs` | 78 / 73 | 3,615 / 3,102 | 326 / 343 | 100 | 37.76 | 18.6 / 17.8 | 0 |
| `glm-5.3-flash-maya` | 79 / 68 | 3,620 / 3,084 | 356 / 365 | 98 | 12.45 | 16.4 / 16.4 | 25.8 MiB |
| `deepseek-v4.1-flash-1017-maya` | 73 / 67 | 3,383 / 2,856 | 308 / 313 | 99 | 49.15 | 16.4 / 16.5 | 0 |
| `deepseek-v4.1-flash-1017-maya-s` | 72 / 62 | 3,293 / 2,734 | 379 / 307 | 100 | 49.41 | 16.4 / 16.4 | 0 |

Peaks are 1 s ThermalRecorder samples per profile run, not guaranteed transient maxima. A separate
5 s whole-run log (`fans.csv`, 18:05–18:46) peaked at GPU hotspot **84 / 73 °C**, GPU fans **3,608 / 3,121 RPM**,
GPU power 517 / 518 W, CPU package 100 °C; CPU cooler fans 2,123 / 1,593 RPM, case fans 1,578–1,957 RPM.
The earlier Maya-XS test had recorded a GPU hotspot peak of 99 °C before these fan changes; that is a
different workload and not a matched comparison. SMU thermal-limit flags were still reported on some
samples; flags are not a measured speed loss.

**GLM owned swap:** the memory monitor recorded 27,045,888 bytes (25.8 MiB) of swap across GLM's
inference process tree while available RAM dipped to 12.45 GiB (GLM pins 40 GiB). The record does not
separate the worker from its router/launcher processes. The other ten profiles recorded zero.
Investigate before treating GLM's no-swap rule as met for this run.

## Fan control set up for this run

- `amdgpu.ppfeaturemask=0xfff7ffff` on the kernel command line exposes `gpu_od/fan_ctrl` on both cards.
- CoolerControl (`/etc/coolercontrol/config.toml`, source `hardware/fan-control/coolercontrol-config.toml`,
  applied with `hardware/fan-control/apply-coolercontrol.sh`; previous config kept as
  `config.toml.before-max-cooling`): CPU cooler fans 1–2 follow CPU package temperature (35% at 30 °C → 100% at 65 °C);
  every case header follows the maximum of CPU and both GPU hotspots (100% at 65 °C CPU or 70 °C hotspot);
  each GPU's own fans follow its hotspot (40% at 30 °C → 100% at 75 °C).
- At idle, GPU1's firmware still parks its fans (0 RPM) despite the curve; under load both cards follow it
  and reach their 3,600 / 3,200 RPM limits.

## Evidence

[Numeric record](results/all-models-2026-10-23.json): every timed trial, actual counts, per-request and
per-profile thermal summaries, memory, previous reference values and the whole-run fan peaks.
Raw logs and the 5 s fan CSV remain private under `hardware/generated/all-models-2026-10-23/`.
