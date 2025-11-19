#!/usr/bin/env python3
"""
Android SDK configuration logic for all platforms.
Provides functions to configure Android SDK components using sdkmanager.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from common.core.logging import (
    printError,
    printInfo,
    printSection,
    printSuccess,
    printWarning,
    safePrint,
)
from common.core.utilities import (
    commandExists,
    getJsonArray,
    getJsonObject,
    getJsonValue,
)
from common.configure.configureShellEnv import (
    configureAndroidEnvironmentVariables,
)


def findAndroidSdkRoot() -> Optional[Path]:
    """
    Find Android SDK root directory.
    Checks common locations and ANDROID_HOME/ANDROID_SDK_ROOT environment variables.

    Returns:
        Path to Android SDK root if found, None otherwise
    """
    envVars = ["ANDROID_HOME", "ANDROID_SDK_ROOT"]
    for envVar in envVars:
        sdkRoot = os.environ.get(envVar)
        if sdkRoot:
            sdkPath = Path(sdkRoot)
            if sdkPath.exists():
                return sdkPath

    commonPaths = []
    if sys.platform == "win32":
        commonPaths = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk",
            Path(os.environ.get("PROGRAMFILES", "")) / "Android" / "android-sdk",
        ]
    elif sys.platform == "darwin":
        commonPaths = [
            Path.home() / "Library" / "Android" / "sdk",
            Path("/usr/local/share/android-sdk"),
        ]
    else:
        commonPaths = [
            Path.home() / "Android" / "Sdk",
            Path("/opt/android-sdk"),
            Path("/usr/local/android-sdk"),
        ]

    for sdkPath in commonPaths:
        if sdkPath.exists():
            return sdkPath

    return None


def findSdkManager() -> Optional[Path]:
    """
    Find sdkmanager executable.

    Returns:
        Path to sdkmanager if found, None otherwise
    """
    sdkRoot = findAndroidSdkRoot()
    if not sdkRoot:
        return None

    if sys.platform == "win32":
        sdkManager = sdkRoot / "cmdline-tools" / "latest" / "bin" / "sdkmanager.bat"
        if not sdkManager.exists():
            sdkManager = sdkRoot / "tools" / "bin" / "sdkmanager.bat"
    else:
        sdkManager = sdkRoot / "cmdline-tools" / "latest" / "bin" / "sdkmanager"
        if not sdkManager.exists():
            sdkManager = sdkRoot / "tools" / "bin" / "sdkmanager"

    return sdkManager if sdkManager.exists() else None


def isAndroidStudioInstalled() -> bool:
    """
    Check if Android Studio is installed.
    Checks for Android Studio executable in common locations.

    Returns:
        True if Android Studio is found, False otherwise
    """
    if sys.platform == "win32":
        studioPaths = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Android" / "Android Studio" / "bin" / "studio64.exe",
            Path(os.environ.get("PROGRAMFILES", "")) / "Android" / "Android Studio" / "bin" / "studio64.exe",
        ]
    elif sys.platform == "darwin":
        studioPaths = [
            Path("/Applications") / "Android Studio.app" / "Contents" / "bin" / "studio.sh",
        ]
    else:
        studioPaths = [
            Path.home() / ".local" / "share" / "applications" / "android-studio.desktop",
            Path("/opt" / "android-studio" / "bin" / "studio.sh"),
        ]

    for studioPath in studioPaths:
        if studioPath.exists():
            return True

    return commandExists("android-studio") or commandExists("studio")


def checkAndroidStudioInConfig(configPath: str) -> bool:
    """
    Check if Android Studio is listed in the platform config packages.

    Args:
        configPath: Path to platform config JSON file

    Returns:
        True if Android Studio is found in config, False otherwise
    """
    if not Path(configPath).exists():
        return False

    androidStudioNames = [
        "Google.AndroidStudio",
        "android-studio",
        "androidstudio",
        "com.google.android.studio",
    ]

    packageArrays = [".winget[]?", ".brew[]?", ".brewCask[]?", ".apt[]?", ".snap[]?", ".dnf[]?", ".zypper[]?", ".pacman[]?"]

    from common.core.utilities import getJsonArray

    for extractor in packageArrays:
        packages = getJsonArray(configPath, extractor)
        for package in packages:
            packageLower = package.lower()
            for androidName in androidStudioNames:
                if androidName.lower() in packageLower:
                    return True

    return False


def installSdkComponents(sdkManager: Path, components: List[str], dryRun: bool = False) -> bool:
    """
    Install Android SDK components using sdkmanager.

    Args:
        sdkManager: Path to sdkmanager executable
        components: List of component names to install
        dryRun: If True, don't actually install

    Returns:
        True if successful, False otherwise
    """
    if dryRun:
        printInfo("  [DRY RUN] Would install SDK components:")
        for component in components:
            printInfo(f"    - {component}")
        return True

    if not components:
        printWarning("No SDK components to install")
        return True

    try:
        cmd = [str(sdkManager), "--install"] + components
        printInfo(f"Installing {len(components)} SDK component(s)...")
        printInfo(f"Command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            printSuccess(f"Successfully installed {len(components)} SDK component(s)")
            return True
        else:
            printError(f"Failed to install SDK components (exit code {result.returncode})")
            if result.stderr:
                printError(f"Error: {result.stderr}")
            return False

    except Exception as e:
        printError(f"Error installing SDK components: {e}")
        return False


def configureAndroid(configPath: Optional[str] = None, platformConfigPath: Optional[str] = None, dryRun: bool = False) -> bool:
    """
    Main function to configure Android SDK components.

    Args:
        configPath: Optional path to android.json config file (used if platform config doesn't override)
        platformConfigPath: Optional path to platform config file (to check for Android override)
        dryRun: If True, don't actually configure

    Returns:
        True if successful, False otherwise
    """
    printSection("Android Configuration", dryRun=dryRun)
    safePrint()

    sdkRoot = findAndroidSdkRoot()
    if not sdkRoot:
        printError("Android SDK not found.")
        printInfo("Please install Android Studio first.")
        printInfo("Android SDK is typically installed with Android Studio.")
        return False

    printInfo(f"Found Android SDK at: {sdkRoot}")
    safePrint()

    sdkManager = findSdkManager()
    if not sdkManager:
        printError("sdkmanager not found.")
        printInfo("Please ensure Android SDK command-line tools are installed.")
        return False

    printInfo(f"Found sdkmanager at: {sdkManager}")
    safePrint()

    androidConfig = None
    sdkComponents = []

    if platformConfigPath and Path(platformConfigPath).exists():
        platformAndroid = getJsonObject(platformConfigPath, ".android")
        if platformAndroid:
            androidConfig = platformAndroid
            printInfo("Using Android configuration from platform config (override)")
            safePrint()

    if not androidConfig:
        if not configPath:
            configPath = str(Path(__file__).parent.parent.parent / "configs" / "android.json")

        if not Path(configPath).exists():
            printWarning(f"Android config file not found: {configPath}")
            printInfo("Skipping Android SDK component installation.")
            return True

        androidConfig = getJsonObject(configPath, ".android")
        if not androidConfig:
            printWarning("No Android configuration found in config file.")
            return True

    sdkComponents = androidConfig.get("sdkComponents", [])
    if not sdkComponents:
        printWarning("No SDK components specified in config.")
        return True

    printInfo(f"Found {len(sdkComponents)} SDK component(s) to install:")
    for component in sdkComponents:
        printInfo(f"  - {component}")
    safePrint()

    success = installSdkComponents(sdkManager, sdkComponents, dryRun=dryRun)
    safePrint()

    if success:
        printInfo("Configuring Android environment variables...")
        safePrint()
        envSuccess = configureAndroidEnvironmentVariables(sdkRoot, dryRun=dryRun)
        if not envSuccess:
            printWarning("Environment variable configuration had some issues, but SDK components were installed.")
        safePrint()

    if success:
        printSuccess("Android SDK configuration completed!")
    else:
        printWarning("Android SDK configuration had some issues.")

    return success


__all__ = [
    "findAndroidSdkRoot",
    "findSdkManager",
    "isAndroidStudioInstalled",
    "checkAndroidStudioInConfig",
    "installSdkComponents",
    "configureAndroid",
]
