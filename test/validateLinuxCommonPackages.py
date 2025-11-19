#!/usr/bin/env python3
"""
Validates linuxCommon packages across ALL package managers (apt, yum, dnf, rpm).
Uses repository APIs to check package availability, not local system state.
Packages that fail in ANY package manager should be removed or moved to OS-specific configs.
"""

import json
import re
import sys
import time
import urllib.parse
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Add project root to path so we can import from common
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent
sys.path.insert(0, str(projectRoot))

from common.common import (
    printError,
    printInfo,
    printSection,
    printSuccess,
    printWarning,
    safePrint,
)


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


class PackageMapper:
    """Maps package names between different package managers."""

    @staticmethod
    def mapForRpm(package: str) -> str:
        """Map Debian/Ubuntu package name to RPM equivalent."""
        return packageMappings.get(package, package)


class PackageManagerChecker(ABC):
    """Abstract base class for package manager checkers."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def checkPackage(self, package: str) -> bool:
        """Check if package exists in this package manager's repositories."""
        pass

    def _fetchUrl(self, url: str, timeout: int = 10) -> Optional[str]:
        """Fetch URL content with error handling."""
        try:
            request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(request, timeout=timeout) as response:
                return response.read().decode('utf-8', errors='ignore')
        except (URLError, HTTPError, TimeoutError):
            return None


class AptChecker(PackageManagerChecker):
    """Checks packages in apt repositories (Debian/Ubuntu)."""

    def __init__(self):
        super().__init__("apt")
        self.baseUrls = [
            "https://packages.ubuntu.com/search",
            "https://packages.debian.org/search",
        ]

    def checkPackage(self, package: str) -> bool:
        """Check if package exists in apt repositories."""
        params = {
            "keywords": package,
            "searchon": "names",
            "suite": "all",
            "section": "all",
        }
        queryString = urllib.parse.urlencode(params)

        for baseUrl in self.baseUrls:
            url = f"{baseUrl}?{queryString}"
            content = self._fetchUrl(url)

            if content and self._parseResponse(content, package):
                return True

        return False

    def _parseResponse(self, content: str, package: str) -> bool:
        """Parse response to determine if package was found."""
        contentLower = content.lower()
        packageLower = package.lower()
        return (
            f"package {packageLower}" in contentLower or
            f">{package}<" in content or
            f">{packageLower}<" in contentLower
        )


class RpmChecker(PackageManagerChecker):
    """Base class for RPM-based package managers (yum, dnf, rpm)."""

    def __init__(self, name: str):
        super().__init__(name)
        self.baseUrls = [
            "https://rpmfind.net/linux/rpm2html/search.php",
            "https://pkgs.org/search/",
            "https://apps.fedoraproject.org/packages",
        ]

    def checkPackage(self, package: str) -> bool:
        """Check if package exists in RPM repositories."""
        rpmPackage = PackageMapper.mapForRpm(package)

        # Try rpmfind.net
        url = f"{self.baseUrls[0]}?query={urllib.parse.quote(rpmPackage)}"
        content = self._fetchUrl(url)
        if content and self._parseRpmFindResponse(content, rpmPackage):
            return True

        # Try pkgs.org
        url = f"{self.baseUrls[1]}?q={urllib.parse.quote(rpmPackage)}"
        content = self._fetchUrl(url)
        if content and self._parsePkgsOrgResponse(content, rpmPackage):
            return True

        # Try Fedora packages
        url = f"{self.baseUrls[2]}/{urllib.parse.quote(rpmPackage)}"
        try:
            request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(request, timeout=10) as response:
                if response.getcode() == 200:
                    return True
        except (URLError, HTTPError, TimeoutError):
            pass

        return False

    def _parseRpmFindResponse(self, content: str, package: str) -> bool:
        """Parse rpmfind.net response."""
        packageLower = package.lower()
        contentLower = content.lower()
        return (
            f">{package}<" in content or
            f">{packageLower}<" in contentLower or
            re.search(rf"href.*{re.escape(package)}", content, re.IGNORECASE) is not None or
            f"package: {package}" in contentLower
        )

    def _parsePkgsOrgResponse(self, content: str, package: str) -> bool:
        """Parse pkgs.org response."""
        packageLower = package.lower()
        return (
            packageLower in content.lower() and
            "no packages found" not in content.lower()
        )


class YumChecker(RpmChecker):
    """Checks packages in yum repositories."""

    def __init__(self):
        super().__init__("yum")


class DnfChecker(RpmChecker):
    """Checks packages in dnf repositories."""

    def __init__(self):
        super().__init__("dnf")


class RpmCheckerImpl(RpmChecker):
    """Checks packages in rpm repositories."""

    def __init__(self):
        super().__init__("rpm")


class PackageValidationResult:
    """Stores validation results for a single package."""

    def __init__(self, package: str):
        self.package = package
        self.aptFound = False
        self.yumFound = False
        self.dnfFound = False
        self.rpmFound = False

    @property
    def isUniversal(self) -> bool:
        """Check if package is available in all package managers."""
        return self.aptFound and self.yumFound and self.rpmFound

    @property
    def isFoundAnywhere(self) -> bool:
        """Check if package is found in at least one package manager."""
        return self.aptFound or self.yumFound or self.dnfFound or self.rpmFound

    @property
    def foundIn(self) -> List[str]:
        """Get list of package managers where package was found."""
        found = []
        if self.aptFound:
            found.append("apt")
        if self.yumFound or self.dnfFound:
            found.append("yum/dnf")
        if self.rpmFound:
            found.append("rpm")
        return found

    @property
    def recommendation(self) -> Tuple[str, str]:
        """
        Get recommendation for this package.
        Returns: (action, target) where action is 'keep', 'move', or 'remove'
        """
        if self.isUniversal:
            return ("keep", "linuxCommon.json")
        elif not self.isFoundAnywhere:
            return ("remove", "linuxCommon.json")
        elif self.aptFound and not (self.yumFound or self.rpmFound):
            return ("move", "ubuntu,raspberrypi")
        elif not self.aptFound and (self.yumFound or self.rpmFound):
            return ("move", "rpm-based")
        else:
            return ("move", "mixed")


