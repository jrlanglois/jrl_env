#!/usr/bin/env python3
"""
Unified setup script that auto-detects the operating system and runs the appropriate setup.
This is the main entry point for jrl_env setup.

Usage:
    python3 setup.py [options]

Options:
    --help, -h        Show this help message and exit
    --version, -v     Show version information and exit
    --configDir DIR   Use custom configuration directory (default: ./configs)
                       Can also be set via JRL_ENV_CONFIG_DIR environment variable
    --skipFonts       Skip font installation
    --skipApps        Skip application installation
    --skipGit         Skip Git configuration
    --skipCursor      Skip Cursor configuration
    --skipRepos       Skip repository cloning
    --skipSsh         Skip GitHub SSH setup
    --appsOnly        Only install/update applications (skip fonts, Git, Cursor, repos, SSH)
    --dryRun          Preview changes without making them
    --noBackup        Skip backing up existing configuration files
    --verbose         Enable verbose output (show debug messages)
    --quiet, -q       Enable quiet mode (only show errors)
    --resume          Automatically resume from last successful step if setup was interrupted
    --noResume        Do not resume from previous setup (start fresh)
    --listSteps       Preview what steps will be executed without running setup
"""

import subprocess
import sys
from pathlib import Path

# Add project root to path so we can import from common
projectRoot = Path(__file__).parent.absolute()
sys.path.insert(0, str(projectRoot))

from common.common import (
    findOperatingSystem,
    getOperatingSystem,
    isOperatingSystem,
    printError,
    printInfo,
    printSection,
    printSuccess,
    printWarning,
    safePrint,
)


def getSystemClass(platformName: str):
    """
    Get the system class for the given platform.

    Args:
        platformName: Platform name (e.g., "ubuntu", "macos", "win11")

    Returns:
        System class if available, None otherwise
    """
    try:
        moduleName = f"systems.{platformName}.system"
        systemModule = __import__(moduleName, fromlist=[f"{platformName.capitalize()}System"])
        className = f"{platformName.capitalize()}System"
        if platformName == "win11":
            className = "Win11System"
        elif platformName == "raspberrypi":
            className = "RaspberrypiSystem"
        elif platformName == "archlinux":
            className = "ArchlinuxSystem"
        elif platformName == "opensuse":
            className = "OpensuseSystem"
        elif platformName == "redhat":
            className = "RedhatSystem"
        return getattr(systemModule, className, None)
    except (ImportError, AttributeError):
        return None


def detectPlatform() -> tuple[str, Path]:
    """
    Detect the operating system and return the platform name and setup script path.

    Returns:
        Tuple of (platform_name, setup_script_path)
        Platform name will be one of: "macos", "ubuntu", "raspberrypi", "redhat", "opensuse", "archlinux", "win11", or "unknown"
    """
    osType = findOperatingSystem()

    if isOperatingSystem("macos"):
        return ("macos", projectRoot / "systems" / "macos" / "setup.py")
    elif isOperatingSystem("linux"):
        # Try to detect specific Linux distribution
        osRelease = Path("/etc/os-release")
        if osRelease.exists():
            try:
                distroId = None
                distroIdLike = None
                with open(osRelease, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith("ID="):
                            distroId = line.split('=', 1)[1].strip().strip('"').strip("'")
                        elif line.startswith("ID_LIKE="):
                            distroIdLike = line.split('=', 1)[1].strip().strip('"').strip("'")

                # Check ID first
                if distroId:
                    if distroId in ("ubuntu", "debian"):
                        return ("ubuntu", projectRoot / "systems" / "ubuntu" / "setup.py")
                    elif distroId == "raspbian":
                        return ("raspberrypi", projectRoot / "systems" / "raspberrypi" / "setup.py")
                    elif distroId in ("rhel", "fedora", "centos"):
                        return ("redhat", projectRoot / "systems" / "redhat" / "setup.py")
                    elif distroId in ("opensuse-leap", "opensuse-tumbleweed", "sles"):
                        return ("opensuse", projectRoot / "systems" / "opensuse" / "setup.py")
                    elif distroId == "arch":
                        return ("archlinux", projectRoot / "systems" / "archlinux" / "setup.py")

                # Check ID_LIKE as fallback
                if distroIdLike:
                    if "rhel" in distroIdLike or "fedora" in distroIdLike or "centos" in distroIdLike:
                        return ("redhat", projectRoot / "systems" / "redhat" / "setup.py")
                    elif "suse" in distroIdLike or "opensuse" in distroIdLike:
                        return ("opensuse", projectRoot / "systems" / "opensuse" / "setup.py")
                    elif "arch" in distroIdLike:
                        return ("archlinux", projectRoot / "systems" / "archlinux" / "setup.py")
            except (OSError, IOError):
                pass
        # Default to ubuntu for generic Linux
        return ("ubuntu", projectRoot / "systems" / "ubuntu" / "setup.py")
    elif isOperatingSystem("windows"):
        # Windows now uses Python setup script
        return ("win11", projectRoot / "systems" / "win11" / "setup.py")
    else:
        return ("unknown", None)


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
    if isOperatingSystem("windows"):
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
    if isOperatingSystem("windows"):
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
        if isOperatingSystem("windows"):
            import os
            cursorSettings = Path(os.environ.get("APPDATA", "")) / "Cursor" / "User" / "settings.json"
        elif isOperatingSystem("macos"):
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

    if isOperatingSystem("windows"):
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
        options=[
            ("--help, -h", "Show this help message and exit"),
            ("--version, -v", "Show version information and exit"),
            ("--skipFonts", "Skip font installation"),
            ("--skipApps", "Skip application installation"),
            ("--skipGit", "Skip Git configuration"),
            ("--skipCursor", "Skip Cursor configuration"),
            ("--skipRepos", "Skip repository cloning"),
            ("--skipSsh", "Skip GitHub SSH setup"),
            ("--appsOnly", "Only install/update applications (skip fonts, Git, Cursor, repos, SSH)"),
            ("--dryRun", "Preview changes without making them"),
            ("--noBackup", "Skip backing up existing configuration files"),
            ("--verbose", "Enable verbose output (show debug messages)"),
            ("--quiet, -q", "Enable quiet mode (only show errors)"),
            ("--resume", "Automatically resume from last successful step if setup was interrupted"),
            ("--noResume", "Do not resume from previous setup (start fresh)"),
            ("--listSteps", "Preview what steps will be executed without running setup"),
        ],
    )


