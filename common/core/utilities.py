#!/usr/bin/env python3
"""
Generic utility functions for Python scripts.
Provides command checking, JSON operations, and OS detection.
"""

import json
import os
import platform
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import logging functions directly (no circular dependency - logging doesn't import utilities)
from common.core.logging import printError, printInfo, printSuccess, getVerbosity, Verbosity


# Cached operating system (similar to Bash variable)
_OPERATING_SYSTEM: Optional[str] = None


def commandExists(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(cmd) is not None


def requireCommand(cmd: str, installHint: str = "") -> bool:
    """Require a command to be available, show install hint if missing."""
    if commandExists(cmd):
        return True

    # Use logging functions if available, otherwise use print
    printError(f"Required command '{cmd}' not found.")
    if installHint:
        printInfo(f"  {installHint}")

    return False


def getJsonValue(configPath: str, jsonPath: str, default: Any = None) -> Any:
    """Get a JSON value using JSONPath-like syntax (e.g., ".key.subkey" or ".array[0]")."""
    configFile = Path(configPath)

    if not configFile.exists():
        return default

    try:
        with open(configFile, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Parse JSONPath (simple implementation for common cases)
        # Remove leading dot if present
        path = jsonPath.lstrip('.')

        # Navigate through the path
        current = data
        parts = path.split('.')

        for part in parts:
            # Handle array access like "key[0]"
            if '[' in part and part.endswith(']'):
                key, indexStr = part.split('[', 1)
                index = int(indexStr.rstrip(']'))
                if key:
                    current = current[key]
                current = current[index]
            else:
                current = current[part]

        return current if current is not None else default

    except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError):
        return default


def getJsonArray(configPath: str, jsonPath: str) -> List[str]:
    """Get a JSON array and return as a list of strings (e.g., ".packages[]")."""
    configFile = Path(configPath)

    if not configFile.exists():
        return []

    try:
        with open(configFile, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle array notation like ".packages[]"
        path = jsonPath.rstrip('[]')
        path = path.lstrip('.')

        # Navigate to the array
        current = data
        if path:
            parts = path.split('.')
            for part in parts:
                if '[' in part and part.endswith(']'):
                    key, indexStr = part.split('[', 1)
                    index = int(indexStr.rstrip(']'))
                    if key:
                        current = current[key]
                    current = current[index]
                else:
                    current = current[part]

        # Ensure we have a list
        if isinstance(current, list):
            # Convert all items to strings, filtering out None
            return [str(item) for item in current if item is not None]
        elif current is not None:
            # Single value, wrap in list
            return [str(current)]
        else:
            return []

    except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError):
        return []


def getJsonObject(configPath: str, jsonPath: str) -> Dict:
    """Get a JSON object (e.g., ".config" or ".key.subkey")."""
    configFile = Path(configPath)

    if not configFile.exists():
        return {}

    try:
        with open(configFile, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Navigate to the object
        path = jsonPath.lstrip('.')
        if not path:
            return data if isinstance(data, dict) else {}

        current = data
        parts = path.split('.')

        for part in parts:
            if '[' in part and part.endswith(']'):
                key, indexStr = part.split('[', 1)
                index = int(indexStr.rstrip(']'))
                if key:
                    current = current[key]
                current = current[index]
            else:
                current = current[part]

        return current if isinstance(current, dict) else {}

    except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError):
        return {}




def findOperatingSystem() -> str:
    """Detect the current operating system ("linux", "macos", "windows", or "unknown")."""
    system = platform.system().lower()

    if system == "linux":
        # Check for specific Linux distributions
        os_release = Path("/etc/os-release")
        if os_release.exists():
            try:
                with open(os_release, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith("ID="):
                            distro_id = line.split('=', 1)[1].strip().strip('"').strip("'")
                            # All Linux distros return "linux" for now
                            # Can be extended later if needed
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
    """Get the operating system (cached to avoid repeated detection)."""
    global _OPERATING_SYSTEM

    if _OPERATING_SYSTEM is None:
        _OPERATING_SYSTEM = findOperatingSystem()

    return _OPERATING_SYSTEM


def isOperatingSystem(target: str) -> bool:
    """Check if the current operating system matches the target."""
    current = getOperatingSystem()
    return current == target


def getConfigDirectory(projectRoot: Path, args: Optional[List[str]] = None) -> Path:
    """
    Get the configuration directory path.
    Checks CLI arguments, environment variable, then defaults to projectRoot/configs.

    Args:
        projectRoot: Root directory of the project
        args: Optional command-line arguments (defaults to sys.argv[1:])

    Returns:
        Path to the configuration directory
    """
    if args is None:
        args = sys.argv[1:]

    # Check CLI arguments for --configDir
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--configDir="):
            return Path(arg.split("=", 1)[1])
        elif arg == "--configDir":
            if i + 1 < len(args):
                return Path(args[i + 1])
        i += 1

    # Check environment variable
    envConfigDir = os.environ.get("JRL_ENV_CONFIG_DIR")
    if envConfigDir:
        return Path(envConfigDir)

    # Default to projectRoot/configs
    return projectRoot / "configs"


def hasInternetConnectivity(timeout: int = 5) -> bool:
    """
    Check if internet connectivity is available.

    Makes a lightweight HTTP HEAD request to a reliable service (GitHub API).
    This is the typical approach - firewall-friendly, cross-platform, no special permissions needed.

    Args:
        timeout: Request timeout in seconds

    Returns:
        True if internet connectivity is available, False otherwise
    """
    # Use GitHub API as it's reliable and we already use it for repository validation
    testUrl = "https://api.github.com"

    try:
        req = urllib.request.Request(testUrl, method='HEAD')
        req.add_header('User-Agent', 'jrl_env-connectivity-check')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status in (200, 301, 302, 307, 308)  # Accept redirects as valid
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return False
    except Exception:
        return False


__all__ = [
    "commandExists",
    "requireCommand",
    "getJsonValue",
    "getJsonArray",
    "getJsonObject",
    "findOperatingSystem",
    "getOperatingSystem",
    "isOperatingSystem",
    "detectPlatform",
    "detectPackageManager",
    "getConfigDirectory",
    "hasInternetConnectivity",
]
