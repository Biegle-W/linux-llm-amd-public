# Automatic temperature logging

User instruction, October20: log temperatures from now on. All future benchmark
reports must include sampled thermal coverage, not reuse old peak temperatures.
Earlier October20 benchmarks did not record temperatures; their missing values
stay missing. October17's107–108C hotspots remain historical evidence.

## Automatic coverage

- Normal llama.cpp, SGLang, vLLM, Strata and Maya launchers start a read-only
  collector before their owned router starts and stop it after backend cleanup.
  Existing PATH names and visible terminals are unchanged. No model is loaded
  just to collect temperatures, and DSH/gateway/unrelated processes are untouched.
- `benchmark-current-amd.py` records each complete profile run and attaches a
  `thermal` summary to each `stream()` trial. Existing callers, including Maya
  selection and Qwen context tests, inherit the request hook on their next
  invocation. API timing boundaries, sampling and throughput formulas are unchanged.
- Strata/Maya candidate helpers and Nemotron Super validation additionally record
  their worker lifecycle, including loading and guarded shutdown. Final result
  JSON contains `thermal`; raw logs and periodic summaries survive a failed run.
- Other ad-hoc tests must use `ThermalRecorder` or the observer below. Directly
  running an upstream binary outside the managed launchers does not automatically
  start a collector. Already-running Python processes retain their loaded code.

Raw timestamped samples are saved every **one second**, with an initial and final
sample, under ignored `dsh/logs/thermals/`. Each unique run has `.jsonl` and
`.summary.json` files. Summaries update about every5seconds and on normal stop.
Files are private0600; raw data is capped at64MiB per collector. After the cap,
cumulative summaries continue and `raw_samples_dropped` explicitly counts the
omitted raw samples. Existing files are never overwritten or deleted for rotation.

## Recorded data and interpretation

Per PCI-address/GPU index: labeled core/edge, junction/hotspot and VRAM/memory
temperatures, critical thresholds when exposed, fan RPM, average/input power and
power cap, GPU/memory clocks and utilization. CPU package temperatures are also
recorded through `coretemp`. Summaries retain sampled peaks, busy-sample peaks
(GPU utilization at least10%), sensor sample counts and telemetry errors.

The installed Navi31 driver exposes120-byte `gpu_metrics` v1.3. That verified
layout supplies both raw ASIC and independent SMU masks; heat/hotspot, power and
current-limit flags are counted separately. Unknown versions, unreadable files
and unsupported sentinels remain **unavailable/null**, never a fabricated zero.
Reported SMU flags are retained even when measured temperatures are low; this
collector does not establish whether a flag caused a current clock reduction.
Flag counts are observations, not seconds throttled or a measured speed penalty.

One-second sampling can miss short transients. Whole-card sensors include other
workloads; a session peak alone does not assign heat to an individual request.
`complete` describes collector lifecycle, not thermal health: inspect card/sensor
coverage, errors and available flags before making a cooling claim. Logger errors
are reported but do not bypass memory guards, stop inference or alter fan curves,
power limits, clocks, placement, engine versions or model settings.

For a test already in progress, follow its exact PID/start time without controlling it:

```sh
python3 hardware/log-gpu-temps.py --label my-test-partial --pid TEST_PID
```

For a finite read-only check:

```sh
python3 hardware/log-gpu-temps.py --label sensor-check --seconds 5
```

The PID observer exits when the original process ends, including PID reuse or a
zombie. Ctrl+C stops only the observer. Coverage starts at attachment; never call
that a full-run maximum. A partial observer was attached to the in-progress
DeepSeek comparison at15:15 Toronto time on October20, without rerunning or
interrupting inference. Do not retroactively add its peaks to earlier trials.

Publish only reviewed numeric summaries tied to the exact workload/build and
actual observation interval. Keep raw logs, local paths and process metadata out
of public Git. The logger adds CPU/sysfs/filesystem work; no performance-neutral
or cooling-speedup claim is inferred from its installation.

Primary interfaces: [Linux AMD thermal/sysfs documentation](https://docs.kernel.org/gpu/amdgpu/thermal.html),
[pinned v1.3 GPU metrics ABI](https://github.com/torvalds/linux/blob/v7.0/drivers/gpu/drm/amd/include/kgd_pp_interface.h),
[pinned independent SMU bit definitions](https://github.com/torvalds/linux/blob/v7.0/drivers/gpu/drm/amd/pm/swsmu/inc/amdgpu_smu.h).
This is observability requested by the user, not a forum-derived optimization.

Validation:99 CPU-only tests pass in each repository, including10 telemetry
checks covering ABI/sentinels/units, missing sensors, bounded logs, shutdown,
PID identity, launcher spawn failure and unchanged benchmark timing fields.
The live partial observer reads both cards without loading or stopping a model;
this validates collection, not inference performance or a cooling improvement.
