#!/usr/bin/env python3
"""
Unit tests for configuration manager.
Tests path resolution and config directory handling.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add project root to path
scriptDir = Path(__file__).parent.absolute()
sys.path.insert(0, str(scriptDir.parent.parent))

from common.core.utilities import getProjectRoot
projectRoot = getProjectRoot()

from common.systems.configManager import ConfigManager
from common.install.setupArgs import SetupArgs


class TestConfigManager(unittest.TestCase):
    """Tests for ConfigManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.setupArgs = SetupArgs()
        self.manager = ConfigManager(
            projectRoot=projectRoot,
            platformName="ubuntu",
            configFileName="ubuntu.json",
            fontInstallDir=str(Path.home() / ".local/share/fonts"),
            cursorSettingsPath=str(Path.home() / ".config/Cursor/User/settings.json"),
            setupArgs=self.setupArgs,
        )

    def testGetPathsDefault(self):
        """Test getPaths returns all required paths."""
        paths = self.manager.getPaths()

        self.assertIn("gitConfigPath", paths)
        self.assertIn("cursorConfigPath", paths)
        self.assertIn("platformConfigPath", paths)
        self.assertIn("fontsConfigPath", paths)
        self.assertIn("reposConfigPath", paths)
        self.assertIn("androidConfigPath", paths)

    def testGetPathsContainsCorrectPlatform(self):
        """Test that platform config path includes platform name."""
        paths = self.manager.getPaths()

        self.assertIn("ubuntu.json", paths["platformConfigPath"])

    @patch.dict(os.environ, {'JRL_ENV_CONFIG_DIR': '/custom/configs'})
    def testGetConfigsDirFromEnvVar(self):
        """Test getting config directory from env var."""
        manager = ConfigManager(
            projectRoot=projectRoot,
            platformName="ubuntu",
            configFileName="ubuntu.json",
            fontInstallDir="/tmp/fonts",
            cursorSettingsPath="/tmp/settings.json",
            setupArgs=SetupArgs(),
        )

        configsDir = manager.getConfigsDir()

        self.assertEqual(str(configsDir), '/custom/configs')

    def testGetConfigsDirFromSetupArgs(self):
        """Test getting config directory from setupArgs."""
        setupArgs = SetupArgs(configDir="/args/configs")
        manager = ConfigManager(
            projectRoot=projectRoot,
            platformName="ubuntu",
            configFileName="ubuntu.json",
            fontInstallDir="/tmp/fonts",
            cursorSettingsPath="/tmp/settings.json",
            setupArgs=setupArgs,
        )

        configsDir = manager.getConfigsDir()

        self.assertEqual(str(configsDir), '/args/configs')

    def testGetConfigsDirDefault(self):
        """Test default config directory."""
        configsDir = self.manager.getConfigsDir()

        self.assertIn("configs", str(configsDir))


if __name__ == "__main__":
    unittest.main()
