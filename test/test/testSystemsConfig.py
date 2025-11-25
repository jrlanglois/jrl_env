#!/usr/bin/env python3
"""
Unit tests for system configuration.
Tests platform config data structures.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
scriptDir = Path(__file__).parent.absolute()
sys.path.insert(0, str(scriptDir.parent.parent))


from common.core.utilities import getProjectRoot
projectRoot = getProjectRoot()

from common.systems.systemsConfig import getSystemConfig
from common.systems.platform import Platform


class TestSystemsConfig(unittest.TestCase):
    """Tests for system configuration retrieval."""

    def testGetSystemConfigMacOs(self):
        """Test getting macOS system config."""
        config = getSystemConfig("macos")

        self.assertIsNotNone(config)
        self.assertEqual(config.platformName, "macos")
        self.assertEqual(config.primaryPackageManager, "brew")

    def testGetSystemConfigWindows(self):
        """Test getting Windows system config."""
        config = getSystemConfig("win11")

        self.assertIsNotNone(config)
        self.assertEqual(config.platformName, "win11")
        self.assertEqual(config.primaryPackageManager, "winget")

    def testGetSystemConfigUbuntu(self):
        """Test getting Ubuntu system config."""
        config = getSystemConfig("ubuntu")

        self.assertIsNotNone(config)
        self.assertEqual(config.platformName, "ubuntu")
        self.assertEqual(config.primaryPackageManager, "apt")

    def testGetSystemConfigRedhat(self):
        """Test getting RedHat system config."""
        config = getSystemConfig("redhat")

        self.assertIsNotNone(config)
        self.assertEqual(config.primaryPackageManager, "dnf")

    def testGetSystemConfigArchLinux(self):
        """Test getting Arch Linux system config."""
        config = getSystemConfig("archlinux")

        self.assertIsNotNone(config)
        self.assertEqual(config.primaryPackageManager, "pacman")

    def testGetSystemConfigInvalid(self):
        """Test that invalid platform returns None."""
        config = getSystemConfig("invalidplatform")

        self.assertIsNone(config)

    def testAllMajorPlatformsHaveConfig(self):
        """Test that major platforms have configs."""
        # Test platforms that have explicit configs in systemsConfig
        majorPlatforms = [
            "macos", "win11",
            "ubuntu", "raspberrypi",
            "redhat",
            "opensuse",
            "archlinux",
        ]

        for platform in majorPlatforms:
            config = getSystemConfig(platform)
            self.assertIsNotNone(config, f"{platform} should have a config")


if __name__ == "__main__":
    unittest.main()
