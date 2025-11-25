#!/usr/bin/env python3
"""
Unit tests for package manager implementations.
Tests all package managers and the DRY helper function.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Add project root to path
scriptDir = Path(__file__).parent.absolute()
sys.path.insert(0, str(scriptDir.parent.parent))

from common.core.utilities import getProjectRoot
projectRoot = getProjectRoot()

from common.install.packageManagers import (
    PackageManager,
    AptPackageManager,
    SnapPackageManager,
    BrewPackageManager,
    BrewCaskPackageManager,
    WingetPackageManager,
    ChocolateyPackageManager,
    VcpkgPackageManager,
    StorePackageManager,
    DnfPackageManager,
    ZypperPackageManager,
    PacmanPackageManager,
    runPackageCommand,
)


class TestRunPackageCommand(unittest.TestCase):
    """Tests for runPackageCommand DRY helper."""

    @patch('subprocess.run')
    def testRunPackageCommandSuccess(self, mockRun):
        """Test runPackageCommand with successful command."""
        mockRun.return_value = MagicMock(returncode=0)

        result = runPackageCommand(["test", "command"], "testpkg", "install")

        self.assertTrue(result)
        mockRun.assert_called_once()

    @patch('subprocess.run')
    def testRunPackageCommandFailureWithCheck(self, mockRun):
        """Test runPackageCommand with failing command (raiseOnError=True)."""
        mockRun.side_effect = subprocess.CalledProcessError(1, ["test"], stderr="error")

        result = runPackageCommand(["test", "command"], "testpkg", "install", raiseOnError=True)

        self.assertFalse(result)

    @patch('subprocess.run')
    def testRunPackageCommandFailureWithoutCheck(self, mockRun):
        """Test runPackageCommand with failing command (raiseOnError=False)."""
        mockRun.return_value = MagicMock(returncode=1, stderr="error")

        result = runPackageCommand(["test", "command"], "testpkg", "install", raiseOnError=False)

        self.assertFalse(result)


class TestAptPackageManager(unittest.TestCase):
    """Tests for APT package manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = AptPackageManager()

    @patch('subprocess.run')
    def testCheckInstalled(self, mockRun):
        """Test checking if package is installed."""
        mockRun.return_value = MagicMock(returncode=0)

        result = self.manager.check("git")

        self.assertTrue(result)

    @patch('subprocess.run')
    def testCheckNotInstalled(self, mockRun):
        """Test checking package not installed."""
        mockRun.return_value = MagicMock(returncode=1)

        result = self.manager.check("nonexistent")

        self.assertFalse(result)

    @patch('common.install.packageManagers.runPackageCommand')
    def testInstall(self, mockRunCommand):
        """Test installing package."""
        mockRunCommand.return_value = True

        result = self.manager.install("git")

        self.assertTrue(result)
        mockRunCommand.assert_called_once()
        args = mockRunCommand.call_args[0]
        self.assertIn("apt-get", args[0])
        self.assertIn("install", args[0])

    @patch('common.install.packageManagers.runPackageCommand')
    def testUpdate(self, mockRunCommand):
        """Test updating package."""
        mockRunCommand.return_value = True

        result = self.manager.update("git")

        self.assertTrue(result)

    @patch('subprocess.run')
    def testUpdateAllDryRun(self, mockRun):
        """Test updateAll in dry-run mode."""
        result = self.manager.updateAll(dryRun=True)

        self.assertTrue(result)
        mockRun.assert_not_called()


class TestBrewPackageManager(unittest.TestCase):
    """Tests for Homebrew package manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = BrewPackageManager()

    @patch('subprocess.run')
    def testCheck(self, mockRun):
        """Test checking if brew package is installed."""
        mockRun.return_value = MagicMock(returncode=0)

        result = self.manager.check("git")

        self.assertTrue(result)
        args = mockRun.call_args[0][0]
        self.assertIn("brew", args)
        self.assertIn("list", args)


class TestWingetPackageManager(unittest.TestCase):
    """Tests for Winget package manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = WingetPackageManager()

    @patch('common.common.isAppInstalled')
    def testCheck(self, mockIsInstalled):
        """Test checking if winget package is installed."""
        mockIsInstalled.return_value = True

        result = self.manager.check("Git.Git")

        self.assertTrue(result)

    @patch('common.install.packageManagers.runPackageCommand')
    def testInstall(self, mockRunCommand):
        """Test installing winget package."""
        mockRunCommand.return_value = True

        result = self.manager.install("Git.Git")

        self.assertTrue(result)
        args = mockRunCommand.call_args[0][0]
        self.assertIn("winget", args)
        self.assertIn("install", args)


class TestChocolateyPackageManager(unittest.TestCase):
    """Tests for Chocolatey package manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = ChocolateyPackageManager()

    @patch('subprocess.run')
    def testCheck(self, mockRun):
        """Test checking if chocolatey package is installed."""
        mockRun.return_value = MagicMock(returncode=0, stdout="git 1.0.0")

        result = self.manager.check("git")

        self.assertTrue(result)

    @patch('common.install.packageManagers.runPackageCommand')
    def testInstall(self, mockRunCommand):
        """Test installing chocolatey package."""
        mockRunCommand.return_value = True

        result = self.manager.install("git")

        self.assertTrue(result)


class TestVcpkgPackageManager(unittest.TestCase):
    """Tests for vcpkg package manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = VcpkgPackageManager()

    @patch('subprocess.run')
    def testCheck(self, mockRun):
        """Test checking if vcpkg package is installed."""
        mockRun.return_value = MagicMock(returncode=0, stdout="boost:x64-windows")

        result = self.manager.check("boost")

        self.assertTrue(result)

    @patch('common.install.packageManagers.runPackageCommand')
    def testInstall(self, mockRunCommand):
        """Test installing vcpkg package."""
        mockRunCommand.return_value = True

        result = self.manager.install("boost")

        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
