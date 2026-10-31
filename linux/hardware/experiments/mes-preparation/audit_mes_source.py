#!/usr/bin/env python3
"""Inspect six MES source files and dry-run a patch. Never build or install."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

FILES = (
    "drivers/gpu/drm/amd/amdgpu/amdgpu_mes.c",
    "drivers/gpu/drm/amd/amdgpu/amdgpu_mes.h",
    "drivers/gpu/drm/amd/amdgpu/mes_userqueue.c",
    "drivers/gpu/drm/amd/amdgpu/mes_v11_0.c",
    "drivers/gpu/drm/amd/amdkfd/kfd_device_queue_manager.c",
    "drivers/gpu/drm/amd/amdkfd/kfd_device_queue_manager.h",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(source, patch):
    source, patch = source.resolve(), patch.resolve()
    data = patch.read_bytes()
    if len(data) > 128 * 1024:
        raise ValueError("Unexpected patch size")
    text = data.decode("utf-8")
    old = re.findall(r"^--- a/([^\t\n]+)(?:\t[^\n]*)?$", text, re.M)
    new = re.findall(r"^\+\+\+ b/([^\t\n]+)(?:\t[^\n]*)?$", text, re.M)
    headers = [x for x in text.splitlines() if x.startswith(("--- ", "+++ "))]
    if (tuple(old) != FILES or tuple(new) != FILES or len(headers) != 12
            or re.search(r"^(?:Index:|diff |GIT binary patch)", text, re.M)):
        raise ValueError("Expected only the six reviewed MES file pairs, in order")
    before = {f: digest(source / f) for f in FILES}
    content = {f: (source / f).read_text() for f in FILES}
    checks = {}
    for mode in ("forward", "reverse"):
        proc = subprocess.run(
            ["patch", "--dry-run", "--force", "--fuzz=0", "--" + mode,
             "-p1", "-i", str(patch)],
            cwd=source, text=True, capture_output=True, timeout=30,
        )
        checks[mode] = {"returncode": proc.returncode,
                        "details": (proc.stdout + proc.stderr).splitlines()}
    if before != {f: digest(source / f) for f in FILES}:
        raise RuntimeError("Source changed during the read-only audit")
    mes, header, userq, v11, kfd, kfd_header = (content[f] for f in FILES)
    features = {
        "notify_api": "int amdgpu_mes_notify_unmap_queue(" in mes,
        "userq_timer": "userq_notify_unmap_work_handler" in mes,
        "userq_map_hook": "amdgpu_mes_userq_queue_mapped(adev);" in userq,
        "userq_unmap_hook": "amdgpu_mes_userq_queue_unmapped(adev);" in userq,
        "firmware_version_gate": bool(re.search(
            r"case MES_MISC_OP_NOTIFY_WORK_ON_UNMAPPED_QUEUE:\s*"
            r"if \(.*?< 0x70\)", v11, re.S)),
        "sriov_keeps_firmware_timer": bool(re.search(
            r"if \(amdgpu_sriov_vf\(adev\)\)\s*"
            r"mes_set_hw_res_pkt\.oversubscription_timer = 50;", v11)),
        "kfd_timer": "static void mes_notify_unmap_work_handler(" in kfd,
        "kfd_work_member": "struct delayed_work\tnotify_unmap_work;" in kfd_header,
        "mes_work_member": "struct delayed_work" in header and
                           "userq_notify_unmap_work;" in header,
        "microsecond_conversion": all("usecs_to_jiffies(" in s for s in (mes, kfd)),
        "userq_reset_guard": bool(re.search(
            r"down_read_trylock\(&adev->reset_domain->sem\)\)\s*\{\s*"
            r"amdgpu_mes_notify_unmap_queue\(adev\);", mes)),
    }
    forward, reverse = (checks[k]["returncode"] == 0 for k in ("forward", "reverse"))
    status = ("clean_source_candidate" if forward and not reverse else
              "patch_present" if reverse and not forward else "needs_review")
    return {"schema": 1, "status": status, "patch_sha256": digest(patch),
            "source_sha256": before, "features": features, "dry_run": checks,
            "source_unchanged": True, "compiled": False, "installed": False,
            "GPU_work_submitted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit(args.source, args.patch)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        parser.exit(2, str(exc) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] != "needs_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
