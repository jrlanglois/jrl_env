#!/usr/bin/env python3
"""
Shared logging utilities for consistent output formatting across Python scripts
"""

import shutil
import sys
import os
from datetime import datetime
from enum import IntEnum
from threading import Lock
from typing import Optional, Union

from common.systems.platform import isWindows

# ANSI colour codes
class Colours:
    red = '\033[0;31m'
    green = '\033[0;32m'
    yellow = '\033[1;33m'
    cyan = '\033[0;36m'
    nc = '\033[0m'  # No Colour

# Verbosity levels
class Verbosity(IntEnum):
    """Verbosity levels for logging."""
    quiet = 0    # Only errors
    normal = 1   # Errors, warnings, success, info (default)
    verbose = 2  # Everything including debug/verbose messages

# Global verbosity level (default to normal)
currentVerbosity: Verbosity = Verbosity.normal

# Global timestamp display toggle (default to show timestamps)
# Logs ALWAYS have timestamps - this only controls console display
showConsoleTimestamps: bool = True

# Global heading depth for hierarchical output
# 0 = H1 (top-level), 1 = H2 (subprocess), 2 = H3 (nested subprocess), etc.
headingDepth: int = 0

# Thread-safe print lock (for scripts that use threading)
printLock = Lock()

# Detect if console supports Unicode emojis
def supportsUnicode() -> bool:
    """Check if the console supports Unicode emoji characters."""
    # On Windows, be conservative - only use Unicode if we can confirm UTF-8 support
    if isWindows():
        try:
            # Try to reconfigure stdout to UTF-8 if possible (Python 3.7+)
            if hasattr(sys.stdout, 'reconfigure'):
                try:
                    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
                except (ValueError, LookupError, OSError):
                    # Reconfiguration failed, fall back to ASCII
                    return False
            # Test if we can actually encode and print a Unicode emoji
            currentEncoding = getattr(sys.stdout, 'encoding', None) or 'utf-8'
            if currentEncoding.lower() in ('cp1252', 'windows-1252', 'ascii'):
                return False
            testEmoji = "✓"
            testEmoji.encode(currentEncoding)
            # Also test that we can actually print it (some consoles claim UTF-8 but don't support it)
            try:
                # Use a test print to verify
                testStr = testEmoji
                testStr.encode(currentEncoding)
                return True
            except (UnicodeEncodeError, UnicodeError):
                return False
        except (UnicodeEncodeError, AttributeError, LookupError, TypeError):
            # If encoding fails, fall back to ASCII
            return False
    # On Unix-like systems, assume UTF-8 support
    return True

# Cache the Unicode support check (do this after potential stdout reconfiguration)
unicodeSupported = supportsUnicode()

# ASCII fallbacks for emojis (use ASCII if Unicode not supported)
emojiError = "✗" if unicodeSupported else "[ERROR]"
emojiSuccess = "✓" if unicodeSupported else "[SUCCESS]"
emojiWarning = "⚠" if unicodeSupported else "[WARNING]"


def setVerbosity(level: Verbosity) -> None:
    """Set the global verbosity level."""
    global currentVerbosity
    currentVerbosity = level


def getVerbosity() -> Verbosity:
    """Get the current verbosity level."""
    return currentVerbosity


def setVerbosityFromArgs(quiet: bool = False, verbose: bool = False) -> None:
    """Set verbosity level from command-line arguments. --quiet takes precedence over --verbose."""
    if quiet:
        setVerbosity(Verbosity.quiet)
    elif verbose:
        setVerbosity(Verbosity.verbose)
    else:
        setVerbosity(Verbosity.normal)


def setShowConsoleTimestamps(show: bool) -> None:
    """
    Set whether to show timestamps in console output.
    Note: Log files ALWAYS contain timestamps regardless of this setting.

    Args:
        show: If True, show timestamps in console output. If False, hide them.
    """
    global showConsoleTimestamps
    showConsoleTimestamps = show


def getShowConsoleTimestamps() -> bool:
    """Get whether timestamps are shown in console output."""
    return showConsoleTimestamps


def setHeadingDepth(depth: int) -> None:
    """
    Set the current heading depth for hierarchical output.

    Args:
        depth: Heading depth (0=H1, 1=H2, 2=H3, etc.)
    """
    global headingDepth
    headingDepth = max(0, min(depth, 3))  # Clamp between 0-3


def getHeadingDepth() -> int:
    """
    Get the current heading depth.
    Checks JRL_ENV_HEADING_DEPTH environment variable first, then global.
    """
    import os
    envDepth = os.environ.get('JRL_ENV_HEADING_DEPTH')
    if envDepth is not None:
        try:
            return max(0, min(int(envDepth), 3))
        except (ValueError, TypeError):
            pass
    return headingDepth


def incrementHeadingDepth() -> None:
    """Increment heading depth (for subprocess calls)."""
    global headingDepth
    headingDepth = min(headingDepth + 1, 3)  # Max depth of 3


def decrementHeadingDepth() -> None:
    """Decrement heading depth (after subprocess returns)."""
    global headingDepth
    headingDepth = max(headingDepth - 1, 0)  # Min depth of 0


