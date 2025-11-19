#!/usr/bin/env python3
"""
Shared Cursor configuration logic.
Merges JSON settings from config file with existing Cursor settings.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional

# Import common utilities directly from source modules
from common.core.logging import (
    printError,
    printInfo,
    printSection,
    printSuccess,
    printWarning,
)


def mergeJsonSettings(existingSettings: Dict, configSettings: Dict) -> Dict:
    """
    Merge two JSON dictionaries, with configSettings taking precedence.

    Args:
        existingSettings: Existing settings dictionary
        configSettings: New settings dictionary (takes precedence)

    Returns:
        Merged dictionary
    """
    # Deep merge: start with existing, then update with config
    merged = existingSettings.copy()

    for key, value in configSettings.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            merged[key] = mergeJsonSettings(merged[key], value)
        else:
            # Config value takes precedence
            merged[key] = value

    return merged


def configureCursor(
    configPath: Optional[str] = None,
    cursorSettingsPath: Optional[str] = None,
    dryRun: bool = False,
) -> bool:
    """
    Configure Cursor settings by merging config file with existing settings.

    Args:
        configPath: Path to cursorSettings.json config file
        cursorSettingsPath: Path to Cursor's settings.json file
        dryRun: If True, don't actually write settings

    Returns:
        True if successful, False otherwise
    """
    printSection("Cursor Configuration", dryRun=dryRun)
    print()

    if not configPath:
        printError("Configuration file path not provided")
        return False

    configFile = Path(configPath)
    if not configFile.exists():
        printError(f"Configuration file not found: {configPath}")
        return False

    if not cursorSettingsPath:
        printError("Cursor settings path not provided")
        return False

    cursorSettingsFile = Path(cursorSettingsPath)
    cursorUserDir = cursorSettingsFile.parent

    if not cursorUserDir.exists():
        printInfo("Creating Cursor User directory...")
        cursorUserDir.mkdir(parents=True, exist_ok=True)

    # Read existing settings
    existingSettings: Dict = {}
    if cursorSettingsFile.exists():
        printInfo("Reading existing Cursor settings...")
        try:
            with open(cursorSettingsFile, 'r', encoding='utf-8') as f:
                existingSettings = json.load(f)
        except json.JSONDecodeError:
            printWarning("Failed to parse existing settings.json. Creating new file.")
            existingSettings = {}
        except Exception as e:
            printWarning(f"Error reading existing settings: {e}. Creating new file.")
            existingSettings = {}

    # Read config file
    try:
        with open(configFile, 'r', encoding='utf-8') as f:
            configSettings = json.load(f)
    except json.JSONDecodeError as e:
        printError(f"Failed to parse config file: {e}")
        return False
    except Exception as e:
        printError(f"Error reading config file: {e}")
        return False

    # Merge settings (config takes precedence)
    printInfo("Merging settings (config file takes precedence)...")
    mergedSettings = mergeJsonSettings(existingSettings, configSettings)

    # Verify that config values are actually in the merged result
    configFontFamily = configSettings.get("editor.fontFamily")
    if configFontFamily:
        mergedFontFamily = mergedSettings.get("editor.fontFamily")
        if mergedFontFamily != configFontFamily:
            printWarning(f"Font family merge may have failed. Expected: {configFontFamily}")
            printInfo(f"  Got: {mergedFontFamily}")

    # Write merged settings
    printInfo(f"Writing settings to: {cursorSettingsPath}")
    if dryRun:
        printInfo("  [DRY RUN] Would write merged settings to file")
        printSuccess("Cursor settings configured successfully!")
        return True

    try:
        with open(cursorSettingsFile, 'w', encoding='utf-8') as f:
            json.dump(mergedSettings, f, indent=4, ensure_ascii=False)
        printSuccess("Cursor settings configured successfully!")
    except Exception as e:
        printError(f"Failed to write settings: {e}")
        return False

    print()

    # Check for workspace settings that might override user settings
    workspaceSettingsPath = Path(".vscode/settings.json")
    cursorWorkspaceSettingsPath = Path(".cursor/settings.json")

    if workspaceSettingsPath.exists() or cursorWorkspaceSettingsPath.exists():
        printWarning("Note: Workspace settings files (.vscode/settings.json or .cursor/settings.json)")
        printInfo("  may override user settings. Check these files if settings don't match.")

    printInfo("Note: You may need to restart Cursor for all changes to take effect.")

    return True


__all__ = [
    "mergeJsonSettings",
    "configureCursor",
]
