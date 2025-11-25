#!/usr/bin/env python3
"""
Unified status checking script for all platforms.
Checks installed applications, configurations, and repositories.

Usage:
    python3 -m common.systems.status
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

# Add project root to path
scriptDir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(scriptDir))

from common.common import (
    commandExists,
    expandPath,
    getJsonArray,
    getJsonValue,
    isAppInstalled,
    isGitInstalled,
    isWingetInstalled,
    printError,
    printInfo,
    printH2,
    printSuccess,
    printWarning,
    safePrint,
)
from common.systems.update import detectPlatform


def checkGit() -> None:
    """Check Git installation and configuration."""
    printInfo("Git:")
    if isGitInstalled():
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            printSuccess(f"Installed: {result.stdout.strip()}")

            # Check Git configuration
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

            if nameResult.returncode == 0 and emailResult.returncode == 0:
                gitName = nameResult.stdout.strip()
                gitEmail = emailResult.stdout.strip()
                printSuccess(f"Configured: {gitName} <{gitEmail}>")
            else:
                printWarning("Not configured")
        except Exception:
            printError("Error checking Git")
    else:
        printError("Not installed")
    safePrint()


def checkZsh() -> None:
    """Check zsh and Oh My Zsh installation."""
    printInfo("zsh:")
    if commandExists("zsh"):
        try:
            result = subprocess.run(
                ["zsh", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            printSuccess(f"Installed: {result.stdout.strip()}")
        except Exception:
            printSuccess("Installed")

        # Use OhMyZshManager for status (proper OOP)
        from common.install.setupZsh import OhMyZshManager
        omzManager = OhMyZshManager()
        omzManager.printStatus()
    else:
        printError("Not installed")
    safePrint()


def checkPackageManagers(platform) -> None:
    """
    Check package managers using the platform's own managers.
    Uses OOP - delegates to PackageManager instances.

    Args:
        platform: Platform instance (BasePlatform subclass)
    """
    printInfo("Package Managers:")

    for manager in platform.packageManagers:
        if manager.isAvailable():
            version = manager.getVersion()
            printSuccess(f"{manager.getName()}: {version}")
        else:
            printWarning(f"{manager.getName()}: Not available")

    safePrint()


def checkInstalledApps(platform, configPath: Path) -> None:
    """
    Check installed applications using platform's package managers.
    Uses OOP - delegates to PackageManager.check() methods.

    Args:
        platform: Platform instance with packageManagers
        configPath: Path to platform config JSON
    """
    if not configPath.exists():
        return

    printInfo("Installed Applications:")

    try:
        # Load the full config
        with open(configPath, 'r', encoding='utf-8') as f:
            config = json.load(f)

        totalInstalled = 0
        totalNotInstalled = 0

        # Check each package manager's packages
        for manager in platform.packageManagers:
            if not manager.isAvailable():
                continue

            # Get package list for this manager (brew, apt, winget, etc.)
            managerType = manager.getName().lower().replace(" ", "")
            packages = config.get(managerType, [])

            if not packages:
                continue

            installed = sum(1 for pkg in packages if manager.check(pkg))
            notInstalled = len(packages) - installed

            totalInstalled += installed
            totalNotInstalled += notInstalled

            if installed > 0:
                printSuccess(f"{installed} {manager.getName()} package(s) installed")
            if notInstalled > 0:
                printWarning(f"{notInstalled} {manager.getName()} package(s) not installed")

        if totalInstalled == 0 and totalNotInstalled == 0:
            printInfo("No packages configured")

    except Exception as e:
        printWarning(f"Error checking apps: {e}")

    safePrint()


def checkRepositories(platformName: str, configsPath: Optional[Path] = None) -> None:
    """Check repository status."""
    if configsPath is None:
        from common.core.utilities import getConfigDirectory
        configsPath = getConfigDirectory(scriptDir)
    reposConfigPath = configsPath / "repositories.json"

    if not reposConfigPath.exists():
        return

    printInfo("Repositories:")

    try:
        # Get work path based on platform
        if platformName == "win11":
            workPath = getJsonValue(str(reposConfigPath), ".workPathWindows", "")
        else:
            workPath = getJsonValue(str(reposConfigPath), ".workPathUnix", "")

        if not workPath or workPath == "null":
            printWarning(" No work path configured")
            safePrint()
            return

        workPath = expandPath(workPath)
        workPathObj = Path(workPath)

        if workPathObj.exists():
            printSuccess(f"Work directory exists: {workPath}")

            # Count owner directories
            ownerDirs = [d for d in workPathObj.iterdir() if d.is_dir()]
            if ownerDirs:
                printSuccess(f"{len(ownerDirs)} owner directory(ies) found")

                # Count repositories
                totalRepos = 0
                for ownerDir in ownerDirs:
                    repos = [d for d in ownerDir.iterdir() if d.is_dir() and (d / ".git").exists()]
                    totalRepos += len(repos)

                if totalRepos > 0:
                    printSuccess(f"{totalRepos} repository(ies) cloned")
            else:
                printWarning(f"Work directory exists but is empty: {workPath}")
        else:
            printWarning(f"Work directory does not exist: {workPath}")
    except Exception as e:
        printWarning(f"Error checking repositories: {e}")

    safePrint()


def checkCursor(platformName: str) -> None:
    """Check Cursor settings."""
    printInfo("Cursor:")

    if platformName == "win11":
        cursorSettingsPath = Path.home() / "AppData/Roaming/Cursor/User/settings.json"
    else:
        cursorSettingsPath = Path.home() / ".config/Cursor/User/settings.json"

    if cursorSettingsPath.exists():
        printSuccess(" Settings file exists")
    else:
        printWarning(" Settings file not found")
    safePrint()


def checkFonts(platformName: str, fontsConfigPath: Path, fontInstallDir: str) -> None:
    """Check installed fonts."""
    if not fontsConfigPath.exists():
        return

    printInfo("Fonts:")

    try:
        import platform as platformModule

        with open(fontsConfigPath, 'r', encoding='utf-8') as f:
            config = json.load(f)
        fontNames = config.get('googleFonts', [])

        if not fontNames:
            printWarning(" No fonts configured")
            safePrint()
            return

        # Check font installation directory
        installDirPath = Path(fontInstallDir)
        if not installDirPath.exists():
            printWarning(f"Font installation directory does not exist: {fontInstallDir}")
            safePrint()
            return

        printSuccess(f"Font installation directory exists: {fontInstallDir}")

        # Count installed fonts
        system = platformModule.system()
        installedCount = 0
        missingCount = 0

        # Check for font files in the directory
        fontFiles = list(installDirPath.glob("*.ttf")) + list(installDirPath.glob("*.otf"))
        if system == "Windows":
            # Also check system fonts folder
            systemFontsFolder = Path(os.environ.get('WINDIR', 'C:\\Windows')) / 'Fonts'
            if systemFontsFolder.exists():
                fontFiles.extend(systemFontsFolder.glob("*.ttf"))
                fontFiles.extend(systemFontsFolder.glob("*.otf"))

        # For each configured font, check if we have at least one variant installed
        for fontName in fontNames:
            # Normalise font name for matching
            normalisedName = fontName.lower().replace(" ", "-")
            found = False
            for fontFile in fontFiles:
                if normalisedName in fontFile.stem.lower():
                    found = True
                    break
            if found:
                installedCount += 1
            else:
                missingCount += 1
                printWarning(f"{fontName} not found")

        if installedCount > 0:
            printSuccess(f"{installedCount} font(s) installed")
        if missingCount > 0:
            printWarning(f"{missingCount} font(s) not found")
        if installedCount == 0 and missingCount == 0:
            printWarning(" No fonts found in installation directory")

    except Exception as e:
        printWarning(f"Error checking fonts: {e}")

    safePrint()


def runStatusCheck(system: Optional[object] = None) -> int:
    """
    Run status check with optional system instance for better context.

    Args:
        system: Optional SystemBase instance (if None, will detect platform)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    from common.core.logging import printH1
    printH1("jrl_env Status Check")
    safePrint()

    # Get config directory (supports --configDir and JRL_ENV_CONFIG_DIR)
    from common.core.utilities import getConfigDirectory
    configsPath = getConfigDirectory(scriptDir)

    # Get platform name
    if system:
        platformName = system.getPlatformName()
        # Use configManager if available, otherwise build paths manually
        if system.configManager:
            paths = system.configManager.getPaths()
        else:
            # Build minimal paths for status check
            paths = {
                "fontsConfigPath": str(configsPath / "fonts.json"),
                "fontInstallDir": system.getFontInstallDir(),
            }
    else:
        # Detect platform
        platformName = detectPlatform()
        if platformName == "unknown":
            printError("Unable to detect platform")
            return 1
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

    # Check common items
    checkGit()
    checkZsh()

    # Check package managers using platform facade (clean OOP)
    from common.systems.platforms import getCurrentPlatform
    platform = getCurrentPlatform(dryRun=True)
    checkPackageManagers(platform)

    # Check installed apps using platform's package managers (OOP)
    from common.systems.platforms import getCurrentPlatform
    platform = getCurrentPlatform(dryRun=True)
    platformConfigPath = configsPath / f"{platform.getPlatformName()}.json"
    checkInstalledApps(platform, platformConfigPath)

    # Check fonts
    fontsConfigPath = Path(paths.get("fontsConfigPath", configsPath / "fonts.json"))
    fontInstallDir = paths.get("fontInstallDir", "")
    if fontInstallDir:
        checkFonts(platformName, fontsConfigPath, fontInstallDir)

    # Check repositories
    checkRepositories(platformName, configsPath)

    # Check Cursor
    checkCursor(platformName)

    printH2("Status Check Complete")
    printSuccess("Status check completed!")
    return 0


