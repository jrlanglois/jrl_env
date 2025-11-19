#!/usr/bin/env python3
"""
Common zsh and Oh My Zsh setup functions.
Shared across all platforms.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

from common.core.logging import printError, printInfo, printSuccess, printWarning
from common.core.utilities import commandExists, getJsonValue


def isZshInstalled() -> bool:
    """Check if zsh is installed."""
    return commandExists("zsh")


def isOhMyZshInstalled() -> bool:
    """Check if Oh My Zsh is installed."""
    ohMyZshPath = Path.home() / ".oh-my-zsh"
    return ohMyZshPath.exists()


def installOhMyZsh(dryRun: bool = False) -> bool:
    """
    Install Oh My Zsh.

    Args:
        dryRun: If True, don't actually install

    Returns:
        True if successful, False otherwise
    """
    printInfo("Installing Oh My Zsh...")

    if isOhMyZshInstalled():
        printSuccess("Oh My Zsh is already installed")
        return True

    if dryRun:
        printInfo("[DRY RUN] Would install Oh My Zsh...")
        return True

    printInfo("Installing Oh My Zsh...")
    try:
        result = subprocess.run(
            [
                "sh", "-c",
                "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
            ],
            input="",
            text=True,
            check=False,
            env={**os.environ, "RUNZSH": "no"},
        )
        # The install script returns non-zero even on success sometimes
        if isOhMyZshInstalled():
            printSuccess("Oh My Zsh installed successfully")
            return True
        else:
            printError("Failed to install Oh My Zsh")
            return False
    except Exception as e:
        printError(f"Failed to install Oh My Zsh: {e}")
        return False


def configureOhMyZshTheme(theme: str = "agnoster", dryRun: bool = False) -> bool:
    """
    Configure Oh My Zsh theme.

    Args:
        theme: Theme name (default: agnoster)
        dryRun: If True, don't actually configure

    Returns:
        True if successful, False otherwise
    """
    zshrc = Path.home() / ".zshrc"

    if not zshrc.exists():
        printWarning(f"{zshrc} not found. Skipping theme update.")
        return True

    if dryRun:
        printInfo(f"[DRY RUN] Would set Oh My Zsh theme to {theme}")
        return True

    try:
        content = zshrc.read_text(encoding='utf-8')

        # Check if ZSH_THEME line exists
        if re.search(r'^ZSH_THEME=', content, re.MULTILINE):
            # Replace existing theme
            content = re.sub(
                r'^ZSH_THEME=.*',
                f'ZSH_THEME="{theme}"',
                content,
                flags=re.MULTILINE,
            )
        else:
            # Add theme line
            content += f'\nZSH_THEME="{theme}"\n'

        zshrc.write_text(content, encoding='utf-8')
        printSuccess(f"Set Oh My Zsh theme to {theme}")
        return True
    except Exception as e:
        printError(f"Failed to configure theme: {e}")
        return False


def setZshAsDefault(dryRun: bool = False) -> bool:
    """
    Set zsh as default shell.

    Args:
        dryRun: If True, don't actually change shell

    Returns:
        True if successful, False otherwise
    """
    printInfo("Setting zsh as default shell...")

    if not isZshInstalled():
        printError("zsh is not installed. Please install it first.")
        return False

    try:
        zshPath = shutil.which("zsh")
        if not zshPath:
            printError("Could not find zsh path")
            return False

        currentShell = os.environ.get("SHELL", "")

        if currentShell == zshPath:
            printSuccess("zsh is already the default shell")
            return True

        if dryRun:
            printInfo(f"[DRY RUN] Would change default shell to zsh ({zshPath})...")
            printInfo("[DRY RUN] Would run: sudo chsh -s zsh")
            return True

        printInfo("Changing default shell to zsh...")
        printInfo("You may be prompted for your password.")

        result = subprocess.run(
            ["sudo", "chsh", "-s", zshPath, os.environ.get("USER", "")],
            check=False,
        )

        if result.returncode == 0:
            printSuccess("Default shell changed to zsh")
            printInfo("Note: This change will take effect after you log out and log back in.")
            return True
        else:
            printError("Failed to change default shell")
            return False
    except Exception as e:
        printError(f"Failed to change default shell: {e}")
        return False


def installZsh(
    dryRun: bool = False,
    installFunc: Optional[Callable[[], bool]] = None,
    dryRunMessage: str = "[DRY RUN] Would install zsh...",
) -> bool:
    """
    Install zsh using a platform-specific installer function.

    Args:
        dryRun: If True, don't actually install
        installFunc: Function to call to install zsh (platform-specific)
        dryRunMessage: Message to show during dry run

    Returns:
        True if successful, False otherwise
    """
    printInfo("Installing zsh...")

    if isZshInstalled():
        try:
            result = subprocess.run(
                ["zsh", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            printSuccess(f"zsh is already installed: {result.stdout.strip()}")
        except Exception:
            printSuccess("zsh is already installed")
        return True

    if dryRun:
        printInfo(dryRunMessage)
        return True

    if installFunc:
        return installFunc()

    printError("No installer function provided")
    return False


def getOhMyZshTheme(configPath: str) -> str:
    """
    Get Oh My Zsh theme from config or return default.

    Args:
        configPath: Path to platform config JSON file

    Returns:
        Theme name
    """
    defaultTheme = "agnoster"

    if not Path(configPath).exists():
        return defaultTheme

    try:
        configuredTheme = getJsonValue(configPath, ".shell.ohMyZshTheme", "")
        if configuredTheme and configuredTheme != "null":
            return configuredTheme
    except Exception:
        pass

    return defaultTheme
