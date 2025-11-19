#!/usr/bin/env python3
"""
Setup verification module.
Verifies that setup completed successfully by checking critical components.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, List, Optional

# Add project root to path
scriptDir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(scriptDir))

from common.common import (
    commandExists,
    expandPath,
    getJsonArray,
    getJsonValue,
    isGitInstalled,
    printError,
    printInfo,
    printSection,
    printSuccess,
    printWarning,
    safePrint,
)
from common.systems.update import detectPlatform


def verifyCriticalPackages(platformName: str, configPath: Path, checkFunc: Optional[Callable[[str], bool]], extractor: str) -> tuple[bool, List[str]]:
    """
    Verify that critical packages are installed.

    Args:
        platformName: Platform name
        configPath: Path to platform config JSON
        checkFunc: Function to check if package is installed
        extractor: JSON path extractor (e.g., ".apt[]?")

    Returns:
        Tuple of (allInstalled, missingPackages)
    """
    if not configPath.exists() or not checkFunc:
        return (True, [])

    try:
        packages = getJsonArray(str(configPath), extractor)
        missing = []

        for package in packages:
            if not package or not package.strip():
                continue
            package = package.strip()
            if not checkFunc(package):
                missing.append(package)

        return (len(missing) == 0, missing)
    except Exception:
        return (True, [])  # If we can't check, assume OK


def verifyGitConfig() -> bool:
    """Verify that Git is configured with user name and email."""
    if not isGitInstalled():
        return False

    try:
        nameResult = subprocess.run(
            ["git", "config", "--global", "user.name"],
            capture_output=True,
            text=True,
            check=False,
        )
        emailResult = subprocess.run(
            ["git", "config", "--global", "user.email"],
            capture_output=True,
            text=True,
            check=False,
        )

        return nameResult.returncode == 0 and emailResult.returncode == 0
    except Exception:
        return False


def verifyFonts(platformName: str, fontsConfigPath: Path, fontInstallDir: str) -> bool:
    """Verify that fonts are installed."""
    if not fontsConfigPath.exists():
        return True  # No fonts configured, so nothing to verify

    try:
        import json
        import platform as platformModule

        with open(fontsConfigPath, 'r', encoding='utf-8') as f:
            config = json.load(f)
        fontNames = config.get('googleFonts', [])

        if not fontNames:
            return True  # No fonts configured

        installDirPath = Path(fontInstallDir)
        if not installDirPath.exists():
            return False

        system = platformModule.system()
        fontFiles = list(installDirPath.glob("*.ttf")) + list(installDirPath.glob("*.otf"))
        if system == "Windows":
            systemFontsFolder = Path(os.environ.get('WINDIR', 'C:\\Windows')) / 'Fonts'
            if systemFontsFolder.exists():
                fontFiles.extend(systemFontsFolder.glob("*.ttf"))
                fontFiles.extend(systemFontsFolder.glob("*.otf"))

        # Check if we have at least one font file for each configured font
        for fontName in fontNames:
            normalisedName = fontName.lower().replace(" ", "-")
            found = any(normalisedName in fontFile.stem.lower() for fontFile in fontFiles)
            if not found:
                return False

        return True
    except Exception:
        return False


def verifySshConnectivity() -> bool:
    """Test SSH key connectivity to GitHub."""
    if not commandExists("ssh"):
        return False

    try:
        # Test SSH connection to GitHub
        # GitHub returns exit code 1 for successful authentication (with "Hi username!" message)
        # Exit code 255 typically means connection/auth failed
        result = subprocess.run(
            ["ssh", "-T", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5", "git@github.com"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        output = (result.stdout + result.stderr).lower()

        # Check for success indicators
        if result.returncode == 1:
            # GitHub returns 1 with success message like "Hi username! You've successfully authenticated..."
            if "successfully authenticated" in output or "hi" in output:
                return True

        # Exit code 0 might also indicate success in some cases
        if result.returncode == 0:
            return True

        return False
    except subprocess.TimeoutExpired:
        return False
    except FileNotFoundError:
        # SSH not available
        return False
    except Exception:
        return False


def getAppChecker(platformName: str) -> tuple[Optional[Callable[[str], bool]], str]:
    """
    Get platform-specific app checker function and extractor.

    Returns:
        Tuple of (checkFunc, extractor)
    """
    if platformName == "win11":
        from common.common import isAppInstalled
        return (isAppInstalled, ".winget[]?")

    elif platformName == "macos":
        def checkBrew(app: str) -> bool:
            try:
                result = subprocess.run(
                    ["brew", "list", app],
                    capture_output=True,
                    check=False,
                )
                return result.returncode == 0
            except Exception:
                return False
        return (checkBrew, ".brew[]?")

    elif platformName in ("ubuntu", "raspberrypi"):
        def checkApt(app: str) -> bool:
            try:
                result = subprocess.run(
                    ["dpkg", "-l", app],
                    capture_output=True,
                    check=False,
                )
                return result.returncode == 0
            except Exception:
                return False
        return (checkApt, ".apt[]?")

    elif platformName == "redhat":
        def checkDnf(app: str) -> bool:
            try:
                result = subprocess.run(
                    ["rpm", "-q", app],
                    capture_output=True,
                    check=False,
                )
                return result.returncode == 0
            except Exception:
                return False
        return (checkDnf, ".dnf[]?")

    elif platformName == "opensuse":
        def checkZypper(app: str) -> bool:
            try:
                result = subprocess.run(
                    ["rpm", "-q", app],
                    capture_output=True,
                    check=False,
                )
                return result.returncode == 0
            except Exception:
                return False
        return (checkZypper, ".zypper[]?")

    elif platformName == "archlinux":
        def checkPacman(app: str) -> bool:
            try:
                result = subprocess.run(
                    ["pacman", "-Q", app],
                    capture_output=True,
                    check=False,
                )
                return result.returncode == 0
            except Exception:
                return False
        return (checkPacman, ".pacman[]?")

    return (None, "")


def runVerification(system: Optional[object] = None) -> bool:
    """
    Run setup verification checks.

    Args:
        system: Optional SystemBase instance (if None, will detect platform)

    Returns:
        True if all verifications passed, False otherwise
    """
    printSection("Setup Verification")
    safePrint()

    # Get config directory (supports --configDir and JRL_ENV_CONFIG_DIR)
    from common.core.utilities import getConfigDirectory
    configsPath = getConfigDirectory(scriptDir)

    # Get platform name
    if system:
        platformName = system.getPlatformName()
        paths = system.setupPaths()
    else:
        platformName = detectPlatform()
        if platformName == "unknown":
            printError("Unable to detect platform for verification")
            return False
        paths = {
            "fontsConfigPath": str(configsPath / "fonts.json"),
            "fontInstallDir": Path.home() / ".local/share/fonts" if platformName != "win11" else str(Path.home() / "AppData/Local/Microsoft/Windows/Fonts"),
        }
        if platformName == "win11":
            paths["fontInstallDir"] = str(Path.home() / "AppData/Local/Microsoft/Windows/Fonts")
        elif platformName == "Darwin":
            paths["fontInstallDir"] = str(Path.home() / "Library/Fonts")
        else:
            paths["fontInstallDir"] = str(Path.home() / ".local/share/fonts")

    allPassed = True

    # 1. Check critical packages
    printInfo("1. Verifying critical packages...")
    platformConfigPath = configsPath / f"{platformName}.json"
    checkFunc, extractor = getAppChecker(platformName)

    if checkFunc:
        packagesOk, missingPackages = verifyCriticalPackages(platformName, platformConfigPath, checkFunc, extractor)
        if packagesOk:
            printSuccess(" All critical packages are installed")
        else:
            printWarning(f" {len(missingPackages)} critical package(s) missing: {', '.join(missingPackages)}")
            allPassed = False
    else:
        printWarning(" Could not verify packages (no checker available)")
    safePrint()

    # 2. Verify Git config
    printInfo("2. Verifying Git configuration...")
    if verifyGitConfig():
        printSuccess(" Git is configured with user name and email")
    else:
        printError(" Git is not properly configured")
        allPassed = False
    safePrint()

    # 3. Verify fonts
    printInfo("3. Verifying fonts...")
    fontsConfigPath = Path(paths.get("fontsConfigPath", configsPath / "fonts.json"))
    fontInstallDir = paths.get("fontInstallDir", "")
    if fontInstallDir:
        if verifyFonts(platformName, fontsConfigPath, fontInstallDir):
            printSuccess(" All configured fonts are installed")
        else:
            printWarning(" Some configured fonts may be missing")
            allPassed = False
    else:
        printInfo("  ℹ No font installation directory configured")
    safePrint()

    # 4. Test SSH connectivity
    printInfo("4. Testing SSH key connectivity to GitHub...")
    if verifySshConnectivity():
        printSuccess(" SSH key authentication to GitHub is working")
    else:
        printWarning(" SSH key connectivity to GitHub failed or not configured")
        printInfo("    This is not critical if you don't use SSH for Git operations")
    safePrint()

    if allPassed:
        printSuccess("All critical verifications passed!")
    else:
        printWarning("Some verifications had issues. Review the output above.")

    return allPassed


def main() -> int:
    """Main verification entry point (standalone)."""
    import sys
    from common.core.logging import setVerbosityFromArgs, getVerbosity, Verbosity

    # Check for --help flag
    if "--help" in sys.argv or "-h" in sys.argv:
        print(
            "Usage: python3 -m common.systems.verify [options]\n"
            "\n"
            "Verifies that setup completed successfully by checking critical components.\n"
            "\n"
            "Options:\n"
            "  --help, -h        Show this help message and exit\n"
            "  --quiet, -q       Enable quiet mode (only show errors)\n"
            "  --configDir DIR   Use custom configuration directory (default: ./configs)\n"
            "                    Can also be set via JRL_ENV_CONFIG_DIR environment variable\n"
            "\n"
            "Examples:\n"
            "  python3 -m common.systems.verify\n"
            "  python3 -m common.systems.verify --quiet\n"
            "  python3 -m common.systems.verify --configDir /path/to/configs\n"
        )
        return 0

    # Parse quiet flag
    quiet = "--quiet" in sys.argv or "-q" in sys.argv
    setVerbosityFromArgs(quiet=quiet, verbose=False)

    result = 0 if runVerification(None) else 1

    # Final success/failure message (always show in quiet mode)
    if getVerbosity() == Verbosity.quiet:
        if result == 0:
            print("Success")
        else:
            print("Failure")

    return result


if __name__ == "__main__":
    sys.exit(main())
