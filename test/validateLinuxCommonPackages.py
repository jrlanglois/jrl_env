#!/usr/bin/env python3
"""
Validates linuxCommon.json packages for each package manager.
Uses repository APIs to check package availability, not local system state.
Each package manager section (apt, dnf, pacman, zypper) is validated independently.
Uses thread pool for parallel API calls (much faster than sequential).
"""

import json
import re
import sys
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Add project root to path
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent
sys.path.insert(0, str(projectRoot))

from common.common import (
    printError,
    printInfo,
    printH2,
    printSuccess,
    printWarning,
    safePrint,
)


class PackageManagerChecker(ABC):
    """Abstract base class for package manager checkers."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def checkPackage(self, package: str) -> bool:
        """Check if package exists in this package manager's repositories."""
        pass

    def fetchUrl(self, url: str, timeout: int = 10) -> Optional[str]:
        """Fetch URL content with error handling."""
        try:
            request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(request, timeout=timeout) as response:
                return response.read().decode('utf-8', errors='ignore')
        except (URLError, HTTPError, TimeoutError):
            return None


class AptChecker(PackageManagerChecker):
    """Checks packages in APT repositories (Debian/Ubuntu)."""

    def __init__(self):
        super().__init__("apt")
        self.baseUrls = [
            "https://packages.ubuntu.com/search",
            "https://packages.debian.org/search",
        ]

    def checkPackage(self, package: str) -> bool:
        """Check if package exists in APT repositories."""
        params = f"?keywords={package}&searchon=names&suite=all&section=all"

        for baseUrl in self.baseUrls:
            url = baseUrl + params
            content = self.fetchUrl(url)
            if content and package in content:
                return True

        return False


class DnfChecker(PackageManagerChecker):
    """Checks packages in DNF repositories (Fedora/RHEL 8+)."""

    def __init__(self):
        super().__init__("dnf")

    def checkPackage(self, package: str) -> bool:
        """Check if package exists in DNF/Fedora repositories."""
        # Use Fedora packages API
        url = f"https://packages.fedoraproject.org/pkgs/{package}/"
        content = self.fetchUrl(url)
        return content is not None and "Package not found" not in content


class PacmanChecker(PackageManagerChecker):
    """Checks packages in Pacman repositories (Arch Linux)."""

    def __init__(self):
        super().__init__("pacman")

    def checkPackage(self, package: str) -> bool:
        """Check if package exists in Arch repositories."""
        # Use Arch Linux package search
        url = f"https://archlinux.org/packages/search/json/?name={package}"
        content = self.fetchUrl(url)
        if content:
            try:
                data = json.loads(content)
                return len(data.get("results", [])) > 0
            except json.JSONDecodeError:
                pass
        return False


class ZypperChecker(PackageManagerChecker):
    """Checks packages in Zypper repositories (OpenSUSE)."""

    def __init__(self):
        super().__init__("zypper")

    def checkPackage(self, package: str) -> bool:
        """Check if package exists in OpenSUSE repositories."""
        # Use OpenSUSE software search
        url = f"https://software.opensuse.org/search?q={package}"
        content = self.fetchUrl(url)
        return content is not None and package in content


class SnapChecker(PackageManagerChecker):
    """Checks packages in Snap Store."""

    def __init__(self):
        super().__init__("snap")

    def checkPackage(self, package: str) -> bool:
        """Check if package exists in Snap Store."""
        # Use snapcraft.io API
        url = f"https://snapcraft.io/api/v2/snaps/info/{package}"
        content = self.fetchUrl(url)
        if content:
            try:
                data = json.loads(content)
                return "error-list" not in data
            except json.JSONDecodeError:
                pass
        return False


class FlatpakChecker(PackageManagerChecker):
    """Checks packages in Flathub."""

    def __init__(self):
        super().__init__("flatpak")

    def checkPackage(self, package: str) -> bool:
        """Check if package exists in Flathub."""
        # Flathub API
        url = f"https://flathub.org/api/v2/appstream/{package}"
        content = self.fetchUrl(url)
        return content is not None and len(content) > 10


