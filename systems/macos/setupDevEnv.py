#!/usr/bin/env python3
"""
Script to set up macOS development environment.
Installs zsh, Oh My Zsh, Homebrew, and other essential tools.
"""

import platform
import subprocess
import sys
from pathlib import Path

# Add project root to path so we can import from common
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent.parent
sys.path.insert(0, str(projectRoot))

try:
    from common.common import (
        commandExists,
        printError,
        printInfo,
        printSection,
        printSuccess,
        printWarning,
        safePrint,
    )
    from common.install.setupZsh import (
        configureOhMyZshTheme,
        getOhMyZshTheme,
        installOhMyZsh,
        installZsh,
        setZshAsDefault,
    )
except ImportError as e:
    print(f"Error importing common modules: {e}", file=sys.stderr)
    sys.exit(1)


osConfigPath = str(projectRoot / "configs" / "macos.json")


def isBrewInstalled() -> bool:
    """Check if Homebrew is installed."""
    return commandExists("brew")


def installBrew(dryRun: bool = False) -> bool:
    """Install Homebrew."""
    printInfo("Installing Homebrew...")

    if isBrewInstalled():
        try:
            result = subprocess.run(
                ["brew", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            version = result.stdout.split("\n")[0] if result.stdout else "Installed"
            printSuccess(f"Homebrew is already installed: {version}")
        except Exception:
            printSuccess("Homebrew is already installed")
        return True

    if dryRun:
        printInfo("[DRY RUN] Would install Homebrew...")
        printInfo("[DRY RUN] Would add Homebrew to PATH in .zprofile...")
        return True

    printInfo("Installing Homebrew...")
    try:
        result = subprocess.run(
            [
                "/bin/bash", "-c",
                "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            ],
            check=False,
        )

        # Add Homebrew to PATH for Apple Silicon Macs
        machine = platform.machine()
        zprofile = Path.home() / ".zprofile"

        if machine == "arm64":
            brewPath = "/opt/homebrew/bin/brew"
            shellenvCmd = 'eval "$(/opt/homebrew/bin/brew shellenv)"'
        else:
            brewPath = "/usr/local/bin/brew"
            shellenvCmd = 'eval "$(/usr/local/bin/brew shellenv)"'

        # Add to .zprofile if not already there
        if zprofile.exists():
            content = zprofile.read_text(encoding='utf-8')
            if shellenvCmd not in content:
                with open(zprofile, 'a', encoding='utf-8') as f:
                    f.write(f'\n{shellenvCmd}\n')
        else:
            with open(zprofile, 'w', encoding='utf-8') as f:
                f.write(f'{shellenvCmd}\n')

        # Set up environment for current session
        if Path(brewPath).exists():
            subprocess.run(
                [brewPath, "shellenv"],
                check=False,
            )

        if isBrewInstalled():
            printSuccess("Homebrew installed successfully")
            return True
        else:
            printWarning("Homebrew installation completed, but may not be available in this session.")
            printInfo("Please restart your terminal or run: eval \"$(brew shellenv)\"")
            return False
    except Exception as e:
        printError(f"Failed to install Homebrew: {e}")
        return False


def installZshBrew() -> bool:
    """Install zsh via Homebrew."""
    if not isBrewInstalled():
        printInfo("zsh should be pre-installed on macOS. If not, please install Xcode Command Line Tools:")
        printInfo("  xcode-select --install")
        return False

    try:
        subprocess.run(
            ["brew", "install", "zsh"],
            check=True,
        )
        return True
    except Exception as e:
        printError(f"Failed to install zsh: {e}")
        return False


def setupDevEnv(dryRun: bool = False) -> bool:
    """Main setup function."""
    printSection("macOS Development Environment Setup", dryRun=dryRun)
    safePrint()

    success = True

    # Install Homebrew first (needed for zsh if not pre-installed)
    if not installBrew(dryRun=dryRun):
        success = False
    safePrint()

    # Install zsh
    if not installZsh(
        dryRun=dryRun,
        installFunc=installZshBrew,
        dryRunMessage="[DRY RUN] Would install zsh via Homebrew...",
    ):
        success = False
    safePrint()

    # Install Oh My Zsh
    if not installOhMyZsh(dryRun=dryRun):
        success = False
    safePrint()

    if not configureOhMyZshTheme(getOhMyZshTheme(osConfigPath), dryRun=dryRun):
        success = False
    safePrint()

    # Set zsh as default
    if not setZshAsDefault(dryRun=dryRun):
        success = False
    safePrint()

    printSection("Setup Complete", dryRun=dryRun)
    if success:
        if dryRun:
            printSuccess("Development environment setup would complete successfully!")
        else:
            printSuccess("Development environment setup completed successfully!")
        printInfo("Note: You may need to restart your terminal for all changes to take effect.")
    else:
        printInfo("Some steps may not have completed successfully. Please review the output above.")

    return True


def main() -> int:
    """Main function."""
    dryRun = "--dryRun" in sys.argv or "--dry-run" in sys.argv

    if setupDevEnv(dryRun=dryRun):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