def printHelp() -> None:
    """Print help information for the status script."""
    safePrint(
        "Usage: python3 -m common.systems.status [options]\n"
        "\n"
        "Checks installed applications, configurations, and repositories.\n"
        "\n"
        "Options:\n"
        "--help, -h        Show this help message and exit\n"
        "--quiet, -q       Enable quiet mode (only show errors)\n"
        "--configDir DIR   Use custom configuration directory (default: ./configs)\n"
        "                  Can also be set via JRL_ENV_CONFIG_DIR environment variable\n"
        "\n"
        "Examples:\n"
        "python3 -m common.systems.status\n"
        "python3 -m common.systems.status --quiet\n"
        "python3 -m common.systems.status --configDir /path/to/configs\n"
    )


def main() -> int:
    """Main status check function (standalone entry point)."""
    # Check for --help flag
    if "--help" in sys.argv or "-h" in sys.argv:
        printHelp()
        return 0

    # Parse quiet flag
    quiet = "--quiet" in sys.argv or "-q" in sys.argv
    from common.core.logging import setVerbosityFromArgs
    setVerbosityFromArgs(quiet=quiet, verbose=False)

    result = runStatusCheck()

    # Final success/failure message (always show in quiet mode)
    if quiet:
        from common.core.logging import getVerbosity, Verbosity
        if getVerbosity() == Verbosity.quiet:
            if result == 0:
                safePrint("Success")
            else:
                safePrint("Failure")

    return result


if __name__ == "__main__":
    sys.exit(main())
