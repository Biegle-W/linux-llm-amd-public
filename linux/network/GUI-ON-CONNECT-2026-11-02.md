# GUI on local device connection — November 2, 2026

Prepared and CPU-validated; system installation is pending administrator
execution. Sudo requires interactive authentication and pkexec found no
authentication agent, so no system detector files or timer were installed.

From the repository root, install with:

```sh
sudo bash network/install-gui-on-connect.sh
```

The installer copies the detector and units into root-owned system locations,
keeps multi-user boot, and enables a system timer. Every five seconds, the
oneshot checks connected HDMI ports and udev's USB keyboard/mouse capability
flags. All three conditions must be present before it starts
`display-manager.service`. Multiple GPUs and composite USB receivers are
supported. It opens the graphical login screen; it does not automatically log
in, stop the desktop on disconnect, restart inference, or load a model. An
already-running desktop is left running. No raw keyboard or mouse events are
read. No inference hardware/memory/context guards change.

HDMI-only is the requested default. A read-only live check found USB keyboard
and mouse capabilities, but the connected monitor reported DisplayPort rather
than HDMI. To include DisplayPort, set this in
`/etc/default/local-llm-gui-on-connect` after installation:

```ini
LOCAL_LLM_GUI_CONNECTORS=HDMI-A,DP
```

The next check reads the configuration; no inference restart is needed.
To disable automatic GUI startup while preserving a running desktop:

```sh
sudo systemctl disable --now local-llm-gui-on-connect.timer
```

Validation: nine CPU tests pass per checkout, covering missing components,
HDMI/DisplayPort selection, non-USB rejection, composite receivers, multiple
GPU connectors, missing udev metadata and safe service activation. Shell syntax
and host systemd unit verification pass. Real-device checks used `--check` and
made no changes. No reboot, hotplug lifecycle or root installation has been
validated. Default boot is already `multi-user.target`; a desktop session is
currently active. Existing inference services and paused engine updater remain.
