#!/usr/bin/env python3
"""
Data-driven system configuration definitions.
Centralises platform-specific details for all supported systems.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional


@dataclass
class SystemConfig:
    """Configuration for a specific system platform."""
    platformName: str
    configFileName: str
    fontInstallDir: str
    cursorSettingsPath: str
    repositoryWorkPathKey: str
    requiredDependencies: List[str]
    optionalDependencyCheckers: List[Callable[[], bool]]

    # Package manager configuration
    primaryPackageManager: str  # e.g., "brew", "apt", "dnf"
    primaryExtractor: str  # JSONPath for primary packages
    primaryLabel: str  # Display label for primary packages

    secondaryPackageManager: Optional[str] = None  # e.g., "brewCask", "snap"
    secondaryExtractor: Optional[str] = None
    secondaryLabel: Optional[str] = None

    useLinuxCommon: bool = False  # If True, merge with linuxCommon.json


# System configurations
# This is the single source of truth for platform-specific details
systemsConfig = {
    "macos": SystemConfig(
        platformName="macos",
        configFileName="macos.json",
        fontInstallDir=str(Path.home() / "Library/Fonts"),
        cursorSettingsPath=str(Path.home() / "Library/Application Support/Cursor/User/settings.json"),
        repositoryWorkPathKey=".workPathUnix",
        requiredDependencies=["git", "brew"],
        optionalDependencyCheckers=[],
        primaryPackageManager="brew",
        primaryExtractor=".brew[]?",
        primaryLabel="Brew packages",
        secondaryPackageManager="brewCask",
        secondaryExtractor=".brewCask[]?",
        secondaryLabel="Brew Cask packages",
        useLinuxCommon=False,
    ),

    "ubuntu": SystemConfig(
        platformName="ubuntu",
        configFileName="ubuntu.json",
        fontInstallDir=str(Path.home() / ".local/share/fonts"),
        cursorSettingsPath=str(Path.home() / ".config/Cursor/User/settings.json"),
        repositoryWorkPathKey=".workPathUnix",
        requiredDependencies=["git"],
        optionalDependencyCheckers=[],
        primaryPackageManager="apt",
        primaryExtractor=".apt[]?",
        primaryLabel="APT packages",
        secondaryPackageManager="snap",
        secondaryExtractor=".snap[]?",
        secondaryLabel="Snap packages",
        useLinuxCommon=False,  # Ubuntu uses its own config, not linuxCommon
    ),

    "archlinux": SystemConfig(
        platformName="archlinux",
        configFileName="archlinux.json",
        fontInstallDir=str(Path.home() / ".local/share/fonts"),
        cursorSettingsPath=str(Path.home() / ".config/Cursor/User/settings.json"),
        repositoryWorkPathKey=".workPathUnix",
        requiredDependencies=["git"],
        optionalDependencyCheckers=[],
        primaryPackageManager="pacman",
        primaryExtractor=".pacman[]?",
        primaryLabel="Pacman packages",
        useLinuxCommon=True,
    ),

    "opensuse": SystemConfig(
        platformName="opensuse",
        configFileName="opensuse.json",
        fontInstallDir=str(Path.home() / ".local/share/fonts"),
        cursorSettingsPath=str(Path.home() / ".config/Cursor/User/settings.json"),
        repositoryWorkPathKey=".workPathUnix",
        requiredDependencies=["git"],
        optionalDependencyCheckers=[],
        primaryPackageManager="zypper",
        primaryExtractor=".zypper[]?",
        primaryLabel="Zypper packages",
        useLinuxCommon=True,
    ),

    "redhat": SystemConfig(
        platformName="redhat",
        configFileName="redhat.json",
        fontInstallDir=str(Path.home() / ".local/share/fonts"),
        cursorSettingsPath=str(Path.home() / ".config/Cursor/User/settings.json"),
        repositoryWorkPathKey=".workPathUnix",
        requiredDependencies=["git"],
        optionalDependencyCheckers=[],
        primaryPackageManager="dnf",
        primaryExtractor=".dnf[]?",
        primaryLabel="DNF packages",
        useLinuxCommon=True,
    ),

    "raspberrypi": SystemConfig(
        platformName="raspberrypi",
        configFileName="raspberrypi.json",
        fontInstallDir=str(Path.home() / ".local/share/fonts"),
        cursorSettingsPath=str(Path.home() / ".config/Cursor/User/settings.json"),
        repositoryWorkPathKey=".workPathUnix",
        requiredDependencies=["git"],
        optionalDependencyCheckers=[],
        primaryPackageManager="apt",
        primaryExtractor=".apt[]?",
        primaryLabel="APT packages",
        secondaryPackageManager="snap",
        secondaryExtractor=".snap[]?",
        secondaryLabel="Snap packages",
        useLinuxCommon=True,
    ),

    "win11": SystemConfig(
        platformName="win11",
        configFileName="win11.json",
        fontInstallDir=str(Path.home() / "AppData/Local/Microsoft/Windows/Fonts"),
        cursorSettingsPath=str(Path.home() / "AppData/Roaming/Cursor/User/settings.json"),
        repositoryWorkPathKey=".workPathWindows",
        requiredDependencies=["git"],
        optionalDependencyCheckers=[],  # Will be populated at runtime with isWingetInstalled
        primaryPackageManager="winget",
        primaryExtractor=".winget[]?",
        primaryLabel="Winget packages",
        useLinuxCommon=False,
    ),
}


def getSystemConfig(platformName: str) -> Optional[SystemConfig]:
    """
    Get system configuration for a platform.

    Args:
        platformName: Name of the platform (e.g., "ubuntu", "macos")

    Returns:
        SystemConfig if found, None otherwise
    """
    return systemsConfig.get(platformName)


def getSupportedPlatforms() -> List[str]:
    """
    Get list of all supported platform names.

    Returns:
        List of platform names
    """
    return list(systemsConfig.keys())


__all__ = [
    "SystemConfig",
    "systemsConfig",
    "getSystemConfig",
    "getSupportedPlatforms",
]
