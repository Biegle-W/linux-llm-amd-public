# Validation scope

The original Linux runtime profiles were tested on the documented hardware.
The sanitized reference paths are examples and have not been used to launch a
second runtime installation. Publication checks cover Python syntax, shell
syntax, JSON parsing, selected unit tests, secret scanning, identity-pattern
scanning and exclusions for private/model files. Windows runtime behavior was
not retested on Linux.

No source-repository commits or raw audit reports are included. Check fresh Git
history as well as working files before making changes public. Keep local
credentials, private configuration and model weights outside tracked files.

The `linux-nvidia/` addition is the sanitized pre-AMD configuration, checked with
37 Python and 29 shell syntax checks, nine JSON parses, and 19 retained
backend-shutdown and shared-mount unit tests (all passed). Historical GPU checks are described in its README; no NVIDIA runtime
or throughput tests were repeated on the current mixed-vendor machine.


October 17 vLLM tuning: the operational profile passed dual-GPU numerical/graph,
JSON/arithmetic/tools, 64K retrieval and actual production-router/prefix-cache
checks. The public copy contains sanitized source, benchmark metadata and a
short runtime handoff; models, binaries, raw logs and private history are excluded.
The historical Windows/NVIDIA snapshots were preserved. Public paths remain
examples; operational inference validation used the private installation.

October 17 forum review: documentation and maintenance-policy changes only.
Source links and relative document targets were checked; public identity/secret
scans were repeated. No inference or performance tests were rerun.

October 17–18 Level1Techs experiments: the isolated head-256 rocWMMA port passed
84 CPU-reference cases across two GPUs and off/on modes, followed by model/tools
and benchmark checks. Current vLLM, native HIP, restored rocWMMA, Vulkan and
Radiance comparisons are documented with contexts and quant/cache differences.
No GPU peer-access prerequisite was available. Manual fan A/B remains pending.
Only source, sanitized metrics and documentation are distributed; generated
runtimes, model files, raw outputs and private paths remain excluded.

October 18 vLLM desktop-startup recovery: real saved profile/router passed
functional, 64K marker retrieval and prefix-cache checks with utilization 0.82,
20 GiB admission per GPU and the same fixed 3.5 GiB KV allocation. Wrapper tests
verified error logging, interactive failure retention and noninteractive exit
status. Python/shell syntax, reviewed public paths and secret scans were checked
before publication. Historical throughput results were not rerun or relabeled.