class LinuxCommonValidator:
    """Validates packages for each package manager in linuxCommon.json."""

    def __init__(self):
        self.checkers: Dict[str, PackageManagerChecker] = {
            "apt": AptChecker(),
            "dnf": DnfChecker(),
            "pacman": PacmanChecker(),
            "zypper": ZypperChecker(),
            "snap": SnapChecker(),
            "flatpak": FlatpakChecker(),
        }
        self.results: Dict[str, List[Tuple[str, bool]]] = {}

    def validatePackageManager(self, pm: str, packages: List[str], maxWorkers: int = 10) -> List[Tuple[str, bool]]:
        """
        Validate packages for a specific package manager using parallel threads.

        Args:
            pm: Package manager name
            packages: List of package names to validate
            maxWorkers: Maximum number of parallel threads (default: 10)

        Returns:
            List of tuples (package_name, found)
        """
        if pm not in self.checkers:
            printWarning(f"  No checker implemented for {pm}, skipping")
            return [(pkg, True) for pkg in packages]

        checker = self.checkers[pm]
        results = []

        def checkSinglePackage(package: str) -> Tuple[str, bool]:
            """Check a single package (for thread pool)."""
            found = checker.checkPackage(package)
            return (package, found)

        # Use ThreadPoolExecutor for parallel API calls
        with ThreadPoolExecutor(max_workers=maxWorkers) as executor:
            # Submit all package checks
            futureToPackage = {
                executor.submit(checkSinglePackage, pkg): pkg
                for pkg in packages
            }

            # Collect results as they complete
            for future in as_completed(futureToPackage):
                package = futureToPackage[future]
                try:
                    pkgName, found = future.result()
                    results.append((pkgName, found))

                    if found:
                        printSuccess(f"  ✓ {pkgName}")
                    else:
                        printError(f"  ✗ {pkgName}")
                except Exception as e:
                    printError(f"  ✗ {package}: Error - {e}")
                    results.append((package, False))

        # Sort results by original package order
        packageOrder = {pkg: i for i, pkg in enumerate(packages)}
        results.sort(key=lambda x: packageOrder.get(x[0], 999))

        return results

    def printSummary(self) -> int:
        """Print validation summary and return exit code."""
        printH2("Validation Summary")
        safePrint()

        allPassed = True
        totalChecked = 0

        for pm, results in self.results.items():
            totalChecked += len(results)
            failed = [pkg for pkg, found in results if not found]

            if failed:
                printError(f"✗ {pm}: {len(failed)}/{len(results)} packages NOT FOUND")
                for pkg in failed:
                    printError(f"    {pkg}")
                allPassed = False
            else:
                printSuccess(f"✓ {pm}: All {len(results)} packages exist")

        safePrint()
        printInfo(f"Total packages validated: {totalChecked}")

        if allPassed:
            printSuccess("✅ All packages validated successfully!")
            return 0
        else:
            printError("❌ Some packages not found")
            printInfo("Fix package names in linuxCommon.json")
            return 1


def loadLinuxCommon(configPath: Path) -> Dict[str, List[str]]:
    """Load package manager sections from linuxCommon.json."""
    try:
        with open(configPath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {
                "apt": data.get("apt", []),
                "dnf": data.get("dnf", []),
                "pacman": data.get("pacman", []),
                "zypper": data.get("zypper", []),
                "snap": data.get("snap", []),
                "flatpak": data.get("flatpak", []),
            }
    except (FileNotFoundError, json.JSONDecodeError) as e:
        printError(f"Error loading config: {e}")
        return {}


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        printError("Usage: python3 validateLinuxCommonPackages.py <path-to-linuxCommon.json> [package-manager] [--quiet]")
        printInfo("")
        printInfo("Options:")
        printInfo("  --all        Validate all package managers (default)")
        printInfo("  --quiet      Suppress detailed output")
        printInfo("  apt          Validate only APT packages")
        printInfo("  dnf          Validate only DNF packages")
        printInfo("  pacman       Validate only Pacman packages")
        printInfo("  zypper       Validate only Zypper packages")
        printInfo("  snap         Validate only Snap packages")
        printInfo("  flatpak      Validate only Flatpak packages")
        return 1

    configPath = Path(sys.argv[1])
    if not configPath.exists():
        printError(f"Config file not found: {configPath}")
        return 1

    # Parse arguments
    quiet = "--quiet" in sys.argv
    checkAll = "--all" in sys.argv or len(sys.argv) == 2

    # Determine which package managers to check
    managersToCheck = ["apt", "dnf", "pacman", "zypper", "snap", "flatpak"] if checkAll else []
    for arg in sys.argv[2:]:
        if arg in ["apt", "dnf", "pacman", "zypper", "snap", "flatpak"]:
            managersToCheck = [arg]
            break

    printH2("Validating linuxCommon.json Packages")
    safePrint()
    printInfo(f"Checking package managers: {', '.join(managersToCheck)}")
    printInfo("Using repository APIs (not local system state)")
    safePrint()

    # Load package sections
    packageSections = loadLinuxCommon(configPath)
    if not packageSections:
        printError("Failed to load package sections")
        return 1

    # Create validator
    startTime = time.time()
    validator = LinuxCommonValidator()

    # Validate each requested package manager
    for pm in managersToCheck:
        packages = packageSections.get(pm, [])
        if not packages:
            printWarning(f"{pm}: No packages defined")
            continue

        printInfo(f"\nValidating {len(packages)} {pm} packages...")
        safePrint()
        results = validator.validatePackageManager(pm, packages)
        validator.results[pm] = results

    elapsedTime = int(time.time() - startTime)

    # Print summary
    exitCode = validator.printSummary()

    printInfo(f"Validation completed in {elapsedTime}s")

    return exitCode


if __name__ == "__main__":
    sys.exit(main())
