# Strata App menu integration

The existing AMD AppImage has a separate **Strata App** application-menu entry.
**Strata Q3** remains the managed DSH inference backend. The AppImage owns its
own settings and model worker; the managed backend's measured dual-GPU profile,
API gateway and watchdog are not automatically inherited by the app. Avoid
loading both workers concurrently. Adding this menu entry does not start either.

Source: [official Strata App](https://github.com/Niko1221/Strata#option-a-the-strata-app).
The existing download is `Strata-0.2.0-beta-linux-amd-rx7900.AppImage`. It is not included in Git.
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

October 19 validation: desktop entry syntax, executable target, installed icon
and desktop application registration checked without launching the AppImage or
loading a second model. No inference benchmark was rerun for menu integration.
