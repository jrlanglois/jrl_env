#!/usr/bin/env python3
"""
Unified update script for all platforms.
Pulls latest changes and re-runs setup.

Usage:
    python3 -m common.systems.update [--dryRun] [other setup args...]
"""

import subprocess
import sys
from pathlib import Path

# Add project root to path
scriptDir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(scriptDir))

from common.common import (
    commandExists,
    findOperatingSystem,
    isOperatingSystem,
    printError,
    printInfo,
    printH2,
    printWarning,
    safePrint,
)


def detectPlatform() -> str:
    """
    Detect the operating system and return the platform name.

    Returns:
        Platform name (e.g., "ubuntu", "macos", "win11")
    """
    osType = findOperatingSystem()

    if isOperatingSystem("macos"):
        return "macos"
    elif isOperatingSystem("linux"):
        osRelease = Path("/etc/os-release")
        if osRelease.exists():
            try:
                distroId = None
                distroIdLike = None
                with open(osRelease, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith("ID="):
                            distroId = line.split('=', 1)[1].strip().strip('"').strip("'")
                        elif line.startswith("ID_LIKE="):
                            distroIdLike = line.split('=', 1)[1].strip().strip('"').strip("'")

                if distroId:
                    if distroId in ("ubuntu", "debian"):
                        return "ubuntu"
                    elif distroId == "raspbian":
                        return "raspberrypi"
                    elif distroId in ("rhel", "fedora", "centos"):
                        return "redhat"
                    elif distroId in ("opensuse-tumbleweed", "opensuse-leap", "sles"):
                        return "opensuse"
                    elif distroId == "arch":
                        return "archlinux"

                if distroIdLike:
                    if "debian" in distroIdLike or "ubuntu" in distroIdLike:
                        return "ubuntu"
                    elif "fedora" in distroIdLike or "rhel" in distroIdLike:
                        return "redhat"
            except Exception:
                pass
        return "ubuntu"
    elif isOperatingSystem("windows"):
        return "win11"
    else:
        return "unknown"


def main() -> int:
    """Main update function."""
    dryRun = "--dryRun" in sys.argv or "--dry-run" in sys.argv

    from common.core.logging import printH1
    printH1("jrl_env Update", dryRun=dryRun)

    # Check if we're in a git repository
    gitDir = scriptDir / ".git"
    if not gitDir.exists():
        printError("Not a git repository. Please clone the repository first.")
        return 1

    # Check if git is available
    if not commandExists("git"):
        printError("git is not available. Please install Git first.")
        return 1

    if dryRun:
        printInfo("[DRY RUN] Would pull latest changes from git...")
    else:
        printInfo("Pulling latest changes...")
        try:
            result = subprocess.run(
                ["git", "pull"],
                cwd=scriptDir,
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                printWarning("Git pull had issues. Continuing anyway...")
                if result.stderr:
                    printWarning(result.stderr)
        except Exception as e:
            printWarning(f"Failed to pull latest changes: {e}")
            printInfo("Continuing with current version...")

    safePrint()
    if dryRun:
        printInfo("[DRY RUN] Would re-run setup...")
    else:
        printInfo("Re-running setup...")
    safePrint()

    # Detect platform and run setup
    platformName = detectPlatform()
    if platformName == "unknown":
        printError("Unable to detect platform. Please run setup.py directly.")
        return 1

    # Use the unified setup.py entry point
    setupScript = scriptDir / "setup.py"
    if not setupScript.exists():
        printError("Setup script not found.")
        return 1

    try:
        setupArgs = [sys.executable, str(setupScript)]
        if dryRun:
            setupArgs.append("--dryRun")
        # Pass through any other arguments (excluding dryRun flags we already handled)
        for arg in sys.argv[1:]:
            if arg not in ("--dryRun", "--dry-run") and arg not in setupArgs:
                setupArgs.append(arg)

        result = subprocess.run(
            setupArgs,
            check=False,
        )
        return result.returncode
    except Exception as e:
        printError(f"Failed to run setup: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
