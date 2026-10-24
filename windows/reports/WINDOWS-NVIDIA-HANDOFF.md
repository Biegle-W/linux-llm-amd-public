# Windows NVIDIA handoff — 23 October 2026

Windows is independent: RTX 3060 12 GB / i5-13600KF /16 GB DDR5 at 6000 MT/s, NVIDIA 610.88, llama.cpp b11630 CUDA 13.4 (`6868a52cb`). Linux remains its separate i9/64-GB/dual-7900-XTX HIP build; do not apply its policies or edit its runtime files here.

Current default: **Ornith 1.5 35B-A3B (IQ2_S) | 32K | GPU + RAM**, API ID `Ornith-1.5-35B-A3B-IQ2_S`, weights in project `models/`. Source registry retains fit on / GPU layers auto / fit-target2816 / no-host true. Q8 KV, FA on, one slot, batch512/ubatch128, thinking off, no speculation. This is not full GPU: normal buffers were 7,840.74 MiB GPU /2,643.67 MiB host. Fresh minimums:4 GiB RAM available /16 GiB commit headroom /9,728 MiB actual free VRAM. Never kill unrelated apps to satisfy these checks.

Selected decode samples: **48.24 /44.29 t/s**; chat, streaming, tool round trip and **8,080-token input retrieval** pass at32K allocation. Normal API streaming leaves1,571MiB whole-card VRAM /1.19GiB available RAM; sampled generation dipped to1,336MiB VRAM. Larger memory targets are not guaranteed real reserves. Early Ornith62–67t/s and Empero60–64t/s results used less desktop headroom; do not label them current default speed. Low-bit trials do not prove general quality superiority.

September Empero Qwen3.8 35B-A3B Distill IQ2_M remains in project `models/`, outside the active catalog. The retired Qwen3.5 9B GGUF was deleted at the user's request on October 23, freeing 5.56 GiB; do not assume its old path exists. Empero is a community Qwen3.8-teacher distillation into Qwen3.6's MoE architecture, not an official small Qwen3.8 release. It passed functional checks but had tight memory margins. Ornith and Empero weights were preserved. Strata stays disabled.

Visible `Start Local LLM.cmd` owns the API at `http://127.0.0.1:10000/v1`; real key remains private in data/credentials, client route LLAMA_CPP_API_KEY. Saved DSH default/catalog updated; Desktop GUI/SDK unverified because executable unavailable. Tailscale forwards only10000; IPv4/MagicDNS host self-checks pass, remote peer untested. LAN was not changed. Actual addresses stay in ignored state.

README is the sole root instruction file. Keep private/public GitHub current with sanitized Windows exports; preserve Linux and all dated historical evidence. Warn near70% of session context using current usage when available. Do not create root AGENTS.md. Stop the owned backend before test_models.py; its low-RAM guard only stops its own test worker. Thermal coverage is short generation GPU samples plus snapshots, not whole-run/CPU peaks.

See [current methods and limits](WINDOWS-MOE-MODELS-20261023.md). No Shared D: drive is attached; this handoff does not overwrite Linux's.

## Later October 23 candidate tests

LFM2.5 24B-A2B and official Qwen3.8 27B, both UD-IQ3_XXS, are verified in project `models/`. Separate8K profiles passed all five checks at~6K input; native total generation78.24/85.04t/s LFM (reasoning only at128-token cap),4.97/5.59t/s Qwen (thinking off). LFM's short visible marker arrived1.828s versus Qwen0.922s. Mixed GPU/RAM buffers:7426/1315MiB LFM,7140/2873MiB Qwen. See [current trial evidence](WINDOWS-LFM-QWEN-TESTS-20261023.md); no model-quality ranking is established.

Ornith's default/catalog and production limits are unchanged. Perplexity, the Quest client and Quest service were temporarily paused with explicit approval and restored; user app state is private. Production restart failed memory admission, so the owned backend is stopped at this snapshot. Do not silently lower its limits. No Linux runtime/profile or network settings were changed.

## Directory consolidation — later October 23

All four inference GGUFs are in project `models/`; source paths are project-relative. Candidate profiles are in `config/test-profiles-lfm-qwen-20261023.json`. Regenerate catalogs after moving the project. Retired Strata source is in `retired/20261023/`; inactive runtimes are in ignored `archive/retired-windows-20261023/runtimes/`. Reports and prior benchmarks remain preserved; no inference rerun. See [cleanup record](WINDOWS-CLEANUP-20261023.md).
