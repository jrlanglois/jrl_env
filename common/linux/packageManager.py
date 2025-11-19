#!/usr/bin/env python3
"""
Generic Linux package manager helpers.
Allows Linux distributions to declare their primary package manager
(apt, yum, dnf, rpm) and reuse shared install/update logic.

⚠️ NOTE: This module is legacy and not actively used in the codebase.
For new code, prefer common/install/packageManagers.py which provides:
- Cross-platform support (Linux, macOS, Windows)
- Simpler interface
- Better error logging
- Active maintenance

This module is kept for potential future use cases requiring:
- Package name mapping (Debian/Ubuntu → RPM-based systems)
- Explicit cache management
- Linux-specific advanced features
"""

import subprocess
import sys
from abc import ABC, abstractmethod
from typing import Dict, Optional

# Import common utilities directly from source modules
from common.core.logging import printError, printInfo
from common.core.utilities import commandExists, requireCommand


# Package name mappings from Debian/Ubuntu to RPM-based systems
packageMappings: Dict[str, str] = {
    "libasound2-dev": "alsa-lib-devel",
    "libbz2-dev": "bzip2-devel",
    "libcurl4-openssl-dev": "libcurl-devel",
    "libffi-dev": "libffi-devel",
    "libfontconfig1-dev": "fontconfig-devel",
    "libfreetype-dev": "freetype-devel",
    "liblzma-dev": "xz-devel",
    "libncursesw5-dev": "ncurses-devel",
    "libreadline-dev": "readline-devel",
    "libsqlite3-dev": "sqlite-devel",
    "libssl-dev": "openssl-devel",
    "zlib1g-dev": "zlib-devel",
    "tk-dev": "tk-devel",
    "xz-utils": "xz",
}

supportedManagers = ["apt", "yum", "dnf", "rpm", "zypper", "pacman"]


def mapPackageName(package: str, manager: str) -> str:
    """
    Map package name from Debian/Ubuntu to RPM-based system if needed.

    Args:
        package: Package name to map
        manager: Package manager name

    Returns:
        Mapped package name or original if no mapping needed
    """
    if manager.lower() in ("yum", "dnf", "rpm", "zypper"):
        return packageMappings.get(package, package)
    return package


class PackageManager(ABC):
    """Abstract base class for package managers."""

    def __init__(self, name: str):
        self.name = name
        self.cacheUpdated = False
        self.labelValue = ""

    @abstractmethod
    def commandName(self) -> str:
        """Get the command name for this package manager."""
        pass

    @abstractmethod
    def prepareCache(self) -> None:
        """Prepare/update the package cache."""
        pass

    @abstractmethod
    def checkPackage(self, package: str) -> bool:
        """Check if a package is installed."""
        pass

    @abstractmethod
    def installPackage(self, package: str) -> bool:
        """Install a package."""
        pass

    @abstractmethod
    def updatePackage(self, package: str) -> bool:
        """Update a package."""
        pass

    def label(self) -> str:
        """Get a human-readable label for this package manager."""
        return self.labelValue

    def requireManager(self) -> bool:
        """Require the package manager command to be available."""
        cmd = self.commandName()
        hint = f"Please install {cmd} or ensure it is available in PATH."
        return requireCommand(cmd, hint)

    def initialise(self) -> bool:
        """Initialise the package manager."""
        if not self.requireManager():
            return False
        self.labelValue = self._getLabel()
        return True

    @abstractmethod
    def _getLabel(self) -> str:
        """Get the label for this package manager."""
        pass

    def _runCommand(self, cmd: list[str], silent: bool = True) -> bool:
        """Run a command and return success status."""
        try:
            stdout = subprocess.DEVNULL if silent else None
            stderr = subprocess.DEVNULL if silent else None
            result = subprocess.run(
                cmd,
                stdout=stdout,
                stderr=stderr,
                check=False
            )
            return result.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False


