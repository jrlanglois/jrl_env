#!/usr/bin/env python3
"""
Shared argument parsing logic for setup scripts.
Provides argument parsing and run flag determination.
"""

import sys
from dataclasses import dataclass, field
from typing import List, Optional

# Import logging functions directly from source module
from common.core.logging import printError


@dataclass
class SetupArgs:
    """Setup script arguments."""
    # Installation targets (composable)
    installTargets: List[str] = field(default_factory=list)

    # Update targets (composable)
    updateTargets: List[str] = field(default_factory=list)

    # SSH passphrase mode: 'require' (default), 'no', or None (prompt)
    passphraseMode: Optional[str] = 'require'

    # Other flags
    dryRun: bool = False
    noBackup: bool = False
    quiet: bool = False
    verbose: bool = False
    resume: bool = False
    noResume: bool = False
    listSteps: bool = False
    autoYes: bool = False
    configDir: Optional[str] = None
    noConsoleTimestamps: bool = False
    clearRepoCache: bool = False


@dataclass
class RunFlags:
    """Determined run flags based on arguments."""
    runFonts: bool = False
    runApps: bool = False
    runGit: bool = False
    runCursor: bool = False
    runRepos: bool = False
    runSsh: bool = False
    runUpdate: bool = False


# Valid target names
validInstallTargets = {'all', 'fonts', 'apps', 'git', 'cursor', 'repos', 'ssh'}
validUpdateTargets = {'all', 'apps', 'system'}


def parseTargets(targetString: str, validTargets: set) -> List[str]:
    """
    Parse comma-separated targets.

    Args:
        targetString: Comma-separated target string (e.g., "fonts,apps,git")
        validTargets: Set of valid target names

    Returns:
        List of parsed targets

    Raises:
        ValueError: If invalid target is specified
    """
    if not targetString:
        return ['all']

    targets = [t.strip() for t in targetString.split(',')]

    # Validate all targets
    for target in targets:
        if target not in validTargets:
            valid = ', '.join(sorted(validTargets))
            raise ValueError(f"Invalid target '{target}'. Valid targets: {valid}")

    return targets


def parseSetupArgs(args: Optional[list[str]] = None) -> SetupArgs:
    """
    Parse setup script arguments.

    Args:
        args: Command line arguments (defaults to sys.argv[1:])

    Returns:
        SetupArgs object with parsed arguments

    Raises:
        SystemExit: If unknown option or invalid target is encountered
    """
    if args is None:
        args = sys.argv[1:]

    setupArgs = SetupArgs()
    i = 0

    while i < len(args):
        arg = args[i]

        # Install targets
        if arg == "--install":
            setupArgs.installTargets = ['all']
        elif arg.startswith("--install="):
            targetString = arg.split("=", 1)[1]
            try:
                setupArgs.installTargets = parseTargets(targetString, validInstallTargets)
            except ValueError as e:
                printError(str(e))
                sys.exit(1)

        # Update targets
        elif arg == "--update":
            setupArgs.updateTargets = ['all']
        elif arg.startswith("--update="):
            targetString = arg.split("=", 1)[1]
            try:
                setupArgs.updateTargets = parseTargets(targetString, validUpdateTargets)
            except ValueError as e:
                printError(str(e))
                sys.exit(1)

        # Passphrase mode
        elif arg.startswith("--passphrase="):
            passphraseValue = arg.split("=", 1)[1]
            if passphraseValue not in ('require', 'no'):
                printError("--passphrase must be 'require' or 'no'")
                sys.exit(1)
            setupArgs.passphraseMode = passphraseValue

        # Legacy flags (kept for backward compatibility with warnings)
        elif arg == "--appsOnly":
            printError("WARNING: --appsOnly is deprecated. Use --install=apps instead.")
            setupArgs.installTargets = ['apps']
        elif arg.startswith("--skip"):
            printError(f"WARNING: {arg} is deprecated. Use --install=<targets> to specify what to install.")
            sys.exit(1)
        elif arg == "--requirePassphrase":
            printError("WARNING: --requirePassphrase is deprecated. Use --passphrase=require instead.")
            setupArgs.passphraseMode = 'require'
        elif arg == "--noPassphrase":
            printError("WARNING: --noPassphrase is deprecated. Use --passphrase=no instead.")
            setupArgs.passphraseMode = 'no'

        # Other flags
        elif arg == "--dryRun":
            setupArgs.dryRun = True
        elif arg in ("--yes", "-y"):
            setupArgs.autoYes = True
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
        elif arg == "--noTimestamps":
            setupArgs.noConsoleTimestamps = True
        elif arg == "--clearRepoCache":
            setupArgs.clearRepoCache = True
        elif arg.startswith("--configDir="):
            setupArgs.configDir = arg.split("=", 1)[1]
        elif arg == "--configDir":
            if i + 1 < len(args):
                setupArgs.configDir = args[i + 1]
                i += 1
            else:
                printError("--configDir requires a directory path")
                sys.exit(1)
        elif arg == "--version" or arg == "-v":
            from common.version import __version__
            from common.core.logging import safePrint
            safePrint(f"jrl_env version {__version__}")
            sys.exit(0)
        else:
            printError(f"Unknown option: {arg}")
            sys.exit(1)

        i += 1

    # If no targets specified, default to full installation
    if not setupArgs.installTargets and not setupArgs.updateTargets:
        setupArgs.installTargets = ['all']

    # Set verbosity level based on parsed arguments
    from common.core.logging import setVerbosityFromArgs, setShowConsoleTimestamps
    setVerbosityFromArgs(quiet=setupArgs.quiet, verbose=setupArgs.verbose)

    # Set console timestamp display
    if setupArgs.noConsoleTimestamps:
        setShowConsoleTimestamps(False)

    return setupArgs


def determineRunFlags(setupArgs: SetupArgs) -> RunFlags:
    """
    Determine what to run based on install/update targets.

    Args:
        setupArgs: Parsed setup arguments

    Returns:
        RunFlags object with determined run flags
    """
    runFlags = RunFlags()

    # If update targets specified, only run updates
    if setupArgs.updateTargets:
        runFlags.runUpdate = True
        return runFlags

    # Otherwise, process install targets
    installTargets = setupArgs.installTargets

    if 'all' in installTargets:
        # Install everything
        runFlags.runFonts = True
        runFlags.runApps = True
        runFlags.runGit = True
        runFlags.runCursor = True
        runFlags.runRepos = True
        runFlags.runSsh = True
    else:
        # Install only specified targets
        runFlags.runFonts = 'fonts' in installTargets
        runFlags.runApps = 'apps' in installTargets
        runFlags.runGit = 'git' in installTargets
        runFlags.runCursor = 'cursor' in installTargets
        runFlags.runRepos = 'repos' in installTargets
        runFlags.runSsh = 'ssh' in installTargets

    return runFlags


__all__ = [
    "SetupArgs",
    "RunFlags",
    "parseSetupArgs",
    "determineRunFlags",
    "validInstallTargets",
    "validUpdateTargets",
]
