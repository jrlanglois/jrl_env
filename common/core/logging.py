#!/usr/bin/env python3
"""
Shared logging utilities for consistent output formatting across Python scripts
"""

import sys
import os
from datetime import datetime
from enum import IntEnum
from threading import Lock
from typing import Optional, Union

# ANSI colour codes
class Colours:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Colour

# Verbosity levels
class Verbosity(IntEnum):
    """Verbosity levels for logging."""
    quiet = 0    # Only errors
    normal = 1   # Errors, warnings, success, info (default)
    verbose = 2  # Everything including debug/verbose messages

# Global verbosity level (default to normal)
_verbosity: Verbosity = Verbosity.normal

# Thread-safe print lock (for scripts that use threading)
printLock = Lock()

# Detect if console supports Unicode emojis
def supportsUnicode() -> bool:
    """Check if the console supports Unicode emoji characters."""
    # On Windows, be conservative - only use Unicode if we can confirm UTF-8 support
    if sys.platform == "win32":
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
    global _verbosity
    _verbosity = level


def getVerbosity() -> Verbosity:
    """Get the current verbosity level."""
    return _verbosity


def setVerbosityFromArgs(quiet: bool = False, verbose: bool = False) -> None:
    """Set verbosity level from command-line arguments. --quiet takes precedence over --verbose."""
    if quiet:
        setVerbosity(Verbosity.quiet)
    elif verbose:
        setVerbosity(Verbosity.verbose)
    else:
        setVerbosity(Verbosity.normal)

def safePrint(*args, **kwargs):
    """Thread-safe print function with encoding error handling."""
    with printLock:
        try:
            print(*args, **kwargs, flush=True)
        except (UnicodeEncodeError, UnicodeError):
            # Fallback: encode to ASCII with error replacement
            encodedArgs = []
            for arg in args:
                if isinstance(arg, str):
                    # Replace Unicode characters that can't be encoded
                    encodedArgs.append(arg.encode('ascii', errors='replace').decode('ascii'))
                else:
                    encodedArgs.append(str(arg).encode('ascii', errors='replace').decode('ascii'))
            try:
                print(*encodedArgs, **kwargs, flush=True)
            except Exception:
                # Last resort: print without any formatting
                print(*[str(arg).encode('ascii', errors='replace').decode('ascii') for arg in args], **kwargs, flush=True)


def getTimestamp() -> str:
    """Get current timestamp in ISO8601 format (e.g., "2024-01-15T14:30:45")."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def formatWithTimestamp(message: str) -> str:
    """Format a message with a timestamp prefix."""
    return f"[{getTimestamp()}] {message}"

def printInfo(message: str, includeTimestamp: bool = True) -> None:
    """Print an info message in cyan. Only shown at normal or verbose verbosity."""
    if _verbosity >= Verbosity.normal:
        formatted = formatWithTimestamp(message) if includeTimestamp else message
        safePrint(f"{Colours.CYAN}{formatted}{Colours.NC}")

def printWarning(message: str, includeTimestamp: bool = True) -> None:
    """Print a warning message in yellow with ⚠ emoji. Only shown at normal or verbose verbosity."""
    if _verbosity >= Verbosity.normal:
        # Prepend emoji if not already present anywhere in the message
        if emojiWarning not in message and "⚠" not in message and "[WARNING]" not in message:
            message = f"{emojiWarning} {message.lstrip()}"
        formatted = formatWithTimestamp(message) if includeTimestamp else message
        safePrint(f"{Colours.YELLOW}{formatted}{Colours.NC}")

def printError(message: str, includeTimestamp: bool = True) -> None:
    """Print an error message in red with ✗ emoji. Always shown (even in quiet mode)."""
    # Prepend emoji if not already present anywhere in the message
    if emojiError not in message and "✗" not in message and "[ERROR]" not in message:
        message = f"{emojiError} {message.lstrip()}"
    formatted = formatWithTimestamp(message) if includeTimestamp else message
    safePrint(f"{Colours.RED}{formatted}{Colours.NC}")

def printSuccess(message: str, includeTimestamp: bool = True) -> None:
    """Print a success message in green with ✓ emoji. Only shown at normal or verbose verbosity."""
    if _verbosity >= Verbosity.normal:
        # Prepend emoji if not already present anywhere in the message
        if emojiSuccess not in message and "✓" not in message and "[SUCCESS]" not in message:
            message = f"{emojiSuccess} {message.lstrip()}"
        formatted = formatWithTimestamp(message) if includeTimestamp else message
        safePrint(f"{Colours.GREEN}{formatted}{Colours.NC}")

def printVerbose(message: str) -> None:
    """Print a verbose/debug message in cyan. Only shown at verbose verbosity."""
    if _verbosity >= Verbosity.verbose:
        safePrint(f"{Colours.CYAN}[VERBOSE] {message}{Colours.NC}")

def printDebug(message: str) -> None:
    """Print a debug message (alias for printVerbose). Only shown at verbose verbosity."""
    printVerbose(message)

def printSection(message: str, dryRun: bool = False, includeTimestamp: bool = False) -> None:
    """Print a section header with === borders in cyan. Only shown at normal or verbose verbosity."""
    if _verbosity >= Verbosity.normal:
        if dryRun:
            message = f"{message} (DRY RUN)"
        formatted = formatWithTimestamp(message) if includeTimestamp else message
        safePrint(f"{Colours.CYAN}=== {formatted} ==={Colours.NC}")

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

    print(title)
    print("")

    # Intent section
    print("Intent:")
    if isinstance(intent, str):
        print(f"  {intent}")
    else:
        for line in intent:
            print(f"  {line}")
    print("")

    # Usage section
    print("Usage:")
    if isinstance(usage, str):
        print(f"  {usage}")
    else:
        for line in usage:
            print(f"  {line}")
    print("")

    # Additional sections (Platforms, Operations, etc.)
    if sections:
        for sectionName, items in sections.items():
            print(f"{sectionName}:")
            for item in items:
                print(f"  {item}")
            print("")

    # Options section
    if options:
        print("Options:")
        for option, description in options:
            print(f"  {option:<20} {description}")
        print("")

    # Examples section
    if examples:
        print("Examples:")
        for example in examples:
            print(f"  {example}")


def colourise(text, code, enable=None):
    """Apply colour to text if enabled (defaults to checking if stdout is a TTY)."""
    if enable is None:
        enable = sys.stdout.isatty()
    if not enable:
        return text
    return f"{code}{text}{Colours.NC}"
