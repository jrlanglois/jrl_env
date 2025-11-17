#!/bin/bash
# Script to configure Cursor editor settings from cursorSettings.json
# Merges settings from config file into Cursor's settings.json

set -e

# Colours for output
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[1;33m'
cyan='\033[0;36m'
nc='\033[0m' # No Colour

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
configPath="${scriptDir}/../configs/cursorSettings.json"

# Function to get Cursor settings path
getCursorSettingsPath()
{
    echo "$HOME/.config/Cursor/User/settings.json"
}

# Function to configure Cursor settings
configureCursor()
{
    local configPath=${1:-$configPath}

    echo -e "${cyan}=== Cursor Configuration ===${nc}"
    echo ""

    # Check if config file exists
    if [ ! -f "$configPath" ]; then
        echo -e "${red}✗ Configuration file not found: $configPath${nc}"
        return 1
    fi

    # Get Cursor settings path
    local cursorSettingsPath=$(getCursorSettingsPath)
    local cursorUserDir=$(dirname "$cursorSettingsPath")

    # Create Cursor User directory if it doesn't exist
    if [ ! -d "$cursorUserDir" ]; then
        echo -e "${yellow}Creating Cursor User directory...${nc}"
        mkdir -p "$cursorUserDir"
    fi

    # Check if jq is available
    if ! command -v jq >/dev/null 2>&1; then
        echo -e "${red}✗ jq is required to merge JSON. Please install it first.${nc}"
        echo -e "${yellow}  sudo apt-get install -y jq${nc}"
        return 1
    fi

    # Read existing settings if they exist
    local existingSettings="{}"
    if [ -f "$cursorSettingsPath" ]; then
        echo -e "${yellow}Reading existing Cursor settings...${nc}"
        if ! existingSettings=$(cat "$cursorSettingsPath" 2>/dev/null | jq . 2>/dev/null); then
            echo -e "${yellow}⚠ Failed to parse existing settings.json. Creating new file.${nc}"
            existingSettings="{}"
        fi
    fi

    # Merge config settings with existing settings (config takes precedence)
    echo -e "${yellow}Merging settings...${nc}"
    local mergedSettings
    if ! mergedSettings=$(jq -s '.[0] * .[1]' <(echo "$existingSettings") "$configPath"); then
        echo -e "${red}✗ Failed to merge settings${nc}"
        return 1
    fi

    # Write to Cursor settings file
    echo -e "${yellow}Writing settings to: $cursorSettingsPath${nc}"
    echo "$mergedSettings" | jq . > "$cursorSettingsPath"

    echo -e "${green}✓ Cursor settings configured successfully!${nc}"
    echo -e "${yellow}Note: You may need to restart Cursor for all changes to take effect.${nc}"

    return 0
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureCursor "$@"
fi
