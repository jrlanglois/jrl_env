#!/usr/bin/env python3
"""
Zsh and Oh My Zsh management classes.
Provides clean OOP interface for shell configuration.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

from common.core.logging import printError, printInfo, printSuccess, printWarning
from common.core.utilities import commandExists, getJsonValue


class ZshManager:
    """Manages Zsh installation and configuration."""

    def __init__(self, dryRun: bool = False):
        """
        Initialise the Zsh manager.

        Args:
            dryRun: If True, don't actually make changes
        """
        self.dryRun = dryRun

    def isInstalled(self) -> bool:
        """
        Check if zsh is installed.

        Returns:
            True if zsh is installed, False otherwise
        """
        return commandExists("zsh")

    def install(self, installFunc: Optional[Callable[[], bool]] = None, dryRunMessage: str = "[DRY RUN] Would install zsh...") -> bool:
        """
        Install zsh using a platform-specific installer function.

        Args:
            installFunc: Function to call to install zsh (platform-specific)
            dryRunMessage: Message to show during dry run

        Returns:
            True if successful, False otherwise
        """
        printInfo("Installing zsh...")

        if self.isInstalled():
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

        if self.dryRun:
            printInfo(dryRunMessage)
            return True

        if installFunc:
            return installFunc()

        printError("No installer function provided")
        return False

    def setAsDefault(self) -> bool:
        """
        Set zsh as default shell.

        Returns:
            True if successful, False otherwise
        """
        printInfo("Setting zsh as default shell...")

        if not self.isInstalled():
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

            if self.dryRun:
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

            printError("Failed to change default shell")
        except Exception as e:
            printError(f"Failed to change default shell: {e}")

        return False


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
    "ZshManager",
    "OhMyZshManager",
]
