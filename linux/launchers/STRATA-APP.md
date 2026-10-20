# Strata App menu integration

The existing AMD AppImage has a separate **Strata App** application-menu entry.
**Strata Q3** remains the managed DSH inference backend. The AppImage owns its
own settings and model worker; the managed backend's measured dual-GPU profile,
API gateway and watchdog are not automatically inherited by the app. Avoid
loading both workers concurrently. Adding this menu entry does not start either.

Source: [official Strata App](https://github.com/Niko1221/Strata#option-a-the-strata-app).
The restored application is `~/Applications/Strata-0.2.0-beta-linux-amd-rx7900.AppImage`.
It is the actual executable file, restored from Trash with SHA-256 comparison;
Downloads is not required. The AppImage is not included in Git.
The official bundled icon is retained in `icons/strata-app.png` with provenance
and checksum in [icons/SOURCES.json](icons/SOURCES.json).

For another installation, adjust `Exec=` and `TryExec=` in `Strata-App.desktop`
to the actual executable AppImage before installing. Moving the AppImage later
requires updating both fields. From this `launchers/` directory:

```sh
chmod +x /path/to/Strata-0.2.0-beta-linux-amd-rx7900.AppImage
install -Dm644 icons/strata-app.png "$HOME/.local/share/icons/hicolor/512x512/apps/strata-desktop.png"
install -Dm644 Strata-App.desktop "$HOME/.local/share/applications/Strata.desktop"
desktop-file-validate "$HOME/.local/share/applications/Strata.desktop"
update-desktop-database "$HOME/.local/share/applications"
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor"
```

October 19 maintenance restored the existing AppImage to `~/Applications` and
updated both `Exec` and `TryExec`; the application was not started.

October 19 validation: desktop entry syntax, executable target, installed icon
and desktop application registration checked without launching the AppImage or
loading a second model. No inference benchmark was rerun for menu integration.

## Shared model assets — October 20

The app's model data directory and installed model/MCP configuration now point to
`/mnt/shared-nvme/LLM-Models/Strata`, the same assets used by the
managed backend. The app engine and AppImage remain on the Linux filesystem.
No duplicate GGUF or MTP download is required. Destination checksums were verified;
unique app vision and conversion assets are retained in the shared tree.

The old generated expert packs differed, so they were checked against a complete
reference hash derived from the GGUF. Only the reference-matching pack is used.
This is an asset-integrity correction, not a quantization or engine update.
The managed profile retains both GPUs, its 13.5 GiB expert budget and watchdog.
The standalone app's legacy preset remains inactive and has not been validated
for generation on this setup; sharing weights does not share runtime settings.
