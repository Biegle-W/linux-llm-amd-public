# Supplied lcz.me links: local applicability — October 27, 2026

Source review only: no engine, profile, sampling setting, workflow, model or
maintenance schedule was changed. External reports are not local benchmarks.

## SGLang: the linked fork is already installed

[flyer666, topic 1532](https://lcz.me/topic/1532) describes dual RX 7900 XTX,
TP2, native W4A16, MTP3 and Radix caching. The
[primary gfx1100 branch](https://github.com/StevenChenSE/sglang/tree/f84475ccf593087df3d1da13c9e675eadee12352)
and the installed SGLang source have the same reviewed HEAD,
`f84475ccf593087df3d1da13c9e675eadee12352`. Existing local KV-cache,
verifier and Qwen/MTP repairs remain present; they must survive any update.
This is not an uninstalled optimization discovered by the new link.

The selected local Qwen27B profile uses TP2, W4A16, DFlash2, 163,840 context,
BF16 KV and bounded 2,048-token prefill. It deliberately disables custom
all-reduce on this topology. The post's MTP3 setting differs from the selected
DFlash2 profile. Cached agent-turn TTFT and the post's table marked as
LLM-generated are not fresh, matched local throughput measurements.

## Strata: useful pipeline and prefill leads, different capacity budget

[懒人烘培, topic 2626](https://lcz.me/topic/2626), October 27, reports
7500F, two 7900 XTX cards, **96 GB RAM**, Strata 0.1.45 and **IQ3_S**.
Its fixed 262,144 context tests use fresh prompts, two runs per length and 256
output tokens. Its configuration uses 16,384 prefill, split 24, INT8 KV with
20,480 resident tokens, 2,048 MiB VRAM reserve, pipeline windows 2, speculative
depth 3 / minimum probability 0.5, and a HIP 7.14 hipBLASLt **100401** table.
The reported controlled prefill gain of about 6.4% combines a larger chunk and
its matching tuning table; it is not evidence for changing only one flag.

The retained local profile is **IQ3_XXS**, source
`7dd5cf18e68c639a8773e096c5c79f971ea2a9f5`, prefill 2,048, split 26,
32,768 resident KV, speculative depth 3 / minimum probability 0.7 and the
validated HIP 7.2.3 hipBLASLt **100202** table. It retains CPU expert residency
with a 13.5 GiB budget, larger VRAM reserves and a **60 GiB host admission**.
The current 14.83 GiB host does not satisfy that admission. The prior
[local tuning report](STRATA-TUNING-2026-10-24.md) records the failed larger
prefill admission; the forum's 96 GB recipe does not override that result.

In [topic 2550, the author's reply](https://lcz.me/post/27547), October 24,
presence penalty 1.5→0, frequency penalty 0 and repetition penalty 1 enabled
the intended two-window decode pipeline. Local
[server code](https://github.com/Niko1221/Strata/blob/7dd5cf18e68c639a8773e096c5c79f971ea2a9f5/serve/server.py)
adds history for non-neutral penalties; the
[engine](https://github.com/Niko1221/Strata/blob/7dd5cf18e68c639a8773e096c5c79f971ea2a9f5/src/program/generate.cpp)
falls back to serial decode when that history is active. RDNA3 also requires
explicit `--pipeline-windows 2`; its automatic selection is gfx12-only.
The local profile does not currently request that flag. Existing
`STRATA_SPLIT_OVERLAP=1` is a separate mechanism. Current client penalty values
were not established by this review. Disabling penalties changes sampling
behavior and needs a matched quality/speed comparison before selection.

## H3: firsthand dual-XTX SP2, plus a separate R9700 native fork

[J I's October 26 reply](https://lcz.me/post/28082) reports two 7900 XTX
cards running H3 SP2 in ComfyUI at 480p for 8–10 seconds. Its approximate speed
recollection is not a recorded benchmark; 576p reliability was mixed. The
exact plugin/workflow is unspecified. This corrects the earlier review's
missing firsthand XTX evidence.

[Bunsei's topic 2582](https://lcz.me/topic/2582), including the
[later discussion supplied by the user](https://lcz.me/topic/2582/50), covers
a separate Radiance TP2 implementation on **R9700/gfx1201**, not an established
RDNA3 port. See the [H3 implementation review](../graphics/H3-MULTIGPU-RESEARCH-2026-10-27.md)
for pinned code, the Kaihui AMD Comfy SP loader, exact timing boundaries,
model-format differences, transport and host-RAM requirements.
