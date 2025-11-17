#!/bin/bash
# Script to install applications on macOS using Homebrew
# Reads from macosApps.json configuration file

set -e

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Colour

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PATH="${SCRIPT_DIR}/../configs/macosApps.json"

# Function to check if a command exists
commandExists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Homebrew is installed
isBrewInstalled() {
    if commandExists brew; then
        return 0
    fi
    return 1
}

# Function to check if a brew package is installed
isBrewPackageInstalled() {
    local package=$1
    if brew list "$package" &>/dev/null; then
        return 0
    fi
    return 1
}

# Function to check if a brew cask is installed
isBrewCaskInstalled() {
    local cask=$1
    if brew list --cask "$cask" &>/dev/null; then
        return 0
    fi
    return 1
}

# Function to install or update apps
installOrUpdateApps() {
    local configPath=${1:-$CONFIG_PATH}
    
    echo -e "${CYAN}=== macOS Application Installation ===${NC}"
    echo ""
    
    # Check if Homebrew is installed
    if ! isBrewInstalled; then
        echo -e "${RED}✗ Homebrew is not installed.${NC}"
        echo -e "${YELLOW}Please install Homebrew first using setupDevEnv.sh${NC}"
        return 1
    fi
    
    # Check if config file exists
    if [ ! -f "$configPath" ]; then
        echo -e "${RED}✗ Configuration file not found: $configPath${NC}"
        return 1
    fi
    
    # Parse JSON (using jq if available, otherwise basic parsing)
    if commandExists jq; then
        brewApps=$(jq -r '.brew[]?' "$configPath" 2>/dev/null || echo "")
        brewCaskApps=$(jq -r '.brewCask[]?' "$configPath" 2>/dev/null || echo "")
    else
        echo -e "${YELLOW}⚠ jq is not installed. Installing basic JSON parsing...${NC}"
        # Basic fallback - install jq first
        if ! isBrewPackageInstalled jq; then
            brew install jq
        fi
        brewApps=$(jq -r '.brew[]?' "$configPath" 2>/dev/null || echo "")
        brewCaskApps=$(jq -r '.brewCask[]?' "$configPath" 2>/dev/null || echo "")
    fi
    
    if [ -z "$brewApps" ] && [ -z "$brewCaskApps" ]; then
        echo -e "${YELLOW}No applications specified in configuration file.${NC}"
        return 0
    fi
    
    local brewCount=$(echo "$brewApps" | grep -c . || echo "0")
    local caskCount=$(echo "$brewCaskApps" | grep -c . || echo "0")
    local totalCount=$((brewCount + caskCount))
    
    echo -e "${CYAN}Found $totalCount application(s) in configuration file ($brewCount brew, $caskCount cask).${NC}"
    echo ""
    
    local installedCount=0
    local updatedCount=0
    local failedCount=0
    
    # Process brew packages
    if [ -n "$brewApps" ]; then
        echo -e "${CYAN}=== Processing Homebrew packages ===${NC}"
        echo ""
        
        while IFS= read -r package; do
            if [ -z "$package" ]; then
                continue
            fi
            
            echo -e "${YELLOW}Processing: $package${NC}"
            
            if isBrewPackageInstalled "$package"; then
                echo -e "  ${CYAN}Package is installed. Updating...${NC}"
                if brew upgrade "$package" &>/dev/null; then
                    echo -e "  ${GREEN}✓ Updated successfully${NC}"
                    ((updatedCount++))
                else
                    echo -e "  ${YELLOW}⚠ Update check completed (may already be up to date)${NC}"
                    ((updatedCount++))
                fi
            else
                echo -e "  ${CYAN}Package is not installed. Installing...${NC}"
                if brew install "$package" &>/dev/null; then
                    echo -e "  ${GREEN}✓ Installed successfully${NC}"
                    ((installedCount++))
                else
                    echo -e "  ${RED}✗ Installation failed${NC}"
                    ((failedCount++))
                fi
            fi
            echo ""
        done <<< "$brewApps"
    fi
    
    # Process brew casks
    if [ -n "$brewCaskApps" ]; then
        echo -e "${CYAN}=== Processing Homebrew Casks ===${NC}"
        echo ""
        
        while IFS= read -r cask; do
            if [ -z "$cask" ]; then
                continue
            fi
            
            echo -e "${YELLOW}Processing: $cask${NC}"
            
            if isBrewCaskInstalled "$cask"; then
                echo -e "  ${CYAN}Application is installed. Updating...${NC}"
                if brew upgrade --cask "$cask" &>/dev/null; then
                    echo -e "  ${GREEN}✓ Updated successfully${NC}"
                    ((updatedCount++))
                else
                    echo -e "  ${YELLOW}⚠ Update check completed (may already be up to date)${NC}"
                    ((updatedCount++))
                fi
            else
                echo -e "  ${CYAN}Application is not installed. Installing...${NC}"
                if brew install --cask "$cask" &>/dev/null; then
                    echo -e "  ${GREEN}✓ Installed successfully${NC}"
                    ((installedCount++))
                else
                    echo -e "  ${RED}✗ Installation failed${NC}"
                    ((failedCount++))
                fi
            fi
            echo ""
        done <<< "$brewCaskApps"
    fi
    
    echo -e "${CYAN}Summary:${NC}"
    echo -e "  ${GREEN}Installed: $installedCount${NC}"
    echo -e "  ${GREEN}Updated: $updatedCount${NC}"
    if [ $failedCount -gt 0 ]; then
        echo -e "  ${RED}Failed: $failedCount${NC}"
    fi
    
    return 0
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    installOrUpdateApps "$@"
fi
