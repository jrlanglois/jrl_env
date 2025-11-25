#!/usr/bin/env python3
"""
Unit tests for platform implementations.
Tests platform hierarchy, package manager integration, and update logic.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
scriptDir = Path(__file__).parent.absolute()
sys.path.insert(0, str(scriptDir.parent.parent))


from common.core.utilities import getProjectRoot
projectRoot = getProjectRoot()

from common.systems.platforms import (
    BasePlatform,
    MacOsPlatform,
    WindowsPlatform,
    UbuntuPlatform,
    FedoraPlatform,
    ArchLinuxPlatform,
    AlpinePlatform,
    createPlatform,
)


class TestPlatformFactory(unittest.TestCase):
    """Tests for createPlatform factory function."""

    def testCreateMacOsPlatform(self):
        """Test creating MacOsPlatform."""
        platform = createPlatform("macos", Path.cwd(), dryRun=True)
        self.assertIsInstance(platform, MacOsPlatform)
        self.assertEqual(platform.getPlatformName(), "macos")
        self.assertTrue(platform.dryRun)

    def testCreateWindowsPlatform(self):
        """Test creating WindowsPlatform."""
        platform = createPlatform("win11", Path.cwd(), dryRun=True)
        self.assertIsInstance(platform, WindowsPlatform)
        self.assertEqual(platform.getPlatformName(), "win11")

    def testCreateUbuntuPlatform(self):
        """Test creating UbuntuPlatform."""
        platform = createPlatform("ubuntu", Path.cwd(), dryRun=True)
        self.assertIsInstance(platform, UbuntuPlatform)
        self.assertEqual(platform.getPlatformName(), "ubuntu")

    def testCreateFedoraPlatform(self):
        """Test creating FedoraPlatform."""
        platform = createPlatform("fedora", Path.cwd(), dryRun=True)
        self.assertIsInstance(platform, FedoraPlatform)

    def testCreateArchLinuxPlatform(self):
        """Test creating ArchLinuxPlatform."""
        platform = createPlatform("archlinux", Path.cwd(), dryRun=True)
        self.assertIsInstance(platform, ArchLinuxPlatform)

    def testCreateAlpinePlatform(self):
        """Test creating AlpinePlatform."""
        platform = createPlatform("alpine", Path.cwd(), dryRun=True)
        self.assertIsInstance(platform, AlpinePlatform)

    def testCreateInvalidPlatform(self):
        """Test that invalid platform raises ValueError."""
        with self.assertRaises(ValueError):
            createPlatform("invalidplatform", Path.cwd())

    def testAllSupportedPlatforms(self):
        """Test all 17 supported platforms can be created."""
        platforms = [
            "macos", "win11",
            "ubuntu", "debian", "popos", "linuxmint", "elementary", "zorin", "mxlinux", "raspberrypi",
            "fedora", "redhat",
            "opensuse",
            "archlinux", "manjaro", "endeavouros",
            "alpine"
        ]

        for platformName in platforms:
            platform = createPlatform(platformName, Path.cwd(), dryRun=True)
            self.assertIsNotNone(platform)
            self.assertIsInstance(platform, BasePlatform)


class TestMacOsPlatform(unittest.TestCase):
    """Tests for MacOsPlatform."""

    def setUp(self):
        """Set up test fixtures."""
        self.platform = MacOsPlatform(Path.cwd(), dryRun=True)

    def testPlatformName(self):
        """Test platform name is correct."""
        self.assertEqual(self.platform.getPlatformName(), "macos")

    def testHasPackageManagers(self):
        """Test that package managers are initialised."""
        self.assertGreater(len(self.platform.packageManagers), 0)
        self.assertEqual(len(self.platform.packageManagers), 2)  # Brew + BrewCask

    def testHasOmzManager(self):
        """Test that OMZ manager is initialised."""
        self.assertIsNotNone(self.platform.omzManager)

    def testHasAndroidManager(self):
        """Test that Android manager is initialised."""
        self.assertIsNotNone(self.platform.androidManager)

    @patch('common.systems.platforms.commandExists')
    def testUpdateMacAppStoreWithMas(self, mockCommandExists):
        """Test updating Mac App Store when mas is installed."""
        mockCommandExists.return_value = True
        result = self.platform.updateMacAppStore()
        self.assertTrue(result)

    @patch('common.systems.platforms.commandExists')
    def testUpdateMacAppStoreWithoutMas(self, mockCommandExists):
        """Test skipping Mac App Store when mas not installed."""
        mockCommandExists.return_value = False
        result = self.platform.updateMacAppStore()
        self.assertTrue(result)  # Returns True (skip gracefully)

    def testCheckMacOsUpdates(self):
        """Test checking for macOS updates in dry-run."""
        result = self.platform.checkMacOsUpdates()
        self.assertTrue(result)

    def testUpdateSystemDryRun(self):
        """Test updateSystem in dry-run mode."""
        result = self.platform.updateSystem()
        self.assertTrue(result)

    @patch.object(MacOsPlatform, 'updatePackages')
    @patch.object(MacOsPlatform, 'updateSystemWithOmz')
    def testUpdateAll(self, mockUpdateSystem, mockUpdatePackages):
        """Test updateAll orchestrates both updates."""
        mockUpdatePackages.return_value = True
        mockUpdateSystem.return_value = True

        result = self.platform.updateAll()

        self.assertTrue(result)
        mockUpdatePackages.assert_called_once()
        mockUpdateSystem.assert_called_once()


class TestWindowsPlatform(unittest.TestCase):
    """Tests for WindowsPlatform."""

    def setUp(self):
        """Set up test fixtures."""
        self.platform = WindowsPlatform(Path.cwd(), dryRun=True)

    def testPlatformName(self):
        """Test platform name is correct."""
        self.assertEqual(self.platform.getPlatformName(), "win11")

    def testHasPackageManagers(self):
        """Test that package managers are initialised."""
        self.assertGreater(len(self.platform.packageManagers), 0)
        # Choco, vcpkg, Winget, Store
        self.assertEqual(len(self.platform.packageManagers), 4)

    def testUpdateSystemProvidesGuidance(self):
        """Test that Windows updateSystem provides guidance."""
        result = self.platform.updateSystem()
        self.assertTrue(result)


class TestUbuntuPlatform(unittest.TestCase):
    """Tests for UbuntuPlatform."""

    def setUp(self):
        """Set up test fixtures."""
        self.platform = UbuntuPlatform(Path.cwd(), dryRun=True)

    def testPlatformName(self):
        """Test platform name is correct."""
        self.assertEqual(self.platform.getPlatformName(), "ubuntu")

    def testHasPackageManagers(self):
        """Test that package managers are initialised."""
        self.assertGreater(len(self.platform.packageManagers), 0)
        # APT + Snap
        self.assertEqual(len(self.platform.packageManagers), 2)

    def testUpdateSystemReturnsTrue(self):
        """Test that updateSystem returns True (APT handled by package managers)."""
        result = self.platform.updateSystem()
        self.assertTrue(result)


class TestPlatformUpdateLogic(unittest.TestCase):
    """Tests for platform update orchestration logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.platform = MacOsPlatform(Path.cwd(), dryRun=True)

    @patch.object(MacOsPlatform, 'updatePackages')
    @patch.object(MacOsPlatform, 'updateSystem')
    def testUpdateSystemWithOmz(self, mockUpdateSystem, mockUpdatePackages):
        """Test updateSystemWithOmz combines system and OMZ updates."""
        mockUpdateSystem.return_value = True

        # Mock OMZ manager
        self.platform.omzManager = MagicMock()
        self.platform.omzManager.update.return_value = True

        result = self.platform.updateSystemWithOmz()

        self.assertTrue(result)
        mockUpdateSystem.assert_called_once()
        self.platform.omzManager.update.assert_called_once()

    @patch.object(MacOsPlatform, 'updatePackages')
    @patch.object(MacOsPlatform, 'updateSystem')
    def testUpdateSystemWithOmzFailure(self, mockUpdateSystem, mockUpdatePackages):
        """Test updateSystemWithOmz returns False if either fails."""
        mockUpdateSystem.return_value = False

        self.platform.omzManager = MagicMock()
        self.platform.omzManager.update.return_value = True

        result = self.platform.updateSystemWithOmz()

        self.assertFalse(result)  # System update failed

    def testUpdatePackagesWithManagers(self):
        """Test updatePackages iterates through package managers."""
        # Mock package managers
        mockManager1 = MagicMock()
        mockManager1.updateAll.return_value = True
        mockManager2 = MagicMock()
        mockManager2.updateAll.return_value = True

        self.platform.packageManagers = [mockManager1, mockManager2]
        self.platform.androidManager = MagicMock()
        self.platform.androidManager.updateSdk.return_value = True

        result = self.platform.updatePackages()

        self.assertTrue(result)
        mockManager1.updateAll.assert_called_once_with(True)  # dryRun=True
        mockManager2.updateAll.assert_called_once_with(True)
        self.platform.androidManager.updateSdk.assert_called_once()


if __name__ == "__main__":
    unittest.main()
