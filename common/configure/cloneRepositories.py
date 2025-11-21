#!/usr/bin/env python3
"""
Shared repository cloning logic.
Clones Git repositories from a JSON config file to a structured work directory.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Import common utilities directly from source modules
from common.core.logging import (
    printError,
    printInfo,
    printH2,
    printSuccess,
    printWarning,
    safePrint,
)
from common.core.utilities import (
    commandExists,
    getJsonArray,
    getJsonValue,
)


def isGitInstalled() -> bool:
    """Check if Git is installed."""
    return commandExists("git")


def getRepositoryOwner(repoUrl: str) -> Optional[str]:
    """
    Extract repository owner from URL.

    Args:
        repoUrl: Repository URL (SSH or HTTPS)

    Returns:
        Owner name, or None if not found
    """
    # Try GitHub HTTPS pattern: https://github.com/owner/repo.git
    match = re.search(r'github\.com/([^/]+)/', repoUrl)
    if match:
        return match.group(1)

    # Try SSH pattern: git@github.com:owner/repo.git
    match = re.search(r':([^/]+)/', repoUrl)
    if match:
        return match.group(1)

    return None


def getRepositoryName(repoUrl: str) -> Optional[str]:
    """
    Extract repository name from URL.

    Args:
        repoUrl: Repository URL (SSH or HTTPS)

    Returns:
        Repository name (without .git extension), or None if not found
    """
    # Match the last segment before .git or end of string
    match = re.search(r'[:/]([^/]+?)(?:\.git)?$', repoUrl)
    if match:
        return match.group(1)

    return None


def isRepositoryCloned(repoUrl: str, workPath: str) -> bool:
    """
    Check if a repository is already cloned.

    Args:
        repoUrl: Repository URL
        workPath: Work directory path

    Returns:
        True if repository exists and has .git directory, False otherwise
    """
    owner = getRepositoryOwner(repoUrl)
    repoName = getRepositoryName(repoUrl)

    if not owner or not repoName:
        return False

    repoPath = Path(workPath) / owner / repoName
    gitDir = repoPath / ".git"

    return repoPath.exists() and repoPath.is_dir() and gitDir.exists() and gitDir.is_dir()


def cloneRepository(repoUrl: str, workPath: str) -> bool:
    """
    Clone a repository to the work directory.

    Args:
        repoUrl: Repository URL to clone
        workPath: Work directory path

    Returns:
        True if successful, False otherwise
    """
    owner = getRepositoryOwner(repoUrl)
    repoName = getRepositoryName(repoUrl)

    if not owner or not repoName:
        printError("Failed to extract owner or repository name from URL")
        return False

    workPathObj = Path(workPath)
    ownerPath = workPathObj / owner
    ownerPath.mkdir(parents=True, exist_ok=True)

    repoPath = ownerPath / repoName

    if isRepositoryCloned(repoUrl, workPath):
        printWarning(f"Repository already exists: {owner}/{repoName}")
        safePrint("Skipping clone. Use 'git pull' to update if needed.")
        return True

    printInfo(f"Cloning {owner}/{repoName}...")

    try:
        subprocess.run(
            ["git", "clone", "--recursive", repoUrl, str(repoPath)],
            check=True,
            capture_output=True,
        )
        printSuccess("Cloned successfully")

        # Check if submodules were initialised
        gitmodulesPath = repoPath / ".gitmodules"
        if gitmodulesPath.exists():
            printSuccess("Submodules initialised")

        return True
    except subprocess.CalledProcessError:
        printError("Clone failed")
        return False


def expandPath(path: str) -> str:
    """
    Expand environment variables in path (e.g., $HOME, $USER).

    Args:
        path: Path string with potential environment variables

    Returns:
        Expanded path string
    """
    return os.path.expandvars(path)


def cloneRepositories(
    configPath: Optional[str] = None,
    dryRun: bool = False,
) -> bool:
    """
    Clone repositories from JSON config file.

    Args:
        configPath: Path to repositories.json config file
        dryRun: If True, don't actually clone repositories

    Returns:
        True if successful, False otherwise
    """
    printH2("Repository Cloning", dryRun=dryRun)
    safePrint()

    if not isGitInstalled():
        printError("Git is not installed.")
        printInfo("Please install Git first.")
        return False

    if not configPath:
        printError("Configuration file path not provided")
        return False

    configFile = Path(configPath)
    if not configFile.exists():
        printError(f"Configuration file not found: {configPath}")
        return False

    # Read work path and repositories
    workPath = getJsonValue(configPath, ".workPathUnix", "")
    repositories = getJsonArray(configPath, ".repositories[]?")

    # Expand environment variables in work path
    workPath = expandPath(workPath)

    if not workPath or workPath == "null":
        printError("JSON file must contain a 'workPathUnix' property.")
        return False

    if not repositories:
        printInfo("No repositories specified in configuration file.")
        return True

    repoCount = len(repositories)
    printInfo(f"Work directory: {workPath}")
    printInfo(f"Found {repoCount} repository/repositories in configuration file.")
    safePrint()

    # Create work directory if it doesn't exist
    workPathObj = Path(workPath)
    if not workPathObj.exists():
        if dryRun:
            printInfo(f"[DRY RUN] Would create work directory: {workPath}")
        else:
            printInfo(f"Creating work directory: {workPath}")
            workPathObj.mkdir(parents=True, exist_ok=True)
            printSuccess("Work directory created")
        safePrint()

    clonedCount = 0
    skippedCount = 0
    failedCount = 0

    if dryRun:
        printInfo("[DRY RUN] Would clone the following repositories:")
        for repoUrl in repositories:
            if not repoUrl or not repoUrl.strip():
                continue
            repoUrl = repoUrl.strip()
            printInfo(f"- {repoUrl}")
        clonedCount = len([r for r in repositories if r and r.strip()])
    else:
        for repoUrl in repositories:
            if not repoUrl or not repoUrl.strip():
                continue

            repoUrl = repoUrl.strip()
            printInfo(f"Processing: {repoUrl}")

            if cloneRepository(repoUrl, workPath):
                clonedCount += 1
            elif isRepositoryCloned(repoUrl, workPath):
                skippedCount += 1
            else:
                failedCount += 1

            safePrint()

    printInfo("Summary:")
    if dryRun:
        printInfo(f"Would clone: {clonedCount} repository/repositories")
    else:
        printSuccess(f"Cloned: {clonedCount} repository/repositories")
        if skippedCount > 0:
            printInfo(f"Skipped: {skippedCount} repository/repositories (already exist)")
        if failedCount > 0:
            printError(f"Failed: {failedCount} repository/repositories")

    safePrint()
    printSuccess("Repository cloning complete!")

    return True


__all__ = [
    "isGitInstalled",
    "getRepositoryOwner",
    "getRepositoryName",
    "isRepositoryCloned",
    "cloneRepository",
    "expandPath",
    "cloneRepositories",
]
