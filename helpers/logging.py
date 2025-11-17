#!/usr/bin/env python3
"""
Shared logging utilities for consistent output formatting across Python scripts
"""

import sys
from threading import Lock

# ANSI colour codes
class Colours:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Colour

# Thread-safe print lock (for scripts that use threading)
printLock = Lock()

def safePrint(*args, **kwargs):
    """Thread-safe print function"""
    with printLock:
        print(*args, **kwargs)

def printInfo(message):
    """Print an info message in cyan"""
    safePrint(f"{Colours.CYAN}{message}{Colours.NC}")

def printWarning(message):
    """Print a warning message in yellow"""
    safePrint(f"{Colours.YELLOW}{message}{Colours.NC}")

def printError(message):
    """Print an error message in red"""
    safePrint(f"{Colours.RED}{message}{Colours.NC}")

def printSuccess(message):
    """Print a success message in green"""
    safePrint(f"{Colours.GREEN}{message}{Colours.NC}")

def printSection(message):
    """Print a section header in cyan"""
    safePrint(f"{Colours.CYAN}=== {message} ==={Colours.NC}")

def colourise(text, code, enable=None):
    """
    Apply colour to text if colour is enabled.
    
    Args:
        text: Text to colourise
        code: ANSI colour code (from Colours class)
        enable: Whether to enable colour (defaults to checking if stdout is a TTY)
    
    Returns:
        Colourised text if enabled, otherwise plain text
    """
    if enable is None:
        enable = sys.stdout.isatty()
    if not enable:
        return text
    return f"{code}{text}{Colours.NC}"

