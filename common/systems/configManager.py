#!/usr/bin/env python3
"""
Configuration path management for jrl_env setup.
Handles config directory resolution, path generation, and environment variable parsing.
"""

import os
from pathlib import Path
from typing import Dict, Optional

from common.install.setupArgs import SetupArgs


class ConfigManager:
    """
    Manages configuration paths and directory resolution.
    Centralises all config path logic in one place.
    """

    def __init__(
        self,
        projectRoot: Path,
        platformName: str,
        configFileName: str,
        fontInstallDir: str,
        cursorSettingsPath: str,
        setupArgs: Optional[SetupArgs] = None,
    ):
        """
        Initialise the config manager.

        Args:
            projectRoot: Root directory of jrl_env project
            platformName: Platform name (e.g., "macos", "ubuntu")
            configFileName: Platform config filename (e.g., "macos.json")
            fontInstallDir: Directory where fonts should be installed
            cursorSettingsPath: Path to Cursor settings file
            setupArgs: Optional setup arguments (for custom config dir)
        """
        self.projectRoot = projectRoot
        self.platformName = platformName
        self.configFileName = configFileName
        self.fontInstallDir = fontInstallDir
        self.cursorSettingsPath = cursorSettingsPath
        self.setupArgs = setupArgs
        self._configsDir: Optional[Path] = None

    def getConfigsDir(self) -> Path:
        """
        Get the configs directory, checking custom paths and environment variables.

        Returns:
            Path to configs directory

        Priority:
            1. setupArgs.configDir (command-line --configDir)
            2. JRL_ENV_CONFIG_DIR environment variable
            3. Default: projectRoot/configs
        """
        if self._configsDir:
            return self._configsDir

        # Check setupArgs first
        if self.setupArgs and self.setupArgs.configDir:
            self._configsDir = Path(self.setupArgs.configDir)
            return self._configsDir

        # Check environment variable
        envConfigDir = os.environ.get("JRL_ENV_CONFIG_DIR")
        if envConfigDir:
            self._configsDir = Path(envConfigDir)
            return self._configsDir

        # Default to project configs directory
        self._configsDir = self.projectRoot / "configs"
        return self._configsDir

    def getPaths(self) -> Dict[str, str]:
        """
        Get all configuration and installation paths.

        Returns:
            Dictionary with path keys:
                - gitConfigPath: Path to gitConfig.json
                - cursorConfigPath: Path to cursorSettings.json
                - cursorSettingsPath: Path to Cursor User settings.json
                - fontsConfigPath: Path to fonts.json
                - fontInstallDir: Directory to install fonts
                - reposConfigPath: Path to repositories.json
                - androidConfigPath: Path to android.json
                - platformConfigPath: Path to platform-specific config (e.g., macos.json)
        """
        configsDir = self.getConfigsDir()

        return {
            "gitConfigPath": str(configsDir / "gitConfig.json"),
            "cursorConfigPath": str(configsDir / "cursorSettings.json"),
            "cursorSettingsPath": self.cursorSettingsPath,
            "fontsConfigPath": str(configsDir / "fonts.json"),
            "fontInstallDir": self.fontInstallDir,
            "reposConfigPath": str(configsDir / "repositories.json"),
            "androidConfigPath": str(configsDir / "android.json"),
            "platformConfigPath": str(configsDir / self.configFileName),
        }

    def validateConfigDirectory(self) -> bool:
        """
        Validate that config directory exists and is accessible.

        Returns:
            True if valid, False otherwise
        """
        configsDir = self.getConfigsDir()

        if not configsDir.exists():
            return False

        if not configsDir.is_dir():
            return False

        return True

    def updateSetupArgs(self, setupArgs: SetupArgs) -> None:
        """
        Update setup args (useful when they're set after initialization).

        Args:
            setupArgs: New setup arguments
        """
        self.setupArgs = setupArgs
        self._configsDir = None  # Clear cache to recompute with new args
