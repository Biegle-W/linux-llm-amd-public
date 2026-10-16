# Retired setup removal — October 16, 2026

The user confirmed this specific cleanup before deletion.

Removed installations: `hyperqwen/upstream`, `sglang/.venv`, `vllm/.venv`,
`llama.cpp/build` (CUDA), `sglang/flash-next-src`, `sglang/flash-next-extra`.
Removed obsolete CUDA wrappers and direct starters, HyperQwen preparation/test
scripts and patches, the three obsolete root llama.cpp CUDA wrappers,
`dsh/hyperqwen-profiles.json`, desktop launcher and
`llm-hyperqwen` in both the repository and the installed SSH PATH.

The 35 repository removal targets reported 29,350,879,232 allocated bytes when
measured individually. This sum can double-count hard-linked dependencies and
is not a measured increase in filesystem free space. The earlier combined
inventory estimated roughly 22 GiB. Detailed manifest is private/ignored in
`hardware/generated/retired-setups-2026-10-16/removed.json`.

No process was using these installations. No active environment had symlinks
into them. No inference job was stopped and no weights were removed in this
cleanup. All five active GGUFs, AutoRound GPTQ and the SGLang DFlash2 drafter
remain. Preserve the `models/HyperQwen/` drafter despite that directory name.

Preserved: AMD llama.cpp Vulkan and HIP builds, both ROCm environments and their
private SDK/toolchain, DSH, Turnstone, gateway, Strata Q3 and HIP preparation.
Strata remains disabled pending stable restored RAM and model validation.
Benchmark Markdown, JSON evidence and research history remain; the public
`linux-nvidia/` and `windows/` reference snapshots are unchanged.

Catalog registration removes the retired HyperQwen provider and resets any stale
local default to an active model. The gateway advertises eight current profiles.
vLLM's router only accepts vLLM mode; its default launcher and SGLang's default
launcher point to ROCm. A stale HyperQwen launch fails before any handover.
Exact legacy shutdown signatures remain to recognize owned workers safely.

Validation: 29 private regression tests and 15 public tests passed. Both retained
ROCm environments imported PyTorch and detected gfx1100 / RX 7900 XTX 24 GB.
All eight enabled profiles retain their required model/launcher paths. Python
syntax and Git whitespace checks passed. No model load or speed benchmark rerun.
