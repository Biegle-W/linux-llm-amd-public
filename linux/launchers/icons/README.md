# Official desktop launcher logos

The launchers use project-owned logo/favicon assets from the official
repositories listed below. The previous custom artwork has been replaced.
Artwork is copied without redrawing, recoloring or adding a background; the
desktop scales each icon normally. Turnstone embeds its official SVG in its
HTML: only that existing data URI was decoded into a standalone SVG file.
DSH uses its official desktop PNG with an opaque light background, replacing
the transparent web favicon so it stays readable against wallpaper. The
background and shadow are part of the original upstream artwork.

| App | Asset and pinned upstream source | Original repository license |
|---|---|---|
| llama.cpp | [`llama.svg`](https://github.com/ggml-org/llama.cpp/blob/f12aaa344c971556ec35be054d7aac1d901fd510/media/llama1-icon.svg) | [MIT](licenses/llama.LICENSE) |
| SGLang | [`sglang.png`](https://github.com/sgl-project/sglang/blob/f84475ccf593087df3d1da13c9e675eadee12352/assets/logo_square.png) | [Apache-2.0](licenses/sglang.LICENSE) |
| vLLM | [`vllm.png`](https://github.com/vllm-project/vllm/blob/83c9a547bf9a3b4f2653fb5766886bdc5dba35be/docs/assets/logos/vllm-logo-only-light.png) | [Apache-2.0](licenses/vllm.LICENSE) |
| Strata Q3 | [`strata.svg`](https://github.com/Niko1221/Strata/blob/296b59d2f73c8f04a805df29c2fa97655adace78/serve/web/favicon.svg) | [MIT](licenses/strata.LICENSE) |
| Maya | [`maya.svg`](https://github.com/mw00/project-maya/blob/8d9a9b5d705049a87da853717cdc59440252de30/serve/web/icon.svg) | [MIT](licenses/maya.LICENSE) |
| dsh | [`dsh.png`](https://github.com/deepseek-ai/deepseek-harness/blob/687f282e8625c6b8d11ff58211a90524be2e4317/apps/desktop/resources/icon.png) | [MIT](licenses/dsh.LICENSE) |
| Turnstone | [`turnstone.svg`](https://github.com/turnstonelabs/turnstone/blob/5c82b17700a73ad0ee84421f77549c8a3d46b06b/turnstone/ui/static/index.html) | [Apache-2.0](licenses/turnstone.LICENSE) |
| Sage | [`sage.png`](https://github.com/InternScience/Agents-A1/blob/ff57c5f2d2819c918a20281a3da76990cd82b554/docs/assets/InternScience_logo.png) (publisher logo; same file as the Sage-A1.5 project-page favicon) | [Apache-2.0](licenses/sage.LICENSE) |
| ComfyUI | [`comfyui.svg`](https://github.com/Comfy-Org/ComfyUI_frontend/blob/79a53509d11d1d5a065b543c148bd11d0f24b36e/public/assets/images/comfy-logo-single.svg) | [GPL-3.0](licenses/comfyui.LICENSE) |

[SOURCES.json](SOURCES.json) records complete commits, original paths, exact byte
sizes and SHA-256 values. Each asset retains its upstream ownership. Original
repository licenses are included per asset; these are not relicensed as locally
created artwork. Turnstone’s [NOTICE](licenses/turnstone.NOTICE) is retained.
Use of a logo here identifies the locally installed app and does not imply
upstream endorsement of this setup. See the upstream
[DeepSeek Harness brand guidelines](https://github.com/deepseek-ai/deepseek-harness/blob/687f282e8625c6b8d11ff58211a90524be2e4317/BRAND_GUIDELINES.md).

The desktop entry `Icon=` points to the corresponding file in `launchers/icons/`.
Keep that directory when copying/reinstalling the setup. For another install
location, update the absolute `Icon=` paths alongside `Exec=` and `Path=` values,
then copy the launchers to your Desktop. Preserve their executable bits and
existing desktop trust state. Backend commands, terminal settings and models
are unaffected by this icon replacement.

Strata App uses `strata-app.png`, the unchanged 512×512 desktop logo bundled in
`Strata-0.2.0-beta-linux-amd-rx7900.AppImage` at
`usr/share/icons/hicolor/512x512/apps/strata-desktop.png`.
See the [official Strata App distribution](https://github.com/Niko1221/Strata#option-a-the-strata-app)
and the retained [Strata license](licenses/strata.LICENSE). Its checksum is in
`SOURCES.json`; this asset comes from the binary distribution rather than a
claimed source commit. Install it as `strata-desktop.png` in the user hicolor
icon directory, as described in [the app-menu setup](../STRATA-APP.md).

Official Comfy Desktop uses the package-installed `comfyui-desktop-2` hicolor
icon, with `StartupWMClass=Comfy Desktop` matching its observed Wayland ID.
The Desktop browser shortcut retains `comfyui.svg`. See the
[package/icon matching record](../../graphics/DESKTOP-2026-10-20.md#dockwindow-identity-correction--october-21);
the native package's PNG is not duplicated in this source tree.
