#!/bin/bash
# Script to install applications on Ubuntu using apt and snap
# Reads from ubuntuApps.json configuration file

set -e

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Colour

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PATH="${SCRIPT_DIR}/../configs/ubuntuApps.json"

# Function to check if a command exists
commandExists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a package is installed via apt
isAptPackageInstalled() {
    local package=$1
    if dpkg -l | grep -q "^ii  $package "; then
        return 0
    fi
    return 1
}

# Function to check if a snap is installed
isSnapInstalled() {
    local snap=$1
    if snap list "$snap" &>/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Function to install or update apps
installOrUpdateApps() {
    local configPath=${1:-$CONFIG_PATH}
    
    echo -e "${CYAN}=== Ubuntu Application Installation ===${NC}"
    echo ""
    
    # Check if config file exists
    if [ ! -f "$configPath" ]; then
        echo -e "${RED}✗ Configuration file not found: $configPath${NC}"
        return 1
    fi
    
    # Check if jq is available
    if ! commandExists jq; then
        echo -e "${YELLOW}⚠ jq is not installed. Installing...${NC}"
        sudo apt-get update
        sudo apt-get install -y jq
    fi
    
    # Parse JSON
    local aptPackages=$(jq -r '.apt[]?' "$configPath" 2>/dev/null || echo "")
    local snapPackages=$(jq -r '.snap[]?' "$configPath" 2>/dev/null || echo "")
    
    if [ -z "$aptPackages" ] && [ -z "$snapPackages" ]; then
        echo -e "${YELLOW}No applications specified in configuration file.${NC}"
        return 0
    fi
    
    local aptCount=$(echo "$aptPackages" | grep -c . || echo "0")
    local snapCount=$(echo "$snapPackages" | grep -c . || echo "0")
    local totalCount=$((aptCount + snapCount))
    
    echo -e "${CYAN}Found $totalCount application(s) in configuration file ($aptCount apt, $snapCount snap).${NC}"
    echo ""
    
    # Update package list
    echo -e "${CYAN}Updating package list...${NC}"
    sudo apt-get update
    echo ""
    
    local installedCount=0
    local updatedCount=0
    local failedCount=0
    
    # Process apt packages
    if [ -n "$aptPackages" ]; then
        echo -e "${CYAN}=== Processing apt packages ===${NC}"
        echo ""
        
        while IFS= read -r package; do
            if [ -z "$package" ]; then
                continue
            fi
            
            echo -e "${YELLOW}Processing: $package${NC}"
            
            if isAptPackageInstalled "$package"; then
                echo -e "  ${CYAN}Package is installed. Updating...${NC}"
                if sudo apt-get install --only-upgrade -y "$package" &>/dev/null; then
                    echo -e "  ${GREEN}✓ Updated successfully${NC}"
                    ((updatedCount++))
                else
                    echo -e "  ${YELLOW}⚠ Update check completed (may already be up to date)${NC}"
                    ((updatedCount++))
                fi
            else
                echo -e "  ${CYAN}Package is not installed. Installing...${NC}"
                if sudo apt-get install -y "$package" &>/dev/null; then
                    echo -e "  ${GREEN}✓ Installed successfully${NC}"
                    ((installedCount++))
                else
                    echo -e "  ${RED}✗ Installation failed${NC}"
                    ((failedCount++))
                fi
            fi
            echo ""
        done <<< "$aptPackages"
    fi
    
    # Process snap packages
    if [ -n "$snapPackages" ]; then
        echo -e "${CYAN}=== Processing snap packages ===${NC}"
        echo ""
        
        while IFS= read -r snap; do
            if [ -z "$snap" ]; then
                continue
            fi
            
            echo -e "${YELLOW}Processing: $snap${NC}"
            
            if isSnapInstalled "$snap"; then
                echo -e "  ${CYAN}Application is installed. Updating...${NC}"
                if sudo snap refresh "$snap" &>/dev/null; then
                    echo -e "  ${GREEN}✓ Updated successfully${NC}"
                    ((updatedCount++))
                else
                    echo -e "  ${YELLOW}⚠ Update check completed (may already be up to date)${NC}"
                    ((updatedCount++))
                fi
            else
                echo -e "  ${CYAN}Application is not installed. Installing...${NC}"
                if sudo snap install "$snap" &>/dev/null; then
                    echo -e "  ${GREEN}✓ Installed successfully${NC}"
                    ((installedCount++))
                else
                    echo -e "  ${RED}✗ Installation failed${NC}"
                    ((failedCount++))
                fi
            fi
            echo ""
        done <<< "$snapPackages"
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
