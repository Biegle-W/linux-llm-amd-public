# GUI on local device connection — November 2, 2026

Installed by the owner and verified on November 2. The system timer is enabled
and active; the latest service check exits successfully. The installed detector
and units match the reviewed source, are root-owned, and have no group/other
write permission. Live detection finds a connected DisplayPort display and USB keyboard/mouse
capabilities; readiness is true with the installed HDMI-plus-DisplayPort setting.

For installation or reinstallation from the repository root:

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

The owner selected HDMI and DisplayPort, applied the configuration, and the
installed setting is verified as `LOCAL_LLM_GUI_CONNECTORS=HDMI-A,DP`. Both
new-install and installed configuration now accept either connector type. The
timer is enabled and active; the latest service check succeeds. The graphical
display manager is active. This verifies detection and operation with the current
desktop already running, not a fresh hotplug-triggered desktop start.

For future configuration changes, edit `/etc/default/local-llm-gui-on-connect`.
The installer preserves existing configuration on reinstallation.

The next check reads the configuration; no inference restart is needed.
To disable automatic GUI startup while preserving a running desktop:

```sh
sudo systemctl disable --now local-llm-gui-on-connect.timer
```

Validation: nine CPU tests pass per checkout, covering missing components,
HDMI/DisplayPort selection, non-USB rejection, composite receivers, multiple
GPU connectors, missing udev metadata and safe service activation. Shell syntax
and host systemd unit verification pass. Real-device checks used `--check` and
made no changes. Installation and ongoing timer execution are verified; no reboot or actual
hotplug lifecycle has been validated. Default boot is already `multi-user.target`; a desktop session is
currently active. Existing inference services and paused engine updater remain.
