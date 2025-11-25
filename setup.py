#!/usr/bin/env python3
"""
Unified setup script that auto-detects the operating system and runs the appropriate setup.
This is the main entry point for jrl_env setup.

Usage:
    python3 setup.py [options]

Installation:
    --install[=TARGETS]   Install components (default: all)
                          Targets: all, fonts, apps, git, cursor, repos, ssh
                          Examples:
                            --install          (install everything)
                            --install=all      (install everything)
                            --install=fonts,apps,git
                            --install=apps

Updates:
    --update[=TARGETS]    Update components (default: all)
                          Targets: all, apps, system
                          Examples:
                            --update           (update everything)
                            --update=all       (update everything)
                            --update=apps      (only update applications)
                            --update=system    (only system updates)

Options:
    --help, -h            Show this help message and exit
    --version, -v         Show version information and exit
    --passphrase=MODE     SSH passphrase mode: 'require' (default) or 'no'
    --configDir DIR       Use custom configuration directory (default: ./configs)
                          Can also be set via JRL_ENV_CONFIG_DIR environment variable
    --dryRun              Preview changes without making them
    --noBackup            Skip backing up existing configuration files
    --verbose             Enable verbose output (show debug messages)
    --quiet, -q           Enable quiet mode (only show errors)
    --noTimestamps        Hide timestamps in console output (logs always have timestamps)
    --clearRepoCache      Clear repository wildcard cache before setup
    --resume              Automatically resume from last successful step if setup was interrupted
    --noResume            Do not resume from previous setup (start fresh)
    --listSteps           Preview what steps will be executed without running setup
"""

import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Add project root to path so we can import from common
projectRoot = Path(__file__).parent.absolute()
sys.path.insert(0, str(projectRoot))

from common.common import (
    findOperatingSystem,
    getOperatingSystem,
    isOperatingSystem,
    isWindows,
    isMacOS,
    isLinux,
    printError,
    printInfo,
    printH1,
    printH2,
    printSuccess,
    printWarning,
    safePrint,
)






