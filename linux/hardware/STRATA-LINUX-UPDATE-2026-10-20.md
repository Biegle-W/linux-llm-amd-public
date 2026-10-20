# Strata Linux app, engine candidate and Intel desktop — October 20

The official **Strata App 0.2.1** RX7900 AppImage and its bundled **HIP engine
0.1.46** are installed. The managed DSH backend still runs **0.1.45 / 477ac13c**:
the latest development engine built successfully, but has not passed its unchanged
actual 6 GiB/card startup admission. No model, context or expert-budget change is
promoted. [Numeric evidence](results/strata-linux-update-2026-10-20.json).

## Installed app

The AppImage's SHA-256 is
`de55db8822ea8ef53872ad1ba6d910e28890d97bc3f4f6957fb5b39bc54b7859`.
It matches both the official release asset digest and `SHA256SUMS.txt`. All twelve
packaged `--self-test` checks pass without a model load. The official bundle
installer verifies every engine source/destination file against its manifest;
`strata --version` reports 0.1.46, build ID `a7bdbfdabc9a+rocm`.

The existing **Strata App** menu points to the new actual AppImage in
`/opt/appimages`. **Strata Q3 / llm-strata** remains a separate managed launcher.
The old AppImage is retained for rollback. Shared NVMe weights and app model
settings are unchanged; no new weights were downloaded. The official icon is
byte-identical. The standalone app's legacy inference preset remains inactive
and has not been benchmarked on this setup. [Menu details](../launchers/STRATA-APP.md).

The [release notes](https://github.com/Niko1221/Strata/releases/tag/v0.2.1) explain
that **0.2.1.1 fixes Windows Terminal packaging**, with no replacement Linux app
or packaged engine. Do not label these Linux components 0.2.1.1.

## Managed development engine: built, not activated

Source is pinned to
[`9ae93f7b1fe989d04a8e404d32cddaeeff10505f`](https://github.com/Niko1221/Strata/commit/9ae93f7b1fe989d04a8e404d32cddaeeff10505f),
engine **0.1.46.1**, built with the retained isolated ROCm 7.2.3 SDK and gfx1100
MMQ support. The existing ggml source archive declares
`3cf03257f219afbe7334045ff7c6a06ac68c627d`; the build record labels that declaration
rather than claiming an enclosing repository commit belongs to ggml.
The new engine SHA-256 is
`c6706bc192c1afb09357e7d1eca9570c35c04562cde5265bd4404fe453848478`.

The isolated candidate uses the original IQ3_XXS weights, corrected NVMe pack,
MTP3, both GPUs/layer boundary 26, 13.5 GiB CPU expert cap, six pool workers,
262,144 context, INT8 KV with 32K GPU residency, and 7/8 GiB reserve targets.
A private copy of the routing-profile seed protects production state. Its 52G
worker-only scope has swap disabled; the continuous latched guard stays enabled.

Small device self-tests pass and both cards allocate model/cache memory.
However, **the actual whole-card startup reserve check fails**. Minimum free VRAM
sampled during loading was **3.986/6.268 GiB** in PCI order; these are loading minima,
not exact loaded-startup snapshots. Owned swap and VRAM spill remained zero.
The guard stopped only the owned worker. A prior attempt had refused even to
load because desktop graphics activity exceeded the benchmark's idle threshold.
Neither event is an inference benchmark or proof of an engine crash.

Functional tools/streaming, fresh short/~8K speed samples, near-256K retrieval and
full-history follow-up are **not completed on this candidate**. Consequently it is
not promoted and has no new PP/TTFT/decode numbers. The README's Strata speeds
remain the dated **0.1.45** measurements; they are not attributed to the app or
new engine. All production profile fields remain unchanged.

## Intel desktop preference

The monitor is already on the motherboard's Intel UHD770 DisplayPort output,
but GNOME 50.1's journal selects AMD **Boot VGA** as the primary renderer.
The AMD display card had about 1.37 GiB allocated and 23–25% baseline activity.
Mutter composites on its selected primary GPU even when scan-out uses another
card, according to its [multi-GPU documentation](https://github.com/GNOME/mutter/blob/main/doc/multi-gpu.md).

The installed and udev-tag-verified [Intel udev rule](61-local-llm-intel-primary.rules) matches vendor
8086/device a780 and requests `mutter-device-preferred-primary`. The
[installer](install-intel-desktop-primary.sh) used successful administrator authentication,
reloads rules and targets the Intel DRM device only. It does not restart the
session, unload AMD drivers, change global DRI/Vulkan/HIP variables or change
inference-device selection. A new GNOME session is required before measuring the
result. Installation and activation status are kept in the numeric record and
current handoff; do not infer activation merely from a prepared rule.

After a new desktop session, verify the GNOME primary-renderer journal and actual
per-process/whole-card AMD allocations. Some applications may still explicitly
offload to AMD; zero VRAM usage is not promised. Retest the original Strata
candidate and all its guard/quality/context gates before promotion. No reserve
was lowered to bypass this failure.

Forum context, not a local speed claim:
[lcz.me topic 2059/7](https://lcz.me/topic/2059/7) describes separating the display
from a single 7900XTX on a different X99/Strata system;
[Level1Techs post 193307/2](https://forum.level1techs.com/t/how-to-get-display-output-on-secondary-gpu-non-primary/193307/2),
DS_DV, January 23, 2023, links the Mutter preferred-primary method on a different
APU/VFIO setup. The GNOME documentation supplies the implementation. No forum
VRAM saving or throughput is substituted for a local post-login measurement.
