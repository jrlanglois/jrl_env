#!/usr/bin/env python3
"""
Format repository: runs Allman brace conversion and whitespace tidying.

Usage:
    python3 formatRepo.py [--dryRun]
"""

import os
import subprocess
import sys
from pathlib import Path

# Import shared logging utilities from common
scriptDir = Path(__file__).parent.absolute()
commonDir = scriptDir.parent / "common"
sys.path.insert(0, str(commonDir.parent))
from common.common import printInfo, printHeading, printSuccess, printError, safePrint, getSubprocessEnv
from common.core.logging import setVerbosityFromArgs, getVerbosity, Verbosity


def printHelp() -> None:
    """Print help information for formatRepo.py."""
    from common.core.logging import printHelpText

    printHelpText(
        title="formatRepo.py",
        intent=[
            "Format the entire repository by running both Allman brace conversion",
            "and whitespace tidying. This is a convenience script that runs:",
            "- convertToAllman.py (converts Bash files to Allman brace style)",
            "- tidy.py (cleans whitespace, enforces line endings for .ps1, .sh, .json, .md, .py, .yml, .yaml, .txt, .rst)",
            "Excludes: .git, __pycache__, node_modules, venv, docs/_build, docs/_static, docs/results",
        ],
        usage="python3 helpers/formatRepo.py [--dryRun]",
        options=[
            ("--help, -h", "Show this help message and exit"),
            ("--dryRun", "Preview changes without modifying files"),
            ("--quiet, -q", "Only show final success/failure message"),
        ],
        examples=[
            "python3 helpers/formatRepo.py",
            "python3 helpers/formatRepo.py --dryRun",
        ],
    )


def main() -> int:
    """Main function to run formatting pipeline."""
    # Check for --help flag
    if "--help" in sys.argv or "-h" in sys.argv:
        printHelp()
        return 0

    # Parse arguments
    dryRun = "--dryRun" in sys.argv or "--dry-run" in sys.argv
    quiet = "--quiet" in sys.argv or "-q" in sys.argv
    setVerbosityFromArgs(quiet=quiet, verbose=False)

    repoRoot = scriptDir.parent

    # Set PAGER to cat to avoid interactive pagers
    os.environ["PAGER"] = "cat"

    # Print title (automatically uses correct heading level)
    printHeading("jrl_env formatRepo.py", dryRun=dryRun)

    success = True

    convertScript = scriptDir / "convertToAllman.py"
    try:
        convertArgs = [sys.executable, str(convertScript), "--subprocess"]
        if dryRun:
            convertArgs.append("--dryRun")
        if quiet:
            convertArgs.append("--quiet")
        result = subprocess.run(
            convertArgs,
            check=False,
            capture_output=quiet,
            env=getSubprocessEnv(),
        )
        if result.returncode != 0:
            success = False
            if not quiet:
                printInfo("convertToAllman.py had issues, continuing...")
    except Exception as e:
        success = False
        if not quiet:
            printInfo(f"Error running convertToAllman.py: {e}")
        else:
            printError(f"Error running convertToAllman.py: {e}")

    if not quiet:
        safePrint()

    tidyScript = scriptDir / "tidy.py"
    try:
        tidyArgs = [sys.executable, str(tidyScript), "--subprocess", "--path", str(repoRoot)]
        if dryRun:
            tidyArgs.append("--dryRun")
        if quiet:
            tidyArgs.append("--quiet")
        result = subprocess.run(
            tidyArgs,
            check=False,
            capture_output=quiet,
            env=getSubprocessEnv(),
        )
        if result.returncode != 0:
            success = False
            if not quiet:
                printInfo("tidy.py had issues, continuing...")
    except Exception as e:
        success = False
        if not quiet:
            printInfo(f"Error running tidy.py: {e}")
        else:
            printError(f"Error running tidy.py: {e}")

    if not quiet:
        safePrint()
        if dryRun:
            printInfo("[DRY RUN] Formatting complete.")
        else:
            printInfo("Formatting complete.")
    else:
        # Final success/failure message (always show in quiet mode)
        if success:
            safePrint("Success")
        else:
            safePrint("Failure")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
