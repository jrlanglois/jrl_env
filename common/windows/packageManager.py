#!/usr/bin/env python3
"""
Windows-specific package manager utilities.
Handles winget operations and Windows Store updates.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Add project root to path so we can import from common
projectRoot = Path(__file__).parent.parent.parent
sys.path.insert(0, str(projectRoot))

# Import directly from source modules to avoid circular import with common.common
from common.core.utilities import commandExists
from common.core.logging import (
    printError,
    printInfo,
    printSuccess,
    printWarning,
)


def isWingetInstalled() -> bool:
    """
    Check if Windows Package Manager (winget) is installed and available.

    Returns:
        True if winget is available, False otherwise
    """
    return commandExists("winget")


def installWinget() -> bool:
    """
    Install Windows Package Manager (winget) if it's not already installed.
    Requires administrative privileges.

    Returns:
        True if installation was successful or already installed, False otherwise
    """
    # Check if already installed
    if isWingetInstalled():
        printSuccess("winget is already installed.")
        return True

    printInfo("Installing winget (Windows Package Manager)...")

    try:
        # Check if running as administrator
        import ctypes
        isAdmin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        if not isAdmin:
            printError("Administrative privileges are required to install winget. Please run as Administrator.")
            return False

        # Download and execute the winget installation script
        installScript = "https://aka.ms/getwinget"
        printInfo("Downloading winget installation script...")

        import urllib.request
        tempFile = Path(os.environ.get("TEMP", "")) / "Microsoft.DesktopAppInstaller.msixbundle"

        urllib.request.urlretrieve(installScript, str(tempFile))

        # Install the MSIX bundle using PowerShell
        printInfo("Installing winget...")
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command",
                f"Add-AppxPackage -Path '{tempFile}'"
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Clean up
        try:
            tempFile.unlink()
        except (OSError, IOError):
            pass

        # Refresh environment variables
        os.environ["Path"] = os.environ.get("Path", "")

        # Verify installation
        import time
        time.sleep(2)
        if isWingetInstalled():
            printSuccess("winget installed successfully!")
            return True
        else:
            printWarning("winget installation completed, but it may not be available in this session. Please restart PowerShell.")
            return False
    except Exception as e:
        printError(f"Failed to install winget: {e}")
        return False


def updateWinget() -> bool:
    """
    Update Windows Package Manager (winget) to the latest version.
    Requires administrative privileges.

    Returns:
        True if the update was successful, False otherwise
    """
    # Check if winget is installed
    if not isWingetInstalled():
        printError("winget is not installed. Please install it first using installWinget().")
        return False

    printInfo("Updating winget (Windows Package Manager)...")

    try:
        # Check if running as administrator
        import ctypes
        isAdmin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        if not isAdmin:
            printWarning("Administrative privileges are recommended for updating winget. Continuing anyway...")

        # Update winget by upgrading the DesktopAppInstaller
        result = subprocess.run(
            [
                "winget",
                "upgrade",
                "--id", "Microsoft.DesktopAppInstaller",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            printSuccess("winget update completed successfully.")

            # Refresh environment variables
            os.environ["Path"] = os.environ.get("Path", "")

            return True
        else:
            printWarning(f"winget update may have failed or no update was available. Exit code: {result.returncode}")
            return False
    except Exception as e:
        printError(f"Failed to update winget: {e}")
        return False


def updateMicrosoftStore() -> bool:
    """
    Update the Microsoft Store application using winget.

    Returns:
        True if the update was successful, False otherwise
    """
    # Check if winget is installed
    if not isWingetInstalled():
        printWarning("winget (Windows Package Manager) is not installed.")
        response = input("Would you like to install winget now? (Y/N): ")
        if response.upper().startswith("Y"):
            if not installWinget():
                printError("Failed to install winget. Please install Windows Package Manager manually or run as Administrator.")
                return False
        else:
            printError("winget is required to update Microsoft Store. Please install it manually.")
            return False

    printInfo("Updating Microsoft Store using winget...")

    try:
        # Update Microsoft Store specifically
        result = subprocess.run(
            [
                "winget",
                "upgrade",
                "Microsoft.WindowsStore",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            printSuccess("Microsoft Store update completed successfully.")
            return True
        else:
            printWarning(f"Microsoft Store update may have failed or no update was available. Exit code: {result.returncode}")
            return False
    except Exception as e:
        printError(f"Failed to update Microsoft Store: {e}")
        return False


def isAppInstalled(appId: str) -> bool:
    """
    Check if a specific application is installed via winget.

    Args:
        appId: The winget package identifier (e.g., "Microsoft.VisualStudioCode")

    Returns:
        True if the app is installed, False otherwise
    """
    if not isWingetInstalled():
        return False

    try:
        result = subprocess.run(
            ["winget", "list", "--id", appId, "--accept-source-agreements"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            # Check if the output contains the app ID
            if appId in result.stdout:
                return True

        return False
    except Exception:
        return False
