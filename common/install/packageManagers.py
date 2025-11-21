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
