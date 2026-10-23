# Maya-XS + DSpark production rollout — October 23, 2026

**Promoted at the user's explicit request.** DeepSeek's existing model ID
`deepseek-v4.1-flash-1017-maya` now selects **Maya-XS IQ1_S + matching IQ2_XXS
`dspark-xs2` drafter**. GLM remains Maya-S v2/MTP; there are still ten models.
The DSH default remains Strata Q3. No model weights, chats or settings were deleted.

Source **25deec505b525212e05faa58697d9d2b7d17fdb3 / Maya1.1.24**, exact tested
HIP binary `4a3b77e997d88498f9fd140867af227553f9c651c4693c0a31b710620bdcd814`,
ROCm7.2.3 and both RX7900XTX cards are unchanged. DeepSeek remains32K/24CPUthreads,
CPU expert backing/GPU hot caching, `DS4_IQ_Q8K=0`, `DS4_STREAM=0` and
`--dspark on`. Both cards use layer groups; **this is not true TP2**.

## Saved performance, not a rerun

[Earlier same-day benchmark](MAYA-XS-DSPARK-2026-10-23.md): three-trial code/prose
medians **31.28 /15.36t/s**, native fresh prefill**445.5t/s**, fresh TTFT**14.156s**.
One1024-output HTML probe was**12.54t/s**. These retain their actual workload,
source, counts and temperature coverage; normal production integration below
is functional validation only and supplies **no new throughput measurements**.
XS is a smaller, lower-quality quant than S; the user authorized this tradeoff.
[Official pinned quant card](https://huggingface.co/peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF/blob/d1fc01009f21e26157acb6858c315d0365483b72/README.md).

## Production proof and guards

Actual existing Desktop entry → visible Ptyxis terminal → normal launcher,
original native browser UI and **GLM → XS → GLM → XS** selector sequence passed.
The final worker is intentionally left on XS, ready for use. JSON, synthetic tool
round-trip, authenticated streaming through the gateway's loopback/LAN/Tailscale
host-self routes and frontend mutation protection passed. These are not
remote-peer tests; no real internet tool was executed and vision remains unvalidated.
The prior native XS test passed31497-input retrieval and31529-input full-history
follow-up; that near-window benchmark was not repeated during promotion.

The loaded command/config/source/binary and pack descriptor/index/Engram
fingerprints match the tested selection. The IQ1_S admission change is confined
to XS with its matching enabled drafter and32K/24threads. Changed context,
threads or disabled drafter are rejected. MixedQ4_K/IQ4_XS remain blocked.
CPU regression coverage includes this boundary; no general format bypass exists.

Native8GiB reserve/card, actual startup>=6GiB/card, continuous3GiB/hard1.5GiB
VRAM floors, RAM admission60GiB physical/52GiB available,52G/no-swap worker scope,
telemetry and latched owned-worker-only shutdown remain unchanged. Zero owned
swap/spill and one native worker were observed. No unrelated apps, DSH, API gateway
or hub were stopped. Other engines and their profiles remain unchanged.
The captured worker scope reached its52GiB ceiling with280 `memory.events max`
notifications and zero OOM/OOM-kill events; max notifications are not OOM counts.

Normal-proof thermal coverage: **511 samples**, about1s interval,
GPU0/GPU1 peak junction **50.0 / 48.0°C**, CPU package peak **81.0°C**. Coverage includes
normal loads/switches/functional requests; the final production worker continues
running beyond this finite proof. This is not its lifetime peak. Full available
sensors/power/clocks/fans/SMU flag counts are retained; flags do not establish a
measured speed loss. [Numeric proof](results/maya-xs-production-2026-10-23.json).

## Storage, preparation and rollback

All weights/generated packs stay on the shared NVMe. XS uses three new GGUF files,
the matching drafter, existing vision pack, and the original S Engram shards5/6.
The [pinned active manifest](../maya/models.json) and
[XS checksum/reuse map](../maya/deepseek-xs-models.json) retain exact published
hashes. The two Engram tensor payloads were fully verified by virtual XS SHA
(official XS header plus entire S payload), not assumed whole-file identical.
No second161GB Engram copy was created. **Never delete S shards5/6: XS depends on them.**

The [old full checksum snapshot](../maya/deepseek-s-rollback-models.json) and S
weights/drafter remain inactive rollback assets. Exact prior configs/code/seed
and checksums are saved privately outside Git. No source/binary rollback is
needed because this rollout reuses the same deployed1.1.24 engine.

`maya/install.sh deepseek` now verifies the existing selected XS pack via
[verify-xs-pack.py](../maya/verify-xs-pack.py); it does not run stock setup that
would download XS-named Engram duplicates or overwrite Linux metadata. This
verifier checks sealed metadata and dependency presence, **not fresh full-weight
checksums**. A new machine must download/verify the pinned assets, build its own
pack metadata and pass local validation; sanitized configs are reference-only.
Windows must create separate Windows pack descriptors, preserving shared weights
and Linux metadata. API clients keep the same model ID and connection settings.

Use `llm-maya --model deepseek-v4.1-flash-1017-maya`, the existing Maya web model
selector, DSH's Maya provider, or the authenticated model hub/API. No new launcher,
exposed port or idle-unload policy was introduced. [Canonical handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md).
