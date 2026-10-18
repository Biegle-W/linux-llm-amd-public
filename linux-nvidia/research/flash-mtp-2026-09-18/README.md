# Historical NVIDIA Flash-MTP patch — September 18, 2026

Retained as text for future reference when the unused local source tree was
removed on October 18. This is not an active AMD backend or a new validation.

Original provenance: Unsloth llama.cpp release
[b11027-mix-3e83366](https://github.com/unslothai/llama.cpp/releases/tag/b11027-mix-3e83366).
The prior local experiment used its CUDA backend plugins and a rebuilt server/core.
The patch changes `hc_head_norm` from a flat hyper-connection dimension to
`{n_embd, hc}` with `TENSOR_ALLOW_RESHAPE`, keeping tensor values unchanged.
It addressed the recorded `[10240]` versus `[2560,4]` graph shape mismatch.
Preserved files: [patch](mtp-hc-head-shape.patch) and upstream [MIT license](LICENSE).

The historical RTX 4070 + RTX 3060 test used 14 target GPU layers, layer split
5:9, output projection and shared Q8 MTP head on CUDA0, two draft tokens, 4,096
context, batch 128, microbatch 64, Q4 main KV, default F16 draft KV and lazy mmap.
This is an old feasibility configuration, superseded by Strata and the AMD
migration; it must not be installed over current llama.cpp builds.

The full old source, original patch and reports remain in the private NVIDIA
recovery tar on Shared SATA. Setup records remain in Git; models and runtime
binaries are excluded. Consult the current handoff before attempting any restore.