def checkIfSetupAlreadyRan() -> bool:
    """
    Check if setup has already been run by looking for multiple indicators.

    Returns:
        True if setup appears to have been run before, False otherwise
    """
    indicators = 0
    maxIndicators = 5

    # Indicator 1: Check for flag files
    flagLocations = []
    if isWindows():
        import os
        localAppData = os.environ.get("LOCALAPPDATA", "")
        if localAppData:
            flagLocations.append(Path(localAppData) / "jrl_env_setup.flag")
    else:
        homeDir = Path.home()
        flagLocations.append(homeDir / ".jrl_env_setup.flag")
        flagLocations.append(Path("/tmp") / "jrl_env_setup.flag")

    for flagFile in flagLocations:
        if flagFile.exists():
            indicators += 1
            break

    # Indicator 2: Check for Git config with jrl_env markers
    gitConfig = None
    if isWindows():
        import os
        gitConfig = Path(os.environ.get("USERPROFILE", "")) / ".gitconfig"
    else:
        gitConfig = Path.home() / ".gitconfig"

    if gitConfig and gitConfig.exists():
        try:
            content = gitConfig.read_text(encoding='utf-8')
            if "[jrl_env]" in content or "jrl_env" in content.lower():
                indicators += 1
        except (OSError, IOError):
            pass

    # Indicator 3: Check for setup state files (from resume system)
    from common.install.setupState import getStateDir
    try:
        stateDir = getStateDir()
        if stateDir.exists() and any(stateDir.glob("*_*.json")):
            indicators += 1
    except Exception:
        pass

    # Indicator 4: Check for rollback session files
    from common.install.rollback import getSessionDir
    try:
        sessionDir = getSessionDir()
        if sessionDir.exists() and any(sessionDir.glob("session_*.json")):
            indicators += 1
    except Exception:
        pass

    # Indicator 5: Check for Cursor settings (platform-specific)
    try:
        if isWindows():
            import os
            cursorSettings = Path(os.environ.get("APPDATA", "")) / "Cursor" / "User" / "settings.json"
        elif isMacOS():
            cursorSettings = Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "settings.json"
        else:
            cursorSettings = Path.home() / ".config" / "Cursor" / "User" / "settings.json"

        if cursorSettings.exists():
            try:
                import json
                with open(cursorSettings, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Check for jrl_env-specific settings (e.g., fontFamily from our config)
                    if "editor.fontFamily" in settings and "Fira Code" in str(settings.get("editor.fontFamily", "")):
                        indicators += 1
            except Exception:
                pass
    except Exception:
        pass

    # Require at least 2 indicators to be confident setup has run
    return indicators >= 2


def markSetupAsRun() -> None:
    """Create a flag file to mark that setup has been run."""
    flagFile = None

    if isWindows():
        import os
        localAppData = os.environ.get("LOCALAPPDATA", "")
        if localAppData:
            flagFile = Path(localAppData) / "jrl_env_setup.flag"
    else:
        homeDir = Path.home()
        flagFile = homeDir / ".jrl_env_setup.flag"

    if flagFile:
        try:
            flagFile.touch()
            flagFile.write_text("jrl_env setup completed\n")
        except (OSError, IOError):
            pass  # Non-fatal if we can't create the flag file


def installRequirements() -> bool:
    """
    Install Python requirements from requirements.txt if it exists.

    Returns:
        True if requirements were installed successfully or not needed, False on error
    """
    requirementsFile = projectRoot / "requirements.txt"

    if not requirementsFile.exists():
        return True  # No requirements file, nothing to install

    try:
        printInfo("Checking Python dependencies...")

        # Check if pip is available
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                check=True,
                capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            printWarning("pip not available. Skipping dependency installation.")
            printWarning("Some features may not work correctly (e.g., JSON schema validation).")
            return True  # Non-fatal, continue anyway

        # Install requirements
        printInfo(f"Installing dependencies from {requirementsFile.name}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", "-r", str(requirementsFile)],
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            printSuccess("Dependencies installed successfully.")
            return True
        else:
            printWarning(f"Failed to install some dependencies (exit code {result.returncode}).")
            if result.stderr:
                printWarning(f"Error: {result.stderr.strip()}")
            printWarning("Continuing anyway, but some features may not work correctly.")
            return True  # Non-fatal, continue anyway

    except Exception as e:
        printWarning(f"Error installing dependencies: {e}")
        printWarning("Continuing anyway, but some features may not work correctly.")
        return True  # Non-fatal, continue anyway


def printHelp() -> None:
    """Print help information for setup.py."""
    from common.core.logging import printHelpText

    printHelpText(
        title="Unified Setup",
        intent=[
            "Automatically configure your development environment by:",
            "- Installing required applications and packages",
            "- Configuring Git with your preferences",
            "- Setting up GitHub SSH keys",
            "- Installing Google Fonts",
            "- Configuring Cursor editor settings",
            "- Cloning your repositories",
            "",
            "The script auto-detects your operating system and runs the appropriate setup.",
        ],
        usage="python3 setup.py [options]",
        sections={
            "Installation": [
                "--install[=TARGETS]  Install components (default: all)",
                "                     Targets: all, fonts, apps, git, cursor, repos, ssh",
                "                     Examples:",
                "                       --install          (install everything)",
                "                       --install=all      (install everything)",
                "                       --install=fonts,apps,git",
                "                       --install=apps",
            ],
            "Updates": [
                "--update[=TARGETS]   Update components (default: all)",
                "                     Targets: all, apps, system",
                "                     Examples:",
                "                       --update           (update everything)",
                "                       --update=all       (update everything)",
                "                       --update=apps      (packages + Android SDK)",
                "                       --update=system    (OS + stores + OMZ)",
            ],
            "Options": [
                "--help, -h           Show this help message and exit",
                "--version, -v        Show version information and exit",
                "--passphrase=MODE    SSH passphrase mode: 'require' (default) or 'no'",
                "--configDir DIR      Use custom configuration directory (default: ./configs)",
                "                     Can also be set via JRL_ENV_CONFIG_DIR environment variable",
                "--dryRun             Preview changes without making them",
                "--noBackup           Skip backing up existing configuration files",
                "--verbose            Enable verbose output (show debug messages)",
                "--quiet, -q          Enable quiet mode (only show errors)",
                "--noTimestamps       Hide timestamps in console output (logs always have timestamps)",
                "--clearRepoCache     Clear repository wildcard cache before setup",
                "--resume             Automatically resume from last successful step if setup was interrupted",
                "--noResume           Do not resume from previous setup (start fresh)",
                "--listSteps          Preview what steps will be executed without running setup",
            ],
        },
    )


def main() -> int:
    """Main entry point for unified setup."""
    # Auto-install shell completions (silent, idempotent)
    try:
        from common.install.completionInstaller import autoInstallCompletion
        autoInstallCompletion(projectRoot)
    except Exception:
        pass  # Non-fatal if completion installation fails

    # Register signal handlers for graceful shutdown
    from common.core.signalHandling import setupSignalHandlers
    setupSignalHandlers(resumeMessage=True)

    # Check for --help flag
    if "--help" in sys.argv or "-h" in sys.argv:
        printHelp()
        return 0

    # Check for --version flag (before verbosity setup)
    if "--version" in sys.argv or "-v" in sys.argv:
        from common.version import __version__
        safePrint(f"jrl_env version {__version__}")
        return 0

    # Parse verbosity and timestamp flags early
    quiet = "--quiet" in sys.argv or "-q" in sys.argv
    verbose = "--verbose" in sys.argv
    noTimestamps = "--noTimestamps" in sys.argv
    from common.core.logging import setVerbosityFromArgs, setShowConsoleTimestamps, printH1, printH2, printSuccess as printSuccessMsg, printWarning as printWarnMsg
    setVerbosityFromArgs(quiet=quiet, verbose=verbose)
    if noTimestamps:
        setShowConsoleTimestamps(False)

    # Parse arguments early to check for update mode
    from common.install.setupArgs import parseSetupArgs
    try:
        preliminaryArgs = parseSetupArgs()
    except SystemExit:
        return 1

    # Check for --update flag early (pure update mode, bypass installation)
    if preliminaryArgs.updateTargets:
        dryRun = preliminaryArgs.dryRun

        printH1("jrl_env Update", dryRun=dryRun)

        # Detect platform
        from common.systems.update import detectPlatform

        printInfo("Detecting operating system...")
        platformName = detectPlatform()

        if platformName == "unknown":
            printError(f"Unsupported operating system: {getOperatingSystem()}")
            return 1

        printSuccessMsg(f"Detected platform: {platformName}")
        safePrint()

        # Run pure update (no installation)
        try:
            from common.systems.platforms import createPlatform

            updateTargets = preliminaryArgs.updateTargets
            if 'all' in updateTargets:
                printH2("System Updates", dryRun=dryRun)
                platform = createPlatform(platformName, projectRoot, dryRun)
                success = platform.updateAll()
            else:
                # Targeted updates
                platform = createPlatform(platformName, projectRoot, dryRun)
                success = True

                if 'apps' in updateTargets:
                    printH2("Updating Applications", dryRun=dryRun)
                    if not platform.updatePackages():
                        success = False
                    safePrint()

                if 'system' in updateTargets:
                    printH2("Updating System", dryRun=dryRun)
                    if not platform.updateSystemWithOmz():
                        success = False
                    safePrint()

            if success:
                printSuccessMsg("All updates completed successfully")
                return 0
            else:
                printWarnMsg("Updates completed with some issues")
                return 1
        except Exception as e:
            printError(f"Update failed: {e}")
            return 1

    printH1("jrl_env Unified Setup")

    # Check internet connectivity (required for package installation, repository cloning, etc.)
    # Skip in dry-run or listSteps mode since we're not making actual changes
    from common.common import hasInternetConnectivity
    from common.core.logging import getVerbosity, Verbosity, printSuccess

    dryRun = "--dryRun" in sys.argv
    listSteps = "--listSteps" in sys.argv

    if not dryRun and not listSteps:
        if getVerbosity() >= Verbosity.verbose:
            printInfo("Checking internet connectivity...")

        if not hasInternetConnectivity():
            printError(
                "No internet connectivity detected!\n"
                "Setup requires internet access for:\n"
                "- Installing Python dependencies\n"
                "- Installing packages via package managers\n"
                "- Cloning repositories\n"
                "- Downloading fonts\n"
                "\n"
                "Please check your network connection and try again."
            )
            safePrint()
            return 1

        if getVerbosity() >= Verbosity.verbose:
            printSuccess("Internet connectivity verified")
        safePrint()

    # Install Python dependencies first
    installRequirements()
    safePrint()

    # Detect platform
    from common.systems.update import detectPlatform

    printInfo("Detecting operating system...")
    platformName = detectPlatform()

    if platformName == "unknown":
        printError(
            f"Unsupported operating system: {getOperatingSystem()}\n"
            "Supported platforms: macOS, Ubuntu, Raspberry Pi, RedHat, OpenSUSE, ArchLinux, Windows 11"
        )
        return 1

    printSuccess(f"Detected platform: {platformName}")
    safePrint()

    # Validate sudo early (for Unix-like systems)
    from common.core.sudoHelper import SudoManager
    sudoManager = SudoManager(dryRun=dryRun)
    if not sudoManager.validate():
        # User refused sudo or validation failed
        return 1

    # Check if setup has already been run
    setupAlreadyRan = checkIfSetupAlreadyRan()

    # If setup already ran, run update script instead
    if setupAlreadyRan:
        printWarning("Setup appears to have been run before.")
        printInfo(
            "Running UPDATE mode:\n"
            "- Pulling latest changes from repository\n"
            "- Re-running setup to update configuration"
        )
        safePrint()

        # Use unified update script
        try:
            from common.systems.update import main as updateMain
            return updateMain()
        except Exception as e:
            printError(f"Failed to run update script: {e}")
            return 1

    # First-time setup
    listSteps = "--listSteps" in sys.argv
    if listSteps:
        printInfo("Preview for FIRST-TIME SETUP mode.")
    else:
        printInfo(
            "Running in FIRST-TIME SETUP mode.\n"
            "This will configure your development environment from scratch."
        )
    safePrint()

    # Use GenericSystem for setup
    systemClass = getSystemClass(platformName)
    if not systemClass:
        printError(f"Failed to get system class for platform: {platformName}")
        return 1

    # Start setup
    try:
        system = systemClass(projectRoot)
        result = system.run()
        if result == 0:
            # Only mark as run and update if not in dry-run or listSteps mode
            dryRun = "--dryRun" in sys.argv
            listSteps = "--listSteps" in sys.argv
            if not dryRun and not listSteps:
                markSetupAsRun()
                # After first-time setup, automatically run update
                safePrint()
                printH2("Running Update After First-Time Setup")
                printInfo("Automatically running update to ensure everything is current...")
                safePrint()
                # Use unified update script
                try:
                    from common.systems.update import main as updateMain
                    updateResult = updateMain()
                    return updateResult
                except Exception as e:
                    printWarning(f"Update script had issues: {e}")
                    return 0  # Don't fail if update has issues
        return result
    except Exception as e:
        printError(f"Failed to run system setup: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
