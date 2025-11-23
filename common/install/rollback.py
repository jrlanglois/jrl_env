#!/usr/bin/env python3
"""
Rollback mechanism for failed setups.
Tracks installed packages and configuration changes, allowing rollback on failure.
"""

import json
import os
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

# Add project root to path
scriptDir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(scriptDir))

from common.core.logging import (
    printError,
    printInfo,
    printH2,
    printSuccess,
    printWarning,
    safePrint,
)
from common.systems.platform import isWindows


@dataclass
class RollbackSession:
    """Session data for tracking setup changes."""
    sessionId: str
    timestamp: str
    backupDir: Optional[str] = None
    installedPackages: List[str] = None
    updatedPackages: List[str] = None
    configuredGit: bool = False
    configuredCursor: bool = False
    configuredSsh: bool = False
    clonedRepos: List[str] = None

    def __post_init__(self):
        if self.installedPackages is None:
            self.installedPackages = []
        if self.updatedPackages is None:
            self.updatedPackages = []
        if self.clonedRepos is None:
            self.clonedRepos = []


def getSessionDir() -> Path:
    """Get the directory for storing rollback sessions."""
    if isWindows():
        tmpBase = os.environ.get("TEMP", os.environ.get("TMP", "C:\\Temp"))
    else:
        tmpBase = os.environ.get("TMPDIR", "/tmp")

    sessionDir = Path(tmpBase) / "jrl_env_sessions"
    sessionDir.mkdir(parents=True, exist_ok=True)
    return sessionDir


def createSession(backupDir: Optional[str] = None) -> RollbackSession:
    """
    Create a new rollback session.

    Args:
        backupDir: Path to backup directory (if configs were backed up)

    Returns:
        RollbackSession instance
    """
    sessionId = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp = datetime.now().isoformat()

    session = RollbackSession(
        sessionId=sessionId,
        timestamp=timestamp,
        backupDir=backupDir,
    )

    return session


def saveSession(session: RollbackSession) -> Path:
    """
    Save a rollback session to disk.

    Args:
        session: RollbackSession to save

    Returns:
        Path to saved session file
    """
    sessionDir = getSessionDir()
    sessionFile = sessionDir / f"session_{session.sessionId}.json"

    with open(sessionFile, 'w', encoding='utf-8') as f:
        json.dump(asdict(session), f, indent=2)

    return sessionFile


def loadSession(sessionId: str) -> Optional[RollbackSession]:
    """
    Load a rollback session from disk.

    Args:
        sessionId: Session ID to load

    Returns:
        RollbackSession if found, None otherwise
    """
    sessionDir = getSessionDir()
    sessionFile = sessionDir / f"session_{sessionId}.json"

    if not sessionFile.exists():
        return None

    try:
        with open(sessionFile, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return RollbackSession(**data)
    except Exception as e:
        printError(f"Failed to load session {sessionId}: {e}")
        return None


def getLatestSession() -> Optional[RollbackSession]:
    """
    Get the most recent rollback session.

    Returns:
        Latest RollbackSession if found, None otherwise
    """
    sessionDir = getSessionDir()
    sessionFiles = sorted(sessionDir.glob("session_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not sessionFiles:
        return None

    latestFile = sessionFiles[0]
    sessionId = latestFile.stem.replace("session_", "")
    return loadSession(sessionId)


def restoreConfigs(backupDir: str) -> bool:
    """
    Restore configuration files from backup.

    Args:
        backupDir: Path to backup directory

    Returns:
        True if restoration succeeded, False otherwise
    """
    backupPath = Path(backupDir)
    if not backupPath.exists():
        printWarning(f"Backup directory does not exist: {backupDir}")
        return False

    printInfo("Restoring configuration files...")

    # Restore Git config
    gitBackup = backupPath / "gitconfig"
    if gitBackup.exists():
        gitConfig = Path.home() / ".gitconfig"
        try:
            shutil.copy2(gitBackup, gitConfig)
            printSuccess("Restored Git config")
        except Exception as e:
            printError(f"Failed to restore Git config: {e}")
            return False

    # Restore Cursor settings
    cursorBackup = backupPath / "Cursor" / "settings.json"
    if cursorBackup.exists():
        # Determine Cursor settings path based on platform
        if isWindows():
            cursorSettings = Path.home() / "AppData/Roaming/Cursor/User/settings.json"
        else:
            cursorSettings = Path.home() / ".config/Cursor/User/settings.json"

        try:
            cursorSettings.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cursorBackup, cursorSettings)
            printSuccess("Restored Cursor settings")
        except Exception as e:
            printError(f"Failed to restore Cursor settings: {e}")
            return False

    return True


def uninstallPackages(
    packages: List[str],
    uninstallFunction: Optional[Callable[[str], bool]] = None,
    packageManager: Optional[str] = None,
) -> bool:
    """
    Uninstall packages that were installed during this session.

    Args:
        packages: List of package names to uninstall
        uninstallFunction: Optional function to uninstall a package (takes package name, returns bool)
        packageManager: Optional package manager name for logging

    Returns:
        True if all uninstalls succeeded, False otherwise
    """
    if not packages:
        return True

    printInfo(f"Uninstalling {len(packages)} package(s)...")

    if not uninstallFunction:
        printWarning("No uninstall function provided. Cannot uninstall packages.")
        printInfo("You may need to manually uninstall:")
        for pkg in packages:
            printInfo(f"- {pkg}")
        return False

    failed = []
    for package in packages:
        try:
            if uninstallFunction(package):
                printSuccess(f"Uninstalled: {package}")
            else:
                printWarning(f"Failed to uninstall: {package}")
                failed.append(package)
        except Exception as e:
            printError(f"Error uninstalling {package}: {e}")
            failed.append(package)

    if failed:
        printWarning(f"Failed to uninstall {len(failed)} package(s)")
        return False

    printSuccess(f"Successfully uninstalled {len(packages)} package(s)")
    return True


def rollback(session: RollbackSession, uninstallFunction: Optional[Callable[[str], bool]] = None) -> bool:
    """
    Perform rollback of a setup session.

    Args:
        session: RollbackSession to rollback
        uninstallFunction: Optional function to uninstall packages

    Returns:
        True if rollback succeeded, False otherwise
    """
    printH2("Rollback")
    printInfo(f"Rolling back session: {session.sessionId}")
    printInfo(f"Session timestamp: {session.timestamp}")
    safePrint()

    success = True

    # Restore configs if backup exists
    if session.backupDir:
        if not restoreConfigs(session.backupDir):
            success = False
        safePrint()

    # Uninstall packages
    if session.installedPackages:
        if not uninstallPackages(session.installedPackages, uninstallFunction):
            success = False
        safePrint()

    if success:
        printSuccess("Rollback completed successfully")
    else:
        printWarning("Rollback completed with some issues")

    return success


def listSessions() -> List[RollbackSession]:
    """
    List all available rollback sessions.

    Returns:
        List of RollbackSession objects, sorted by timestamp (newest first)
    """
    sessionDir = getSessionDir()
    sessionFiles = sorted(sessionDir.glob("session_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    sessions = []
    for sessionFile in sessionFiles:
        sessionId = sessionFile.stem.replace("session_", "")
        session = loadSession(sessionId)
        if session:
            sessions.append(session)

    return sessions
