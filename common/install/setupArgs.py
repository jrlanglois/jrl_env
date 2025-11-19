#!/usr/bin/env python3
"""
Shared argument parsing logic for setup scripts.
Provides argument parsing and run flag determination.
"""

import sys
from dataclasses import dataclass
from typing import Optional

# Import logging functions directly from source module
from common.core.logging import printError


@dataclass
class SetupArgs:
    """Setup script arguments."""
    skipFonts: bool = False
    skipApps: bool = False
    skipGit: bool = False
    skipCursor: bool = False
    skipRepos: bool = False
    skipSsh: bool = False
    appsOnly: bool = False
    dryRun: bool = False
    noBackup: bool = False
    quiet: bool = False
    verbose: bool = False
    resume: bool = False
    noResume: bool = False
    listSteps: bool = False


@dataclass
class RunFlags:
    """Determined run flags based on arguments."""
    runFonts: bool = False
    runApps: bool = False
    runGit: bool = False
    runCursor: bool = False
    runRepos: bool = False
    runSsh: bool = False


def parseSetupArgs(args: Optional[list[str]] = None) -> SetupArgs:
    """
    Parse setup script arguments.

    Args:
        args: Command line arguments (defaults to sys.argv[1:])

    Returns:
        SetupArgs object with parsed arguments

    Raises:
        SystemExit: If unknown option is encountered
    """
    if args is None:
        args = sys.argv[1:]

    setupArgs = SetupArgs()

    for arg in args:
        if arg == "--skipFonts":
            setupArgs.skipFonts = True
        elif arg == "--skipApps":
            setupArgs.skipApps = True
        elif arg == "--skipGit":
            setupArgs.skipGit = True
        elif arg == "--skipCursor":
            setupArgs.skipCursor = True
        elif arg == "--skipRepos":
            setupArgs.skipRepos = True
        elif arg == "--skipSsh":
            setupArgs.skipSsh = True
        elif arg == "--appsOnly":
            setupArgs.appsOnly = True
        elif arg == "--dryRun":
            setupArgs.dryRun = True
        elif arg == "--noBackup":
            setupArgs.noBackup = True
        elif arg == "--quiet" or arg == "-q":
            setupArgs.quiet = True
        elif arg == "--verbose":
            setupArgs.verbose = True
        elif arg == "--resume":
            setupArgs.resume = True
        elif arg == "--noResume":
            setupArgs.noResume = True
        elif arg == "--listSteps":
            setupArgs.listSteps = True
        elif arg == "--version" or arg == "-v":
            from common.version import __version__
            print(f"jrl_env version {__version__}")
            sys.exit(0)
        else:
            printError(f"Unknown option: {arg}")
            sys.exit(1)

    # Set verbosity level based on parsed arguments
    from common.core.logging import setVerbosityFromArgs
    setVerbosityFromArgs(quiet=setupArgs.quiet, verbose=setupArgs.verbose)

    return setupArgs


def determineRunFlags(setupArgs: SetupArgs) -> RunFlags:
    """
    Determine what to run based on skip flags and appsOnly.

    Args:
        setupArgs: Parsed setup arguments

    Returns:
        RunFlags object with determined run flags
    """
    runFlags = RunFlags()

    # Fonts: run if not skipped and not apps-only
    runFlags.runFonts = not setupArgs.skipFonts and not setupArgs.appsOnly

    # Apps: run if not skipped OR if apps-only
    runFlags.runApps = not setupArgs.skipApps or setupArgs.appsOnly

    # Git: run if not skipped and not apps-only
    runFlags.runGit = not setupArgs.skipGit and not setupArgs.appsOnly

    # Cursor: run if not skipped and not apps-only
    runFlags.runCursor = not setupArgs.skipCursor and not setupArgs.appsOnly

    # Repos: run if not skipped and not apps-only
    runFlags.runRepos = not setupArgs.skipRepos and not setupArgs.appsOnly

    # SSH: run if not skipped and not apps-only
    runFlags.runSsh = not setupArgs.skipSsh and not setupArgs.appsOnly

    return runFlags


__all__ = [
    "SetupArgs",
    "RunFlags",
    "parseSetupArgs",
    "determineRunFlags",
]
