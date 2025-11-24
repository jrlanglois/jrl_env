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

from common.core.logging import printError


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
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            cmdStr = " ".join(cmd)
            stderr = e.stderr.strip() if e.stderr else "No error output"
            printError(f"Failed to install '{package}': Command '{cmdStr}' returned exit code {e.returncode}")
            if stderr:
                printError(f"Error output: {stderr}")
            return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to install '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

    def update(self, package: str) -> bool:
        cmd = ["sudo", "apt-get", "install", "--only-upgrade", "-y", package]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            cmdStr = " ".join(cmd)
            stderr = e.stderr.strip() if e.stderr else "No error output"
            printError(f"Failed to update '{package}': Command '{cmdStr}' returned exit code {e.returncode}")
            if stderr:
                printError(f"Error output: {stderr}")
            return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to update '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

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
        cmd = ["sudo", "snap", "install", package]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            cmdStr = " ".join(cmd)
            stderr = e.stderr.strip() if e.stderr else "No error output"
            printError(f"Failed to install '{package}': Command '{cmdStr}' returned exit code {e.returncode}")
            if stderr:
                printError(f"Error output: {stderr}")
            return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to install '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

    def update(self, package: str) -> bool:
        cmd = ["sudo", "snap", "refresh", package]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            cmdStr = " ".join(cmd)
            stderr = e.stderr.strip() if e.stderr else "No error output"
            printError(f"Failed to update '{package}': Command '{cmdStr}' returned exit code {e.returncode}")
            if stderr:
                printError(f"Error output: {stderr}")
            return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to update '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

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
        cmd = ["brew", "install", package]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            cmdStr = " ".join(cmd)
            stderr = e.stderr.strip() if e.stderr else "No error output"
            printError(f"Failed to install '{package}': Command '{cmdStr}' returned exit code {e.returncode}")
            if stderr:
                printError(f"Error output: {stderr}")
            return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to install '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

    def update(self, package: str) -> bool:
        cmd = ["brew", "upgrade", package]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            cmdStr = " ".join(cmd)
            stderr = e.stderr.strip() if e.stderr else "No error output"
            printError(f"Failed to update '{package}': Command '{cmdStr}' returned exit code {e.returncode}")
            if stderr:
                printError(f"Error output: {stderr}")
            return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to update '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

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
        cmd = ["brew", "install", "--cask", package]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            cmdStr = " ".join(cmd)
            stderr = e.stderr.strip() if e.stderr else "No error output"
            printError(f"Failed to install '{package}': Command '{cmdStr}' returned exit code {e.returncode}")
            if stderr:
                printError(f"Error output: {stderr}")
            return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to install '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

    def update(self, package: str) -> bool:
        cmd = ["brew", "upgrade", "--cask", package]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            cmdStr = " ".join(cmd)
            stderr = e.stderr.strip() if e.stderr else "No error output"
            printError(f"Failed to update '{package}': Command '{cmdStr}' returned exit code {e.returncode}")
            if stderr:
                printError(f"Error output: {stderr}")
            return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to update '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

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
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return True
            else:
                cmdStr = " ".join(cmd)
                stderr = result.stderr.strip() if result.stderr else "No error output"
                printError(f"Failed to install '{package}': Command '{cmdStr}' returned exit code {result.returncode}")
                if stderr:
                    printError(f"Error output: {stderr}")
                return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to install '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

    def update(self, package: str) -> bool:
        cmd = [
            "winget",
            "upgrade",
            "--id", package,
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--silent",
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return True
            else:
                cmdStr = " ".join(cmd)
                stderr = result.stderr.strip() if result.stderr else "No error output"
                printError(f"Failed to update '{package}': Command '{cmdStr}' returned exit code {result.returncode}")
                if stderr:
                    printError(f"Error output: {stderr}")
                return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to update '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

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
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return True
            else:
                cmdStr = " ".join(cmd)
                stderr = result.stderr.strip() if result.stderr else "No error output"
                printError(f"Failed to install '{package}': Command '{cmdStr}' returned exit code {result.returncode}")
                if stderr:
                    printError(f"Error output: {stderr}")
                return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to install '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

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
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return True
            else:
                cmdStr = " ".join(cmd)
                stderr = result.stderr.strip() if result.stderr else "No error output"
                printError(f"Failed to update '{package}': Command '{cmdStr}' returned exit code {result.returncode}")
                if stderr:
                    printError(f"Error output: {stderr}")
                return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to update '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

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
        cmd = ["sudo", "dnf", "install", "-y", package]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            cmdStr = " ".join(cmd)
            stderr = e.stderr.strip() if e.stderr else "No error output"
            printError(f"Failed to install '{package}': Command '{cmdStr}' returned exit code {e.returncode}")
            if stderr:
                printError(f"Error output: {stderr}")
            return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to install '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

    def update(self, package: str) -> bool:
        cmd = ["sudo", "dnf", "upgrade", "-y", package]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            cmdStr = " ".join(cmd)
            stderr = e.stderr.strip() if e.stderr else "No error output"
            printError(f"Failed to update '{package}': Command '{cmdStr}' returned exit code {e.returncode}")
            if stderr:
                printError(f"Error output: {stderr}")
            return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to update '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

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
        cmd = ["sudo", "zypper", "install", "-y", package]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            cmdStr = " ".join(cmd)
            stderr = e.stderr.strip() if e.stderr else "No error output"
            printError(f"Failed to install '{package}': Command '{cmdStr}' returned exit code {e.returncode}")
            if stderr:
                printError(f"Error output: {stderr}")
            return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to install '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

    def update(self, package: str) -> bool:
        cmd = ["sudo", "zypper", "update", "-y", package]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            cmdStr = " ".join(cmd)
            stderr = e.stderr.strip() if e.stderr else "No error output"
            printError(f"Failed to update '{package}': Command '{cmdStr}' returned exit code {e.returncode}")
            if stderr:
                printError(f"Error output: {stderr}")
            return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to update '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

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
        cmd = ["sudo", "pacman", "-S", "--noconfirm", package]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            cmdStr = " ".join(cmd)
            stderr = e.stderr.strip() if e.stderr else "No error output"
            printError(f"Failed to install '{package}': Command '{cmdStr}' returned exit code {e.returncode}")
            if stderr:
                printError(f"Error output: {stderr}")
            return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to install '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

    def update(self, package: str) -> bool:
        cmd = ["sudo", "pacman", "-S", "--noconfirm", "--needed", package]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            cmdStr = " ".join(cmd)
            stderr = e.stderr.strip() if e.stderr else "No error output"
            printError(f"Failed to update '{package}': Command '{cmdStr}' returned exit code {e.returncode}")
            if stderr:
                printError(f"Error output: {stderr}")
            return False
        except Exception as e:
            cmdStr = " ".join(cmd)
            printError(f"Failed to update '{package}': Command '{cmdStr}' raised exception: {e}")
            return False

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
    "SnapPackageManager",
    "BrewPackageManager",
    "BrewCaskPackageManager",
    "WingetPackageManager",
    "StorePackageManager",
    "DnfPackageManager",
    "ZypperPackageManager",
    "PacmanPackageManager",
]
