#!/usr/bin/env python3
"""
Unified package validation script.
Takes a JSON config file and validates packages against appropriate package managers.
Uses OOP to abstract package manager validation logic.
"""

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path so we can import from common
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent
sys.path.insert(0, str(projectRoot))

from common.common import (
    commandExists,
    getJsonArray,
    getJsonValue,
    printError,
    printInfo,
    printSection,
    printSuccess,
    printWarning,
    safePrint,
)


class PackageManagerChecker(ABC):
    """Abstract base class for package manager checkers."""

    def __init__(self, name: str, jsonKey: str):
        """
        Initialise package manager checker.

        Args:
            name: Human-readable name of the package manager
            jsonKey: JSON key in config file (e.g., "brew", "apt", "winget")
        """
        self.name = name
        self.jsonKey = jsonKey

    @abstractmethod
    def checkPackage(self, package: str) -> bool:
        """
        Check if a package exists in this package manager.

        Args:
            package: Package name/identifier to check

        Returns:
            True if package exists, False otherwise
        """
        pass

    @abstractmethod
    def isAvailable(self) -> bool:
        """
        Check if this package manager is available on the system.

        Returns:
            True if available, False otherwise
        """
        pass

    def getInstallHint(self) -> str:
        """
        Get installation hint for this package manager.

        Returns:
            Installation hint message
        """
        return f"Please install {self.name} to validate packages."


