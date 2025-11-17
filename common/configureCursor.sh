#!/bin/bash
# Shared Cursor configuration logic

# shellcheck disable=SC2154 # colour variables provided by callers

configureCursor()
{
    local configPath=${1:-$cursorConfigPath}
    local jqHint="${jqInstallHint:-${yellow}Please install jq via your package manager.${nc}}"
    local cursorSettingsPath="${cursorSettingsPath:?cursorSettingsPath must be set}"
    local cursorUserDir

    echo -e "${cyan}=== Cursor Configuration ===${nc}"
    echo ""

    if [ ! -f "$configPath" ]; then
        echo -e "${red}✗ Configuration file not found: $configPath${nc}"
        return 1
    fi

    cursorUserDir=$(dirname "$cursorSettingsPath")

    if [ ! -d "$cursorUserDir" ]; then
        echo -e "${yellow}Creating Cursor User directory...${nc}"
        mkdir -p "$cursorUserDir"
    fi

    if ! command -v jq >/dev/null 2>&1; then
        echo -e "${red}✗ jq is required to merge JSON. Please install it first.${nc}"
        echo -e "  $jqHint"
        return 1
    fi

    local existingSettings="{}"
    if [ -f "$cursorSettingsPath" ]; then
        echo -e "${yellow}Reading existing Cursor settings...${nc}"
        if ! existingSettings=$(jq . "$cursorSettingsPath" 2>/dev/null); then
            echo -e "${yellow}⚠ Failed to parse existing settings.json. Creating new file.${nc}"
            existingSettings="{}"
        fi
    fi

    echo -e "${yellow}Merging settings...${nc}"
    local mergedSettings
    if ! mergedSettings=$(jq -s '.[0] * .[1]' <(echo "$existingSettings") "$configPath"); then
        echo -e "${red}✗ Failed to merge settings${nc}"
        return 1
    fi

    echo -e "${yellow}Writing settings to: $cursorSettingsPath${nc}"
    echo "$mergedSettings" | jq . > "$cursorSettingsPath"

    echo -e "${green}✓ Cursor settings configured successfully!${nc}"
    echo -e "${yellow}Note: You may need to restart Cursor for all changes to take effect.${nc}"

    return 0
}
