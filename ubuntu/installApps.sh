#!/bin/bash
# Script to install applications on Ubuntu using apt and snap
# Reads from ubuntuApps.json configuration file

set -e

# Colours for output
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[1;33m'
cyan='\033[0;36m'
nc='\033[0m' # No Colour

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
configPath="${scriptDir}/../configs/ubuntuApps.json"

# Function to check if a command exists
commandExists()
{
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a package is installed via apt
isAptPackageInstalled()
{
    local package=$1
    if dpkg -l | grep -q "^ii  $package "; then
        return 0
    fi
    return 1
}

# Function to check if a snap is installed
isSnapInstalled()
{
    local snap=$1
    if snap list "$snap" &>/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Function to install or update apps
installOrUpdateApps()
{
    local configPath=${1:-$configPath}

    echo -e "${cyan}=== Ubuntu Application Installation ===${nc}"
    echo ""

    # Check if config file exists
    if [ ! -f "$configPath" ]; then
        echo -e "${red}✗ Configuration file not found: $configPath${nc}"
        return 1
    fi

    # Check if jq is available
    if ! commandExists jq; then
        echo -e "${yellow}⚠ jq is not installed. Installing...${nc}"
        sudo apt-get update
        sudo apt-get install -y jq
    fi

    # Parse JSON
    local aptPackages=$(jq -r '.apt[]?' "$configPath" 2>/dev/null || echo "")
    local snapPackages=$(jq -r '.snap[]?' "$configPath" 2>/dev/null || echo "")

    if [ -z "$aptPackages" ] && [ -z "$snapPackages" ]; then
        echo -e "${yellow}No applications specified in configuration file.${nc}"
        return 0
    fi

    local aptCount=$(echo "$aptPackages" | grep -c . || echo "0")
    local snapCount=$(echo "$snapPackages" | grep -c . || echo "0")
    local totalCount=$((aptCount + snapCount))

    echo -e "${cyan}Found $totalCount application(s) in configuration file ($aptCount apt, $snapCount snap).${nc}"
    echo ""

    # Update package list
    echo -e "${cyan}Updating package list...${nc}"
    sudo apt-get update
    echo ""

    local installedCount=0
    local updatedCount=0
    local failedCount=0

    # Process apt packages
    if [ -n "$aptPackages" ]; then
        echo -e "${cyan}=== Processing apt packages ===${nc}"
        echo ""

        while IFS= read -r package; do
            if [ -z "$package" ]; then
                continue
            fi

            echo -e "${yellow}Processing: $package${nc}"

            if isAptPackageInstalled "$package"; then
                echo -e "  ${cyan}Package is installed. Updating...${nc}"
                if sudo apt-get install --only-upgrade -y "$package" &>/dev/null; then
                    echo -e "  ${green}✓ Updated successfully${nc}"
                    ((updatedCount++))
                else
                    echo -e "  ${yellow}⚠ Update check completed (may already be up to date)${nc}"
                    ((updatedCount++))
                fi
            else
                echo -e "  ${cyan}Package is not installed. Installing...${nc}"
                if sudo apt-get install -y "$package" &>/dev/null; then
                    echo -e "  ${green}✓ Installed successfully${nc}"
                    ((installedCount++))
                else
                    echo -e "  ${red}✗ Installation failed${nc}"
                    ((failedCount++))
                fi
            fi
            echo ""
        done <<< "$aptPackages"
    fi

    # Process snap packages
    if [ -n "$snapPackages" ]; then
        echo -e "${cyan}=== Processing snap packages ===${nc}"
        echo ""

        while IFS= read -r snap; do
            if [ -z "$snap" ]; then
                continue
            fi

            echo -e "${yellow}Processing: $snap${nc}"

            if isSnapInstalled "$snap"; then
                echo -e "  ${cyan}Application is installed. Updating...${nc}"
                if sudo snap refresh "$snap" &>/dev/null; then
                    echo -e "  ${green}✓ Updated successfully${nc}"
                    ((updatedCount++))
                else
                    echo -e "  ${yellow}⚠ Update check completed (may already be up to date)${nc}"
                    ((updatedCount++))
                fi
            else
                echo -e "  ${cyan}Application is not installed. Installing...${nc}"
                if sudo snap install "$snap" &>/dev/null; then
                    echo -e "  ${green}✓ Installed successfully${nc}"
                    ((installedCount++))
                else
                    echo -e "  ${red}✗ Installation failed${nc}"
                    ((failedCount++))
                fi
            fi
            echo ""
        done <<< "$snapPackages"
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