def getSubprocessEnv() -> dict:
    """
    Get environment dict for subprocess with incremented heading depth.

    Returns:
        Environment dict with JRL_ENV_HEADING_DEPTH set
    """
    import os
    env = os.environ.copy()
    currentDepth = getHeadingDepth()
    env['JRL_ENV_HEADING_DEPTH'] = str(currentDepth + 1)
    return env

def safePrint(*args, end: str = '\n', flush: bool = True, **kwargs):
    """
    Thread-safe print function with automatic timestamp handling.
    This is the ONLY function that calls Python's print() - all other functions use this.

    Timestamp behaviour:
    - If showConsoleTimestamps is True, prepends timestamp to each line
    - If False, prints without timestamps
    - Handles multiline strings by timestamping each line
    - Blank lines get just the timestamp

    Args:
        *args: Arguments to print
        end: String appended after the last value (default: '\\n')
        flush: Whether to forcibly flush the stream (default: True)
        **kwargs: Additional keyword arguments passed to print()
    """
    with printLock:
        # Handle blank lines
        if len(args) == 0:
            if showConsoleTimestamps:
                args = (f"[{getTimestamp()}]",)
            try:
                print(*args, end=end, flush=flush, **kwargs)
            except Exception:
                pass
            return

        # Handle timestamped output
        if showConsoleTimestamps:
            timestamp = getTimestamp()
            outputArgs = []
            for arg in args:
                argStr = str(arg)
                # Split by newlines and timestamp each line
                lines = argStr.split('\n')
                timestampedLines = [f"[{timestamp}] {line}" for line in lines]
                outputArgs.append('\n'.join(timestampedLines))

            try:
                print(*outputArgs, end=end, flush=flush, **kwargs)
            except (UnicodeEncodeError, UnicodeError):
                # Fallback: encode to ASCII
                encodedArgs = []
                for arg in outputArgs:
                    encodedArgs.append(arg.encode('ascii', errors='replace').decode('ascii'))
                try:
                    print(*encodedArgs, end=end, flush=flush, **kwargs)
                except Exception:
                    print(*[str(arg).encode('ascii', errors='replace').decode('ascii') for arg in outputArgs], end=end, flush=flush, **kwargs)
        else:
            # Without timestamps, print as-is
            try:
                print(*args, end=end, flush=flush, **kwargs)
            except (UnicodeEncodeError, UnicodeError):
                # Fallback: encode to ASCII
                encodedArgs = []
                for arg in args:
                    if isinstance(arg, str):
                        encodedArgs.append(arg.encode('ascii', errors='replace').decode('ascii'))
                    else:
                        encodedArgs.append(str(arg).encode('ascii', errors='replace').decode('ascii'))
                try:
                    print(*encodedArgs, end=end, flush=flush, **kwargs)
                except Exception:
                    print(*[str(arg).encode('ascii', errors='replace').decode('ascii') for arg in args], end=end, flush=flush, **kwargs)