def main() -> int:
    """Main entry point for unified setup."""
    # Check for --help flag
    if "--help" in sys.argv or "-h" in sys.argv:
        printHelp()
        return 0

    # Check for --version flag (before verbosity setup)
    if "--version" in sys.argv or "-v" in sys.argv:
        from common.version import __version__
        print(f"jrl_env version {__version__}")
        return 0

    # Parse verbosity flags early
    quiet = "--quiet" in sys.argv or "-q" in sys.argv
    verbose = "--verbose" in sys.argv
    from common.core.logging import setVerbosityFromArgs
    setVerbosityFromArgs(quiet=quiet, verbose=verbose)

    printSection("jrl_env Unified Setup")
    safePrint()

    # Check internet connectivity (required for package installation, repository cloning, etc.)
    from common.common import hasInternetConnectivity
    from common.core.logging import getVerbosity, Verbosity, printSuccess

    if getVerbosity() >= Verbosity.verbose:
        printInfo("Checking internet connectivity...")

    if not hasInternetConnectivity():
        printError(
            "No internet connectivity detected!\n"
            "Setup requires internet access for:\n"
            "  - Installing Python dependencies\n"
            "  - Installing packages via package managers\n"
            "  - Cloning repositories\n"
            "  - Downloading fonts\n"
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
    printInfo("Detecting operating system...")
    platformName, setupScript = detectPlatform()

    if platformName == "unknown" or setupScript is None:
        printError(
            f"Unsupported operating system: {getOperatingSystem()}\n"
            "Supported platforms: macOS, Ubuntu, Raspberry Pi, Windows 11"
        )
        return 1

    if not setupScript.exists():
        printError(f"Setup script not found: {setupScript}")
        return 1

    printSuccess(f"Detected platform: {platformName}")
    safePrint()

    # Check if setup has already been run
    setupAlreadyRan = checkIfSetupAlreadyRan()

    # If setup already ran, run update script instead
    if setupAlreadyRan:
        printWarning("Setup appears to have been run before.")
        printInfo(
            "Running UPDATE mode:\n"
            "  - Pulling latest changes from repository\n"
            "  - Re-running setup to update configuration"
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
    printInfo(
        "Running in FIRST-TIME SETUP mode.\n"
        "This will configure your development environment from scratch."
    )
    safePrint()

    # Try to use system class if available, otherwise fall back to script
    systemClass = getSystemClass(platformName)
    if systemClass:
        printInfo(f"Using system class: {systemClass.__name__}")
        safePrint()
        try:
            system = systemClass(projectRoot)
            result = system.run()
            if result == 0:
                markSetupAsRun()
                # After first-time setup, automatically run update
                safePrint()
                printSection("Running Update After First-Time Setup")
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
    else:
        # Fall back to calling setup script
        printInfo(f"Using setup script: {setupScript}")
        safePrint()

        if not setupScript.exists():
            printError(f"Setup script not found: {setupScript}")
            return 1

        import subprocess
        try:
            # Pass through all command-line arguments
            result = subprocess.run(
                [sys.executable, str(setupScript)] + sys.argv[1:],
                check=False,
            )
            if result.returncode == 0:
                markSetupAsRun()
                # After first-time setup, automatically run update
                safePrint()
                printSection("Running Update After First-Time Setup")
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
            return result.returncode
        except Exception as e:
            printError(f"Failed to run Python setup: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(main())
