# Current owner RAM holds — October 29, 2026

**Four routes remain paused until the owner reports more RAM.** RAM detection alone does not resume them. The owner's later explicit SGLang retry superseded that route's earlier hold; Qwen27B/SGLang is now qualified and enabled with its original 160K DFlash2/graph settings and the ROCm multicast fix.

| Paused route | Model ID | Retained requirement |
|---|---|---|
| Ornith / llama.cpp | `ornith-1.5-122b` | 60 GiB OS-visible physical RAM |
| DeepSeek XS / Maya | `deepseek-v4.1-flash-1017-maya` | 60 GiB physical / 52 GiB available RAM; experimental 32 GB tiers unselected |
| DeepSeek XS / Strata | `deepseek-v4.1-flash-1017-strata-xs` | Same retained RAM requirement; experimental 32 GB tiers unselected |
| Qwen Flash Next / Strata | `qwen3.8-flash-next-iq3_xxs` | 25 GiB available RAM; fresh candidate/rollback load remains unverified |

Eight profiles are available: Empero, Super, Flint, Qwen27B/vLLM, Bolt/vLLM, Sage/vLLM, GLM/Maya and Qwen27B/SGLang. All four held IDs are absent from the hub and authenticated API and reject cached requests. Their weights/settings/pins remain retained. Resume them only after the owner's RAM notification and normal guarded qualification.

The 03:00 full-registry timer/recovery remains enabled. Strata Qwen and separate Strata DeepSeek skip upstream checks, builds and GPU qualification while all their profiles are disabled. Maya tests GLM; llama.cpp tests Empero/Super/Flint; vLLM retains the Bolt manual hold. SGLang is eligible again, with its current upstream revision unchanged. Other guards, holds and schedules remain.

The initial five-route pause and its 84 CPU checks remain historical; the subsequent SGLang investigation used 118 affected CPU checks per checkout, full isolated qualification and normal authenticated API checks. The raw requested/resident counter difference alone was inconclusive, but fresh explicit-counter samples established the unwanted allocation. [Resolved cause, source fix and verification](SGLANG-VRAM-GUARD-FIX-2026-10-29.md).

[Strata retry evidence](STRATA-RETRY-SAMPLER-2026-10-29.md): its restored source/build files are byte-verified, but a fresh restored-build load is still pending RAM admission and the owner resume condition. No automatic RAM-detection resume is enabled.
