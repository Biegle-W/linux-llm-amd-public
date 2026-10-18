# DeepSeek Harness runtime

**October 17 Harness update:** DeepSeek Harness is pinned to
`@deepseek-ai/dsh@0.2.1-rc.2`, the newest official npm prerelease checked on
October 17 (`next` tag), upgraded from `0.1.5-rc.2`. Private Node.js remains
24.21.0. The normal launcher, authenticated web page, four frontend assets and
native terminal smoke check passed. All eight local models, default selection,
chat/session files, stored data and credentials were preserved. This release
imports `data/settings.yaml` into `data/profiles/web/cordis.patch.yml` and retains
`settings.yaml.imported`; the configuration helper now refreshes that profile
without recreating legacy settings. Two configuration regression tests passed.
No inference throughput or model-generation tests were repeated for this UI
upgrade. Harness was stopped after validation; launch it normally when needed.

The package and lockfile pin the official published prerelease exactly;
`npm ci` recreates that dependency set. The CLI tarball SHA-1 is
`a502d1551aabc881020e3cb7961c38901565731a`; the lockfile records SHA-512
integrity for the CLI and its dependencies. All 295 installed Harness packages
resolve to `0.2.1-rc.2`. This is the published npm build, not a source checkout.
Sources: [official repository](https://github.com/deepseek-ai/deepseek-harness)
and [official npm package](https://www.npmjs.com/package/@deepseek-ai/dsh).

The manifest approves version-pinned install scripts for the subprocess helper,
node-pty, Koffi and protobufjs. Preserve the existing private `data/` directory
and workspace when upgrading. Back up the prior runtime and data together before
first launch because the new settings layout is profile-specific. Do not commit
settings, chat files, credentials, runtime binaries or rollback backups.

Run `python3 -m unittest discover -s tests -v` from this directory to check
legacy settings compatibility, profile updates, unrelated provider/plugin
preservation, repeatability and explicit default-provider selection.
The historical `linux-nvidia/` snapshot retains its previous Harness version.
