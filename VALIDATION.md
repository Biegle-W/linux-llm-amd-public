# Validation scope

The original Linux runtime profiles were tested on the documented hardware.
The sanitized reference paths are examples and have not been used to launch a
second runtime installation. Publication checks cover Python syntax, shell
syntax, JSON parsing, selected unit tests, secret scanning, identity-pattern
scanning and exclusions for private/model files. Windows runtime behavior was
not retested on Linux.

No source-repository commits or raw audit reports are included. Check fresh Git
history as well as working files before making changes public. Keep local
credentials, private configuration and model weights outside tracked files.
