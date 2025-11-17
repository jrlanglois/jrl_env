#!/bin/bash
# Script to configure Cursor editor settings from cursorSettings.json
# Merges settings from config file into Cursor's settings.json

set -e

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Colour

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PATH="${SCRIPT_DIR}/../configs/cursorSettings.json"

# Function to get Cursor settings path
getCursorSettingsPath() {
    echo "$HOME/Library/Application Support/Cursor/User/settings.json"
}

# Function to configure Cursor settings
configureCursor() {
    local configPath=${1:-$CONFIG_PATH}
    
    echo -e "${CYAN}=== Cursor Configuration ===${NC}"
    echo ""
    
    # Check if config file exists
    if [ ! -f "$configPath" ]; then
        echo -e "${RED}✗ Configuration file not found: $configPath${NC}"
        return 1
    fi
    
    # Get Cursor settings path
    local cursorSettingsPath=$(getCursorSettingsPath)
    local cursorUserDir=$(dirname "$cursorSettingsPath")
    
    # Create Cursor User directory if it doesn't exist
    if [ ! -d "$cursorUserDir" ]; then
        echo -e "${YELLOW}Creating Cursor User directory...${NC}"
        mkdir -p "$cursorUserDir"
    fi
    
    # Check if jq is available
    if ! command -v jq >/dev/null 2>&1; then
        echo -e "${RED}✗ jq is required to merge JSON. Please install it first.${NC}"
        echo -e "${YELLOW}  brew install jq${NC}"
        return 1
    fi
    
    # Read existing settings if they exist
    local existingSettings="{}"
    if [ -f "$cursorSettingsPath" ]; then
        echo -e "${YELLOW}Reading existing Cursor settings...${NC}"
        if ! existingSettings=$(cat "$cursorSettingsPath" 2>/dev/null | jq . 2>/dev/null); then
            echo -e "${YELLOW}⚠ Failed to parse existing settings.json. Creating new file.${NC}"
            existingSettings="{}"
        fi
    fi
    
    # Merge config settings with existing settings (config takes precedence)
    echo -e "${YELLOW}Merging settings...${NC}"
    local mergedSettings
    if ! mergedSettings=$(jq -s '.[0] * .[1]' <(echo "$existingSettings") "$configPath"); then
        echo -e "${RED}✗ Failed to merge settings${NC}"
        return 1
    fi
    
    # Write to Cursor settings file
    echo -e "${YELLOW}Writing settings to: $cursorSettingsPath${NC}"
    echo "$mergedSettings" | jq . > "$cursorSettingsPath"
    
    echo -e "${GREEN}✓ Cursor settings configured successfully!${NC}"
    echo -e "${YELLOW}Note: You may need to restart Cursor for all changes to take effect.${NC}"
    
    return 0
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureCursor "$@"
fi
