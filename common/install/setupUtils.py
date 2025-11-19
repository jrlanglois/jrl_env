#!/usr/bin/env python3
"""
Shared setup utilities for all platforms.
Provides common functions used across platform-specific setup scripts.
"""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

# Add project root to path so we can import from common
scriptDir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(scriptDir))

# Import directly from source modules to avoid circular import with common.common
from common.core.utilities import (
    commandExists,
    getJsonValue,
)
from common.core.logging import (
    printError,
    printInfo,
    printSuccess,
    printWarning,
)
from common.configure.cloneRepositories import expandPath
from common.configure.configureGit import isGitInstalled


def initLogging(platformName: str) -> str:
    """
    Initialise logging to a file.

    Args:
        platformName: Name of the platform (e.g., "macos", "ubuntu", "win11")

    Returns:
        Path to log file
    """
    # Determine temp directory based on platform
    if sys.platform == "win32":
        tmpBase = os.environ.get("TEMP", os.environ.get("TMP", "C:\\Temp"))
    else:
        tmpBase = os.environ.get("TMPDIR", "/tmp")

    logDir = Path(tmpBase) / "jrl_env_logs"
    logDir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logFilePath = logDir / f"setup_{platformName}_{timestamp}.log"

    # Write initial log entry
    initMessage = f"=== jrl_env Setup Log - Started at {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')} ===\n"
    with open(logFilePath, 'w', encoding='utf-8') as f:
        f.write(initMessage)

    return str(logFilePath)


def backupConfigs(noBackup: bool, dryRun: bool, cursorSettingsPath: Optional[str] = None) -> Optional[str]:
    """
    Backup configuration files before setup.

    Args:
        noBackup: If True, skip backup
        dryRun: If True, skip backup
        cursorSettingsPath: Platform-specific path to Cursor settings (optional)

    Returns:
        Path to backup directory if backup was created, None otherwise
    """
    if noBackup or dryRun:
        printInfo("Backup skipped (noBackup or dryRun flag set)")
        return None

    # Determine temp directory based on platform
    if sys.platform == "win32":
        tmpBase = os.environ.get("TEMP", os.environ.get("TMP", "C:\\Temp"))
    else:
        tmpBase = os.environ.get("TMPDIR", "/tmp")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backupDir = Path(tmpBase) / f"jrl_env_backup_{timestamp}"
    backupDir.mkdir(parents=True, exist_ok=True)

    printInfo("Creating backup...")

    # Backup Git config
    gitConfig = Path.home() / ".gitconfig"
    if gitConfig.exists():
        try:
            shutil.copy2(gitConfig, backupDir / "gitconfig")
            printSuccess("Backed up Git config")
        except Exception:
            pass

    # Backup Cursor settings (platform-specific path)
    if cursorSettingsPath:
        cursorSettings = Path(cursorSettingsPath)
        if cursorSettings.exists():
            try:
                cursorBackupDir = backupDir / "Cursor"
                cursorBackupDir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(cursorSettings, cursorBackupDir / "settings.json")
                printSuccess("Backed up Cursor settings")
            except Exception:
                pass

    printSuccess(f"Backup created: {backupDir}")
    return str(backupDir)


def checkDependencies(
    requiredCommands: List[str],
    checkFunctions: Optional[List[Callable[[], bool]]] = None,
) -> bool:
    """
    Check if required dependencies are installed.

    Args:
        requiredCommands: List of command names to check (e.g., ["git", "brew"])
        checkFunctions: Optional list of functions that return True if dependency is available

    Returns:
        True if user wants to continue, False otherwise
    """
    printInfo("Checking dependencies...")
    missing = []

    # Check commands
    for cmd in requiredCommands:
        if not commandExists(cmd):
            missing.append(cmd)
            printWarning(f"{cmd} is not installed")
        else:
            printSuccess(f"{cmd} is installed")

    # Check custom functions
    if checkFunctions:
        for checkFunc in checkFunctions:
            if not checkFunc():
                # Try to get a name from the function
                funcName = checkFunc.__name__
                missing.append(funcName)
                printWarning(f"{funcName} check failed")
            else:
                funcName = checkFunc.__name__
                printSuccess(f"{funcName} check passed")

    if missing:
        printWarning(f"Missing dependencies: {', '.join(missing)}")
        response = input("Some features may not work. Continue anyway? (Y/N): ").strip()
        if response.upper() != "Y":
            printError("Setup cancelled by user due to missing dependencies")
            return False
        printInfo("User chose to continue despite missing dependencies")
    else:
        printSuccess("All dependencies are installed")

    return True


def shouldCloneRepositories(configPath: str, workPathKey: str = ".workPathUnix") -> bool:
    """
    Check if repositories should be cloned (only on first run).

    Args:
        configPath: Path to repositories.json config file
        workPathKey: JSON key for work path (".workPathUnix" for Unix, ".workPathWindows" for Windows)

    Returns:
        True if repositories should be cloned, False otherwise
    """
    workPath = getJsonValue(configPath, workPathKey, "")
    if not workPath or workPath == "null":
        return False

    workPath = expandPath(workPath)
    workPathObj = Path(workPath)

    if not workPathObj.exists():
        return True

    # Check if work directory has any owner subdirectories
    ownerDirs = [d for d in workPathObj.iterdir() if d.is_dir()]
    return len(ownerDirs) == 0
