import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

s = importlib.util.spec_from_file_location('disable', Path(__file__).with_name('amd_p2p_disable.py'))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.config, self.grub = root/'dropin', root/'grub'
        self.state = root/'state'/'state.json'
        self.rc, self.rs = root/'routing.cfg', root/'routing.json'
        self.original = "linux /boot/vmlinuz-7 root=UUID=test 'pci=config_acs=xx100x1@0000:00:01.0/00.0' iommu=pt quiet splash\n"
        self.param = 'pci=config_acs=xx100x1@0000:00:01.0/00.0'
        self.routing = ("# Managed local-llm AMD PEX peer routing; no live PCI writes.\n"
                        "GRUB_CMDLINE_LINUX=\"${GRUB_CMDLINE_LINUX} '"+self.param+"'\"\n"
                        'GRUB_CMDLINE_LINUX="${GRUB_CMDLINE_LINUX} iommu=pt"\n').encode()
        self.rc.write_bytes(self.routing)
        self.rs.write_text(json.dumps({'parameter': self.param, 'IOMMU_policy_changed': True,
            'dropin_sha256': hashlib.sha256(self.routing).hexdigest()}))
        self.grub.write_text(self.original)

    def generated(self, cmd, check):
        if cmd[0] == 'update-grub':
            self.grub.write_text(self.original if not self.config.exists() else
                'linux /boot/vmlinuz-7 root=UUID=test amdgpu.pcie_p2p=0 amdgpu.use_xgmi_p2p=0 quiet splash\n')

    def stage(self, run=None):
        return m.stage(self.config, self.state, self.grub, run or self.generated,
                       self.rc, self.rs, sources=[self.rc])

    def rollback(self, run=None):
        return m.rollback(self.config, self.state, self.grub, run or self.generated, self.rc, self.rs)

    def test_stage_and_rollback_preserve_routing_and_boot(self):
        oldstate = self.rs.read_bytes()
        d = self.stage()
        self.assertEqual(d['removed_managed_routing_arguments'], [self.param, 'iommu=pt'])
        self.assertFalse(self.rc.exists())
        self.assertFalse(self.rs.exists())
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o644)
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o600)
        self.rollback()
        self.assertEqual(self.rc.read_bytes(), self.routing)
        self.assertEqual(self.rs.read_bytes(), oldstate)
        self.assertEqual(self.grub.read_text(), self.original)

    def test_install_generation_failure_restores_all_preimages(self):
        def bad(cmd, check):
            self.grub.write_text('broken')
            raise subprocess.CalledProcessError(1, cmd)
        with self.assertRaises(subprocess.CalledProcessError):
            self.stage(bad)
        self.assertEqual(self.rc.read_bytes(), self.routing)
        self.assertEqual(self.grub.read_text(), self.original)
        self.assertFalse(self.config.exists())
        self.assertFalse(self.state.exists())

    def test_validator_failure_restores_all_preimages(self):
        def bad(cmd, check):
            if cmd[0] == 'update-grub':
                self.grub.write_text('linux /boot/vmlinuz-7 root=UUID=WRONG amdgpu.pcie_p2p=0 amdgpu.use_xgmi_p2p=0 quiet splash\n')
        with self.assertRaises(RuntimeError):
            self.stage(bad)
        self.assertEqual(self.rc.read_bytes(), self.routing)
        self.assertEqual(self.grub.read_text(), self.original)

    def test_changed_routing_refused_before_writes(self):
        self.rc.write_bytes(self.routing + b'# changed\n')
        with self.assertRaises(RuntimeError):
            self.stage()
        self.assertFalse(self.config.exists())
        self.assertEqual(self.grub.read_text(), self.original)

    def test_existing_disable_refused(self):
        self.stage()
        with self.assertRaises(RuntimeError):
            self.stage()

    def test_failed_rollback_preserves_staged_configuration(self):
        self.stage()
        before = self.grub.read_bytes()
        def bad(cmd, check):
            raise subprocess.CalledProcessError(1, cmd)
        with self.assertRaises(subprocess.CalledProcessError):
            self.rollback(bad)
        self.assertEqual(self.config.read_bytes(), m.BODY)
        self.assertEqual(self.grub.read_bytes(), before)
        self.assertFalse(self.rc.exists())
        self.assertTrue(self.state.exists())

    def test_changed_disable_refuses_rollback(self):
        self.stage()
        self.config.write_bytes(m.BODY+b'# modified\n')
        with self.assertRaises(RuntimeError):
            self.rollback()

    def test_partial_options_and_entry_loss_refused(self):
        for after in ['linux /boot/vmlinuz-7 root=UUID=test quiet splash\n',
                      'linux /boot/vmlinuz-7 root=UUID=test amdgpu.pcie_p2p=0 quiet splash\n',
                      'linux /boot/vmlinuz-7 root=UUID=test amdgpu.pcie_p2p=0 amdgpu.pcie_p2p=0 amdgpu.use_xgmi_p2p=0 quiet splash\n']:
            with self.assertRaises(RuntimeError):
                m.validate_generated(self.original, after, routing_args=[self.param, 'iommu=pt'])
        with self.assertRaises(RuntimeError):
            m.validate_generated(self.original*2, self.original)

    def test_dropin_shell_syntax(self):
        self.config.write_bytes(m.BODY)
        value = subprocess.check_output(['sh', '-c',
            'GRUB_CMDLINE_LINUX="existing"; . "$1"; printf "%s" "$GRUB_CMDLINE_LINUX"',
            'sh', str(self.config)], text=True)
        self.assertEqual(value.split(), ['existing', *m.PARAMS])


if __name__ == '__main__':
    unittest.main()
