#!/usr/bin/env python3
"""
Platform implementations that know how to update themselves.
Each platform owns its package managers and update logic.
"""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from common.core.logging import printInfo, printSuccess, printWarning
from common.core.utilities import commandExists
from common.install.packageManagers import PackageManager
from common.install.setupZsh import OhMyZshManager
from common.install.androidStudio import AndroidStudioManager


class BasePlatform(ABC):
    """
    Platform representation and update layer.

    Each platform (macOS, Windows, Ubuntu, etc.) knows:
    - Which package managers it uses
    - How to update itself
    - What managers and tools are available

    This is the middle layer between:
    - PackageManager (bottom): Individual package operations
    - GenericSystem (top): Full installation orchestration

    Use getCurrentPlatform() to get a cached instance.
    """

    def __init__(self, projectRoot: Path, dryRun: bool = False):
        """
        Initialise the platform.

        Args:
            projectRoot: Root directory of jrl_env project
            dryRun: If True, don't actually make changes
        """
        self.projectRoot = projectRoot
        self.dryRun = dryRun
        self.packageManagers: List[PackageManager] = []
        self.omzManager = OhMyZshManager(dryRun=dryRun)
        self.androidManager = AndroidStudioManager(dryRun=dryRun)
        self.initialisePackageManagers()

    @abstractmethod
    def initialisePackageManagers(self) -> None:
        """Set up the package managers for this platform."""
        pass

    @abstractmethod
    def getPlatformName(self) -> str:
        """Get the platform name (e.g., 'macos', 'ubuntu')."""
        pass

    def updatePackages(self) -> bool:
        """
        Update all packages via all package managers and Android SDK.

        Returns:
            True if successful, False if errors occurred
        """
        allSuccess = True

        # Update via package managers
        for manager in self.packageManagers:
            if not manager.updateAll(self.dryRun):
                allSuccess = False

        # Update Android SDK (application development kit)
        if not self.androidManager.updateSdk():
            allSuccess = False

        return allSuccess

    @abstractmethod
    def updateSystem(self) -> bool:
        """
        Update OS-level system components (app stores, OS updates, OMZ, etc).
        This includes system-level updates but NOT package managers or apps.

        Returns:
            True if successful, False if errors occurred
        """
        pass

    def updateSystemWithOmz(self) -> bool:
        """
        Update system components and Oh My Zsh.
        Internal helper that combines system updates with OMZ.

        Returns:
            True if successful, False if errors occurred
        """
        return self.updateSystem() and self.omzManager.update()

    def updateAll(self) -> bool:
        """
        Update everything: packages (including Android SDK) and system (including OMZ).

        Returns:
            True if successful, False if errors occurred
        """
        return self.updatePackages() and self.updateSystemWithOmz()


class MacOsPlatform(BasePlatform):
    """macOS platform implementation."""

    def initialisePackageManagers(self) -> None:
        from common.install.packageManagers import BrewPackageManager, BrewCaskPackageManager

        self.packageManagers = [
            BrewPackageManager(),
            BrewCaskPackageManager(),
        ]

    def getPlatformName(self) -> str:
        return "macos"

    def updateMacAppStore(self) -> bool:
        """
        Update Mac App Store applications.

        Returns:
            True if successful, False if errors occurred
        """
        if not commandExists("mas"):
            return True  # Not installed, skip

        printInfo("Updating Mac App Store applications...")
        if self.dryRun:
            printInfo("[DRY RUN] Would run: mas upgrade")
            return True

        try:
            result = subprocess.run(["mas", "upgrade"], capture_output=True, check=False)
            if result.returncode == 0:
                printSuccess("Mac App Store apps updated")
                return True

            printWarning("Mac App Store update had issues")
        except Exception as e:
            printWarning(f"Failed to update Mac App Store apps: {e}")

        return False

    def checkMacOsUpdates(self) -> bool:
        """
        Check for macOS system updates.

        Returns:
            True if successful, False if errors occurred
        """
        printInfo("Checking for macOS system updates...")
        if self.dryRun:
            printInfo("[DRY RUN] Would run: softwareupdate --list")
            return True

        try:
            result = subprocess.run(
                ["softwareupdate", "--list"],
                capture_output=True,
                text=True,
                check=False
            )
            if "No new software available" in result.stdout or result.returncode == 0:
                printSuccess("macOS is up to date")
            else:
                printInfo("System updates available. Run 'softwareupdate --install --recommended' to install.")

            return True
        except Exception as e:
            printWarning(f"Failed to check for system updates: {e}")

        return False

    def updateSystem(self) -> bool:
        """Update Mac App Store and check for macOS updates."""
        return self.updateMacAppStore() and self.checkMacOsUpdates()


class WindowsPlatform(BasePlatform):
    """Windows platform implementation."""

    def initialisePackageManagers(self) -> None:
        from common.install.packageManagers import WingetPackageManager, ChocolateyPackageManager, VcpkgPackageManager, StorePackageManager

        self.packageManagers = [
            ChocolateyPackageManager(),
            StorePackageManager(),
            VcpkgPackageManager(),
            WingetPackageManager(),
        ]

    def getPlatformName(self) -> str:
        return "win11"

    def updateSystem(self) -> bool:
        """Provide guidance for Windows Update."""
        printInfo("For Windows system updates, please use Windows Update in Settings")
        printInfo("Or run as administrator: Install-Module PSWindowsUpdate; Get-WindowsUpdate; Install-WindowsUpdate")
        return True


