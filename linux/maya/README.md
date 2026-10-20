# Project Maya on two RX 7900 XTX cards

The isolated HIP build uses [Project Maya v1.1.17, commit `8d9a9b5d`](https://github.com/mw00/project-maya/tree/8d9a9b5d705049a87da853717cdc59440252de30).
Both models are active at **32,768 tokens**. Current local validation is in
[the Maya report](../hardware/MAYA-2026-10-20.md). All profiles use both cards;
this is experimental upstream AMD support. Existing llama.cpp, Strata,
vLLM/SGLang environments and the saved DSH default are preserved.

## Installation and files

[Runtime pins](runtime.json) include the isolated llama.cpp dependency `3cf03257`
and [official rocWMMA 2.2.0 headers for ROCm 7.2.3](https://github.com/ROCm/rocWMMA/tree/48b7db12a9ade97f0b7ab2ff9321ba0cbb4e5b77).
The SDK itself stays 7.2.3. [build-env.sh](build-env.sh) selects the existing
GCC 14.4 cross-toolchain, sysroot and library search paths; no system packages or
other engines are patched. Maya uses its own Python 3.12.14 environment and
[locked Python package versions](requirements-lock.txt).

Model files live beneath the **Maya directory on the new shared NVMe**:
`/mnt/shared-nvme/LLM-Models/Maya`. The [pinned download manifest](models.json)
records the active assets' revisions, byte sizes and published SHA-256. The [S24 rollback manifest](glm-s24-rollback-models.json) records the retained control files; it is not another active model.
GLM is **Maya-S v2**, three GGUF shards (mixed IQ2/IQ3 experts, Q6_K attention/shared weights). DeepSeek is **Maya-S**, six GGUF shards
including Q6_K Engram, plus the matching DSpark draft and vision assets.
No original FP8 checkpoint, EXL3 copy or second full expert pack was downloaded.
The engine reads experts from GGUF in place; the generated indexes/dense packs
are additional required assets. DeepSeek's vision source is converted losslessly
into `vision.bin` and `vision.json`, then the installer deletes that raw source
shard/config. This conversion does not remove its GGUF target weights.

For a fresh installation after providing the retained ROCm/toolchain dependencies:

```bash
export MAYA_MODELS_ROOT='/mnt/shared-nvme/LLM-Models/Maya'
python3 maya/download-models.py --root "$MAYA_MODELS_ROOT"
maya/install.sh glm
maya/install.sh deepseek
```

The downloader resumes partials and checks full SHA-256 before publishing a file.
Existing complete mismatches are preserved for review. The preparation scripts
never start or calibrate inference, and never activate newly generated configs.
They use `--no-start --no-speed-calibration`; the latter matters because
DeepSeek's installer can otherwise run calibration despite `--no-start`.
Do not run bulk transfers/builds during clean timing measurements.

## Serving and guards

`llm-maya` starts the backend and opens its native Chat/Monitor in a local browser.
The **Maya** desktop launcher also keeps a visible terminal. DSH is optional;
start `dsh` separately and select the **Local Maya** provider when wanted.
The router's OpenAI chat API is loopback port **30030**, with one owned worker
on **30031**. Remote clients use the existing authenticated LAN/Tailscale gateway
on port **10000**, with the exact model IDs in the current report. Switching
between Maya models unloads the previous model. Switching to another configured
backend unloads only the configured inference processes and their owned workers.
DSH, the API gateway, ComfyUI and unrelated jobs are preserved.

Admission requires both cards, at least 60 GiB OS-visible physical RAM,
52 GiB available RAM and 16 GiB free per card after handover. Swap is not capacity.
Final profiles request 8 GiB native reserves on both cards, then verify at
least 6 GiB whole-card free at startup. HIP
free-memory estimates alone omit other desktop allocations. An owned no-swap 52 GiB
systemd scope and the continuous latched RAM/VRAM watchdog protect the desktop.
A guard failure requires explicit reload after freeing memory. No automatic
single-card fallback or quality-changing expert skipping is enabled.
Source revision, native binary SHA and configuration fingerprint must match
local validation before a profile can load.

GLM uses an explicit **40 GiB whole-machine expert RAM ceiling**, divided between
the two layer partitions, plus GPU hot-expert caches and cold NVMe reads.
This is not 40 GiB per GPU. Its MTP block runs on the second card. The upstream
hipBLASLt tables are selected only for the matching gfx1100/library version.
DeepSeek's native GGUF expert placement and exact speculation selection are
recorded in the test report. OS page caching is not an explicit pinned expert tier.

Both use layer splitting with host transfers. DeepSeek is requested with
`--tp 2`, but its selected GGUF's 256-value blocks do not divide its 2,304-wide
experts into two valid partitions: the engine explicitly changes TP2 to separate
GPU layer groups. **That still uses both cards; it is not true TP2.** The model
is never described as running true TP merely because `--tp 2` appears in the config.

## Validation limits and research

The 14 documented GLM/kernel numerical checks passed independently on each GPU.
DeepSeek's broader GGUF suite retains two failed bit-exact token/window tests
for mixed Q4_K/IQ4_XS on each card, although numerical CPU-reference checks pass.
Those formats are absent from this exact Maya-S target. No test assertion or
tolerance was weakened; passing this target does not validate other DeepSeek quants.
Small functional/tool/retrieval checks are not a general model-quality evaluation.

[lcz.me, johnnybegood, October 8](https://lcz.me/topic/2195/3) reports Maya 1.0.11
on RTX 3080/3090, 128 GB RAM, 65K context. Its sampling changes and timings are
external evidence, not a dual-7900-XTX target or a quality-neutral speed gain.
[Level1Techs, rqzer0, October 8](https://forum.level1techs.com/t/advice-on-a-local-ai-server-before-buying/258001)
discusses a proposed 9900X/96 GB/3090 build, not this Maya setup. No matching
dual-7900-XTX Maya benchmark was found there in this search. See the
[both-forum source ledger](../hardware/FORUM-OPTIMIZATION-SOURCES.md) and the pinned
[AMD implementation guide](https://github.com/mw00/project-maya/blob/8d9a9b5d705049a87da853717cdc59440252de30/docs/AMD_MAYA.md).

## Linux and Windows sharing

GGUF weights may be shared across operating systems; builds and environments
stay on Linux ext4. The new NVMe's Windows drive letter has not been assigned
in these records. DeepSeek's generated pack contains a Linux absolute model path.
Windows must generate a **separate pack/index directory** with its own paths;
do not overwrite the Linux pack metadata. Linux launchers, HIP binaries and
absolute paths cannot be used unchanged in Windows. The canonical
[Linux/Windows handoff](../network/LINUX-LLM-RUNTIME-HANDOFF.md) remains on Shared SATA / D:.

The Maya desktop entry explicitly opens Ptyxis on this Ubuntu installation.
Adapt that terminal command on another desktop. Upstream installer configs are
preparation outputs; use the guarded managed profiles for serving.

Strata Q3 and Maya now also open their own local Chat/Monitor page when ready.
DSH stays optional and separate; `--no-browser` suppresses browser opening.
[Native frontend behavior and controls](../hardware/NATIVE-FRONTENDS-2026-10-20.md).


## GLM S/S24 comparison

Current selected GLM quant: **Maya-S**,32K, same RAM40/MTP/reserves. [Six-trial ABBA results](../hardware/MAYA-S-VS-S24-2026-10-20.md) supersede the earlier GLM speed row; DeepSeek is unchanged.
