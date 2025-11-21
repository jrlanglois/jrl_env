#!/usr/bin/env python3
"""
Shell environment variable configuration utilities.
Handles adding environment variables to shell config files (.zshrc, .bashrc, etc.)
without overriding existing values.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from common.core.logging import (
    printError,
    printInfo,
    printSuccess,
    printWarning,
    safePrint,
)


def getShellConfigFile() -> Optional[Path]:
    """
    Detect which shell config file to use based on current shell.

    Returns:
        Path to shell config file (.zshrc, .bashrc, .bash_profile, etc.) or None
        Returns None on Windows (uses registry/system env vars instead)
    """
    if sys.platform == "win32":
        return None

    shell = os.environ.get("SHELL", "")
    home = Path.home()

    if "zsh" in shell.lower():
        zshrc = home / ".zshrc"
        if zshrc.exists() or os.environ.get("ZSH"):
            return zshrc
        return home / ".zshrc"
    elif "bash" in shell.lower():
        bashrc = home / ".bashrc"
        bashProfile = home / ".bash_profile"
        if bashProfile.exists():
            return bashProfile
        return bashrc
    elif sys.platform == "darwin":
        bashProfile = home / ".bash_profile"
        if bashProfile.exists():
            return bashProfile
        return home / ".bashrc"
    else:
        bashrc = home / ".bashrc"
        if bashrc.exists():
            return bashrc
        return home / ".profile"

    return None


def hasEnvironmentVariable(configFile: Path, varName: str) -> bool:
    """
    Check if an environment variable is already set in the config file.

    Args:
        configFile: Path to shell config file
        varName: Environment variable name

    Returns:
        True if variable exists, False otherwise
    """
    if not configFile.exists():
        return False

    try:
        content = configFile.read_text(encoding='utf-8')
        pattern = rf'^\s*export\s+{re.escape(varName)}='
        return bool(re.search(pattern, content, re.MULTILINE))
    except Exception:
        return False


def addEnvironmentVariable(
    configFile: Path,
    varName: str,
    varValue: str,
    dryRun: bool = False,
) -> bool:
    """
    Add an environment variable to shell config file if it doesn't already exist.

    Args:
        configFile: Path to shell config file
        varName: Environment variable name
        varValue: Environment variable value
        dryRun: If True, don't actually modify file

    Returns:
        True if successful, False otherwise
    """
    if hasEnvironmentVariable(configFile, varName):
        printInfo(f"{varName} already set in {configFile.name}, skipping")
        return True

    exportLine = f'export {varName}="{varValue}"\n'

    if dryRun:
        printInfo(f"[DRY RUN] Would add to {configFile.name}: {exportLine.strip()}")
        return True

    try:
        if configFile.exists():
            content = configFile.read_text(encoding='utf-8')
            if not content.endswith('\n'):
                content += '\n'
            content += f'\n# Android SDK configuration (added by jrl_env)\n{exportLine}'
        else:
            content = f'# Android SDK configuration (added by jrl_env)\n{exportLine}'

        configFile.write_text(content, encoding='utf-8')
        printSuccess(f"Added {varName} to {configFile.name}")
        return True
    except Exception as e:
        printError(f"Failed to add {varName} to {configFile.name}: {e}")
        return False


def addToPath(
    configFile: Path,
    pathToAdd: str,
    dryRun: bool = False,
) -> bool:
    """
    Add a path to PATH environment variable if not already present.

    Args:
        configFile: Path to shell config file
        pathToAdd: Path to add to PATH
        dryRun: If True, don't actually modify file

    Returns:
        True if successful, False otherwise
    """
    if not configFile.exists():
        if dryRun:
            printInfo(f"[DRY RUN] Would create {configFile.name} and add {pathToAdd} to PATH")
            return True
        try:
            configFile.touch()
        except Exception as e:
            printError(f"Failed to create {configFile.name}: {e}")
            return False

    try:
        content = configFile.read_text(encoding='utf-8')
    except Exception as e:
        printError(f"Failed to read {configFile.name}: {e}")
        return False

    pathToAddNormalised = str(Path(pathToAdd).resolve())
    pathPattern = rf'PATH.*{re.escape(pathToAddNormalised)}'
    if re.search(pathPattern, content, re.MULTILINE):
        printInfo(f"{pathToAddNormalised} already in PATH in {configFile.name}, skipping")
        return True

    exportPathLine = f'export PATH="$PATH:{pathToAddNormalised}"\n'

    if dryRun:
        printInfo(f"[DRY RUN] Would add to PATH in {configFile.name}: {pathToAddNormalised}")
        return True

    try:
        if not content.endswith('\n'):
            content += '\n'
        content += f'\n# Android SDK PATH (added by jrl_env)\n{exportPathLine}'
        configFile.write_text(content, encoding='utf-8')
        printSuccess(f"Added {pathToAddNormalised} to PATH in {configFile.name}")
        return True
    except Exception as e:
        printError(f"Failed to add {pathToAddNormalised} to PATH: {e}")
        return False


def configureWindowsEnvironmentVariables(
    sdkRoot: Path,
    dryRun: bool = False,
) -> bool:
    """
    Configure Android environment variables on Windows using setx.

    Args:
        sdkRoot: Path to Android SDK root directory
        dryRun: If True, don't actually configure

    Returns:
        True if successful, False otherwise
    """
    import subprocess

    sdkRootStr = str(sdkRoot.resolve())
    success = True

    envVars = [
        ("ANDROID_HOME", sdkRootStr),
        ("ANDROID_SDK_ROOT", sdkRootStr),
    ]

    ndkRoot = findNdkRoot(sdkRoot)
    if ndkRoot:
        envVars.extend([
            ("ANDROID_NDK_HOME", str(ndkRoot.resolve())),
            ("NDK_HOME", str(ndkRoot.resolve())),
        ])

    printInfo("Configuring Android environment variables (Windows):")
    for varName, varValue in envVars:
        if dryRun:
            printInfo(f"[DRY RUN] Would set {varName}={varValue}")
            continue

        try:
            result = subprocess.run(
                ["setx", varName, varValue],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                printSuccess(f"Set {varName}={varValue}")
            else:
                printWarning(f"Failed to set {varName}: {result.stderr}")
                success = False
        except FileNotFoundError:
            printWarning("setx command not found. Please set environment variables manually:")
            printInfo(f"{varName}={varValue}")
            success = False
        except Exception as e:
            printError(f"Error setting {varName}: {e}")
            success = False
        safePrint()

    pathsToAdd = [
        sdkRoot / "platform-tools",
        sdkRoot / "tools",
        sdkRoot / "tools" / "bin",
        sdkRoot / "cmdline-tools" / "latest" / "bin",
    ]

    currentPath = os.environ.get("PATH", "")
    pathsToAddStr = [str(p.resolve()) for p in pathsToAdd if p.exists()]

    if pathsToAddStr:
        printInfo("Adding Android SDK tools to PATH:")
        if dryRun:
            for path in pathsToAddStr:
                printInfo(f"[DRY RUN] Would add to PATH: {path}")
        else:
            newPaths = [p for p in pathsToAddStr if p not in currentPath]
            if newPaths:
                try:
                    pathValue = currentPath + ";" + ";".join(newPaths)
                    result = subprocess.run(
                        ["setx", "PATH", pathValue],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if result.returncode == 0:
                        printSuccess(f"Added {len(newPaths)} path(s) to PATH")
                    else:
                        printWarning(f"Failed to update PATH: {result.stderr}")
                        printInfo("Please add these paths manually to PATH:")
                        for path in newPaths:
                            printInfo(f"{path}")
                        success = False
                except FileNotFoundError:
                    printWarning("setx command not found. Please add paths manually to PATH:")
                    for path in pathsToAddStr:
                        printInfo(f"{path}")
                    success = False
                except Exception as e:
                    printError(f"Error updating PATH: {e}")
                    success = False
            else:
                printInfo("All Android SDK paths already in PATH")
        safePrint()

    if success:
        printSuccess("Android environment variables configured successfully!")
        printInfo("Note: Restart your terminal for changes to take effect.")
    else:
        printWarning("Some environment variables may not have been configured.")

    return success


def configureAndroidEnvironmentVariables(
    sdkRoot: Path,
    dryRun: bool = False,
) -> bool:
    """
    Configure Android environment variables (ANDROID_HOME, ANDROID_SDK_ROOT, etc.)
    and add Android SDK tools to PATH.

    Args:
        sdkRoot: Path to Android SDK root directory
        dryRun: If True, don't actually configure

    Returns:
        True if successful, False otherwise
    """
    if sys.platform == "win32":
        return configureWindowsEnvironmentVariables(sdkRoot, dryRun=dryRun)

    configFile = getShellConfigFile()
    if not configFile:
        printWarning("Could not detect shell config file. Skipping environment variable configuration.")
        return False

    printInfo(f"Configuring Android environment variables in {configFile.name}")
    safePrint()

    sdkRootStr = str(sdkRoot.resolve())
    success = True

    envVars = [
        ("ANDROID_HOME", sdkRootStr),
        ("ANDROID_SDK_ROOT", sdkRootStr),
    ]

    for varName, varValue in envVars:
        if not addEnvironmentVariable(configFile, varName, varValue, dryRun=dryRun):
            success = False
        safePrint()

    pathsToAdd = [
        sdkRoot / "platform-tools",
        sdkRoot / "tools",
        sdkRoot / "tools" / "bin",
        sdkRoot / "cmdline-tools" / "latest" / "bin",
    ]

    printInfo("Adding Android SDK tools to PATH:")
    for path in pathsToAdd:
        if path.exists():
            if not addToPath(configFile, str(path), dryRun=dryRun):
                success = False
            safePrint()

    ndkRoot = findNdkRoot(sdkRoot)
    if ndkRoot:
        printInfo("Found Android NDK, configuring NDK_HOME")
        if not addEnvironmentVariable(configFile, "ANDROID_NDK_HOME", str(ndkRoot.resolve()), dryRun=dryRun):
            success = False
        if not addEnvironmentVariable(configFile, "NDK_HOME", str(ndkRoot.resolve()), dryRun=dryRun):
            success = False
        safePrint()

    if success:
        printSuccess("Android environment variables configured successfully!")
        printInfo(f"Note: Restart your terminal or run 'source {configFile.name}' for changes to take effect.")
    else:
        printWarning("Some environment variables may not have been configured.")

    return success


def findNdkRoot(sdkRoot: Path) -> Optional[Path]:
    """
    Find Android NDK root directory.

    Args:
        sdkRoot: Android SDK root directory

    Returns:
        Path to NDK root if found, None otherwise
    """
    ndkDir = sdkRoot / "ndk"
    if not ndkDir.exists():
        return None

    ndkVersions = sorted(ndkDir.iterdir(), key=lambda p: p.name, reverse=True)
    if ndkVersions:
        return ndkVersions[0]

    return None


__all__ = [
    "getShellConfigFile",
    "hasEnvironmentVariable",
    "addEnvironmentVariable",
    "addToPath",
    "configureWindowsEnvironmentVariables",
    "configureAndroidEnvironmentVariables",
    "findNdkRoot",
]
