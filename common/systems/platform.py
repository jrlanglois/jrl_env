#!/usr/bin/env python3
"""
Platform enumeration and OS detection for jrl_env.
Provides type-safe platform identifiers and detection functions.
"""

import platform as platformModule
from enum import Enum
from pathlib import Path
from typing import Optional

# Cache for OS detection (avoid repeated system calls)
cachedOperatingSystem: Optional[str] = None

class Platform(Enum):
    """Supported platform identifiers."""
    macos = "macos"
    ubuntu = "ubuntu"
    archlinux = "archlinux"
    opensuse = "opensuse"
    redhat = "redhat"
    raspberrypi = "raspberrypi"
    win11 = "win11"

    def __str__(self) -> str:
        """Return the string value of the platform."""
        return self.value


def findOperatingSystem() -> str:
    """
    Detect the current operating system.

    Returns:
        OS string: "linux", "macos", "windows", or "unknown"
    """
    system = platformModule.system().lower()

    if system == "linux":
        # Check for specific Linux distributions
        osRelease = Path("/etc/os-release")
        if osRelease.exists():
            try:
                with open(osRelease, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith("ID="):
                            distroId = line.split('=', 1)[1].strip().strip('"').strip("'")
                            # All Linux distros return "linux" for now
                            return "linux"
            except (OSError, IOError):
                pass
        return "linux"
    elif system == "darwin":
        return "macos"
    elif system in ("windows", "cygwin", "mingw", "msys"):
        return "windows"
    else:
        return "unknown"


def getOperatingSystem() -> str:
    """
    Get the operating system (cached to avoid repeated detection).

    Returns:
        OS string: "linux", "macos", "windows", or "unknown"
    """
    global cachedOperatingSystem

    if cachedOperatingSystem is None:
        cachedOperatingSystem = findOperatingSystem()

    return cachedOperatingSystem


def isOperatingSystem(platform: Platform) -> bool:
    """
    Check if running on specified platform (type-safe).

    Args:
        platform: Platform enum value (NOT a string!)

    Returns:
        True if running on specified platform, False otherwise

    Raises:
        TypeError: If platform is not a Platform enum
    """
    if not isinstance(platform, Platform):
        raise TypeError(
            f"isOperatingSystem() requires Platform enum, not {type(platform).__name__}. "
            f"Use Platform.win11, Platform.macos, etc."
        )

    current = getOperatingSystem()
    platformStr = str(platform)

    # Map platform enum values to OS strings
    if platformStr == "win11":
        return current == "windows"
    elif platformStr == "macos":
        return current == "macos"
    elif platformStr in ("ubuntu", "archlinux", "opensuse", "redhat", "raspberrypi"):
        return current == "linux"

    return False


def isWindows() -> bool:
    """Check if running on Windows."""
    return isOperatingSystem(Platform.win11)


def isMacOS() -> bool:
    """Check if running on macOS."""
    return isOperatingSystem(Platform.macos)


def isLinux() -> bool:
    """Check if running on Linux (any distribution)."""
    # All Linux platforms (ubuntu, archlinux, etc.) map to "linux" in getOperatingSystem()
    # So we can check any Linux Platform value - they all return True on Linux
    return isOperatingSystem(Platform.ubuntu)


def isUnix() -> bool:
    """Check if running on Unix-like system (macOS or Linux)."""
    return isMacOS() or isLinux()


__all__ = [
    "Platform",
    "findOperatingSystem",
    "getOperatingSystem",
    "isOperatingSystem",
    "isWindows",
    "isMacOS",
    "isLinux",
    "isUnix",
]
