#!/usr/bin/env python3
"""
Script to set up Raspberry Pi development environment.
Installs zsh, Oh My Zsh, and essential development tools.
"""

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


osConfigPath = str(projectRoot / "configs" / "raspberrypi.json")


def ensureEssentialTools(dryRun: bool = False) -> bool:
    """Ensure essential tools (curl, wget) are installed."""
    printInfo("Ensuring essential tools are installed...")

    needsUpdate = False

    if not commandExists("curl"):
        if dryRun:
            printInfo("[DRY RUN] Would install curl...")
            needsUpdate = True
        else:
            printInfo("Installing curl...")
            try:
                subprocess.run(
                    ["sudo", "apt-get", "install", "-y", "curl"],
                    check=True,
                )
                needsUpdate = True
            except Exception as e:
                printError(f"Failed to install curl: {e}")
                return False

    if not commandExists("wget"):
        if dryRun:
            printInfo("[DRY RUN] Would install wget...")
            needsUpdate = True
        else:
            printInfo("Installing wget...")
            try:
                subprocess.run(
                    ["sudo", "apt-get", "install", "-y", "wget"],
                    check=True,
                )
                needsUpdate = True
            except Exception as e:
                printError(f"Failed to install wget: {e}")
                return False

    if not needsUpdate:
        printSuccess("Essential tools already installed")

    return True


def installZshApt() -> bool:
    """Install zsh via apt."""
    try:
        subprocess.run(
            ["sudo", "apt-get", "update"],
            check=True,
        )
        subprocess.run(
            ["sudo", "apt-get", "install", "-y", "zsh"],
            check=True,
        )
        return True
    except Exception as e:
        printError(f"Failed to install zsh: {e}")
        return False


def setupDevEnv(dryRun: bool = False) -> bool:
    """Main setup function."""
    printSection("Raspberry Pi Development Environment Setup", dryRun=dryRun)
    safePrint()

    success = True

    # Update package list
    if dryRun:
        printInfo("[DRY RUN] Would update package list...")
    else:
        printInfo("Updating package list...")
        try:
            subprocess.run(
                ["sudo", "apt-get", "update"],
                check=True,
            )
        except Exception as e:
            printWarning(f"Package list update had issues: {e}")
    safePrint()

    # Ensure essential tools (curl, wget) are installed
    if not ensureEssentialTools(dryRun=dryRun):
        success = False
    safePrint()

    # Install zsh
    if not installZsh(
        dryRun=dryRun,
        installFunc=installZshApt,
        dryRunMessage="[DRY RUN] Would install zsh via apt...",
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
