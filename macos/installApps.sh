#!/bin/bash
# Script to install applications on macOS using Homebrew
# Reads from macosApps.json configuration file

set -e

# Colours for output
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[1;33m'
cyan='\033[0;36m'
nc='\033[0m' # No Colour

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
configPath="${scriptDir}/../configs/macosApps.json"

# Function to check if a command exists
commandExists()
{
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Homebrew is installed
isBrewInstalled()
{
    if commandExists brew; then
        return 0
    fi
    return 1
}

# Function to check if a brew package is installed
isBrewPackageInstalled()
{
    local package=$1
    if brew list "$package" &>/dev/null; then
        return 0
    fi
    return 1
}

# Function to check if a brew cask is installed
isBrewCaskInstalled()
{
    local cask=$1
    if brew list --cask "$cask" &>/dev/null; then
        return 0
    fi
    return 1
}

# Function to install or update apps
installOrUpdateApps()
{
    local configPath=${1:-$configPath}

    echo -e "${cyan}=== macOS Application Installation ===${nc}"
    echo ""

    # Check if Homebrew is installed
    if ! isBrewInstalled; then
        echo -e "${red}✗ Homebrew is not installed.${nc}"
        echo -e "${yellow}Please install Homebrew first using setupDevEnv.sh${nc}"
        return 1
    fi

    # Check if config file exists
    if [ ! -f "$configPath" ]; then
        echo -e "${red}✗ Configuration file not found: $configPath${nc}"
        return 1
    fi

    # Parse JSON (using jq if available, otherwise basic parsing)
    if commandExists jq; then
        brewApps=$(jq -r '.brew[]?' "$configPath" 2>/dev/null || echo "")
        brewCaskApps=$(jq -r '.brewCask[]?' "$configPath" 2>/dev/null || echo "")
    else
        echo -e "${yellow}⚠ jq is not installed. Installing basic JSON parsing...${nc}"
        # Basic fallback - install jq first
        if ! isBrewPackageInstalled jq; then
            brew install jq
        fi
        brewApps=$(jq -r '.brew[]?' "$configPath" 2>/dev/null || echo "")
        brewCaskApps=$(jq -r '.brewCask[]?' "$configPath" 2>/dev/null || echo "")
    fi

    if [ -z "$brewApps" ] && [ -z "$brewCaskApps" ]; then
        echo -e "${yellow}No applications specified in configuration file.${nc}"
        return 0
    fi

    local brewCount=$(echo "$brewApps" | grep -c . || echo "0")
    local caskCount=$(echo "$brewCaskApps" | grep -c . || echo "0")
    local totalCount=$((brewCount + caskCount))

    echo -e "${cyan}Found $totalCount application(s) in configuration file ($brewCount brew, $caskCount cask).${nc}"
    echo ""

    local installedCount=0
    local updatedCount=0
    local failedCount=0

    # Process brew packages
    if [ -n "$brewApps" ]; then
        echo -e "${cyan}=== Processing Homebrew packages ===${nc}"
        echo ""

        while IFS= read -r package; do
            if [ -z "$package" ]; then
                continue
            fi

            echo -e "${yellow}Processing: $package${nc}"

            if isBrewPackageInstalled "$package"; then
                echo -e "  ${cyan}Package is installed. Updating...${nc}"
                if brew upgrade "$package" &>/dev/null; then
                    echo -e "  ${green}✓ Updated successfully${nc}"
                    ((updatedCount++))
                else
                    echo -e "  ${yellow}⚠ Update check completed (may already be up to date)${nc}"
                    ((updatedCount++))
                fi
            else
                echo -e "  ${cyan}Package is not installed. Installing...${nc}"
                if brew install "$package" &>/dev/null; then
                    echo -e "  ${green}✓ Installed successfully${nc}"
                    ((installedCount++))
                else
                    echo -e "  ${red}✗ Installation failed${nc}"
                    ((failedCount++))
                fi
            fi
            echo ""
        done <<< "$brewApps"
    fi

    # Process brew casks
    if [ -n "$brewCaskApps" ]; then
        echo -e "${cyan}=== Processing Homebrew Casks ===${nc}"
        echo ""

        while IFS= read -r cask; do
            if [ -z "$cask" ]; then
                continue
            fi

            echo -e "${yellow}Processing: $cask${nc}"

            if isBrewCaskInstalled "$cask"; then
                echo -e "  ${cyan}Application is installed. Updating...${nc}"
                if brew upgrade --cask "$cask" &>/dev/null; then
                    echo -e "  ${green}✓ Updated successfully${nc}"
                    ((updatedCount++))
                else
                    echo -e "  ${yellow}⚠ Update check completed (may already be up to date)${nc}"
                    ((updatedCount++))
                fi
            else
                echo -e "  ${cyan}Application is not installed. Installing...${nc}"
                if brew install --cask "$cask" &>/dev/null; then
                    echo -e "  ${green}✓ Installed successfully${nc}"
                    ((installedCount++))
                else
                    echo -e "  ${red}✗ Installation failed${nc}"
                    ((failedCount++))
                fi
            fi
            echo ""
        done <<< "$brewCaskApps"
    fi

    echo -e "${cyan}Summary:${nc}"
    echo -e "  ${green}Installed: $installedCount${nc}"
    echo -e "  ${green}Updated: $updatedCount${nc}"
    if [ $failedCount -gt 0 ]; then
        echo -e "  ${red}Failed: $failedCount${nc}"
    fi

    return 0
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    installOrUpdateApps "$@"
fi