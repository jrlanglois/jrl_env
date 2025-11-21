#!/usr/bin/env python3
"""
Shared application installation logic.
Provides package installation, configuration command execution, and Linux common package merging.
"""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, List, Optional

# Import common utilities directly from source modules
from common.core.logging import (
    printError,
    printInfo,
    printLock,
    printH2,
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


@dataclass
class InstallResult:
    """Result of package installation operation."""
    installedCount: int = 0
    updatedCount: int = 0
    failedCount: int = 0
    installedPackages: List[str] = None
    updatedPackages: List[str] = None

    def __post_init__(self):
        if self.installedPackages is None:
            self.installedPackages = []
        if self.updatedPackages is None:
            self.updatedPackages = []


def installPackages(
    packageList: List[str],
    checkFunction: Callable[[str], bool],
    installFunction: Callable[[str], bool],
    updateFunction: Callable[[str], bool],
    label: str,
    dryRun: bool = False,
) -> InstallResult:
    """Install packages from a list in parallel."""
    result = InstallResult()

    if not packageList:
        return result

    printH2(f"Processing {label}", dryRun=dryRun)
    safePrint()

    # Filter out empty packages
    validPackages = [p.strip() for p in packageList if p and p.strip()]
    totalPackages = len(validPackages)

    if dryRun:
        printInfo("[DRY RUN] Would process the following packages:")
        for idx, packageName in enumerate(validPackages, 1):
            printInfo(f"[{idx}/{totalPackages}] {packageName}")
        result.installedCount = totalPackages
        return result

    # Process packages in parallel
    maxWorkers = min(8, totalPackages)  # Limit concurrent installations to avoid overwhelming the system
    printInfo(f"Processing {totalPackages} package(s) in parallel (max {maxWorkers} workers)...")
    safePrint()

    def processPackage(packageName: str) -> tuple[str, str, bool]:
        """Process a single package (check, install, or update). Returns (packageName, action, success)."""
        if checkFunction(packageName):
            if updateFunction(packageName):
                return (packageName, "updated", True)
            else:
                return (packageName, "updated", True)  # Update check completed
        else:
            if installFunction(packageName):
                return (packageName, "installed", True)
            else:
                return (packageName, "failed", False)

    def printPackageResult(pkgName: str, action: str, completedCount: int) -> None:
        """Helper to print package installation result."""
        if action == "installed":
            printSuccess(f"Installing package {completedCount}/{totalPackages}: ✓ {pkgName} (installed)")
            result.installedCount += 1
            result.installedPackages.append(pkgName)
        elif action == "updated":
            printWarning(f"Installing package {completedCount}/{totalPackages}: ↻ {pkgName} (updated)")
            result.updatedCount += 1
            result.updatedPackages.append(pkgName)
        else:  # failed
            printError(f"Installing package {completedCount}/{totalPackages}: ✗ {pkgName} (failed)")
            result.failedCount += 1

    completedCount = 0
    with ThreadPoolExecutor(max_workers=maxWorkers) as executor:
        futures = {
            executor.submit(processPackage, packageName): packageName
            for packageName in validPackages
        }

        for future in as_completed(futures):
            packageName = futures[future]
            completedCount += 1
            try:
                pkgName, action, success = future.result()
                if printLock:
                    with printLock:
                        printPackageResult(pkgName, action, completedCount)
                else:
                    printPackageResult(pkgName, action, completedCount)
            except Exception as e:
                # Note: completedCount already incremented above, don't double-count
                if printLock:
                    with printLock:
                        printError(f"Installing package {completedCount}/{totalPackages}: ✗ {packageName} (exception: {e})")
                        result.failedCount += 1
                else:
                    printError(f"Installing package {completedCount}/{totalPackages}: ✗ {packageName} (exception: {e})")
                    result.failedCount += 1

    safePrint()
    return result


def mergeJsonArrays(configPath: str, array1Path: str, array2Path: str) -> List[str]:
    """Merge two JSON arrays from a config file and deduplicate."""
    array1 = getJsonArray(configPath, array1Path)
    array2 = getJsonArray(configPath, array2Path)

    # Merge and deduplicate
    merged = list(set(array1 + array2))
    return sorted(merged)


def installFromConfig(
    configPath: str,
    packageExtractor: str,
    packageLabel: str,
    checkFunction: Callable[[str], bool],
    installFunction: Callable[[str], bool],
    updateFunction: Callable[[str], bool],
    dryRun: bool = False,
) -> InstallResult:
    """Install packages from a JSON config file."""
    packages = getJsonArray(configPath, packageExtractor)
    return installPackages(
        packages,
        checkFunction,
        installFunction,
        updateFunction,
        packageLabel,
        dryRun=dryRun,
    )


def installFromConfigWithLinuxCommon(
    configPath: str,
    commonPath: str,
    distroPath: str,
    packageLabel: str,
    checkFunction: Callable[[str], bool],
    installFunction: Callable[[str], bool],
    updateFunction: Callable[[str], bool],
    dryRun: bool = False,
) -> InstallResult:
    """Install packages from config with Linux common packages merged."""
    # Get common config path (assume it's in the same directory as distro config)
    configFile = Path(configPath)
    commonConfigPath = configFile.parent / "linuxCommon.json"

    if commonConfigPath.exists():
        # Merge packages from both files
        commonPackages = getJsonArray(str(commonConfigPath), commonPath)
        distroPackages = getJsonArray(configPath, distroPath)
        # Combine and deduplicate
        packages = list(set(commonPackages + distroPackages))
        packages = sorted(packages)
    else:
        packages = getJsonArray(configPath, distroPath)

    return installPackages(
        packages,
        checkFunction,
        installFunction,
        updateFunction,
        packageLabel,
        dryRun=dryRun,
    )


@dataclass
class CommandConfig:
    """Configuration for a command to execute."""
    name: str
    shell: str = "bash"
    command: str = ""
    runOnce: bool = False


def parseCommandJson(cmdJson: dict) -> CommandConfig:
    """Parse a command JSON object into a CommandConfig."""
    return CommandConfig(
        name=cmdJson.get("name", "command"),
        shell=cmdJson.get("shell", "bash"),
        command=cmdJson.get("command", ""),
        runOnce=cmdJson.get("runOnce", False),
    )


def getCommandFlagFile(phase: str, name: str) -> Path:
    """Get the flag file path for a run-once command."""
    import os
    cacheDir = Path.home() / ".cache" / "jrl_env" / "commands"
    cacheDir.mkdir(parents=True, exist_ok=True)

    # Sanitise name for filename (en-ca spelling)
    safeName = "".join(c if c.isalnum() or c == "_" else "_" for c in f"{phase}_{name}")
    return cacheDir / f"{safeName}.flag"


def isCommandAlreadyRun(flagFile: Path) -> bool:
    """
    Check if a run-once command has already been executed.

    Args:
        flagFile: Path to flag file

    Returns:
        True if command has been run, False otherwise
    """
    return flagFile.exists()


def markCommandAsRun(flagFile: Path) -> None:
    """Mark a run-once command as executed."""
    flagFile.touch()


def executeConfigCommand(phase: str, cmdJson: dict, configPath: Optional[str] = None, dryRun: bool = False) -> bool:
    """Execute a single command from the config."""
    if not cmdJson:
        return True

    cmdConfig = parseCommandJson(cmdJson)

    if not cmdConfig.command or cmdConfig.command == "null":
        return True

    if dryRun:
        printInfo(f"[DRY RUN] Would run {cmdConfig.name}: {cmdConfig.command}")
        return True

    flagFile = getCommandFlagFile(phase, cmdConfig.name)

    if cmdConfig.runOnce and isCommandAlreadyRun(flagFile):
        printWarning(f"Skipping {cmdConfig.name} (run once already executed).")
        return True

    if not commandExists(cmdConfig.shell):
        printError(f"Command shell '{cmdConfig.shell}' not available for {cmdConfig.name}.")
        return False

    printInfo(f"Running {cmdConfig.name}...")
    try:
        result = subprocess.run(
            [cmdConfig.shell, "-lc", cmdConfig.command],
            check=False,
            capture_output=True,
        )

        if result.returncode == 0:
            printSuccess(f"{cmdConfig.name} completed")
            if cmdConfig.runOnce:
                markCommandAsRun(flagFile)
            return True
        else:
            printError(f"{cmdConfig.name} failed")
            if result.stderr:
                printError(f"Error: {result.stderr.decode('utf-8', errors='ignore')}")
            return False
    except Exception as e:
        printError(f"{cmdConfig.name} failed: {e}")
        return False


def runConfigCommands(phase: str, configPath: str, dryRun: bool = False) -> None:
    """Run commands from a specific phase (preInstall/postInstall)."""
    configFile = Path(configPath)

    if not configFile.exists():
        return

    # Get commands array
    commands = getJsonValue(configPath, f".commands.{phase}", [])

    if not commands or not isinstance(commands, list):
        return

    for cmdJson in commands:
        if isinstance(cmdJson, dict):
            executeConfigCommand(phase, cmdJson, configPath, dryRun)


def installApps(
    configPath: str,
    primaryExtractor: str = ".brew[]?",
    secondaryExtractor: str = ".brewCask[]?",
    primaryLabel: str = "Primary packages",
    secondaryLabel: str = "Secondary packages",
    checkPrimary: Optional[Callable[[str], bool]] = None,
    installPrimary: Optional[Callable[[str], bool]] = None,
    updatePrimary: Optional[Callable[[str], bool]] = None,
    checkSecondary: Optional[Callable[[str], bool]] = None,
    installSecondary: Optional[Callable[[str], bool]] = None,
    updateSecondary: Optional[Callable[[str], bool]] = None,
    dryRun: bool = False,
) -> InstallResult:
    """Install applications from a config file (primary and optional secondary package managers)."""
    configFile = Path(configPath)

    if not configFile.exists():
        printError(f"Configuration file not found: {configPath}")
        return InstallResult()

    printH2("Application Installation", dryRun=dryRun)
    safePrint()

    totalResult = InstallResult()

    # Install primary packages
    if checkPrimary and installPrimary and updatePrimary:
        result = installFromConfig(
            configPath,
            primaryExtractor,
            primaryLabel,
            checkPrimary,
            installPrimary,
            updatePrimary,
            dryRun=dryRun,
        )
        totalResult.installedCount += result.installedCount
        totalResult.updatedCount += result.updatedCount
        totalResult.failedCount += result.failedCount

    # Install secondary packages
    if checkSecondary and installSecondary and updateSecondary:
        result = installFromConfig(
            configPath,
            secondaryExtractor,
            secondaryLabel,
            checkSecondary,
            installSecondary,
            updateSecondary,
            dryRun=dryRun,
        )
        totalResult.installedCount += result.installedCount
        totalResult.updatedCount += result.updatedCount
        totalResult.failedCount += result.failedCount

    printInfo("Summary:")
    if dryRun:
        printInfo(f"Would install: {totalResult.installedCount}")
    else:
        if totalResult.installedCount > 0:
            printSuccess(f"Installed: {totalResult.installedCount}")
        if totalResult.updatedCount > 0:
            printWarning(f"Updated: {totalResult.updatedCount}")
        if totalResult.failedCount > 0:
            printError(f"Failed: {totalResult.failedCount}")

    return totalResult


__all__ = [
    "InstallResult",
    "CommandConfig",
    "installPackages",
    "mergeJsonArrays",
    "installFromConfig",
    "installFromConfigWithLinuxCommon",
    "parseCommandJson",
    "getCommandFlagFile",
    "isCommandAlreadyRun",
    "markCommandAsRun",
    "executeConfigCommand",
    "runConfigCommands",
    "installApps",
]
