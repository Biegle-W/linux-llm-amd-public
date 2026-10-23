# Both DeepSeek Maya quants deployed — October23,2026

The larger **Maya-S** remains intact on shared NVMe and is now a separate active
selection alongside XS and GLM. Existing XS ID **deepseek-v4.1-flash-1017-maya**
stays unchanged; new higher-quality-quant option **deepseek-v4.1-flash-1017-maya-s**
uses the retained S pack with **no DSpark**. These are two quantizations of the
same DeepSeek-V4.1-Flash-1017 architecture, not different parameter counts.
Maya now has three profiles; the complete catalog has eleven. Select them in the
Maya web sidebar, DSH's Local Maya provider, or authenticated OpenAI chat API.

Both DeepSeek profiles retain32K/24CPUthreads, both7900XTX cards, source
**25deec505b525212e05faa58697d9d2b7d17fdb3 /1.1.24**, ROCm7.2.3 and exact binary
SHA **4a3b77e997d88498f9fd140867af227553f9c651c4693c0a31b710620bdcd814**. The XS config is unchanged. S differs from its
previously validated configuration only by API alias, log filename and a separate
copy of its saved S expert-routing seed. Config/pack fingerprints are checked;
there is no bypass for failed mixedQ4_K/IQ4_XS formats. Both use layer groups,
**not true TP2**. `DS4_IQ_Q8K=0`/`DS4_STREAM=0` remain; CPU expert backing and GPU
hot caching are retained. GLM stays S v2/MTP40GiB/fused0; Strata stays DSH default.

## Validation

All six S GGUF files passed fresh full-file SHA256 against the pinned published
manifest: **339,477,953,988 bytes** (316.16GiB). No weight download, model
deletion or second Engram copy was needed. XS still depends on S shards5/6.
The active [manifest](../maya/models.json) now includes S shards1–4 again; the
old full rollback manifest remains historical. Windows must keep separate pack
metadata for each quant and OS, while sharing the same weight files.

Normal existing Desktop terminal command/Ptyxis launch and original native web selector
passed **S→XS→S→XS**. Both DeepSeek selections passed authenticated streaming
on loopback/LAN/Tailscale host-self routes, JSON and synthetic tool round-trip;
original UI assets, three-model catalog and blocked runtime/config/load mutations
passed. No remote peer or real internet tool was tested; vision is unvalidated.
An initial default-GLM cold start was intentionally stopped before readiness
because expert-tier warming was slow; partial logs/thermal coverage are preserved
privately. It did not establish a GLM functional failure. The final proof starts
directly on S; GLM keeps its previous validation and unchanged settings.

Exactly one native worker, dual-card allocations, zero worker swap/spill and all
source/binary/config arguments were verified. The final XS worker is ready.
DSH, the model hub, gateway and unrelated applications were preserved.

Native8GiB reserve/card, actual6GiB startup, continuous3GiB/hard1.5GiB floors,
60GiB physical/52GiB available admission,52G/no-swap cgroup and latched watchdog
remain unchanged. S's prior near31.5K retrieval/full-history proof remains tied
to source24's original test; this alias deployment does not rerun full-window
validation or claim a new speed measurement.

Thermal recording covers **207 samples**, about1s interval, during
normal load/switch/functional validation. Sampled GPUjunction peaks **53.0/54.0°C**;
CPUpackage **82.0°C**. Full available sensors/power/clocks/fans/SMU flags are in the
[numeric record](results/maya-dual-deepseek-2026-10-23.json). This is finite
functional-test coverage, not a throughput stress test or lifetime worker peak;
flags alone do not demonstrate a speed loss. Zero OOM kills were verified in
recorded scope events; a memory.max notification is not itself an OOM kill.

## Saved benchmark comparison (not rerun)

| Selection | Context | Short code/prose decode t/s | Native fresh PP t/s | Fresh TTFT s |
|---|---:|---:|---:|---:|
| S, no DSpark |32768|6.42 /6.78|299.0|21.062|
| XS + matching DSpark|32768|31.28 /15.36|445.5|14.156|

These are earlier same-day three-trial medians on this hardware/source/binary,
with short256-output code/prose and fresh approximately6.3K actual DeepSeek
input probes. They came from separate sessions and have different quantization
quality. Preserve exact counts/methods/thermals in the
[S source24 report](MAYA-UPDATE-2026-10-23.md) and
[XS matching-drafter report](MAYA-XS-DSPARK-2026-10-23.md). The earlier single
1024-output XS HTML probe was12.54t/s; short-code median is not every workload.
Primary quant details: [pinned model card](https://huggingface.co/peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF/blob/d1fc01009f21e26157acb6858c315d0365483b72/README.md).
No forum-derived optimization or new runtime/source update is introduced here.

## Use

- XS API ID: `deepseek-v4.1-flash-1017-maya`.
- S API ID: `deepseek-v4.1-flash-1017-maya-s`.
- `llm-maya --model deepseek-v4.1-flash-1017-maya-s` starts S initially.
- Existing Maya web sidebar clearly labels **XS + DSpark** and **S (higher quality)**.
- API clients request the exact ID through existing gateway/hub; only one worker
  loads at a time. No new exposed port or idle unloading was added.

`maya/install.sh deepseek` verifies the existing sealed XS pack;
`maya/install.sh deepseek-s` verifies S without rerunning stock setup or
rewriting either profile. Neither verifier is a fresh full-weight checksum test;
the six-file full verification above is separate. New machines must validate
local source/binary/packs/configs; sanitized public configs are reference-only.
[Current handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md).
