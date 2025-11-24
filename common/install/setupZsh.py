#!/usr/bin/env python3
"""
Oh My Zsh management class.
Provides clean OOP interface for OMZ configuration.

Note: Zsh itself is installed via package managers (brew, apt, dnf, etc.).
This module only manages Oh My Zsh, which is a framework that runs on top of Zsh.
"""

import os
import re
import subprocess
from pathlib import Path

from common.core.logging import printError, printInfo, printSuccess, printWarning
from common.core.utilities import getJsonValue


class OhMyZshManager:
    """Manages Oh My Zsh installation, updates, and theming."""

    def __init__(self, dryRun: bool = False):
        """
        Initialise the Oh My Zsh manager.

        Args:
            dryRun: If True, don't actually make changes
        """
        self.dryRun = dryRun
        self.installPath = Path.home() / ".oh-my-zsh"
        self.zshrcPath = Path.home() / ".zshrc"

    def isInstalled(self) -> bool:
        """
        Check if Oh My Zsh is installed.

        Returns:
            True if installed, False otherwise
        """
        return self.installPath.exists()

    def install(self) -> bool:
        """
        Install Oh My Zsh.

        Returns:
            True if successful, False otherwise
        """
        printInfo("Installing Oh My Zsh...")

        if self.isInstalled():
            printSuccess("Oh My Zsh is already installed")
            return True

        if self.dryRun:
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
            if self.isInstalled():
                printSuccess("Oh My Zsh installed successfully")
                return True

            printError("Failed to install Oh My Zsh")
        except Exception as e:
            printError(f"Failed to install Oh My Zsh: {e}")

        return False

    def update(self) -> bool:
        """
        Update Oh My Zsh to the latest version.

        Returns:
            True if successful, False otherwise
        """
        if not self.isInstalled():
            printInfo("Oh My Zsh is not installed, skipping update")
            return True

        if self.dryRun:
            printInfo("[DRY RUN] Would update Oh My Zsh...")
            return True

        printInfo("Updating Oh My Zsh...")
        try:
            # Run update script directly instead of using omz function
            # The omz function requires an interactive shell with .zshrc sourced
            updateScript = self.installPath / "tools" / "upgrade.sh"

            if not updateScript.exists():
                printWarning("Oh My Zsh update script not found, skipping update")
                return True

            result = subprocess.run(
                ["sh", str(updateScript)],
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "ZSH": str(self.installPath)},
            )

            # upgrade.sh returns 0 even if already up to date
            if result.returncode == 0:
                printSuccess("Oh My Zsh update completed")
                return True
            else:
                printWarning("Oh My Zsh update had issues")
                if result.stderr:
                    printWarning(f"Error: {result.stderr.strip()}")

                return True  # Non-fatal
        except Exception as e:
            printWarning(f"Failed to update Oh My Zsh: {e}")
            return True  # Non-fatal

    def getTheme(self, configPath: str) -> str:
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

    def configureTheme(self, theme: str = "agnoster") -> bool:
        """
        Configure Oh My Zsh theme.

        Args:
            theme: Theme name (default: agnoster)

        Returns:
            True if successful, False otherwise
        """
        if not self.zshrcPath.exists():
            printWarning(f"{self.zshrcPath} not found. Skipping theme update.")
            return True

        if self.dryRun:
            printInfo(f"[DRY RUN] Would set Oh My Zsh theme to {theme}")
            return True

        try:
            content = self.zshrcPath.read_text(encoding='utf-8')

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

            self.zshrcPath.write_text(content, encoding='utf-8')
            printSuccess(f"Set Oh My Zsh theme to {theme}")
            return True
        except Exception as e:
            printError(f"Failed to configure theme: {e}")
            return False


__all__ = [
    "OhMyZshManager",
]
