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
    """Base class for package managers."""

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


class AptPackageManager(PackageManager):
    """APT package manager (Ubuntu, Debian, Raspberry Pi)."""

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


class SnapPackageManager(PackageManager):
    """Snap package manager."""

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


class BrewPackageManager(PackageManager):
    """Homebrew package manager (macOS)."""

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


class BrewCaskPackageManager(PackageManager):
    """Homebrew Cask package manager (macOS)."""

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


class WingetPackageManager(PackageManager):
    """Windows Package Manager (winget)."""

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


class ChocolateyPackageManager(PackageManager):
    """Chocolatey package manager (Windows)."""

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


class StorePackageManager(PackageManager):
    """Microsoft Store package manager (Windows)."""

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


class DnfPackageManager(PackageManager):
    """DNF package manager (RedHat, Fedora, CentOS)."""

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
                return False
        except Exception as e:
            printWarning(f"Failed to update DNF packages: {e}")
            return False


class ZypperPackageManager(PackageManager):
    """Zypper package manager (OpenSUSE)."""

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
                return False
        except Exception as e:
            printWarning(f"Failed to update Zypper packages: {e}")
            return False


class PacmanPackageManager(PackageManager):
    """Pacman package manager (ArchLinux)."""

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
                return False
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
    "WingetPackageManager",
    "ZypperPackageManager",
    "runPackageCommand",
]