class LinuxCommonValidator:
    """Validates linuxCommon packages across all package managers."""

    def __init__(self):
        self.checkers = {
            "apt": AptChecker(),
            "yum": YumChecker(),
            "dnf": DnfChecker(),
            "rpm": RpmCheckerImpl(),
        }
        self.results: List[PackageValidationResult] = []

    def validate(self, configPath: str) -> int:
        """Validate all packages in linuxCommon.json. Returns exit code."""
        packages = self._loadPackages(configPath)
        if not packages:
            printError(f"No packages found in {configPath}")
            return 1

        printSection("Validating Linux Common Packages Across ALL Package Managers")
        safePrint()
        printInfo("Checking each package against: apt, yum, dnf, rpm")
        printInfo("Using repository APIs (not local system state)")
        safePrint()

        for package in packages:
            result = self._validatePackage(package)
            self.results.append(result)
            self._printPackageResult(result)

        return self._printSummary()

    def _loadPackages(self, configPath: str) -> List[str]:
        """Load packages from JSON config file."""
        try:
            with open(configPath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("linuxCommon", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            printError(f"Error loading config: {e}")
            return []

    def _validatePackage(self, package: str) -> PackageValidationResult:
        """Validate a single package against all package managers."""
        result = PackageValidationResult(package)

        printInfo(f"Checking: {package}")

        # Check each package manager
        result.aptFound = self.checkers["apt"].checkPackage(package)
        result.yumFound = self.checkers["yum"].checkPackage(package)
        result.dnfFound = self.checkers["dnf"].checkPackage(package)
        result.rpmFound = self.checkers["rpm"].checkPackage(package)

        # Print individual results
        if result.aptFound:
            printSuccess("  ✓ apt: found")
        else:
            printError("  ✗ apt: not found")

        if result.yumFound or result.dnfFound:
            rpmPackage = PackageMapper.mapForRpm(package)
            if rpmPackage != package:
                printSuccess(f"  ✓ yum/dnf: found (as {rpmPackage})")
            else:
                printSuccess("  ✓ yum/dnf: found")
        else:
            printError("  ✗ yum/dnf: not found")

        if result.rpmFound:
            printSuccess("  ✓ rpm: found")
        else:
            printError("  ✗ rpm: not found")

        return result

    def _printPackageResult(self, result: PackageValidationResult):
        """Print result summary for a package."""
        if result.isUniversal:
            printSuccess("  → Universal: available in all package managers")
        elif result.isFoundAnywhere:
            foundList = ", ".join(result.foundIn)
            printWarning(f"  → Partial: available in {foundList} only")
        else:
            printError("  → FAILED: not found in any package manager")
        safePrint()

    def _printSummary(self) -> int:
        """Print validation summary and return exit code."""
        printSection("Validation Summary")
        safePrint()

        totalPackages = len(self.results)
        universalPackages = sum(1 for r in self.results if r.isUniversal)
        packagesToMove = [r for r in self.results if not r.isUniversal and r.isFoundAnywhere]
        packagesToRemove = [r for r in self.results if not r.isFoundAnywhere]

        printInfo(f"Total packages checked: {totalPackages}")
        printSuccess(f"Universal packages (all managers): {universalPackages}")

        if packagesToMove:
            safePrint()
            printWarning(f"Packages to move to OS-specific configs: {len(packagesToMove)}")
            printInfo("These packages are available in some but not all package managers.")
            safePrint()
            for result in packagesToMove:
                action, target = result.recommendation
                if target == "ubuntu,raspberrypi":
                    printInfo(f"  - {result.package} → Move to ubuntu.json and raspberrypi.json")
                elif target == "rpm-based":
                    printInfo(f"  - {result.package} → Move to RPM-based OS configs (when created)")
                else:
                    printInfo(f"  - {result.package} → Review and move to appropriate OS config")

        if packagesToRemove:
            safePrint()
            printError(f"Packages to remove (not found anywhere): {len(packagesToRemove)}")
            printInfo("These packages were not found in any package manager repository.")
            printInfo("They should be removed from linuxCommon.json")
            safePrint()
            for result in packagesToRemove:
                printError(f"  - {result.package}")

        safePrint()
        if packagesToRemove:
            printError(f"Validation failed: {len(packagesToRemove)} package(s) not found in any package manager")
            printInfo("")
            printInfo("Action required: Remove these packages from linuxCommon.json:")
            for result in packagesToRemove:
                safePrint(f'    "{result.package}",')
            return 1
        elif packagesToMove:
            printWarning("Validation completed with warnings")
            printInfo("")
            printInfo("Action required: Move these packages to OS-specific config files:")
            for result in packagesToMove:
                safePrint(f'    "{result.package}",')
            return 1
        else:
            printSuccess("All packages are available in all package managers!")
            return 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        printError("Usage: python3 validateLinuxCommonPackages.py <path-to-linuxCommon.json>")
        sys.exit(1)

    configPath = sys.argv[1]
    startTime = time.time()

    validator = LinuxCommonValidator()
    exitCode = validator.validate(configPath)

    elapsed = int(time.time() - startTime)
    safePrint()
    printInfo(f"Validation completed in {elapsed}s")

    sys.exit(exitCode)


if __name__ == "__main__":
    main()
