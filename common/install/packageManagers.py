#!/usr/bin/env python3
"""
Platform-specific package manager helper classes.
Encapsulates check, install, and update operations for each package manager.

This is the recommended package manager abstraction for all new code.
It provides a simple, cross-platform interface for package management.
"""

import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import final
from typing import Optional

# Add project root to path for imports
scriptDir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(scriptDir))

from common.core.logging import printError, printSuccess, printWarning


def runPackageCommand(cmd: list, package: str, operation: str, raiseOnError: bool = True) -> bool:
    """
    Run a package manager command with standardised error handling.

    Args:
        cmd: Command to run (list format)
        package: Package name being operated on
        operation: Operation name ('install', 'update', etc) for error messages
        raiseOnError: If True, use check=True (raise on error). If False, check returncode manually.

    Returns:
        True if command succeeded, False otherwise
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=raiseOnError,
        )

        # If check=False, manually check return code
        if not raiseOnError and result.returncode != 0:
            cmdStr = " ".join(cmd)
            stderr = result.stderr.strip() if result.stderr else "No error output"
            printError(f"Failed to {operation} '{package}': Command '{cmdStr}' returned exit code {result.returncode}")
            if stderr:
                printError(f"Error output: {stderr}")
            return False

        return True
    except subprocess.CalledProcessError as e:
        cmdStr = " ".join(cmd)
        stderr = e.stderr.strip() if e.stderr else "No error output"
        printError(f"Failed to {operation} '{package}': Command '{cmdStr}' returned exit code {e.returncode}")
        if stderr:
            printError(f"Error output: {stderr}")
        return False
    except Exception as e:
        cmdStr = " ".join(cmd)
        printError(f"Failed to {operation} '{package}': Command '{cmdStr}' raised exception: {e}")
        return False


class PackageManager(ABC):
    """
    Base class for package managers (bottom layer).

    All package managers (APT, Brew, Winget, etc.) inherit from this.
    Provides unified interface for package operations.

    Required methods (enforced via @abstractmethod):
    - check(), install(), update(), updateAll()
    - isAvailable(), getName(), getVersion()

    Used by BasePlatform to manage packages across different platforms.
    """

    @abstractmethod
    def check(self, package: str) -> bool:
        """
        Check if a package is installed.

        Args:
            package: Package name/identifier

        Returns:
            True if package is installed, False otherwise
        """
        pass

    @abstractmethod
    def install(self, package: str) -> bool:
        """
        Install a package.

        Args:
            package: Package name/identifier

        Returns:
            True if installation succeeded, False otherwise
        """
        pass

    @abstractmethod
    def update(self, package: str) -> bool:
        """
        Update a package.

        Args:
            package: Package name/identifier

        Returns:
            True if update succeeded, False otherwise
        """
        pass

    @abstractmethod
    def updateAll(self, dryRun: bool = False) -> bool:
        """
        Update the package manager itself and all installed packages.

        Args:
            dryRun: If True, don't actually update

        Returns:
            True if update succeeded, False otherwise
        """
        pass

    @abstractmethod
    def isAvailable(self) -> bool:
        """
        Check if this package manager is available on the system.
        Override in subclasses.

        Returns:
            True if package manager is available, False otherwise
        """
        return False

    @abstractmethod
    def getVersion(self) -> str:
        """
        Get package manager version.
        Override in subclasses for specific version command.

        Returns:
            Version string, or "Unknown" if cannot determine
        """
        return "Unknown"

    @abstractmethod
    def getName(self) -> str:
        """
        Get human-readable package manager name.
        Default implementation derives from class name.

        Returns:
            Package manager name
        """
        return self.__class__.__name__.replace("PackageManager", "")


@final
class AptPackageManager(PackageManager):
    """APT package manager (Ubuntu, Debian, Raspberry Pi)."""

    def isAvailable(self) -> bool:
        """Check if APT is available."""
        from common.core.utilities import commandExists
        return commandExists("apt-get")

    def getName(self) -> str:
        """Get package manager name."""
        return "APT"

    def getVersion(self) -> str:
        """Get APT version."""
        try:
            result = subprocess.run(
                ["apt-get", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip().split("\n")[0]
        except Exception:
            return "Unknown"

    def check(self, package: str) -> bool:
        try:
            result = subprocess.run(
                ["dpkg", "-l", package],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def install(self, package: str) -> bool:
        cmd = ["sudo", "apt-get", "install", "-y", package]
        return runPackageCommand(cmd, package, "install")

    def update(self, package: str) -> bool:
        cmd = ["sudo", "apt-get", "install", "--only-upgrade", "-y", package]
        return runPackageCommand(cmd, package, "update")

    def updateAll(self, dryRun: bool = False) -> bool:
        from common.core.logging import printInfo, printSuccess, printWarning

        if dryRun:
            printInfo("[DRY RUN] Would run: sudo apt update && sudo apt upgrade -y")
            return True

        try:
            # Update package lists
            result = subprocess.run(["sudo", "apt", "update"], capture_output=True, check=False)
            if result.returncode != 0:
                printWarning("APT update had issues")
                return False

            # Upgrade packages
            result = subprocess.run(["sudo", "apt", "upgrade", "-y"], capture_output=True, check=False)
            if result.returncode == 0:
                printSuccess("APT packages updated")
                return True
            else:
                printWarning("APT upgrade had issues")
                return False
        except Exception as e:
            printWarning(f"Failed to update APT packages: {e}")
            return False


@final
class SnapPackageManager(PackageManager):
    """Snap package manager."""

    def isAvailable(self) -> bool:
        """Check if Snap is available."""
        from common.core.utilities import commandExists
        return commandExists("snap")

    def getName(self) -> str:
        """Get package manager name."""
        return "Snap"

    def getVersion(self) -> str:
        """Get Snap version."""
        try:
            result = subprocess.run(
                ["snap", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip().split("\n")[0]
        except Exception:
            return "Unknown"

    def check(self, package: str) -> bool:
        try:
            result = subprocess.run(
                ["snap", "list", package],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def install(self, package: str) -> bool:
        return runPackageCommand(["sudo", "snap", "install", package], package, "install")

    def update(self, package: str) -> bool:
        return runPackageCommand(["sudo", "snap", "refresh", package], package, "update")

    def updateAll(self, dryRun: bool = False) -> bool:
        from common.core.logging import printInfo, printSuccess, printWarning

        if dryRun:
            printInfo("[DRY RUN] Would run: sudo snap refresh")
            return True

        try:
            result = subprocess.run(["sudo", "snap", "refresh"], capture_output=True, check=False)
            if result.returncode == 0:
                printSuccess("Snap packages updated")
                return True
            else:
                printWarning("Snap refresh had issues")
                return False
        except Exception as e:
            printWarning(f"Failed to update Snap packages: {e}")
            return False


@final
class BrewPackageManager(PackageManager):
    """Homebrew package manager (macOS)."""

    def isAvailable(self) -> bool:
        """Check if Homebrew is available."""
        from common.core.utilities import commandExists
        return commandExists("brew")

    def getName(self) -> str:
        """Get package manager name."""
        return "Homebrew"

    def getVersion(self) -> str:
        """Get Homebrew version."""
        try:
            result = subprocess.run(
                ["brew", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.split("\n")[0] if result.stdout else "Unknown"
        except Exception:
            return "Unknown"

    def check(self, package: str) -> bool:
        try:
            result = subprocess.run(
                ["brew", "list", package],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def install(self, package: str) -> bool:
        return runPackageCommand(["brew", "install", package], package, "install")

    def update(self, package: str) -> bool:
        return runPackageCommand(["brew", "upgrade", package], package, "update")

    def updateAll(self, dryRun: bool = False) -> bool:
        from common.core.logging import printInfo, printSuccess, printWarning

        if dryRun:
            printInfo("[DRY RUN] Would run: brew update && brew upgrade")
            return True

        try:
            # Update Homebrew
            result = subprocess.run(["brew", "update"], capture_output=True, check=False)
            if result.returncode != 0:
                printWarning("Homebrew update had issues")
                return False

            # Upgrade packages
            result = subprocess.run(["brew", "upgrade"], capture_output=True, check=False)
            if result.returncode == 0:
                printSuccess("Homebrew packages updated")
                return True
            else:
                printWarning("Homebrew upgrade had issues")
                return False
        except Exception as e:
            printWarning(f"Failed to update Homebrew: {e}")
            return False


@final
class BrewCaskPackageManager(PackageManager):
    """Homebrew Cask package manager (macOS)."""

    def isAvailable(self) -> bool:
        """Check if Homebrew Cask is available."""
        from common.core.utilities import commandExists
        return commandExists("brew")

    def getName(self) -> str:
        """Get package manager name."""
        return "Homebrew Cask"

    def getVersion(self) -> str:
        """Get Homebrew version (Cask uses same binary)."""
        try:
            result = subprocess.run(
                ["brew", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip().split("\n")[0]
        except Exception:
            return "Unknown"

    def check(self, package: str) -> bool:
        try:
            result = subprocess.run(
                ["brew", "list", "--cask", package],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def install(self, package: str) -> bool:
        return runPackageCommand(["brew", "install", "--cask", package], package, "install")

    def update(self, package: str) -> bool:
        return runPackageCommand(["brew", "upgrade", "--cask", package], package, "update")

    def updateAll(self, dryRun: bool = False) -> bool:
        from common.core.logging import printInfo, printSuccess, printWarning

        if dryRun:
            printInfo("[DRY RUN] Would run: brew upgrade --cask")
            return True

        try:
            result = subprocess.run(["brew", "upgrade", "--cask"], capture_output=True, check=False)
            if result.returncode == 0:
                printSuccess("Homebrew Cask applications updated")
                return True
            else:
                printWarning("Homebrew Cask upgrade had issues")
                return False
        except Exception as e:
            printWarning(f"Failed to update Homebrew Cask: {e}")
            return False


@final
class WingetPackageManager(PackageManager):
    """Windows Package Manager (winget)."""

    def isAvailable(self) -> bool:
        """Check if Winget is available."""
        from common.common import isWingetInstalled
        return isWingetInstalled()

    def getName(self) -> str:
        """Get package manager name."""
        return "Winget"

    def getVersion(self) -> str:
        """Get Winget version."""
        try:
            result = subprocess.run(
                ["winget", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return "Unknown"

    def check(self, package: str) -> bool:
        try:
            from common.common import isAppInstalled
            return isAppInstalled(package)
        except Exception:
            return False

    def install(self, package: str) -> bool:
        cmd = [
            "winget",
            "install",
            "--id", package,
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--silent",
        ]
        return runPackageCommand(cmd, package, "install", raiseOnError=False)

    def update(self, package: str) -> bool:
        cmd = [
            "winget",
            "upgrade",
            "--id", package,
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--silent",
        ]
        return runPackageCommand(cmd, package, "update", raiseOnError=False)

    def updateAll(self, dryRun: bool = False) -> bool:
        from common.core.logging import printInfo, printSuccess, printWarning

        if dryRun:
            printInfo("[DRY RUN] Would run: winget upgrade --all")
            return True

        try:
            result = subprocess.run(
                ["winget", "upgrade", "--all", "--accept-package-agreements", "--accept-source-agreements", "--silent"],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                printSuccess("Winget packages updated")
                return True
            else:
                printWarning("Winget upgrade had issues")
                return False
        except Exception as e:
            printWarning(f"Failed to update winget packages: {e}")
            return False


@final
class ChocolateyPackageManager(PackageManager):
    """Chocolatey package manager (Windows)."""

    def isAvailable(self) -> bool:
        """Check if Chocolatey is available."""
        from common.core.utilities import commandExists
        return commandExists("choco")

    def getName(self) -> str:
        """Get package manager name."""
        return "Chocolatey"

    def getVersion(self) -> str:
        """Get Chocolatey version."""
        try:
            result = subprocess.run(
                ["choco", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return "Unknown"

    def check(self, package: str) -> bool:
        try:
            result = subprocess.run(
                ["choco", "list", "--local-only", "--exact", package],
                capture_output=True,
                text=True,
                check=False,
            )
            # Chocolatey returns the package if installed
            return package.lower() in result.stdout.lower()
        except Exception:
            return False

    def install(self, package: str) -> bool:
        cmd = ["choco", "install", package, "-y"]
        return runPackageCommand(cmd, package, "install", raiseOnError=False)

    def update(self, package: str) -> bool:
        cmd = ["choco", "upgrade", package, "-y"]
        return runPackageCommand(cmd, package, "update", raiseOnError=False)

    def updateAll(self, dryRun: bool = False) -> bool:
        from common.core.logging import printInfo, printSuccess, printWarning

        if dryRun:
            printInfo("[DRY RUN] Would run: choco upgrade all -y")
            return True

        try:
            result = subprocess.run(
                ["choco", "upgrade", "all", "-y"],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                printSuccess("Chocolatey packages updated")
                return True
            else:
                printWarning("Chocolatey upgrade had issues")
                return False
        except Exception as e:
            printWarning(f"Failed to update Chocolatey packages: {e}")
            return False


@final
class VcpkgPackageManager(PackageManager):
    """vcpkg package manager (Windows C/C++ libraries)."""

    def isAvailable(self) -> bool:
        """Check if vcpkg is available."""
        from common.core.utilities import commandExists
        return commandExists("vcpkg")

    def getName(self) -> str:
        """Get package manager name."""
        return "vcpkg"

    def getVersion(self) -> str:
        """Get vcpkg version."""
        try:
            result = subprocess.run(
                ["vcpkg", "version"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip().split("\n")[0]
        except Exception:
            return "Unknown"

    def check(self, package: str) -> bool:
        try:
            result = subprocess.run(
                ["vcpkg", "list", package],
                capture_output=True,
                text=True,
                check=False,
            )
            # vcpkg list shows installed packages
            return package in result.stdout
        except Exception:
            return False

    def install(self, package: str) -> bool:
        cmd = ["vcpkg", "install", package]
        return runPackageCommand(cmd, package, "install", raiseOnError=False)

    def update(self, package: str) -> bool:
        cmd = ["vcpkg", "upgrade", package, "--no-dry-run"]
        return runPackageCommand(cmd, package, "update", raiseOnError=False)

    def updateAll(self, dryRun: bool = False) -> bool:
        from common.core.logging import printInfo, printSuccess, printWarning

        if dryRun:
            printInfo("[DRY RUN] Would run: vcpkg upgrade --no-dry-run")
            return True

        try:
            result = subprocess.run(
                ["vcpkg", "upgrade", "--no-dry-run"],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                printSuccess("vcpkg packages updated")
                return True
            else:
                printWarning("vcpkg upgrade had issues")
        except Exception as e:
            printWarning(f"Failed to update vcpkg packages: {e}")

        return False


@final
class StorePackageManager(PackageManager):
    """Microsoft Store package manager (Windows)."""

    def isAvailable(self) -> bool:
        """Check if Microsoft Store is available (Windows only)."""
        from common.systems.platform import isWindows
        return isWindows()

    def getName(self) -> str:
        """Get package manager name."""
        return "Microsoft Store"

    def getVersion(self) -> str:
        """Get version (N/A for Microsoft Store)."""
        return "N/A"

    def check(self, package: str) -> bool:
        # Store apps can't be easily checked, so always return False
        # This will attempt installation/update each time
        return False

    def install(self, package: str) -> bool:
        cmd = [
            "winget",
            "install",
            "--id", package,
            "--source", "msstore",
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--silent",
        ]
        return runPackageCommand(cmd, package, "install", raiseOnError=False)

    def update(self, package: str) -> bool:
        cmd = [
            "winget",
            "upgrade",
            "--id", package,
            "--source", "msstore",
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--silent",
        ]
        return runPackageCommand(cmd, package, "update", raiseOnError=False)

    def updateAll(self, dryRun: bool = False) -> bool:
        from common.core.logging import printInfo, printWarning

        if dryRun:
            printInfo("[DRY RUN] Would update Microsoft Store apps")
            return True

        # Microsoft Store doesn't have a good CLI for updating all apps
        printInfo("Microsoft Store apps update via Windows Store UI")
        return True


@final
class DnfPackageManager(PackageManager):
    """DNF package manager (RedHat, Fedora, CentOS)."""

    def isAvailable(self) -> bool:
        """Check if DNF is available."""
        from common.core.utilities import commandExists
        return commandExists("dnf")

    def getName(self) -> str:
        """Get package manager name."""
        return "DNF"

    def getVersion(self) -> str:
        """Get DNF version."""
        try:
            result = subprocess.run(
                ["dnf", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip().split("\n")[0]
        except Exception:
            return "Unknown"

    def check(self, package: str) -> bool:
        try:
            result = subprocess.run(
                ["rpm", "-q", package],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def install(self, package: str) -> bool:
        return runPackageCommand(["sudo", "dnf", "install", "-y", package], package, "install")

    def update(self, package: str) -> bool:
        return runPackageCommand(["sudo", "dnf", "upgrade", "-y", package], package, "update")

    def updateAll(self, dryRun: bool = False) -> bool:
        from common.core.logging import printInfo, printSuccess, printWarning

        if dryRun:
            printInfo("[DRY RUN] Would run: sudo dnf upgrade -y")
            return True

        try:
            result = subprocess.run(["sudo", "dnf", "upgrade", "-y"], capture_output=True, check=False)
            if result.returncode == 0:
                printSuccess("DNF packages updated")
                return True
            else:
                printWarning("DNF upgrade had issues")
        except Exception as e:
            printWarning(f"Failed to update DNF packages: {e}")

        return False


@final
class ZypperPackageManager(PackageManager):
    """Zypper package manager (OpenSUSE)."""

    def isAvailable(self) -> bool:
        """Check if Zypper is available."""
        from common.core.utilities import commandExists
        return commandExists("zypper")

    def getName(self) -> str:
        """Get package manager name."""
        return "Zypper"

    def getVersion(self) -> str:
        """Get Zypper version."""
        try:
            result = subprocess.run(
                ["zypper", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return "Unknown"

    def check(self, package: str) -> bool:
        try:
            result = subprocess.run(
                ["rpm", "-q", package],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def install(self, package: str) -> bool:
        return runPackageCommand(["sudo", "zypper", "install", "-y", package], package, "install")

    def update(self, package: str) -> bool:
        return runPackageCommand(["sudo", "zypper", "update", "-y", package], package, "update")

    def updateAll(self, dryRun: bool = False) -> bool:
        from common.core.logging import printInfo, printSuccess, printWarning

        if dryRun:
            printInfo("[DRY RUN] Would run: sudo zypper refresh && sudo zypper update -y")
            return True

        try:
            # Refresh repositories
            result = subprocess.run(["sudo", "zypper", "refresh"], capture_output=True, check=False)
            if result.returncode != 0:
                printWarning("Zypper refresh had issues")
                return False

            # Update packages
            result = subprocess.run(["sudo", "zypper", "update", "-y"], capture_output=True, check=False)
            if result.returncode == 0:
                printSuccess("Zypper packages updated")
                return True
            else:
                printWarning("Zypper update had issues")
        except Exception as e:
            printWarning(f"Failed to update Zypper packages: {e}")

        return False


@final
class PacmanPackageManager(PackageManager):
    """Pacman package manager (ArchLinux)."""

    def isAvailable(self) -> bool:
        """Check if Pacman is available."""
        from common.core.utilities import commandExists
        return commandExists("pacman")

    def getName(self) -> str:
        """Get package manager name."""
        return "Pacman"

    def getVersion(self) -> str:
        """Get Pacman version."""
        try:
            result = subprocess.run(
                ["pacman", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            # Pacman outputs multiple lines, take first
            return result.stdout.strip().split("\n")[0]
        except Exception:
            return "Unknown"

    def check(self, package: str) -> bool:
        try:
            result = subprocess.run(
                ["pacman", "-Q", package],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def install(self, package: str) -> bool:
        return runPackageCommand(["sudo", "pacman", "-S", "--noconfirm", package], package, "install")

    def update(self, package: str) -> bool:
        return runPackageCommand(["sudo", "pacman", "-S", "--noconfirm", "--needed", package], package, "update")

    def updateAll(self, dryRun: bool = False) -> bool:
        from common.core.logging import printInfo, printSuccess, printWarning

        if dryRun:
            printInfo("[DRY RUN] Would run: sudo pacman -Syu --noconfirm")
            return True

        try:
            result = subprocess.run(["sudo", "pacman", "-Syu", "--noconfirm"], capture_output=True, check=False)
            if result.returncode == 0:
                printSuccess("Pacman packages updated")
                return True
            else:
                printWarning("Pacman update had issues")
        except Exception as e:
            printWarning(f"Failed to update Pacman packages: {e}")

        return False


__all__ = [
    "PackageManager",
    "AptPackageManager",
    "BrewCaskPackageManager",
    "BrewPackageManager",
    "ChocolateyPackageManager",
    "DnfPackageManager",
    "PacmanPackageManager",
    "SnapPackageManager",
    "StorePackageManager",
    "VcpkgPackageManager",
    "WingetPackageManager",
    "ZypperPackageManager",
    "runPackageCommand",
]