class AptPackageManager(PackageManager):
    """APT package manager (Debian/Ubuntu)."""

    def __init__(self):
        super().__init__("apt")

    def commandName(self) -> str:
        return "apt-get"

    def prepareCache(self) -> None:
        if self.cacheUpdated:
            return
        printInfo("Updating apt package cache...")
        self._runCommand(["sudo", "apt-get", "update", "-y"])
        self.cacheUpdated = True

    def checkPackage(self, package: str) -> bool:
        """Check if package is installed using dpkg."""
        result = subprocess.run(
            ["dpkg", "-l"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            return False
        # Check for "^ii  package " pattern
        for line in result.stdout.splitlines():
            if line.startswith("ii  ") and f" {package} " in line:
                return True
        return False

    def installPackage(self, package: str) -> bool:
        self.prepareCache()
        return self._runCommand(["sudo", "apt-get", "install", "-y", package])

    def updatePackage(self, package: str) -> bool:
        self.prepareCache()
        return self._runCommand(["sudo", "apt-get", "install", "--only-upgrade", "-y", package])

    def _getLabel(self) -> str:
        return "APT packages"


class YumPackageManager(PackageManager):
    """YUM package manager (RHEL/CentOS 7)."""

    def __init__(self):
        super().__init__("yum")

    def commandName(self) -> str:
        return "yum"

    def prepareCache(self) -> None:
        if self.cacheUpdated:
            return
        printInfo("Refreshing yum metadata...")
        self._runCommand(["sudo", "yum", "makecache", "-y"])
        self.cacheUpdated = True

    def checkPackage(self, package: str) -> bool:
        mappedPackage = mapPackageName(package, "yum")
        result = subprocess.run(
            ["rpm", "-q", mappedPackage],
            capture_output=True,
            check=False
        )
        return result.returncode == 0

    def installPackage(self, package: str) -> bool:
        self.prepareCache()
        mappedPackage = mapPackageName(package, "yum")
        return self._runCommand(["sudo", "yum", "install", "-y", mappedPackage])

    def updatePackage(self, package: str) -> bool:
        self.prepareCache()
        mappedPackage = mapPackageName(package, "yum")
        return self._runCommand(["sudo", "yum", "update", "-y", mappedPackage])

    def _getLabel(self) -> str:
        return "YUM packages"


class DnfPackageManager(PackageManager):
    """DNF package manager (Fedora/RHEL 8+)."""

    def __init__(self):
        super().__init__("dnf")

    def commandName(self) -> str:
        return "dnf"

    def prepareCache(self) -> None:
        if self.cacheUpdated:
            return
        printInfo("Refreshing dnf metadata...")
        self._runCommand(["sudo", "dnf", "makecache", "-y"])
        self.cacheUpdated = True

    def checkPackage(self, package: str) -> bool:
        mappedPackage = mapPackageName(package, "dnf")
        result = subprocess.run(
            ["rpm", "-q", mappedPackage],
            capture_output=True,
            check=False
        )
        return result.returncode == 0

    def installPackage(self, package: str) -> bool:
        self.prepareCache()
        mappedPackage = mapPackageName(package, "dnf")
        return self._runCommand(["sudo", "dnf", "install", "-y", mappedPackage])

    def updatePackage(self, package: str) -> bool:
        self.prepareCache()
        mappedPackage = mapPackageName(package, "dnf")
        return self._runCommand(["sudo", "dnf", "upgrade", "-y", mappedPackage])

    def _getLabel(self) -> str:
        return "DNF packages"


class RpmPackageManager(PackageManager):
    """RPM package manager (low-level)."""

    def __init__(self):
        super().__init__("rpm")

    def commandName(self) -> str:
        return "rpm"

    def prepareCache(self) -> None:
        # rpm uses the local database; no cache update needed
        self.cacheUpdated = True

    def checkPackage(self, package: str) -> bool:
        mappedPackage = mapPackageName(package, "rpm")
        result = subprocess.run(
            ["rpm", "-q", mappedPackage],
            capture_output=True,
            check=False
        )
        return result.returncode == 0

    def installPackage(self, package: str) -> bool:
        self.prepareCache()
        mappedPackage = mapPackageName(package, "rpm")
        return self._runCommand(["sudo", "rpm", "-i", mappedPackage])

    def updatePackage(self, package: str) -> bool:
        self.prepareCache()
        mappedPackage = mapPackageName(package, "rpm")
        return self._runCommand(["sudo", "rpm", "-U", mappedPackage])

    def _getLabel(self) -> str:
        return "RPM packages"


class ZypperPackageManager(PackageManager):
    """Zypper package manager (OpenSUSE/SLES)."""

    def __init__(self):
        super().__init__("zypper")

    def commandName(self) -> str:
        return "zypper"

    def prepareCache(self) -> None:
        if self.cacheUpdated:
            return
        printInfo("Refreshing zypper repositories...")
        self._runCommand(["sudo", "zypper", "refresh"])
        self.cacheUpdated = True

    def checkPackage(self, package: str) -> bool:
        mappedPackage = mapPackageName(package, "zypper")
        result = subprocess.run(
            ["rpm", "-q", mappedPackage],
            capture_output=True,
            check=False
        )
        return result.returncode == 0

    def installPackage(self, package: str) -> bool:
        self.prepareCache()
        mappedPackage = mapPackageName(package, "zypper")
        return self._runCommand(["sudo", "zypper", "install", "-y", mappedPackage])

    def updatePackage(self, package: str) -> bool:
        self.prepareCache()
        mappedPackage = mapPackageName(package, "zypper")
        return self._runCommand(["sudo", "zypper", "update", "-y", mappedPackage])

    def _getLabel(self) -> str:
        return "Zypper packages"


class PacmanPackageManager(PackageManager):
    """Pacman package manager (ArchLinux)."""

    def __init__(self):
        super().__init__("pacman")

    def commandName(self) -> str:
        return "pacman"

    def prepareCache(self) -> None:
        if self.cacheUpdated:
            return
        printInfo("Synchronising pacman package database...")
        self._runCommand(["sudo", "pacman", "-Sy"])
        self.cacheUpdated = True

    def checkPackage(self, package: str) -> bool:
        result = subprocess.run(
            ["pacman", "-Q", package],
            capture_output=True,
            check=False
        )
        return result.returncode == 0

    def installPackage(self, package: str) -> bool:
        self.prepareCache()
        return self._runCommand(["sudo", "pacman", "-S", "--noconfirm", package])

    def updatePackage(self, package: str) -> bool:
        self.prepareCache()
        return self._runCommand(["sudo", "pacman", "-S", "--noconfirm", "--needed", package])

    def _getLabel(self) -> str:
        return "Pacman packages"


def validateManager(manager: str) -> bool:
    """
    Validate that a package manager is supported.

    Args:
        manager: Package manager name to validate

    Returns:
        True if supported, False otherwise
    """
    managerLower = manager.lower()
    if managerLower not in supportedManagers:
        printError(f"Unsupported Linux package manager: {manager}")
        printInfo(f"Supported managers: {', '.join(supportedManagers)}")
        return False
    return True


def createPackageManager(manager: Optional[str] = None) -> Optional[PackageManager]:
    """
    Create a package manager instance.

    Args:
        manager: Package manager name (defaults to "apt")

    Returns:
        PackageManager instance or None if invalid
    """
    if manager is None:
        manager = "apt"

    managerLower = manager.lower()

    if not validateManager(managerLower):
        return None

    if managerLower == "apt":
        return AptPackageManager()
    elif managerLower == "yum":
        return YumPackageManager()
    elif managerLower == "dnf":
        return DnfPackageManager()
    elif managerLower == "rpm":
        return RpmPackageManager()
    elif managerLower == "zypper":
        return ZypperPackageManager()
    elif managerLower == "pacman":
        return PacmanPackageManager()
    else:
        return None


# Global instance (initialised on first use)
_packageManager: Optional[PackageManager] = None


def getPackageManager(manager: Optional[str] = None) -> Optional[PackageManager]:
    """
    Get or create the global package manager instance.

    Args:
        manager: Package manager name (only used on first call)

    Returns:
        PackageManager instance or None if invalid
    """
    global _packageManager

    if _packageManager is None:
        _packageManager = createPackageManager(manager)
        if _packageManager and not _packageManager.initialise():
            _packageManager = None

    return _packageManager


__all__ = [
    "PackageManager",
    "AptPackageManager",
    "YumPackageManager",
    "DnfPackageManager",
    "RpmPackageManager",
    "ZypperPackageManager",
    "PacmanPackageManager",
    "validateManager",
    "createPackageManager",
    "getPackageManager",
    "mapPackageName",
    "packageMappings",
    "supportedManagers",
]
