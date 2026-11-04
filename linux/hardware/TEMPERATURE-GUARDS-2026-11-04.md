# Current software temperature guards — November 4, 2026

The owner requested all software temperature guards at **100°C**. The current policy stops at **100°C or above** for:

| Temperature | Software stop threshold |
|---|---:|
| CPU package | 100°C |
| GPU edge, each card | 100°C |
| GPU junction, each card | 100°C |
| GPU memory, each card | 100°C |
| SSD live temperature | 100°C |
| SSD SMART numeric temperature | 100°C |

The shared policy is in `dsh/temperature_policy.py`; `dsh/storage_health.py` uses the same ceiling for live and SMART temperatures. All twelve current isolated peer/model controller copies use the shared thermal evaluator. GPU sensor critical-temperature values remain telemetry and no longer supply a separate software stop threshold in those controllers. Device firmware protections and SMART health-warning, failing-status, media-error and spare-capacity checks remain unchanged; a device health warning can still block work independently of the numeric ceiling.

The 1 GiB host-RAM reserve, 128 MiB per-card VRAM reserve, dedicated-spill rejection, existing swap policy, SSD telemetry freshness/validity, resource caps, timing, ownership, kernel-fault and cleanup checks are unchanged. Engine/weight pins, boot configuration, services and paused schedules are unchanged. No service restart, GPU check, PLE retry or Super launch was performed. Existing fault hold and STOP remain latched; changing the ceiling does not authorize or automatically resume GPU work.

The completed campaign still records three strict short tool passes, three decode-guard stops, PLE's historical **85°C guard / sampled 87°C stop**, and Super not started. Those results have not been reclassified under the new ceiling. Pre-change controller sources and source manifests were retained privately, and current controller/runtime manifests were resealed for the new software policy. Older completed experiment snapshots retain their original policy and are not current controller templates.

Validation used CPU-only synthetic inputs: twelve focused thermal/resource/storage tests passed in each repository, and 144 boundary cases passed against the actual twelve updated campaign-controller thermal call sites. Below-ceiling samples pass; exact-ceiling and above-ceiling samples stop. No GPU qualification or sustained thermal result is implied.

[Completed model outcomes](PATCHED-KERNEL-MODEL-CHECKS-2026-11-04.md).
