#!/usr/bin/env python3
"""
Enhanced validation for repositories config.
Checks if repositories exist and validates work paths.
"""

import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

# Add project root to path so we can import from common
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent
sys.path.insert(0, str(projectRoot))

from common.common import (
    commandExists,
    getJsonArray,
    getJsonValue,
    printError,
    printInfo,
    printH2,
    printSuccess,
    printWarning,
    safePrint,
)


def validateUnixPath(path: str) -> bool:
    """
    Validate Unix path syntax.

    Args:
        path: Path string to validate

    Returns:
        True if path is valid, False otherwise
    """
    # Check for valid path characters (basic validation)
    # Should start with ~, /, $HOME, or $USER
    pattern = r'^(~|/|\$HOME|\$USER)'
    return bool(re.match(pattern, path))


def validateWindowsPath(path: str) -> bool:
    """
    Validate Windows path syntax.

    Args:
        path: Path string to validate

    Returns:
        True if path is valid, False otherwise
    """
    # Check for valid Windows path (drive letter or UNC)
    # Should start with drive letter, \\, $USERPROFILE, or $HOME
    pattern = r'^([A-Za-z]:|\\\\|\$USERPROFILE|\$HOME)'
    return bool(re.match(pattern, path))


def convertSshToHttps(repoUrl: str) -> Optional[str]:
    """
    Convert GitHub SSH URL to HTTPS URL for validation.

    Args:
        repoUrl: Repository URL (SSH or HTTPS)

    Returns:
        HTTPS URL if conversion successful, None otherwise
    """
    # Convert git@github.com:owner/repo.git to https://github.com/owner/repo
    match = re.match(r'^git@github\.com:(.+?)(?:\.git)?$', repoUrl)
    if match:
        ownerRepo = match.group(1)
        return f"https://github.com/{ownerRepo}"

    return None


def checkGitHubRepository(ownerRepo: str) -> Tuple[Optional[bool], str]:
    """
    Check if a GitHub repository exists via API.

    Args:
        ownerRepo: Repository in format "owner/repo"

    Returns:
        Tuple of (exists: bool|None, message: str)
        None means we couldn't determine (network error, etc.)
    """
    apiUrl = f"https://api.github.com/repos/{ownerRepo}"

    try:
        req = urllib.request.Request(apiUrl)
        req.add_header('User-Agent', 'jrl_env-validator')

        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                return True, "Repository exists"
            else:
                return False, f"Unexpected status: {response.status}"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Could be private repo or doesn't exist
            return None, "Repository not found or is private (404)"
        elif e.code == 403:
            return None, "Repository access forbidden (403) - may be private or rate limited"
        else:
            return None, f"HTTP error: {e.code}"
    except urllib.error.URLError:
        return None, "Could not reach GitHub API - network issue or timeout"
    except Exception as e:
        return None, f"Error: {str(e)}"


