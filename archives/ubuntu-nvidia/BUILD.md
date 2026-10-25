# Historical CUDA build and environment notes

These are the pinned versions used by the previous dual-NVIDIA setup. They are
an October 2026 snapshot, not a claim that these remain the latest releases.
Download upstream source and packages separately. Neither compiled artifacts nor
the private toolchain is distributed in this repository.

| Runtime | Source/package version |
|---|---|
| llama.cpp | `a0e6dc7384edb8f5d927155e1d26c10b4a310e6d` |
| Strata | `296b59d2f73c8f04a805df29c2fa97655adace78`, engine 0.1.44.1 |
| SGLang | `0.5.22.dev20261015+ga12814c158`, PyTorch 2.14.1+cu130 |
| vLLM | `0.32.0rc1.dev182+g429a3da66`, PyTorch 2.14.0+cu130 |
| HyperQwen | `95ee3b64b0df7014ee2626529524d6b99c3dcdd1`, patched vLLM 0.31.0, PyTorch 2.13.0+cu130 |

Source repositories: [llama.cpp](https://github.com/ggml-org/llama.cpp),
[Strata](https://github.com/Niko1221/Strata),
[HyperQwen](https://github.com/syv-ai/HyperQwen).
The SGLang nightly index used was `https://docs.sglang.ai/whl/cu130/`;
vLLM used `https://wheels.vllm.ai/nightly/cu130`; PyTorch CUDA packages used
`https://download.pytorch.org/whl/cu130`. Historical wheels may need to be located
by exact version or rebuilt from their matching source. Do not silently substitute
newer versions underneath version-specific patch helpers.

## Native builds

The previous installation used a private CUDA 13.0 toolkit under
`/opt/local-llm/llm-tools/cuda-build`, Ninja, and host C/C++ compilers named
`x86_64-conda-linux-gnu-cc` / `x86_64-conda-linux-gnu-c++`.
Adapt `sglang/env.sh`, `vllm/env.sh` and wrappers if using a different toolchain.
Build both SM86 (3060) and SM89 (4070). From the configured workspace:

```bash
source sglang/env.sh
export LD_LIBRARY_PATH="$TOOLCHAIN/lib64:$TOOLCHAIN/lib:${LD_LIBRARY_PATH:-}"
"$TOOLCHAIN/bin/cmake" -S llama.cpp -B llama.cpp/build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON \
  -DCMAKE_CUDA_COMPILER="$TOOLCHAIN/bin/nvcc" \
  -DCMAKE_CUDA_ARCHITECTURES='86;89' -DLLAMA_BUILD_IS_DEV=ON
"$TOOLCHAIN/bin/cmake" --build llama.cpp/build \
  --target llama-server llama-cli llama-bench -j 8
```

Compiler/linker/OpenMP paths depend on your toolchain; the original CMake caches
are intentionally not published. The historical llama router expects
`llama.cpp/llama-server`; install a wrapper that executes `build/bin/llama-server`
with its arguments, or consistently adjust the router and shutdown classifier.
Use Strata's pinned upstream setup/build procedure for `strata/build`, with
release optimization and both CUDA architectures. Its expected engine path is
`strata/engine/strata`. Generate BUILD.json using that revision's setup logic and
source fingerprint; copying another build's fingerprint is not valid.

## Python runtimes and local patches

Use separate Python 3.12 environments: `sglang/.venv`, `vllm/.venv`, and
`hyperqwen/upstream/venv`. The package inventories in the first two directories
record the historical environment; they are not portable, hardware-independent
lockfiles. Install the exact matching upstream versions before applying fixes.

```bash
mkdir -p dsh/logs dsh/research/upgrade-2026-10-14
python3 sglang/research/apply-nightly-qwen-fixes.py
python3 sglang/research/apply-nightly-context-memory-fix.py
python3 vllm/apply-local-qwen-fixes.py
```

The SGLang fixes share target/MTP vocabulary allocations, handle a quantized
output head, reset JIT architecture per GPU worker, and opt out of unsupported
NVLink multicast probes while retaining NCCL fallback. vLLM's fix avoids duplicate
MTP vocabulary allocations. Helpers are version/source gated; apply to pristine
matching package source. Generated reports are ignored. Do not blindly reapply
non-idempotent helpers or mix patch sets across versions.

For HyperQwen, check out its pinned source into `hyperqwen/upstream`, follow its
own vLLM 0.31.0 installation and apply its 50 upstream patches with
`patches/apply.sh`, then apply `hyperqwen/apply-dflash-share.py`. Use upstream
`verify.sh --install` to verify the patch installation. The local DFlash fix
requires the headless drafter checked by `hyperqwen/start-test`. Optional KVarN
was not installed. The standalone vLLM 0.32 nightly cannot replace this fork's
0.31 environment.

Model preparation in `hyperqwen/prepare-local.py` also needs separately obtained
fast-head source files. Preserve model licenses and provenance when downloading
checkpoints. Run package dependency checks and validate load, tools, memory and
switching on the intended hardware before treating a rebuilt stack as usable.
