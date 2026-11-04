"""Regression cases for stock-default trial staging and built-in root/display drivers."""
import unittest
from kernel_initrd_validation import install_action, validate_initrd_listing

K = '7.0.14-test'
BASE = 'usr/lib/modules/' + K
LISTING = '\n'.join(['init', BASE, BASE + '/kernel/drivers/nvme/host/nvme.ko',
                     BASE + '/kernel/drivers/nvme/host/nvme-core.ko'])
CONFIG = '\n'.join(['CONFIG_BLK_DEV_NVME=m', 'CONFIG_NVME_CORE=m',
                    'CONFIG_EXT4_FS=y', 'CONFIG_DRM_SIMPLEDRM=y', 'CONFIG_DRM_AMDGPU=m'])


class InitrdValidation(unittest.TestCase):
    def test_bootable_builtin_display_and_filesystem_with_gpu_on_root(self):
        result = validate_initrd_listing(LISTING, K, CONFIG)
        self.assertTrue(result['ext4_builtin'])
        self.assertTrue(result['simpledrm_builtin'])
        self.assertFalse(result['amdgpu_in_initrd'])

    def test_wrong_kernel_archive_rejected(self):
        with self.assertRaisesRegex(ValueError, 'release mismatch'):
            validate_initrd_listing(LISTING.replace(K, '7.0.0-old'), K, CONFIG)

    def test_each_boot_critical_component_is_required(self):
        for missing in ['init', BASE + '/kernel/drivers/nvme/host/nvme.ko',
                        BASE + '/kernel/drivers/nvme/host/nvme-core.ko']:
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                validate_initrd_listing('\n'.join(x for x in LISTING.splitlines() if x != missing), K, CONFIG)

    def test_modular_ext4_must_be_present(self):
        cfg = CONFIG.replace('CONFIG_EXT4_FS=y', 'CONFIG_EXT4_FS=m')
        with self.assertRaisesRegex(ValueError, 'ext4.ko'):
            validate_initrd_listing(LISTING, K, cfg)
        validate_initrd_listing(LISTING + '\n' + BASE + '/kernel/fs/ext4/ext4.ko.zst', K, cfg)

    def test_compressed_modules_and_lib_layout(self):
        listing = LISTING.replace('usr/lib/', './lib/').replace('.ko', '.ko.zst')
        validate_initrd_listing(listing, K, CONFIG)

    def test_partial_install_only_resumes_verification(self):
        self.assertEqual(install_action(None), 'stage')
        for phase in ('staging', 'staged-not-booted', 'one-shot-armed'):
            self.assertEqual(install_action(phase), 'verify-stage')
        for phase in ('reboot-scheduled', 'failed', 'unknown'):
            with self.subTest(phase=phase), self.assertRaises(ValueError):
                install_action(phase)


if __name__ == '__main__':
    unittest.main()
