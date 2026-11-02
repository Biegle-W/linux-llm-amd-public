# Headless inference defaults — November 2, 2026

This supersedes the earlier automatic terminal-window behavior. The model hub
starts guarded backends without opening a browser or terminal, even when a
desktop display is available. Persistent launcher logs remain available.
`LOCAL_LLM_GUI_LOGS=1` explicitly opts the hub into desktop log windows; manual
GUI/terminal launchers remain available on demand. Closing a log viewer leaves
inference running. Queue, ownership, memory guards and idle unloading remain.

The API and hub are enabled user services, with user lingering enabled. The
model-drive verifier now belongs to `default.target`, independent of the
graphical session; existing system fstab entries mount model drives at boot.
SSH and networking are active, and SSH is enabled for startup. The existing
backend was preserved during the completed idle hub restart; DSH was not restarted.

The OS still defaults to `graphical.target`: changing it requires administrator
authentication, which was unavailable during this change. To finish headless
boot, run on the server:

```sh
sudo systemctl set-default multi-user.target
```

This changes future boots and leaves the current desktop session running.
To open the desktop on demand from a console or SSH session:

```sh
sudo systemctl start display-manager.service
```

To restore graphical boot: `sudo systemctl set-default graphical.target`.
No reboot or desktop shutdown was performed. Boot without desktop login remains
unverified until the owner applies the administrator command and later reboots.

Validation: 62 CPU launcher/routing checks pass in each checkout; no model was
loaded for validation. Active inference, profile/context settings, RAM holds and
the paused daily updater are preserved.
