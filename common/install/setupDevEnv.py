#!/usr/bin/env python3
"""
Unified development environment setup for all platforms.
Installs zsh, Oh My Zsh, and essential development tools.
"""

import subprocess
from pathlib import Path
from typing import Callable, List, Optional

from common.core.logging import (
    printError,
    printInfo,
    printSection,
    printSuccess,
    printWarning,
    safePrint,
)
from common.core.utilities import commandExists
from common.install.setupZsh import (
    configureOhMyZshTheme,
    getOhMyZshTheme,
    installOhMyZsh,
    installZsh,
    setZshAsDefault,
)
from common.systems.platform import Platform
from common.systems.systemsConfig import getSystemConfig


def getPackageManagerCommands(packageManager: str) -> dict:
    """
    Get package manager commands for a given package manager.

    Args:
        packageManager: Package manager name (e.g., "apt", "brew", "pacman")

    Returns:
        Dictionary with 'update', 'install', 'sudo' keys
    """
    commands = {
        "apt": {
            "update": ["sudo", "apt-get", "update"],
            "install": ["sudo", "apt-get", "install", "-y"],
            "sudo": True,
        },
        "brew": {
            "update": ["brew", "update"],
            "install": ["brew", "install"],
            "sudo": False,
        },
        "pacman": {
            "update": ["sudo", "pacman", "-Sy"],
            "install": ["sudo", "pacman", "-S", "--noconfirm"],
            "sudo": True,
        },
        "zypper": {
            "update": ["sudo", "zypper", "refresh"],
            "install": ["sudo", "zypper", "install", "-y"],
            "sudo": True,
        },
        "dnf": {
            "update": ["sudo", "dnf", "check-update"],
            "install": ["sudo", "dnf", "install", "-y"],
            "sudo": True,
        },
    }
    return commands.get(packageManager, commands["apt"])


def ensureEssentialTools(
    packageManager: str,
    tools: List[str],
    dryRun: bool = False
) -> bool:
    """
    Ensure essential tools are installed.

    Args:
        packageManager: Package manager to use
        tools: List of tools to install (e.g., ["curl", "wget"])
        dryRun: If True, don't actually install

    Returns:
        True if successful, False otherwise
    """
    printInfo("Ensuring essential tools are installed...")

    commands = getPackageManagerCommands(packageManager)
    needsUpdate = False

    for tool in tools:
        if not commandExists(tool):
            if dryRun:
                printInfo(f"[DRY RUN] Would install {tool}...")
                needsUpdate = True
            else:
                printInfo(f"Installing {tool}...")
                try:
                    subprocess.run(
                        commands["install"] + [tool],
                        check=True,
                    )
                    needsUpdate = True
                except Exception as e:
                    printError(f"Failed to install {tool}: {e}")
                    return False

    if not needsUpdate:
        printSuccess("Essential tools already installed")

    return True


def installZshForPackageManager(packageManager: str) -> Callable[[], bool]:
    """
    Create a zsh install function for a specific package manager.

    Args:
        packageManager: Package manager name

    Returns:
        Function that installs zsh using the specified package manager
    """
    def installZshFunc() -> bool:
        """Install zsh via the configured package manager."""
        commands = getPackageManagerCommands(packageManager)
        try:
            # Update package list first (ignore errors for check-update)
            subprocess.run(commands["update"], check=False)
            # Install zsh
            subprocess.run(commands["install"] + ["zsh"], check=True)
            return True
        except Exception as e:
            printError(f"Failed to install zsh: {e}")
            return False

    return installZshFunc


def installBrewForMacOS(dryRun: bool = False) -> bool:
    """
    Install Homebrew on macOS.

    Args:
        dryRun: If True, don't actually install

    Returns:
        True if successful, False otherwise
    """
    import platform

    printInfo("Installing Homebrew...")

    if commandExists("brew"):
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
            subprocess.run([brewPath, "shellenv"], check=False)

        if commandExists("brew"):
            printSuccess("Homebrew installed successfully")
            return True
        else:
            printWarning("Homebrew installation completed, but may not be available in this session.")
            printInfo("Please restart your terminal or run: eval \"$(brew shellenv)\"")
            return False
    except Exception as e:
        printError(f"Failed to install Homebrew: {e}")
        return False


def setupDevEnv(
    platform: Platform,
    projectRoot: Path,
    dryRun: bool = False
) -> bool:
    """
    Set up development environment for any platform.

    Args:
        platform: Platform enum value
        projectRoot: Root directory of jrl_env project
        dryRun: If True, don't actually install/configure

    Returns:
        True if successful, False otherwise
    """
    # Get system configuration
    config = getSystemConfig(str(platform))
    if not config:
        printError(f"Unsupported platform: {platform}")
        return False

    platformName = config.platformName.capitalize()
    packageManager = config.primaryPackageManager

    printSection(f"{platformName} Development Environment Setup", dryRun=dryRun)
    safePrint()

    success = True

    # macOS: Install Homebrew first
    if platform == Platform.macos:
        if not installBrewForMacOS(dryRun=dryRun):
            success = False
        safePrint()

    # Update package list
    commands = getPackageManagerCommands(packageManager)
    if dryRun:
        printInfo("[DRY RUN] Would update package list...")
    else:
        printInfo("Updating package list...")
        try:
            subprocess.run(commands["update"], check=False)
        except Exception as e:
            printWarning(f"Package list update had issues: {e}")
    safePrint()

    # Ensure essential tools (curl, wget) for Unix platforms
    # macOS usually has these pre-installed, Linux platforms need them for Oh My Zsh
    if platform != Platform.win11:
        essentialTools = ["curl", "wget"] if platform != Platform.macos else []
        if essentialTools and not ensureEssentialTools(packageManager, essentialTools, dryRun=dryRun):
            success = False
        if essentialTools:
            safePrint()

    # Install zsh
    installFunc = installZshForPackageManager(packageManager)
    dryRunMessage = f"[DRY RUN] Would install zsh via {packageManager}..."
    if not installZsh(dryRun=dryRun, installFunc=installFunc, dryRunMessage=dryRunMessage):
        success = False
    safePrint()

    # Install Oh My Zsh
    if not installOhMyZsh(dryRun=dryRun):
        success = False
    safePrint()

    # Configure Oh My Zsh theme
    configPath = str(projectRoot / "configs" / config.configFileName)
    theme = getOhMyZshTheme(configPath)
    if not configureOhMyZshTheme(theme, dryRun=dryRun):
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


__all__ = [
    "setupDevEnv",
    "ensureEssentialTools",
    "installZshForPackageManager",
    "installBrewForMacOS",
]
