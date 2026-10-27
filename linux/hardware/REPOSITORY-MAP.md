# Local LLM repository map — October 25, 2026

| Repository | Visibility | Ownership |
|---|---|---|
| [windows-llm-nvidia](https://github.com/Biegle-W/windows-llm-nvidia) | Private | Windows NVIDIA operational source |
| [windows-llm-nvidia-public](https://github.com/Biegle-W/windows-llm-nvidia-public) | Public | Reviewed Windows examples and measurements |
| [linux-llm-nvidia](https://github.com/Biegle-W/linux-llm-nvidia) | Private | Native Linux NVIDIA operational source and migration |
| [linux-llm-nvidia-public](https://github.com/Biegle-W/linux-llm-nvidia-public) | Public | Reviewed native Linux NVIDIA reference |
| [linux-llm-amd](https://github.com/Biegle-W/linux-llm-amd) | Private | Existing dual-RX-7900-XTX Linux operation |
| [linux-llm-amd-public](https://github.com/Biegle-W/linux-llm-amd-public) | Public | Reviewed AMD Linux source and measurements |
| [retired-llm-setting](https://github.com/Biegle-W/retired-llm-setting) | Private | Central retired source/settings and provenance |

The AMD pair was renamed from `ubuntu-llm-amd` / `ubuntu-llm-amd-public`, retaining
repository identities and history. Do not create duplicate AMD repositories.
Windows names and installed checkout paths remain unchanged. Update the old AMD
checkout's `origin` URL after pulling; its local directory and publisher paths stay
fixed. Other projects, including the independent Colab project, are outside this
seven-repository hardware family.

Private repositories remain private. Public references are curated trees with
independent history; never merge or push a private branch/history into public.
Retired settings leave current active/public trees only after a hash-verified copy
in the private archive. Older public commits remain in retained public history;
this reorganization does not erase previously published material.

Archive entries record original repository, source commit, path, mode and hashes.
Historical Windows/4070/3060 setups do not become the new Linux NVIDIA baseline.
Keep active benchmark ledgers and required regression fixtures with their engine.
Exclude model weights, binaries/environments, credentials, chats and raw logs from
all seven repositories. Local ignored recovery binaries/backups remain where they
were; central Git archival concerns source/settings, not a weight backup service.

**October27 source-review update:** the NVIDIA Linux repository now records native
installation, per-GPU correctness/unlock, real inference and six selected profiles.
P2P is documented as not enabled. This supersedes the October25 prepared-only status;
it is a read-only documentation observation, not fresh remote-host validation.
See the [gap audit](AMD-NVIDIA-GAP-AUDIT-2026-10-27.md) and
[NVIDIA README](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/main/README.md).
The separate AMD Linux machine's runtime, profiles, guards, mounts and schedules
are unchanged by repository organization. Keep all GitHub-facing prose in English.

## Migration validation

The central archive contains 1,171 hash-verified files with source provenance.
All 375 retained operational configuration payloads checked across Windows and
AMD private/public trees are unchanged. Only the disabled Windows Strata archive
pointer/description was refreshed. New local Markdown links resolve, selected
public changes pass identity/credential checks and modified Python parses.
The Linux NVIDIA helper passes 11 host-only tests, including explicit pair/trio
target selection; real Linux driver/unlock/P2P/inference remains untested.
No models, runtime environments, running services, host mounts or schedules were
changed by the repository migration.