class UbuntuPlatform(BasePlatform):
    """Ubuntu/Debian-based platform implementation."""

    def initialisePackageManagers(self) -> None:
        from common.install.packageManagers import AptPackageManager, SnapPackageManager

        self.packageManagers = [
            AptPackageManager(),
            SnapPackageManager(),
        ]

    def getPlatformName(self) -> str:
        return "ubuntu"

    def updateSystem(self) -> bool:
        """APT updates are handled by package managers, nothing extra needed."""
        return True


class FedoraPlatform(BasePlatform):
    """Fedora/RedHat-based platform implementation."""

    def initialisePackageManagers(self) -> None:
        from common.install.packageManagers import DnfPackageManager

        self.packageManagers = [
            DnfPackageManager(),
        ]

    def getPlatformName(self) -> str:
        return "fedora"

    def updateSystem(self) -> bool:
        """DNF updates are handled by package managers, nothing extra needed."""
        return True


class OpenSusePlatform(BasePlatform):
    """OpenSUSE platform implementation."""

    def initialisePackageManagers(self) -> None:
        from common.install.packageManagers import ZypperPackageManager

        self.packageManagers = [
            ZypperPackageManager(),
        ]

    def getPlatformName(self) -> str:
        return "opensuse"

    def updateSystem(self) -> bool:
        """Zypper updates are handled by package managers, nothing extra needed."""
        return True


class ArchLinuxPlatform(BasePlatform):
    """Arch Linux platform implementation."""

    def initialisePackageManagers(self) -> None:
        from common.install.packageManagers import PacmanPackageManager

        self.packageManagers = [
            PacmanPackageManager(),
        ]

    def getPlatformName(self) -> str:
        return "archlinux"

    def updateSystem(self) -> bool:
        """Pacman updates are handled by package managers, nothing extra needed."""
        return True


class AlpinePlatform(BasePlatform):
    """Alpine Linux platform implementation."""

    def initialisePackageManagers(self) -> None:
        # Alpine uses APK, we need to create an ApkPackageManager
        # For now, just an empty list
        self.packageManagers = []

    def getPlatformName(self) -> str:
        return "alpine"

    def updateSystem(self) -> bool:
        """Update Alpine packages using apk."""
        printInfo("Updating APK packages...")
        if self.dryRun:
            printInfo("[DRY RUN] Would run: sudo apk update && sudo apk upgrade")
            return True

        try:
            # Update package index
            result = subprocess.run(["sudo", "apk", "update"], capture_output=True, check=False)
            if result.returncode != 0:
                printWarning("APK update had issues")
                return False

            # Upgrade packages
            result = subprocess.run(["sudo", "apk", "upgrade"], capture_output=True, check=False)
            if result.returncode == 0:
                printSuccess("APK packages updated")
                return True

            printWarning("APK upgrade had issues")
        except Exception as e:
            printWarning(f"Failed to update APK packages: {e}")

        return False


class RaspberryPiPlatform(UbuntuPlatform):
    """Raspberry Pi platform (inherits from Ubuntu as it's Debian-based)."""

    def getPlatformName(self) -> str:
        return "raspberrypi"


# Platform factory function
def createPlatform(platformName: str, projectRoot: Path, dryRun: bool = False) -> BasePlatform:
    """
    Factory function to create a platform instance.

    Args:
        platformName: Platform name (e.g., 'macos', 'ubuntu')
        projectRoot: Root directory of jrl_env project
        dryRun: If True, don't actually make changes

    Returns:
        Platform instance

    Raises:
        ValueError: If platform is not supported
    """
    platformMap = {
        "macos": MacOsPlatform,
        "win11": WindowsPlatform,
        "ubuntu": UbuntuPlatform,
        "debian": UbuntuPlatform,
        "popos": UbuntuPlatform,
        "linuxmint": UbuntuPlatform,
        "elementary": UbuntuPlatform,
        "zorin": UbuntuPlatform,
        "mxlinux": UbuntuPlatform,
        "raspberrypi": RaspberryPiPlatform,
        "fedora": FedoraPlatform,
        "redhat": FedoraPlatform,
        "opensuse": OpenSusePlatform,
        "archlinux": ArchLinuxPlatform,
        "manjaro": ArchLinuxPlatform,
        "endeavouros": ArchLinuxPlatform,
        "alpine": AlpinePlatform,
    }

    platformClass = platformMap.get(platformName)
    if not platformClass:
        raise ValueError(f"Unsupported platform: {platformName}")

    return platformClass(projectRoot, dryRun)


# Cached platform instance (singleton per session)
_platformInstance = None


def getCurrentPlatform(dryRun: bool = False):
    """
    Get or create the current platform instance.
    Cached singleton - same instance returned on subsequent calls.

    Args:
        dryRun: If True, platform operations won't make actual changes

    Returns:
        Platform instance (MacOsPlatform, WindowsPlatform, etc.)

    Example:
        platform = getCurrentPlatform()
        platform.updateAll()
        platform.packageManagers  # Already knows what's available
    """
    global _platformInstance

    if _platformInstance is None:
        from common.systems.update import detectPlatform
        from common.core.utilities import getProjectRoot

        platformName = detectPlatform()
        projectRoot = getProjectRoot()
        _platformInstance = createPlatform(platformName, projectRoot, dryRun)

    return _platformInstance


def resetPlatformCache() -> None:
    """
    Reset the cached platform instance.
    Useful for testing or when dryRun state changes.
    """
    global _platformInstance
    _platformInstance = None


__all__ = [
    "BasePlatform",
    "MacOsPlatform",
    "WindowsPlatform",
    "UbuntuPlatform",
    "FedoraPlatform",
    "OpenSusePlatform",
    "ArchLinuxPlatform",
    "AlpinePlatform",
    "RaspberryPiPlatform",
    "createPlatform",
    "getCurrentPlatform",
    "resetPlatformCache",
]
