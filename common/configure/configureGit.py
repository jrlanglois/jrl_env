#!/usr/bin/env python3
"""
Shared Git configuration logic for macOS, Ubuntu, and Windows.
Provides functions to configure Git user info, defaults, aliases, and LFS.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

# Import common utilities directly from source modules
from common.core.logging import (
    printError,
    printInfo,
    printSection,
    printSuccess,
    printWarning,
)
from common.core.utilities import (
    commandExists,
    getJsonObject,
    getJsonValue,
    requireCommand,
)


def isGitInstalled() -> bool:
    """Check if Git is installed."""
    return commandExists("git")


def readJsonSection(configPath: str, sectionKey: str) -> Dict:
    """
    Read a JSON section from a config file.

    Args:
        configPath: Path to JSON config file
        sectionKey: Key of the section to read

    Returns:
        Dictionary containing the section data, or empty dict if not found
    """
    if not configPath or not Path(configPath).exists():
        return {}

    try:
        with open(configPath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get(sectionKey, {})
    except Exception:
        return {}


def setGitConfig(
    configKey: str,
    configValue: str,
    description: Optional[str] = None,
    successMessage: Optional[str] = None,
    dryRun: bool = False,
) -> bool:
    """
    Set a Git config value with output.

    Args:
        configKey: Git config key (e.g., "user.name")
        configValue: Value to set
        description: Optional description message
        successMessage: Optional success message
        dryRun: If True, don't actually set the config

    Returns:
        True if successful, False otherwise
    """
    if not description:
        description = f"Setting {configKey}..."
    if not successMessage:
        successMessage = f"✓ {configKey} set to '{configValue}'"

    printInfo(description)
    if dryRun:
        printInfo(f"  [DRY RUN] Would set {configKey} = '{configValue}'")
        printSuccess(successMessage)
        return True

    try:
        subprocess.run(
            ["git", "config", "--global", configKey, configValue],
            check=True,
            capture_output=True,
        )
        printSuccess(successMessage)
        return True
    except subprocess.CalledProcessError:
        printError(f"Failed to set {configKey}")
        return False


def configureGitUser(dryRun: bool = False) -> bool:
    """
    Configure Git user information interactively.

    Args:
        dryRun: If True, don't actually configure

    Returns:
        True if successful, False otherwise
    """
    printInfo("Configuring Git user information...")

    try:
        currentName = subprocess.run(
            ["git", "config", "--global", "user.name"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()

        currentEmail = subprocess.run(
            ["git", "config", "--global", "user.email"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
    except Exception:
        currentName = ""
        currentEmail = ""

    if dryRun:
        printInfo("  [DRY RUN] Would configure Git user information interactively")
        printSuccess("Git user information configured successfully")
        return True

    if currentName and currentEmail:
        printInfo("Current Git user configuration:")
        print(f"  Name:  {currentName}")
        print(f"  Email: {currentEmail}")
        keepExisting = input("Keep existing configuration? (Y/N): ").strip()
        if keepExisting.upper() == "Y":
            printSuccess("Keeping existing configuration")
            return True

    if not currentName:
        userName = input("Enter your name: ").strip()
    else:
        userNameInput = input(f"Enter your name [{currentName}]: ").strip()
        userName = userNameInput if userNameInput else currentName

    if not currentEmail:
        userEmail = input("Enter your email: ").strip()
    else:
        userEmailInput = input(f"Enter your email [{currentEmail}]: ").strip()
        userEmail = userEmailInput if userEmailInput else currentEmail

    try:
        subprocess.run(
            ["git", "config", "--global", "user.name", userName],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "--global", "user.email", userEmail],
            check=True,
            capture_output=True,
        )
        printSuccess("Git user information configured successfully")
        return True
    except subprocess.CalledProcessError:
        printError("Failed to configure Git user information")
        return False


def configureGitDefaults(configPath: Optional[str] = None, dryRun: bool = False) -> bool:
    """
    Configure Git default settings from JSON config.

    Args:
        configPath: Optional path to gitConfig.json file
        dryRun: If True, don't actually configure

    Returns:
        True if successful, False otherwise
    """
    printInfo("Configuring Git default settings...")

    defaultsJson = readJsonSection(configPath or "", "defaults")

    # defaultsJson is a dict, access it directly
    defaultBranch = defaultsJson.get("init.defaultBranch", "main")
    colourUi = defaultsJson.get("color.ui", "auto")
    pullRebase = defaultsJson.get("pull.rebase", "false")
    pushDefault = defaultsJson.get("push.default", "simple")
    pushAutoSetup = defaultsJson.get("push.autoSetupRemote", "true")
    rebaseAutoStash = defaultsJson.get("rebase.autoStash", "true")
    mergeFf = defaultsJson.get("merge.ff", "false")
    fetchParallel = defaultsJson.get("fetch.parallel", "8")

    setGitConfig(
        "init.defaultBranch",
        defaultBranch,
        f"Setting default branch name to '{defaultBranch}'...",
        f"✓ Default branch set to '{defaultBranch}'",
        dryRun=dryRun,
    )

    setGitConfig(
        "color.ui",
        colourUi,
        "Enabling colour output...",
        "✓ Colour output enabled",
        dryRun=dryRun,
    )

    setGitConfig("pull.rebase", pullRebase, "Configuring pull behaviour...", "", dryRun=dryRun)
    pullBehaviour = "rebase" if pullRebase == "true" else "merge (default)"
    printSuccess(f"Pull behaviour set to {pullBehaviour}")

    setGitConfig(
        "push.default",
        pushDefault,
        "Configuring push behaviour...",
        f"✓ Push default set to '{pushDefault}'",
        dryRun=dryRun,
    )

    setGitConfig(
        "push.autoSetupRemote",
        pushAutoSetup,
        "Configuring push auto-setup...",
        "✓ Push auto-setup remote enabled",
        dryRun=dryRun,
    )

    setGitConfig(
        "rebase.autoStash",
        rebaseAutoStash,
        "Configuring rebase behaviour...",
        "✓ Rebase auto-stash enabled",
        dryRun=dryRun,
    )

    setGitConfig("merge.ff", mergeFf, "Configuring merge strategy...", "", dryRun=dryRun)
    if mergeFf == "false":
        printSuccess("Merge fast-forward disabled (creates merge commits)")
    else:
        printSuccess("Merge fast-forward enabled")

    if fetchParallel and fetchParallel != "null":
        setGitConfig(
            "fetch.parallel",
            fetchParallel,
            "Configuring fetch parallel jobs...",
            f"✓ Fetch parallel jobs set to {fetchParallel}",
            dryRun=dryRun,
        )

    printSuccess("Git default settings configured successfully!")
    return True


def addGitAlias(aliasName: str, aliasCommand: str, dryRun: bool = False) -> bool:
    """
    Add a Git alias if it doesn't exist.

    Args:
        aliasName: Name of the alias
        aliasCommand: Command for the alias
        dryRun: If True, don't actually add the alias

    Returns:
        True if alias was added, False if it already exists
    """
    if dryRun:
        printInfo(f"  [DRY RUN] Would add alias: {aliasName} = {aliasCommand}")
        printSuccess(f"Added alias: {aliasName}")
        return True

    try:
        result = subprocess.run(
            ["git", "config", "--global", "--get", f"alias.{aliasName}"],
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            printWarning(f"Alias '{aliasName}' already exists, skipping...")
            return False
        else:
            subprocess.run(
                ["git", "config", "--global", f"alias.{aliasName}", aliasCommand],
                check=True,
                capture_output=True,
            )
            printSuccess(f"Added alias: {aliasName}")
            return True
    except subprocess.CalledProcessError:
        printError(f"Failed to add alias '{aliasName}'")
        return False


def configureGitAliases(configPath: Optional[str] = None, dryRun: bool = False) -> bool:
    """
    Configure Git aliases from JSON config or use defaults.

    Args:
        configPath: Optional path to gitConfig.json file
        dryRun: If True, don't actually configure

    Returns:
        True if successful, False otherwise
    """
    printInfo("Configuring Git aliases...")

    aliasesJson = readJsonSection(configPath or "", "aliases")

    # If no aliases found in config, use defaults
    if not aliasesJson:
        defaultAliases = {
            "st": "status",
            "co": "checkout",
            "br": "branch",
            "ci": "commit",
            "unstage": "reset HEAD --",
            "last": "log -1 HEAD",
            "visual": "!code",
            "log1": "log --oneline",
            "logg": "log --oneline --graph --decorate --all",
            "amend": "commit --amend",
            "uncommit": "reset --soft HEAD^",
            "stash-all": "stash --include-untracked",
            "undo": "reset HEAD~1",
        }

        for aliasName, aliasCommand in defaultAliases.items():
            addGitAlias(aliasName, aliasCommand, dryRun=dryRun)
    else:
        # Process aliases from JSON
        for aliasName, aliasCommand in aliasesJson.items():
            if not aliasCommand or aliasCommand == "null":
                continue
            addGitAlias(aliasName, aliasCommand, dryRun=dryRun)

    printSuccess("Git aliases configured successfully!")
    return True


def configureGitLfs(dryRun: bool = False) -> bool:
    """
    Configure Git LFS if available.

    Args:
        dryRun: If True, don't actually configure

    Returns:
        True if successful or skipped, False on error
    """
    printInfo("Configuring Git LFS...")

    if not commandExists("git-lfs"):
        printWarning("git-lfs is not installed. Skipping LFS configuration.")
        return True

    if dryRun:
        printInfo("  [DRY RUN] Would initialise Git LFS")
        printSuccess("Git LFS initialised successfully")
        return True

    try:
        # Check if git lfs is available
        result = subprocess.run(
            ["git", "lfs", "version"],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            printWarning("Git LFS command not available")
            return True

        printInfo("Initialising Git LFS...")
        result = subprocess.run(
            ["git", "lfs", "install"],
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            printSuccess("Git LFS initialised successfully")
        else:
            printWarning("Git LFS may already be initialised")

        printSuccess("Git LFS configured successfully!")
        return True
    except Exception as e:
        printError(f"Error configuring Git LFS: {e}")
        return False


def configureGit(configPath: Optional[str] = None, installHint: str = "Please install Git via your package manager.", dryRun: bool = False) -> bool:
    """
    Main function to configure Git.

    Args:
        configPath: Optional path to gitConfig.json file
        installHint: Hint message if Git is not installed
        dryRun: If True, don't actually configure

    Returns:
        True if successful, False otherwise
    """
    printSection("Git Configuration", dryRun=dryRun)
    print()

    if not isGitInstalled():
        printError("Git is not installed.")
        printInfo("Please install Git first.")
        print(f"  {installHint}")
        return False

    success = True

    if not configureGitUser(dryRun=dryRun):
        success = False
    print()

    if not configureGitDefaults(configPath, dryRun=dryRun):
        success = False
    print()

    if not configureGitAliases(configPath, dryRun=dryRun):
        success = False
    print()

    if not configureGitLfs(dryRun=dryRun):
        success = False
    print()

    printSection("Configuration Complete")
    if success:
        printSuccess("Git has been configured successfully!")
    else:
        printInfo("Some settings may not have been configured. Please review the output above.")

    return success


__all__ = [
    "isGitInstalled",
    "readJsonSection",
    "setGitConfig",
    "configureGitUser",
    "configureGitDefaults",
    "configureGitAliases",
    "configureGitLfs",
    "configureGit",
]
