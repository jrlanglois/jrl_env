#!/usr/bin/env python3
"""
Unified CLI for running individual system operations.
Replaces the need for individual wrapper scripts.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
scriptDir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(scriptDir))

from common.systems.systemBase import SystemBase
from common.core.logging import safePrint


def getSystemClass(platformName: str):
    """
    Get the system class for the given platform.

    Args:
        platformName: Platform name (e.g., "ubuntu", "macos", "win11")

    Returns:
        GenericSystem configured for the platform
    """
    try:
        from common.systems.genericSystem import GenericSystem
        from common.systems.platform import Platform

        # Convert platform name to Platform enum
        try:
            platform = Platform[platformName]
            # Return a lambda that creates GenericSystem with the platform
            return lambda projectRoot: GenericSystem(projectRoot, platform)
        except KeyError:
            return None
    except (ImportError, AttributeError):
        return None


def runOperation(system: SystemBase, operation: str, dryRun: bool = False) -> int:
    """
    Run a specific operation on a system.

    Args:
        system: System instance
        operation: Operation name (fonts, apps, git, ssh, cursor, repos)
        dryRun: If True, don't actually make changes

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    from common.common import (
        configureCursor,
        configureGit,
        configureGithubSsh,
        cloneRepositories,
        printError,
        printInfo,
        printH2,
        printSuccess,
        printWarning,
        safePrint,
    )

    paths = system.setupPaths()

    if operation == "fonts":
        printH2("Installing fonts", dryRun=dryRun)
        if system.installGoogleFonts(paths["fontsConfigPath"], paths["fontInstallDir"], dryRun):
            printSuccess("Font installation completed")
            return 0
        else:
            printWarning("Font installation had some issues")
            return 1

    elif operation == "apps":
        printH2("Installing applications", dryRun=dryRun)
        if system.installOrUpdateApps(paths["platformConfigPath"], dryRun):
            printSuccess("Application installation completed")
            return 0
        else:
            printWarning("Application installation had some issues")
            return 1

    elif operation == "git":
        printH2("Configuring Git", dryRun=dryRun)
        if configureGit(paths["gitConfigPath"], dryRun=dryRun):
            printSuccess("Git configuration completed")
            return 0
        else:
            printWarning("Git configuration had some issues")
            return 1

    elif operation == "ssh":
        printH2("Configuring GitHub SSH", dryRun=dryRun)
        if configureGithubSsh(paths["gitConfigPath"], dryRun=dryRun):
            printSuccess("GitHub SSH configuration completed")
            return 0
        else:
            printWarning("GitHub SSH configuration had some issues")
            return 1

    elif operation == "cursor":
        printH2("Configuring Cursor", dryRun=dryRun)
        if configureCursor(paths["cursorConfigPath"], paths["cursorSettingsPath"], dryRun=dryRun):
            printSuccess("Cursor configuration completed")
            return 0
        else:
            printWarning("Cursor configuration had some issues")
            return 1

    elif operation == "repos":
        printH2("Cloning repositories", dryRun=dryRun)
        from common.install.setupUtils import shouldCloneRepositories
        if dryRun or shouldCloneRepositories(paths["reposConfigPath"], system.getRepositoryWorkPathKey()):
            if cloneRepositories(paths["reposConfigPath"], dryRun=dryRun):
                printSuccess("Repository cloning completed")
                return 0
            else:
                printWarning("Repository cloning had some issues")
                return 1
        else:
            printWarning("Repositories directory already exists with content. Skipping repository cloning.")
            return 0

    elif operation == "status":
        from common.systems.status import runStatusCheck
        return runStatusCheck(system)

    elif operation == "rollback":
        from common.install.rollback import getLatestSession, rollback

        latestSession = getLatestSession()
        if not latestSession:
            printError("No rollback session found")
            return 1

        # Get uninstall function based on platform
        platformName = system.getPlatformName()
        uninstallFunc = None

        if platformName == "macos":
            def uninstallBrew(package: str) -> bool:
                try:
                    result = subprocess.run(
                        ["brew", "uninstall", package],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    return result.returncode == 0
                except Exception:
                    return False
            uninstallFunc = uninstallBrew
        elif platformName in ("ubuntu", "raspberrypi"):
            def uninstallApt(package: str) -> bool:
                try:
                    result = subprocess.run(
                        ["sudo", "apt-get", "remove", "-y", package],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    return result.returncode == 0
                except Exception:
                    return False
            uninstallFunc = uninstallApt
        # Add more platforms as needed

        return 0 if rollback(latestSession, uninstallFunc) else 1

    elif operation == "verify":
        from common.systems.verify import runVerification
        return 0 if runVerification(system) else 1

    else:
        printError(f"Unknown operation: {operation}")
        printInfo("Valid operations: fonts, apps, git, ssh, cursor, repos, status, rollback, verify")
        return 1


def printHelp() -> None:
    """Print help information for the CLI."""
    from common.core.logging import printHelpText

    printHelpText(
        title="Unified CLI",
        intent=[
            "Run individual setup operations without running the full setup process.",
            "Useful for updating specific components or troubleshooting.",
        ],
        usage="python3 -m common.systems.cli <platform> <operation> [options]",
        sections={
            "Platforms": [
                "macos       - macOS",
                "win11       - Windows 11",
                "",
                "APT-based Linux:",
                "debian      - Debian",
                "ubuntu      - Ubuntu",
                "popos       - Pop!_OS",
                "linuxmint   - Linux Mint",
                "elementary  - Elementary OS",
                "zorin       - Zorin OS",
                "mxlinux     - MX Linux",
                "raspberrypi - Raspberry Pi OS",
                "",
                "RPM-based Linux:",
                "fedora      - Fedora",
                "redhat      - RedHat/CentOS",
                "",
                "Other Linux:",
                "opensuse    - OpenSUSE",
                "archlinux   - Arch Linux",
                "manjaro     - Manjaro",
                "endeavouros - EndeavourOS",
                "alpine      - Alpine Linux",
            ],
            "Operations": [
                "fonts    - Install Google Fonts from configs/fonts.json",
                "apps     - Install/update applications from platform config",
                "git      - Configure Git with settings from configs/gitConfig.json",
                "ssh      - Set up GitHub SSH keys",
                "cursor   - Configure Cursor editor with settings from configs/cursorSettings.json",
                "repos    - Clone repositories from configs/repositories.json",
                "status   - Check environment status (packages, Git, fonts, repos)",
                "rollback - Rollback the last setup session",
                "verify   - Verify installed packages and configurations",
            ],
        },
        options=[
            ("--help, -h", "Show this help message and exit"),
            ("--version, -v", "Show version information and exit"),
            ("--verbose", "Enable verbose output (show debug messages)"),
            ("--quiet, -q", "Enable quiet mode (only show errors)"),
            ("--dryRun", "Preview changes without making them"),
            ("--configDir DIR", "Use custom configuration directory (default: ./configs)\n"
             "                  Can also be set via JRL_ENV_CONFIG_DIR environment variable"),
        ],
        examples=[
            "python3 -m common.systems.cli ubuntu fonts",
            "python3 -m common.systems.cli macos apps --dryRun",
            "python3 -m common.systems.cli win11 git",
            "python3 -m common.systems.cli ubuntu status",
            "python3 -m common.systems.cli ubuntu rollback",
        ],
    )


def main() -> int:
    """Main CLI entry point."""
    # Parse verbosity flags early
    quiet = "--quiet" in sys.argv or "-q" in sys.argv
    verbose = "--verbose" in sys.argv
    from common.core.logging import setVerbosityFromArgs
    setVerbosityFromArgs(quiet=quiet, verbose=verbose)

    # Check for --help flag
    if "--help" in sys.argv or "-h" in sys.argv:
        printHelp()
        return 0

    # Check for --version flag
    if "--version" in sys.argv or "-v" in sys.argv:
        from common.version import __version__
        safePrint(f"jrl_env version {__version__}")
        return 0

    # Filter out configDir args for platform/operation parsing
    filteredArgs = [arg for arg in sys.argv[1:] if not arg.startswith("--configDir") and arg not in ("--help", "-h", "--version", "-v", "--dryRun", "--dry-run", "--verbose", "--quiet", "-q")]

    if len(filteredArgs) < 2:
        printHelp()
        return 1

    platformName = filteredArgs[0]
    operation = filteredArgs[1]
    dryRun = "--dryRun" in sys.argv or "--dry-run" in sys.argv

    systemClass = getSystemClass(platformName)
    if not systemClass:
        safePrint(f"Error: Unknown or unsupported platform: {platformName}", file=sys.stderr)
        return 1

    projectRoot = scriptDir
    system = systemClass(projectRoot)

    # Set configDir if provided via CLI or env var
    from common.core.utilities import getConfigDirectory
    configDir = getConfigDirectory(scriptDir)
    if configDir != (scriptDir / "configs"):
        # Create a mock SetupArgs with configDir
        from common.install.setupArgs import SetupArgs
        system.setupArgs = SetupArgs(configDir=str(configDir))

    return runOperation(system, operation, dryRun)


if __name__ == "__main__":
    sys.exit(main())
