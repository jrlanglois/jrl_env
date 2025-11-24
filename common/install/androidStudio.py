#!/usr/bin/env python3
"""
Android Studio and SDK management.
Provides OOP interface for Android SDK operations including updates.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional

from common.core.logging import printError, printInfo, printSuccess, printWarning
from common.systems.platform import isWindows, isMacOS


class AndroidStudioManager:
    """Manages Android Studio and SDK operations."""

    def __init__(self, dryRun: bool = False):
        """
        Initialise the Android Studio manager.

        Args:
            dryRun: If True, don't actually make changes
        """
        self.dryRun = dryRun
        self.sdkRoot: Optional[Path] = None
        self.sdkManager: Optional[Path] = None

    def findSdkRoot(self) -> Optional[Path]:
        """
        Find Android SDK root directory.
        Checks common locations and ANDROID_HOME/ANDROID_SDK_ROOT environment variables.

        Returns:
            Path to Android SDK root if found, None otherwise
        """
        if self.sdkRoot:
            return self.sdkRoot

        # Check environment variables first
        envVars = ["ANDROID_HOME", "ANDROID_SDK_ROOT"]
        for envVar in envVars:
            sdkRoot = os.environ.get(envVar)
            if sdkRoot:
                sdkPath = Path(sdkRoot)
                if sdkPath.exists():
                    self.sdkRoot = sdkPath
                    return sdkPath

        # Check common installation paths
        commonPaths = []
        if isWindows():
            commonPaths = [
                Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk",
                Path(os.environ.get("PROGRAMFILES", "")) / "Android" / "android-sdk",
            ]
        elif isMacOS():
            commonPaths = [
                Path.home() / "Library" / "Android" / "sdk",
                Path("/usr/local/share/android-sdk"),
            ]
        else:  # Linux
            commonPaths = [
                Path.home() / "Android" / "Sdk",
                Path("/opt/android-sdk"),
                Path("/usr/local/android-sdk"),
            ]

        for sdkPath in commonPaths:
            if sdkPath.exists():
                self.sdkRoot = sdkPath
                return sdkPath

        return None

    def findSdkManager(self) -> Optional[Path]:
        """
        Find sdkmanager executable.

        Returns:
            Path to sdkmanager if found, None otherwise
        """
        if self.sdkManager:
            return self.sdkManager

        sdkRoot = self.findSdkRoot()
        if not sdkRoot:
            return None

        # Check common sdkmanager locations
        possiblePaths = [
            sdkRoot / "cmdline-tools" / "latest" / "bin" / "sdkmanager",
            sdkRoot / "tools" / "bin" / "sdkmanager",
            sdkRoot / "cmdline-tools" / "bin" / "sdkmanager",
        ]

        # On Windows, add .bat extension
        if isWindows():
            possiblePaths.extend([
                sdkRoot / "cmdline-tools" / "latest" / "bin" / "sdkmanager.bat",
                sdkRoot / "tools" / "bin" / "sdkmanager.bat",
                sdkRoot / "cmdline-tools" / "bin" / "sdkmanager.bat",
            ])

        for path in possiblePaths:
            if path.exists():
                self.sdkManager = path
                return path

        return None

    def isInstalled(self) -> bool:
        """
        Check if Android SDK is installed.

        Returns:
            True if SDK is installed, False otherwise
        """
        return self.findSdkRoot() is not None

    def isSdkManagerAvailable(self) -> bool:
        """
        Check if sdkmanager is available.

        Returns:
            True if sdkmanager is available, False otherwise
        """
        return self.findSdkManager() is not None

    def updateSdk(self) -> bool:
        """
        Update all Android SDK components.
        Uses 'sdkmanager --update' to update all installed packages.

        Returns:
            True if successful, False otherwise
        """
        if not self.isInstalled():
            printInfo("Android SDK is not installed, skipping update")
            return True

        sdkManager = self.findSdkManager()
        if not sdkManager:
            printWarning("sdkmanager not found, skipping Android SDK update")
            printInfo("Please ensure Android SDK command-line tools are installed")
            return True

        printInfo("Updating Android SDK components...")

        if self.dryRun:
            printInfo(f"[DRY RUN] Would run: {sdkManager} --update")
            return True

        try:
            # Run sdkmanager --update
            # Note: sdkmanager may prompt for license acceptance
            result = subprocess.run(
                [str(sdkManager), "--update"],
                capture_output=True,
                text=True,
                check=False,
                env={**os.environ, "JAVA_HOME": os.environ.get("JAVA_HOME", "")},
            )

            if result.returncode == 0:
                printSuccess("Android SDK components updated")
                return True
            else:
                printWarning("Android SDK update had issues")
                if result.stderr:
                    printWarning(f"Error: {result.stderr.strip()}")
                return True  # Non-fatal
        except Exception as e:
            printWarning(f"Failed to update Android SDK: {e}")
            return True  # Non-fatal

    def listInstalledPackages(self) -> List[str]:
        """
        List installed Android SDK packages.

        Returns:
            List of installed package names, empty list if error
        """
        sdkManager = self.findSdkManager()
        if not sdkManager:
            return []

        try:
            result = subprocess.run(
                [str(sdkManager), "--list_installed"],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                # Parse output to extract package names
                packages = []
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('---') and '|' in line:
                        # Extract package name (first column)
                        parts = line.split('|')
                        if len(parts) >= 1:
                            packageName = parts[0].strip()
                            if packageName and packageName != "Path":
                                packages.append(packageName)
                return packages
            else:
                return []
        except Exception:
            return []

    def installComponents(self, components: List[str]) -> bool:
        """
        Install specific Android SDK components.

        Args:
            components: List of SDK component names to install

        Returns:
            True if successful, False otherwise
        """
        if not components:
            return True

        sdkManager = self.findSdkManager()
        if not sdkManager:
            printError("sdkmanager not found")
            return False

        printInfo(f"Installing {len(components)} Android SDK component(s)...")

        if self.dryRun:
            for component in components:
                printInfo(f"[DRY RUN] Would install: {component}")
            return True

        allSuccess = True
        for component in components:
            printInfo(f"Installing {component}...")
            try:
                result = subprocess.run(
                    [str(sdkManager), "--install", component],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if result.returncode == 0:
                    printSuccess(f"Installed {component}")
                else:
                    printError(f"Failed to install {component}")
                    if result.stderr:
                        printError(f"Error: {result.stderr.strip()}")
                    allSuccess = False
            except Exception as e:
                printError(f"Failed to install {component}: {e}")
                allSuccess = False

        return allSuccess


__all__ = [
    "AndroidStudioManager",
]
