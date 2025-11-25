#!/usr/bin/env python3
"""
Unit tests for Oh My Zsh manager.
Tests OMZ installation, updates, and theme configuration.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add project root to path
scriptDir = Path(__file__).parent.absolute()
sys.path.insert(0, str(scriptDir.parent.parent))

from common.core.utilities import getProjectRoot
projectRoot = getProjectRoot()

from common.install.setupZsh import OhMyZshManager


class TestOhMyZshManager(unittest.TestCase):
    """Tests for OhMyZshManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = OhMyZshManager(dryRun=True)

    def testInitialization(self):
        """Test OhMyZshManager initialises with correct paths."""
        self.assertTrue(self.manager.dryRun)
        self.assertEqual(self.manager.installPath, Path.home() / ".oh-my-zsh")
        self.assertEqual(self.manager.zshrcPath, Path.home() / ".zshrc")

    @patch('pathlib.Path.exists')
    def testIsInstalledTrue(self, mockExists):
        """Test isInstalled returns True when OMZ directory exists."""
        mockExists.return_value = True

        result = self.manager.isInstalled()

        self.assertTrue(result)

    @patch('pathlib.Path.exists')
    def testIsInstalledFalse(self, mockExists):
        """Test isInstalled returns False when OMZ directory doesn't exist."""
        mockExists.return_value = False

        result = self.manager.isInstalled()

        self.assertFalse(result)

    @patch('pathlib.Path.exists')
    def testInstallAlreadyInstalled(self, mockExists):
        """Test install skips when already installed."""
        mockExists.return_value = True

        result = self.manager.install()

        self.assertTrue(result)

    @patch('pathlib.Path.exists')
    def testInstallDryRun(self, mockExists):
        """Test install in dry-run mode."""
        mockExists.return_value = False

        result = self.manager.install()

        self.assertTrue(result)

    @patch('pathlib.Path.exists')
    def testUpdateNotInstalled(self, mockExists):
        """Test update skips when not installed."""
        mockExists.return_value = False

        result = self.manager.update()

        self.assertTrue(result)  # Non-fatal

    @patch('pathlib.Path.exists')
    def testUpdateDryRun(self, mockExists):
        """Test update in dry-run mode."""
        mockExists.return_value = True

        result = self.manager.update()

        self.assertTrue(result)

    @patch('pathlib.Path.exists')
    def testGetThemeFromConfig(self, mockExists):
        """Test getting theme from config file."""
        mockExists.return_value = False

        result = self.manager.getTheme("/nonexistent/config.json")

        self.assertEqual(result, "agnoster")  # Default theme

    @patch('pathlib.Path.exists')
    def testConfigureThemeDryRun(self, mockExists):
        """Test configuring theme in dry-run mode."""
        mockExists.return_value = True

        result = self.manager.configureTheme("robbyrussell")

        self.assertTrue(result)

    @patch('pathlib.Path.exists')
    def testConfigureThemeZshrcMissing(self, mockExists):
        """Test configuring theme when .zshrc doesn't exist."""
        mockExists.return_value = False

        result = self.manager.configureTheme("agnoster")

        self.assertTrue(result)  # Non-fatal, returns True


if __name__ == "__main__":
    unittest.main()
