# Headless boot with GUI on keyboard/mouse activity — November 2, 2026

The owner requested headless boot even with all peripherals connected, then graphical login only after actual keyboard or mouse input. The replacement is installed and verified: `multi-user.target` remains the default, the persistent activity watcher is enabled/running, and the old presence-only timer is disabled/inactive. The installed detector and unit exactly match the reviewed source, are root-owned and have no group/other write permission.

## Behavior

The boot target remains `multi-user.target`. A connected HDMI or DisplayPort display and USB keyboard/mouse capabilities remain prerequisites. Their presence alone never starts the desktop. The persistent service waits for either a fresh keyboard press or mouse motion, button press or scroll, then starts only `display-manager.service`. Graphical login still requires normal login; no automatic login is added.

Each newly opened device has a two-second settling/arming period. Linux evdev timestamps are explicitly set to the monotonic clock; events before that deadline, releases, key repeats, connection/synchronization/LED reports and zero movement do not trigger startup. Hotplugged USB devices are discovered while waiting. A composite receiver can supply both keyboard and mouse capabilities. Events while display/device prerequisites are missing are not saved for a later start.

While the display manager is active, the watcher closes its input descriptors and leaves the current desktop running. It never grabs exclusive input, saves keys, prints key codes, changes login credentials, stops the desktop on disconnect, restarts inference, or loads a model. Its log records only watcher readiness or a generic GUI-start event. It runs as a hardened root system service because Linux input-device reads require privilege. The old presence-only timer is disabled by the installer.

## Installation

From the repository root:

```sh
sudo bash network/install-gui-on-connect.sh
```

The installer stops only the old detector, disables its timer, copies the reviewed detector/unit to root-owned system locations, preserves `/etc/default/local-llm-gui-on-connect`, reloads systemd, keeps `multi-user.target` as the default and enables the persistent service. It preserves the current display-manager and inference sessions. The accepted connector setting remains `LOCAL_LLM_GUI_CONNECTORS=HDMI-A,DP`.

To disable future input-triggered activation while preserving the running desktop:

```sh
sudo systemctl disable --now local-llm-gui-on-connect.service
```

## Verification and limits

Twenty-four CPU tests pass in each checkout. They cover connected-device/no-input boot behavior, USB and connector prerequisites, keyboard and mouse activation, key-repeat/release rejection, monotonic arming and stale-event rejection, passive reports, device removal, clock-setup failure, display-manager error states, closing readers while the GUI is active, and rechecking readiness before startup. Shell syntax and host systemd unit validation pass. Read-only live detection confirms the current connected display and keyboard/mouse capabilities.

Root installation and the preserved running desktop are verified. The accepted installed connector setting remains HDMI plus DisplayPort. A fresh reboot/input lifecycle test remains pending; it requires leaving inputs untouched after reboot, confirming no graphical login, then pressing a key or moving the mouse. No reboot, desktop termination, synthetic input injection, inference restart or GPU test was performed for this change. Current numerical/runtime/source pins, holds, guards and paused engine updater remain.

## Earlier behavior and observed cause

The earlier November 2 installation polled for device presence every five seconds. The reboot observed by the owner confirmed that already-connected display and USB keyboard/mouse started graphical login immediately. That behavior explains the unexpected GUI boot and is superseded by this actual-input requirement; the old nine-test presence-only result remains historical evidence.
