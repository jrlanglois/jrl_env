#!/bin/bash
# Shared Cursor configuration logic

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../core/logging.sh"

configureCursor()
{
    local configPath=${1:-$cursorConfigPath}
    local jqHint="${jqInstallHint:-Please install jq via your package manager.}"
    local cursorSettingsPath="${cursorSettingsPath:?cursorSettingsPath must be set}"
    local cursorUserDir

    logSection "Cursor Configuration"
    echo ""

    if [ ! -f "$configPath" ]; then
        logError "Configuration file not found: $configPath"
        return 1
    fi

    cursorUserDir=$(dirname "$cursorSettingsPath")

    if [ ! -d "$cursorUserDir" ]; then
        logNote "Creating Cursor User directory..."
        mkdir -p "$cursorUserDir"
    fi

    if ! command -v jq >/dev/null 2>&1; then
        logError "jq is required to merge JSON. Please install it first."
        echo -e "  $jqHint"
        return 1
    fi

    local existingSettings="{}"
    if [ -f "$cursorSettingsPath" ]; then
        logNote "Reading existing Cursor settings..."
        if ! existingSettings=$(jq . "$cursorSettingsPath" 2>/dev/null); then
            logWarning "Failed to parse existing settings.json. Creating new file."
            existingSettings="{}"
        fi
    fi

    logNote "Merging settings (config file takes precedence)..."
    local mergedSettings
    # Merge: existing settings first, then config file (config values override existing)
    if ! mergedSettings=$(jq -s '.[0] * .[1]' <(echo "$existingSettings") "$configPath"); then
        logError "Failed to merge settings"
        return 1
    fi

    # Verify that config values are actually in the merged result
    local configFontFamily
    configFontFamily=$(jq -r '.["editor.fontFamily"] // empty' "$configPath")
    if [ -n "$configFontFamily" ]; then
        local mergedFontFamily
        mergedFontFamily=$(echo "$mergedSettings" | jq -r '.["editor.fontFamily"] // empty')
        if [ "$mergedFontFamily" != "$configFontFamily" ]; then
            logWarning "Font family merge may have failed. Expected: $configFontFamily"
            logNote "  Got: $mergedFontFamily"
        fi
    fi

    logNote "Writing settings to: $cursorSettingsPath"
    echo "$mergedSettings" | jq . > "$cursorSettingsPath"

    logSuccess "Cursor settings configured successfully!"
    echo ""

    # Check for workspace settings that might override user settings
    local workspaceSettingsPath=".vscode/settings.json"
    if [ -f "$workspaceSettingsPath" ] || [ -f ".cursor/settings.json" ]; then
        logWarning "Note: Workspace settings files (.vscode/settings.json or .cursor/settings.json)"
        logNote "  may override user settings. Check these files if settings don't match."
    fi

    logNote "Note: You may need to restart Cursor for all changes to take effect."

    return 0
}
