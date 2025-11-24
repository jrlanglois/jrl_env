#!/usr/bin/env python3
"""
Generic data-driven system implementation.
Uses SystemConfig to provide platform-specific behaviour without code duplication.
"""

import sys
from pathlib import Path
from typing import List

from common.systems.platform import Platform
from common.systems.systemBase import DependencyChecker, SystemBase
from common.systems.systemsConfig import SystemConfig, getSystemConfig


class GenericSystem(SystemBase):
    """
    Generic system implementation driven by SystemConfig data.
    Eliminates the need for per-platform system.py files.
    """

    def __init__(self, projectRoot: Path, platform: Platform):
        """
        Initialise the generic system with a platform configuration.

        Args:
            projectRoot: Root directory of jrl_env project
            platform: Platform enum value
        """
        self.config = getSystemConfig(str(platform))
        if not self.config:
            raise ValueError(f"Unsupported platform: {platformName}")

        super().__init__(projectRoot)

    # ========== Platform-Specific Methods (using config) ==========

    def getPlatformName(self) -> str:
        return self.config.platformName

    def getConfigFileName(self) -> str:
        return self.config.configFileName

    def getFontInstallDir(self) -> str:
        return self.config.fontInstallDir

    def getCursorSettingsPath(self) -> str:
        return self.config.cursorSettingsPath

    def getRepositoryWorkPathKey(self) -> str:
        return self.config.repositoryWorkPathKey

    def getRequiredDependencies(self) -> List[str]:
        return self.config.requiredDependencies

    def getOptionalDependencyCheckers(self) -> List[DependencyChecker]:
        # For Windows, add winget checker if available
        if self.config.platformName == "win11":
            try:
                from common.windows.packageManager import isWingetInstalled
                return [isWingetInstalled]
            except ImportError:
                return []
        return self.config.optionalDependencyCheckers

    def installOrUpdateApps(self, configPath: str, dryRun: bool) -> bool:
        """Install or update applications using configured package managers."""
        # Get package manager instances
        primaryManager = self.getPackageManager(self.config.primaryPackageManager)
        secondaryManager = None
        if self.config.secondaryPackageManager:
            secondaryManager = self.getPackageManager(self.config.secondaryPackageManager)

        # Check if using Linux common packages
        useLinuxCommon = self.config.useLinuxCommon
        if not useLinuxCommon and self.config.primaryPackageManager == "apt":
            # For Ubuntu, check config file for useLinuxCommon flag
            from common.core.utilities import getJsonValue
            useLinuxCommon = getJsonValue(configPath, ".useLinuxCommon", False)

        return self.installAppsWithPackageManagers(
            configPath=configPath,
            dryRun=dryRun,
            primaryExtractor=self.config.primaryExtractor,
            secondaryExtractor=self.config.secondaryExtractor,
            primaryLabel=self.config.primaryLabel,
            secondaryLabel=self.config.secondaryLabel,
            checkPrimary=primaryManager.check,
            installPrimary=primaryManager.install,
            updatePrimary=primaryManager.update,
            checkSecondary=secondaryManager.check if secondaryManager else None,
            installSecondary=secondaryManager.install if secondaryManager else None,
            updateSecondary=secondaryManager.update if secondaryManager else None,
            useLinuxCommon=useLinuxCommon,
        )

    def getPackageManager(self, managerName: str):
        """Get package manager instance by name."""
        if managerName == "brew":
            from common.install.packageManagers import BrewPackageManager
            return BrewPackageManager()
        elif managerName == "brewCask":
            from common.install.packageManagers import BrewCaskPackageManager
            return BrewCaskPackageManager()
        elif managerName == "apt":
            from common.install.packageManagers import AptPackageManager
            return AptPackageManager()
        elif managerName == "snap":
            from common.install.packageManagers import SnapPackageManager
            return SnapPackageManager()
        elif managerName == "pacman":
            from common.install.packageManagers import PacmanPackageManager
            return PacmanPackageManager()
        elif managerName == "zypper":
            from common.install.packageManagers import ZypperPackageManager
            return ZypperPackageManager()
        elif managerName == "dnf":
            from common.install.packageManagers import DnfPackageManager
            return DnfPackageManager()
        elif managerName == "winget":
            from common.install.packageManagers import WingetPackageManager
            return WingetPackageManager()
        else:
            raise ValueError(f"Unknown package manager: {managerName}")


def createSystem(platform: Platform, projectRoot: Path = None) -> GenericSystem:
    """
    Factory function to create a system instance for a platform.

    Args:
        platform: Platform enum value
        projectRoot: Optional project root (defaults to jrl_env root)

    Returns:
        GenericSystem instance configured for the platform
    """
    if projectRoot is None:
        # Try to determine project root from this file's location
        thisFile = Path(__file__).resolve()
        projectRoot = thisFile.parent.parent.parent

    return GenericSystem(projectRoot, platform)


__all__ = [
    "GenericSystem",
    "createSystem",
]