def checkGitRepository(repoUrl: str) -> bool:
    """
    Check if a Git repository exists via git ls-remote.

    Args:
        repoUrl: Repository URL

    Returns:
        True if repository exists, False otherwise
    """
    try:
        result = subprocess.run(
            ["git", "ls-remote", repoUrl],
            capture_output=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def validateRepositories(configPath: str) -> int:
    """
    Validate repositories from config file.

    Args:
        configPath: Path to repositories.json config file

    Returns:
        0 if all repositories are valid, 1 otherwise
    """
    configFile = Path(configPath)

    if not configFile.exists():
        printError(f"Config file not found: {configPath}")
        return 1

    printH2("Validating Repositories Config")
    safePrint()

    # Validate JSON syntax
    try:
        with open(configFile, 'r', encoding='utf-8') as f:
            json.load(f)
    except json.JSONDecodeError as e:
        printError(f"Invalid JSON syntax: {e}")
        return 1
    except Exception as e:
        printError(f"Error reading config: {e}")
        return 1

    errors = 0

    # Validate work paths
    printInfo("Validating work paths...")
    workPathUnix = getJsonValue(configPath, ".workPathUnix", "")
    workPathWindows = getJsonValue(configPath, ".workPathWindows", "")

    if not workPathUnix and not workPathWindows:
        printError("Missing workPathUnix or workPathWindows")
        errors += 1
    else:
        # Validate Unix path syntax
        if workPathUnix and workPathUnix != "null":
            if validateUnixPath(workPathUnix):
                printSuccess(f"workPathUnix: {workPathUnix}")
            else:
                printError(f"workPathUnix: {workPathUnix} (should start with ~, /, $HOME, or $USER)")
                errors += 1

        # Validate Windows path syntax
        if workPathWindows and workPathWindows != "null":
            if validateWindowsPath(workPathWindows):
                printSuccess(f"workPathWindows: {workPathWindows}")
            else:
                printError(f"workPathWindows: {workPathWindows} (should start with drive letter, \\\\, $USERPROFILE, or $HOME)")
                errors += 1

    safePrint()

    # Validate repositories
    printInfo("Validating repositories...")
    repositories = getJsonArray(configPath, ".repositories[]?")

    if not repositories:
        printWarning("No repositories specified")
        return 0

    # Check if git is available
    if not commandExists("git"):
        printWarning("git is not available. Cannot validate repository existence.")
        printInfo("Repositories will be validated at clone time.")
        return 0

    repoCount = 0

    for repoUrl in repositories:
        if not repoUrl or not repoUrl.strip():
            continue

        repoUrl = repoUrl.strip()
        repoCount += 1
        printInfo(f"Checking: {repoUrl}")

        # Validate URL format
        if re.match(r'^(https?|git)://|^git@', repoUrl):
            # Convert SSH URL to HTTPS for validation (if it's a GitHub URL)
            checkUrl = convertSshToHttps(repoUrl)

            if checkUrl:
                # Check GitHub repository via API
                ownerRepo = checkUrl.replace("https://github.com/", "")
                exists, message = checkGitHubRepository(ownerRepo)

                if exists:
                    printSuccess(f"  Repository exists")
                elif exists is None:
                    printWarning(f"  {message} - will be validated at clone time")
                else:
                    printWarning(f"  {message} - will be validated at clone time")
            elif repoUrl.startswith("git@"):
                # Other SSH URLs - can't easily validate without SSH keys
                printWarning("SSH URL detected - cannot validate without SSH keys (format is valid)")
            elif repoUrl.startswith("https://github.com/"):
                # Direct GitHub HTTPS URL
                ownerRepo = repoUrl.replace("https://github.com/", "").replace(".git", "")
                exists, message = checkGitHubRepository(ownerRepo)

                if exists:
                    printSuccess(f"  Repository exists")
                elif exists is None:
                    printWarning(f"  {message} - will be validated at clone time")
                else:
                    printWarning(f"  {message} - will be validated at clone time")
            else:
                # Other HTTPS/Git URLs - try git ls-remote
                if checkGitRepository(repoUrl):
                    printSuccess(f"  Repository exists")
                else:
                    printError(f"  Repository not accessible or does not exist")
                    errors += 1
        else:
            printError(f"  Invalid repository URL format")
            errors += 1

    safePrint()
    printInfo(f"Checked {repoCount} repository/repositories")

    if errors == 0:
        printSuccess("All repositories are valid!")
        return 0
    else:
        printError(f"Found {errors} validation error(s)")
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        printError("Usage: python3 validateRepositories.py <path-to-repositories.json>")
        sys.exit(1)

    configPath = sys.argv[1]
    startTime = time.perf_counter()
    exitCode = validateRepositories(configPath)
    elapsed = time.perf_counter() - startTime
    safePrint()
    printInfo(f"Validation completed in {elapsed:.2f}s")
    sys.exit(exitCode)
