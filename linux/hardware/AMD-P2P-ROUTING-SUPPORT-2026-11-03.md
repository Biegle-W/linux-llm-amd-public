# AMD PEX88096 routing support — November 3, 2026

**Current state: HIP peer capability is available both ways, but ACS controls need correction before full qualification.** The first owner-controlled reboot applied the scoped parameter. A fresh guarded diagnostic reports peer access true in both directions under default HIP, fine grain, and fine grain with SDMA disabled. Both owned diagnostic processes and reservations were cleaned up; no data-buffer, direct-kernel, IPC or RCCL test has yet qualified this boot.

The privileged register audit found **0x00 on all six downstream bridges**, rather than the intended 0x11. The initial `xxx00xx` flags preserved firmware defaults; those defaults were zero, unlike Linux's earlier 0x1d controls. The revised flags **`xx100x1`** explicitly enable Source Validation and Upstream Forwarding and disable Request/Completion Redirect. The resulting controlled mask is 0x1d, with desired value 0x11. Other bits retain firmware defaults. This corrects the installer's initial assumption; it is not a successful final P2P result.

The helper selects exactly four Broadcom PEX880xx downstream bridges plus exactly one AMD 1479 downstream parent directly above each of the two Navi31 GPUs. CPU roots, endpoints, other bridges and unrelated paths are excluded. Hierarchical path selectors tolerate bus renumbering. No vendor-wide ACS override or IOMMU-mode change is used. The current GPU domains remain translated. Linux already supplies the pcieport driver; no NVIDIA or replacement AMD driver is installed.

The revised install action can transactionally replace its own previous configuration only when the managed marker, saved state and SHA256 match. The zero-control exception is admitted only for that authenticated prior xxx00xx policy. Unknown controls/policies still refuse installation. On generation/validation failure, prior drop-in, state and GRUB files are restored. Root-private backups are retained. No live PCI write, driver reset or automatic reboot occurs.

From the operational checkout, run with administrator authentication:

```bash
sudo python3 hardware/amd_p2p_support.py install
```

After successful corrected staging and owner-controlled reboot:

```bash
sudo python3 hardware/amd_p2p_support.py verify
```

Verification now requires the active staged parameter and **exact ACS 0x11 on all six ports**, rather than only clear redirect bits. Only then continue guarded peer enable, direct read/write integrity, HIP IPC and bounded RCCL qualification. Production host fallback, RAM holds, guards and updater pause remain unchanged.

Rollback removes the managed next-boot policy and validates regenerated GRUB:

```bash
sudo python3 hardware/amd_p2p_support.py rollback
```

**31 CPU checks pass per checkout**, including the actual zero-firmware flag regression, authenticated previous-policy upgrade and full rollback after failed upgrade, plus topology/capability admission and GRUB token quoting. Corrected administrator staging succeeded; drop-in SHA256, root ownership and mode 0644 are verified. Corrected reboot remains pending. No new inference/model-speed result exists.

Sources: [Linux kernel parameters](https://www.kernel.org/doc/html/v7.0/admin-guide/kernel-parameters.html), [PCI ACS implementation and firmware-control semantics](https://github.com/torvalds/linux/blob/v7.0/drivers/pci/pci.c). [Curated state](results/amd-p2p-routing-support-2026-11-03.json).

## Corrected-boot data checks and identity-domain trial

The next owner reboot loaded the corrected xx100x1 parameter; the kernel logs ACS 0x11 on all six intended ports. Fresh HIP capability is true both ways in all three environments. However, a bounded 16 MiB GPU-kernel remote-read test returned incorrect data in each direction (first mismatch at element 1). A separate local-kernel baseline passed three deterministic patterns on each GPU, and the fine-grain/no-SDMA peer variant still failed. No passing direct-write, IPC or RCCL result is claimed; those stages remain gated on correct remote reads. Failed results are retained. All owned test processes exited and reservations were released; sampled owned swap/spill were zero and no new kernel fault/reset was found.

The active GPU IOMMU domains are translated, unlike the working NVIDIA reference's identity domains. The prepared **install-identity** action retains the exact six-path ACS policy and adds only `iommu=pt` to normal/recovery Ubuntu entries. This keeps IOMMU support enabled but changes the default host DMA domains to identity. It is a controlled causal trial, not a proven fix. It refuses conflicting explicit IOMMU options and requires authenticated managed ACS state; boot generation is validated and changes remain owner-reboot controlled.

```bash
sudo python3 hardware/amd_p2p_support.py install-identity
```

After reboot, verify requires both exact ACS 0x11 and identity GPU domains before repeating guarded direct-memory checks. To revert only the identity trial while retaining the prior ACS-only configuration:

```bash
sudo python3 hardware/amd_p2p_support.py rollback-trial
```

The prior drop-in/state are retained with hash verification; failed staging or rollback restores the configuration it started with. **31 CPU tests pass per checkout**, including identity token staging, conflicting-option refusal and restoring the ACS-only policy. The identity trial remains unstaged until administrator execution; production host transport, RAM holds and paused updater remain.