class BrewChecker(PackageManagerChecker):
    """Checker for Homebrew packages."""

    def __init__(self):
        super().__init__("Homebrew", "brew")

    def isAvailable(self) -> bool:
        return commandExists("brew")

    def checkPackage(self, package: str) -> bool:
        """Check if a brew package exists."""
        try:
            result = subprocess.run(
                ["brew", "info", package],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                output = result.stdout
                if any(marker in output for marker in [f"{package}:", "==>", "From:"]):
                    return True

            return False
        except Exception:
            return False

    def getInstallHint(self) -> str:
        return 'Install with: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'


class BrewCaskChecker(PackageManagerChecker):
    """Checker for Homebrew Cask packages."""

    def __init__(self):
        super().__init__("Homebrew Cask", "brewCask")

    def isAvailable(self) -> bool:
        return commandExists("brew")

    def checkPackage(self, package: str) -> bool:
        """Check if a brew cask package exists."""
        try:
            result = subprocess.run(
                ["brew", "info", "--cask", package],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                output = result.stdout
                if any(marker in output for marker in [f"{package}:", "==>", "From:"]):
                    return True

            return False
        except Exception:
            return False

    def getInstallHint(self) -> str:
        return 'Install Homebrew first: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'


class AptChecker(PackageManagerChecker):
    """Checker for APT packages (Debian/Ubuntu)."""

    def __init__(self):
        super().__init__("APT", "apt")

    def isAvailable(self) -> bool:
        return commandExists("apt-cache")

    def checkPackage(self, package: str) -> bool:
        """Check if an apt package exists."""
        try:
            result = subprocess.run(
                ["apt-cache", "show", package],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False


class SnapChecker(PackageManagerChecker):
    """Checker for Snap packages."""

    def __init__(self):
        super().__init__("Snap", "snap")

    def isAvailable(self) -> bool:
        return commandExists("snap")

    def checkPackage(self, package: str) -> bool:
        """Check if a snap package exists."""
        try:
            result = subprocess.run(
                ["snap", "info", package],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False


class WingetChecker(PackageManagerChecker):
    """Checker for Windows Package Manager (winget) packages."""

    def __init__(self):
        super().__init__("Winget", "winget")

    def isAvailable(self) -> bool:
        # Winget validation uses HTTP API, so always available
        return True

    def checkPackage(self, package: str) -> bool:
        """Check if a winget package exists via winstall.app API."""
        try:
            url = f"https://winstall.app/apps/{package}"
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0")

            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    content = response.read().decode("utf-8")
                    if "Sorry! We could not load this app" not in content:
                        return True

            return False
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False
            return False
        except Exception:
            return False


class WindowsStoreChecker(PackageManagerChecker):
    """Checker for Windows Store packages."""

    def __init__(self):
        super().__init__("Windows Store", "windowsStore")

    def isAvailable(self) -> bool:
        # Windows Store validation not yet implemented
        return True

    def checkPackage(self, package: str) -> bool:
        """Check if a Windows Store package exists."""
        # Not yet implemented - will validate at installation time
        return True


class YumChecker(PackageManagerChecker):
    """Checker for YUM packages (RHEL, CentOS)."""

    def __init__(self):
        super().__init__("YUM", "yum")

    def isAvailable(self) -> bool:
        return commandExists("yum")

    def checkPackage(self, package: str) -> bool:
        """Check if a yum package exists."""
        try:
            result = subprocess.run(
                ["yum", "info", package],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False


class DnfChecker(PackageManagerChecker):
    """Checker for DNF packages (Fedora, newer RHEL)."""

    def __init__(self):
        super().__init__("DNF", "dnf")

    def isAvailable(self) -> bool:
        return commandExists("dnf")

    def checkPackage(self, package: str) -> bool:
        """Check if a dnf package exists."""
        try:
            result = subprocess.run(
                ["dnf", "info", package],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False


class RpmChecker(PackageManagerChecker):
    """Checker for RPM packages (generic RPM-based systems)."""

    def __init__(self):
        super().__init__("RPM", "rpm")

    def isAvailable(self) -> bool:
        return commandExists("rpm")

    def checkPackage(self, package: str) -> bool:
        """
        Check if an rpm package exists.

        Note: RPM doesn't have a direct repository search command like apt/dnf/yum.
        This checks if the package is installed or can be queried.
        For better validation, use yum or dnf checkers on RPM-based systems.
        """
        try:
            # Try to query the package (works if installed or in local cache)
            result = subprocess.run(
                ["rpm", "-q", package],
                capture_output=True,
                check=False,
            )
            # If rpm -q succeeds, package exists (may be installed or in cache)
            if result.returncode == 0:
                return True
            # Check if error indicates "not installed" vs "package not found"
            # "package X is not installed" means package exists but isn't installed
            if result.stderr:
                stderrStr = result.stderr.decode("utf-8", errors="ignore")
                if "is not installed" in stderrStr:
                    return True
            return False
        except Exception:
            return False


class PackageValidator:
    """Main validator class that orchestrates package validation."""

    # Registry of available checkers
    CHECKERS: Dict[str, type] = {
        "brew": BrewChecker,
        "brewCask": BrewCaskChecker,
        "apt": AptChecker,
        "snap": SnapChecker,
        "winget": WingetChecker,
        "windowsStore": WindowsStoreChecker,
        "yum": YumChecker,
        "dnf": DnfChecker,
        "rpm": RpmChecker,
    }

    # Linux package managers for linuxCommon validation
    LINUX_PACKAGE_MANAGERS = ["apt", "yum", "dnf", "rpm"]

    def __init__(self, configPath: str):
        """
        Initialise package validator.

        Args:
            configPath: Path to JSON config file
        """
        self.configPath = Path(configPath)
        self.config = {}
        self.checkers: Dict[str, PackageManagerChecker] = {}
        self.errors = 0

        if not self.configPath.exists():
            raise FileNotFoundError(f"Config file not found: {configPath}")

        # Load config
        with open(self.configPath, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        # Detect and initialise appropriate checkers
        self._initialiseCheckers()

    def _initialiseCheckers(self) -> None:
        """Detect which package managers are used and initialise checkers."""
        # Special handling for linuxCommon - detect available Linux package managers
        if self._isLinuxCommon():
            # For linuxCommon, detect and use all available Linux package managers
            for pmKey in self.LINUX_PACKAGE_MANAGERS:
                if pmKey in self.CHECKERS:
                    checker = self.CHECKERS[pmKey]()
                    if checker.isAvailable():
                        self.checkers[pmKey] = checker
        else:
            # Normal config - use package managers specified in JSON
            for jsonKey, checkerClass in self.CHECKERS.items():
                # Check if this package manager is used in the config
                if jsonKey in self.config and self.config[jsonKey]:
                    checker = checkerClass()
                    self.checkers[jsonKey] = checker

    def _getPlatformName(self) -> str:
        """Get platform name from config file name."""
        name = self.configPath.stem
        # Map config names to platform names
        nameMap = {
            "macos": "macOS",
            "ubuntu": "Ubuntu",
            "raspberrypi": "Raspberry Pi",
            "win11": "Windows 11",
            "linuxCommon": "Linux Common",
        }
        return nameMap.get(name, name.capitalize())

    def _isLinuxCommon(self) -> bool:
        """Check if this is a linuxCommon config file."""
        return self.configPath.stem == "linuxCommon" or "linuxCommon" in self.config

    def _mergeLinuxCommon(self) -> List[str]:
        """Merge linuxCommon packages if enabled."""
        aptPackages = []

        # Check if linuxCommon is enabled
        useLinuxCommon = getJsonValue(str(self.configPath), ".useLinuxCommon", False)

        if useLinuxCommon:
            commonConfigPath = self.configPath.parent / "linuxCommon.json"
            if commonConfigPath.exists():
                printInfo("Merging linuxCommon packages...")
                commonPackages = getJsonArray(str(commonConfigPath), ".linuxCommon[]?")
                distroPackages = getJsonArray(str(self.configPath), ".apt[]?")
                # Merge and deduplicate
                aptPackages = sorted(list(set(commonPackages + distroPackages)))
            else:
                aptPackages = getJsonArray(str(self.configPath), ".apt[]?")
        else:
            aptPackages = getJsonArray(str(self.configPath), ".apt[]?")

        return aptPackages

    def validate(self) -> int:
        """
        Validate all packages in the config.

        Returns:
            0 if all packages are valid, 1 otherwise
        """
        platformName = self._getPlatformName()
        printSection(f"Validating {platformName} Packages")
        safePrint()

        # Special handling for linuxCommon.json - validate against all available Linux package managers
        if self._isLinuxCommon():
            packages = getJsonArray(str(self.configPath), ".linuxCommon[]?")
            if not packages:
                printWarning("No packages found in linuxCommon.json")
                return 0

            if not self.checkers:
                printError("No Linux package managers available on this system.")
                printInfo("Available package managers: apt, yum, dnf, rpm")
                return 1

            printInfo(f"Detected {len(self.checkers)} available Linux package manager(s) on this system:")
            for pmKey in self.checkers.keys():
                printInfo(f"  - {self.checkers[pmKey].name}")
            safePrint()

            # Validate each package against all available package managers
            for package in packages:
                if not package or not package.strip():
                    continue

                package = package.strip()
                foundIn = []
                notFoundIn = []

                # Check package against all available package managers
                for pmKey, checker in self.checkers.items():
                    if checker.checkPackage(package):
                        foundIn.append(checker.name)
                    else:
                        notFoundIn.append(checker.name)

                # Report results
                if foundIn:
                    if len(foundIn) == len(self.checkers):
                        # Found in all package managers - universal package
                        printSuccess(f"  {package} (found in all: {', '.join(foundIn)})")
                    else:
                        # Found in some but not all
                        printWarning(f"  {package} (found in: {', '.join(foundIn)}, missing in: {', '.join(notFoundIn)})")
                        self.errors += 1
                else:
                    # Not found in any package manager
                    printError(f"  {package} (not found in any package manager: {', '.join(notFoundIn)})")
                    self.errors += 1
        else:
            # Normal validation for platform-specific configs
            for jsonKey, checker in self.checkers.items():
                if jsonKey == "apt" and self.config.get("useLinuxCommon") is True:
                    # Special handling for apt with linuxCommon
                    packages = self._mergeLinuxCommon()
                else:
                    packages = getJsonArray(str(self.configPath), f".{jsonKey}[]?")

                if not packages:
                    continue

                # Check if package manager is available
                if not checker.isAvailable():
                    printWarning(f"{checker.name} is not available, skipping {jsonKey} package validation")
                    printInfo(f"  {checker.getInstallHint()}")
                    safePrint()
                    continue

                # Validate packages
                printInfo(f"Validating {checker.name.lower()} packages...")
                for package in packages:
                    if not package or not package.strip():
                        continue

                    package = package.strip()
                    if checker.checkPackage(package):
                        printSuccess(f"  {package}")
                    else:
                        printError(f"  {package} (not found in {checker.name.lower()})")
                        self.errors += 1

                safePrint()

        # Summary
        if self.errors == 0:
            printSuccess(f"All {platformName} packages are valid!")
            return 0
        else:
            printError(f"Found {self.errors} invalid package(s)")
            return 1


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        printError("Usage: python3 validatePackages.py <path-to-config.json>")
        printInfo("Example: python3 validatePackages.py configs/macos.json")
        return 1

    configPath = sys.argv[1]

    try:
        validator = PackageValidator(configPath)
        startTime = time.perf_counter()
        exitCode = validator.validate()
        elapsed = time.perf_counter() - startTime
        safePrint()
        printInfo(f"Validation completed in {elapsed:.2f}s")
        return exitCode
    except FileNotFoundError as e:
        printError(str(e))
        return 1
    except json.JSONDecodeError as e:
        printError(f"Failed to parse JSON config: {e}")
        return 1
    except Exception as e:
        printError(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
