# Linux LAN and Tailscale client access

The [consolidated handoff](LINUX-LLM-RUNTIME-HANDOFF.md) is the single current
reference for Linux-host access, Windows/phone clients, exact model IDs,
contexts, storage, runtime pins, backend launching and troubleshooting.
It replaces the separate Shared client, Windows-network and upgrade guides;
the original nine files are preserved in the dated Shared archive described there.

The authenticated gateway uses TCP **10000** and OpenAI-compatible chat and
completion APIs. Request any of the **12 enabled profiles** from `/v1/models`;
the loopback model hub starts or switches its backend through the guarded launcher.
Catalog/health reads do not start a model. Existing explicit Desktop/CLI launches
remain supported.

The [router admission report](../hardware/ROUTER-ADMISSION-2026-10-28.md) describes
validated FIFO admission, pending count/body bounds, consistent health and preserved
HTTP/SSE errors. New source is installed; production coordinators retain their prior
in-memory code until an authorized idle restart. Native capacity, access policy,
worker ownership and 600-second inference-aware idle release remain unchanged.

Credentials and live addresses stay in ignored `dsh/data/` configuration.
Public documentation uses example paths and addresses. Never place an actual
API key in a handoff, source file or chat. Obtain exact IDs and coordinator state
from authenticated `/v1/models` and `/health`.

`python3 -B network/check.py` validates authentication, health, enabled IDs and
contexts, and retired-Q2 rejection without loading a model. It derives the
catalog from local configuration; `--output PATH` optionally saves a report.
`--generate` is the additional Strata Q3 SDK streaming/tool test and requires
that backend. Maya's separate normal-launcher proofs cover both selected models.

Earlier October 20 authentication/catalog checks passed for the then-thirteen profiles on
loopback/LAN/Tailscale host-self routes. Maya generation, JSON, tool round trips
and model switching passed there too; a separate remote client was not tested.
The Maya addition refreshed only the gateway; credentials and access controls
are unchanged. See the canonical handoff and [Maya report](../hardware/MAYA-2026-10-20.md).