def getTimestamp() -> str:
    """Get current timestamp in ISO8601 format (e.g., "2024-01-15T14:30:45")."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def printFormatted(
    message: str,
    colour: str = Colours.nc,
    emoji: str = "",
    minVerbosity: Verbosity = Verbosity.normal,
    alwaysShow: bool = False,
) -> None:
    """
    Common formatted printing function.
    Adds emoji and colour, then delegates to safePrint() for timestamp handling.

    Args:
        message: Message to print (can contain \\n for multiple lines)
        colour: ANSI colour code
        emoji: Emoji/symbol to prepend (✓, ✗, ⚠, etc.)
        minVerbosity: Minimum verbosity level required to show this message
        alwaysShow: If True, show even in quiet mode (for errors)
    """
    # Check verbosity
    if not alwaysShow and currentVerbosity < minVerbosity:
        return

    # Prepend emoji if provided and not already in message
    if emoji and emoji not in message:
        # Check for both Unicode and ASCII versions
        emojiVariants = [emojiError, emojiSuccess, emojiWarning, "✗", "✓", "⚠", "[ERROR]", "[SUCCESS]", "[WARNING]"]
        hasEmoji = any(variant in message for variant in emojiVariants)
        if not hasEmoji:
            message = f"{emoji} {message.lstrip()}"

    # Apply colour and delegate to safePrint() for timestamp handling
    safePrint(f"{colour}{message}{Colours.nc}")


def printInfo(message: str) -> None:
    """Print an info message in cyan with timestamp. Only shown at normal or verbose verbosity."""
    printFormatted(message, colour=Colours.cyan, minVerbosity=Verbosity.normal)


def printWarning(message: str) -> None:
    """Print a warning message in yellow with ⚠ emoji and timestamp. Only shown at normal or verbose verbosity."""
    printFormatted(message, colour=Colours.yellow, emoji=emojiWarning, minVerbosity=Verbosity.normal)


def printError(message: str) -> None:
    """Print an error message in red with ✗ emoji and timestamp. Always shown (even in quiet mode)."""
    printFormatted(message, colour=Colours.red, emoji=emojiError, minVerbosity=Verbosity.normal, alwaysShow=True)


def printSuccess(message: str) -> None:
    """Print a success message in green with ✓ emoji and timestamp. Only shown at normal or verbose verbosity."""
    printFormatted(message, colour=Colours.green, emoji=emojiSuccess, minVerbosity=Verbosity.normal)


def printVerbose(message: str) -> None:
    """Print a verbose/debug message in cyan with timestamp. Only shown at verbose verbosity."""
    printFormatted(f"[VERBOSE] {message}", colour=Colours.cyan, minVerbosity=Verbosity.verbose)


def printDebug(message: str) -> None:
    """Print a debug message (alias for printVerbose) with timestamp. Only shown at verbose verbosity."""
    printVerbose(message)


def printH1(message: str, dryRun: bool = False) -> None:
    """Print a top-level heading (H1) with borders, centred text, and extra spacing."""
    if currentVerbosity >= Verbosity.normal:
        if dryRun:
            message = f"{message} (DRY RUN)"

        # Get terminal width with multiple fallbacks
        terminalWidth = 80  # Default fallback
        
        # Try tput first (most reliable for actual terminal)
        try:
            import subprocess
            result = subprocess.run(['tput', 'cols'], capture_output=True, text=True, check=False, timeout=0.5)
            if result.returncode == 0:
                detectedWidth = int(result.stdout.strip())
                if detectedWidth > 0:
                    terminalWidth = detectedWidth
        except Exception:
            # Fall back to shutil
            try:
                size = shutil.get_terminal_size()
                if size.columns > 0:
                    terminalWidth = size.columns
            except (AttributeError, ValueError, OSError):
                pass
        
        # Account for timestamp width if timestamps are enabled
        # Timestamp format: "[YYYY-MM-DDTHH:MM:SS] " = 21 characters
        # Add 1 char safety margin for ANSI codes
        timestampWidth = 21 if showConsoleTimestamps else 0
        safetyMargin = 1
        availableWidth = max(40, terminalWidth - timestampWidth - safetyMargin)

        # Calculate centring
        padding = (availableWidth - len(message)) // 2
        centredMessage = " " * max(0, padding) + message

        safePrint()
        safePrint(f"{Colours.cyan}{'=' * availableWidth}{Colours.nc}")
        safePrint(f"{Colours.cyan}{centredMessage}{Colours.nc}")
        safePrint(f"{Colours.cyan}{'=' * availableWidth}{Colours.nc}")
        safePrint()


def printH2(message: str, dryRun: bool = False) -> None:
    """Print a second-level heading (H2) with === borders."""
    if currentVerbosity >= Verbosity.normal:
        if dryRun:
            message = f"{message} (DRY RUN)"
        safePrint(f"{Colours.cyan}=== {message} ==={Colours.nc}")


def printH3(message: str, dryRun: bool = False) -> None:
    """Print a third-level heading (H3) with --- style."""
    if currentVerbosity >= Verbosity.normal:
        if dryRun:
            message = f"{message} (DRY RUN)"
        safePrint(f"{Colours.cyan}--- {message}{Colours.nc}")


def printHeading(message: str, dryRun: bool = False) -> None:
    """
    Print a heading at the current depth level.
    Uses global headingDepth to determine H1/H2/H3 automatically.

    Args:
        message: Heading message
        dryRun: If True, append (DRY RUN) to message
    """
    depth = getHeadingDepth()
    if depth == 0:
        printH1(message, dryRun=dryRun)
    elif depth == 1:
        printH2(message, dryRun=dryRun)
    else:
        printH3(message, dryRun=dryRun)



def printHelpText(
    title: str,
    intent: Union[str, list[str]],
    usage: Union[str, list[str]],
    options: Optional[list[tuple[str, str]]] = None,
    examples: Optional[list[str]] = None,
    sections: Optional[dict[str, list[str]]] = None,
) -> None:
    """Print formatted help text following a consistent pattern."""
    # Prepend "jrl_env " to title if not already present
    if not title.startswith("jrl_env "):
        title = f"jrl_env {title}"

    safePrint(title)
    safePrint("")

    # Intent section
    safePrint("Intent:")
    if isinstance(intent, str):
        safePrint(f"{intent}")
    else:
        for line in intent:
            safePrint(f"{line}")
    safePrint("")

    # Usage section
    safePrint("Usage:")
    if isinstance(usage, str):
        safePrint(f"{usage}")
    else:
        for line in usage:
            safePrint(f"{line}")
    safePrint("")

    # Additional sections (Platforms, Operations, etc.)
    if sections:
        for sectionName, items in sections.items():
            safePrint(f"{sectionName}:")
            for item in items:
                safePrint(f"{item}")
            safePrint("")

    # Options section
    if options:
        safePrint("Options:")
        for option, description in options:
            safePrint(f"{option:<20} {description}")
        safePrint("")

    # Examples section
    if examples:
        safePrint("Examples:")
        for example in examples:
            safePrint(f"{example}")


def colourise(text, code, enable=None):
    """Apply colour to text if enabled (defaults to checking if stdout is a TTY)."""
    if enable is None:
        enable = sys.stdout.isatty()
    if not enable:
        return text
    return f"{code}{text}{Colours.nc}"
