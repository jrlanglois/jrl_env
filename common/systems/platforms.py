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
    """Base class for all platform implementations."""

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
        self.initializePackageManagers()

    @abstractmethod
    def initializePackageManagers(self) -> None:
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
        hasErrors = False

        # Update via package managers
        for manager in self.packageManagers:
            if not manager.updateAll(self.dryRun):
                hasErrors = True

        # Update Android SDK (application development kit)
        if not self.androidManager.updateSdk():
            hasErrors = True

        return not hasErrors

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
        hasErrors = False

        # Update OS-level components
        if not self.updateSystem():
            hasErrors = True

        # Update Oh My Zsh (system shell configuration)
        if not self.omzManager.update():
            hasErrors = True

        return not hasErrors

    def updateAll(self) -> bool:
        """
        Update everything: packages (including Android SDK) and system (including OMZ).

        Returns:
            True if successful, False if errors occurred
        """
        hasErrors = False

        # Update apps: package managers + Android SDK
        if not self.updatePackages():
            hasErrors = True

        # Update system: OS updates + stores + OMZ
        if not self.updateSystemWithOmz():
            hasErrors = True

        return not hasErrors


class MacOsPlatform(BasePlatform):
    """macOS platform implementation."""

    def initializePackageManagers(self) -> None:
        from common.install.packageManagers import BrewPackageManager, BrewCaskPackageManager

        self.packageManagers = [
            BrewPackageManager(),
            BrewCaskPackageManager(),
        ]

    def getPlatformName(self) -> str:
        return "macos"

    def updateSystem(self) -> bool:
        """Update Mac App Store and check for macOS updates."""
        hasErrors = False

        # Update Mac App Store apps
        if commandExists("mas"):
            printInfo("Updating Mac App Store applications...")
            if self.dryRun:
                printInfo("[DRY RUN] Would run: mas upgrade")
            else:
                try:
                    result = subprocess.run(["mas", "upgrade"], capture_output=True, check=False)
                    if result.returncode == 0:
                        printSuccess("Mac App Store apps updated")
                    else:
                        printWarning("Mac App Store update had issues")
                except Exception as e:
                    printWarning(f"Failed to update Mac App Store apps: {e}")

        # Check for macOS system updates
        printInfo("Checking for macOS system updates...")
        if self.dryRun:
            printInfo("[DRY RUN] Would run: softwareupdate --list")
        else:
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
            except Exception as e:
                printWarning(f"Failed to check for system updates: {e}")

        return not hasErrors


class WindowsPlatform(BasePlatform):
    """Windows platform implementation."""

    def initializePackageManagers(self) -> None:
        from common.install.packageManagers import WingetPackageManager, StorePackageManager

        self.packageManagers = [
            WingetPackageManager(),
            StorePackageManager(),
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

    def initializePackageManagers(self) -> None:
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

    def initializePackageManagers(self) -> None:
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

    def initializePackageManagers(self) -> None:
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

    def initializePackageManagers(self) -> None:
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

    def initializePackageManagers(self) -> None:
        # Alpine uses APK, we need to create an ApkPackageManager
        # For now, just an empty list
        self.packageManagers = []

    def getPlatformName(self) -> str:
        return "alpine"

    def updateSystem(self) -> bool:
        """Update Alpine packages using apk."""
        hasErrors = False

        printInfo("Updating APK packages...")
        if self.dryRun:
            printInfo("[DRY RUN] Would run: sudo apk update && sudo apk upgrade")
        else:
            try:
                # Update package index
                result = subprocess.run(["sudo", "apk", "update"], capture_output=True, check=False)
                if result.returncode != 0:
                    printWarning("APK update had issues")
                    hasErrors = True
                else:
                    # Upgrade packages
                    result = subprocess.run(["sudo", "apk", "upgrade"], capture_output=True, check=False)
                    if result.returncode != 0:
                        printWarning("APK upgrade had issues")
                        hasErrors = True
                    else:
                        printSuccess("APK packages updated")
            except Exception as e:
                printWarning(f"Failed to update APK packages: {e}")
                hasErrors = True

        return not hasErrors


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
]
