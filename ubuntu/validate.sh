#!/bin/bash
# Script to validate JSON configuration files
# Checks syntax, required fields, and basic validity

set -e

# Colours for output
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[1;33m'
cyan='\033[0;36m'
nc='\033[0m' # No Colour

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
configsPath="$scriptDir/../configs"

errors=()
warnings=()

echo -e "${cyan}=== Validating Configuration Files ===${nc}"
echo ""

# Check if jq is available
if ! command -v jq >/dev/null 2>&1; then
    echo -e "${red}✗ jq is required for validation. Please install it first.${nc}"
    echo -e "${yellow}  sudo apt-get install -y jq${nc}"
    exit 1
fi

# Function to validate JSON file
validateJsonFile() {
    local file_path=$1
    local description=$2
    
    if [ ! -f "$file_path" ]; then
        errors+=("$description: File not found: $file_path")
        return 1
    fi
    
    if jq empty "$file_path" 2>/dev/null; then
        echo -e "${green}✓ $description${nc}"
        return 0
    else
        errors+=("$description: Invalid JSON")
        return 1
    fi
}

# Function to validate apps JSON
validateAppsJson() {
    local file_path=$1
    local platform=$2
    
    if [ "$platform" = "macos" ]; then
        local brew_count=$(jq '.brew | length' "$file_path" 2>/dev/null || echo "0")
        local cask_count=$(jq '.brewCask | length' "$file_path" 2>/dev/null || echo "0")
        
        if [ "$brew_count" = "0" ] && [ "$cask_count" = "0" ]; then
            warnings+=("$platform apps: No apps specified")
        fi
    elif [ "$platform" = "ubuntu" ]; then
        local apt_count=$(jq '.apt | length' "$file_path" 2>/dev/null || echo "0")
        local snap_count=$(jq '.snap | length' "$file_path" 2>/dev/null || echo "0")
        
        if [ "$apt_count" = "0" ] && [ "$snap_count" = "0" ]; then
            warnings+=("$platform apps: No apps specified")
        fi
    fi
}

# Function to validate repositories JSON
validateRepositoriesJson() {
    local file_path=$1
    
    local work_path_win=$(jq -r '.workPathWindows' "$file_path" 2>/dev/null)
    local work_path_unix=$(jq -r '.workPathUnix' "$file_path" 2>/dev/null)
    
    if [ -z "$work_path_win" ] || [ "$work_path_win" = "null" ]; then
        if [ -z "$work_path_unix" ] || [ "$work_path_unix" = "null" ]; then
            errors+=("repositories: Missing workPathWindows or workPathUnix")
        fi
    fi
    
    local repo_count=$(jq '.repositories | length' "$file_path" 2>/dev/null || echo "0")
    if [ "$repo_count" = "0" ]; then
        warnings+=("repositories: No repositories specified")
    fi
}

# Function to validate Git config JSON
validateGitConfigJson() {
    local file_path=$1
    
    local has_user=$(jq 'has("user")' "$file_path" 2>/dev/null)
    if [ "$has_user" != "true" ]; then
        warnings+=("gitConfig: No user section specified")
    else
        local user_name=$(jq -r '.user.name' "$file_path" 2>/dev/null)
        local user_email=$(jq -r '.user.email' "$file_path" 2>/dev/null)
        
        if [ -z "$user_name" ] || [ "$user_name" = "null" ]; then
            warnings+=("gitConfig: Missing user.name")
        fi
        if [ -z "$user_email" ] || [ "$user_email" = "null" ]; then
            warnings+=("gitConfig: Missing user.email")
        fi
    fi
}

# Validate all config files
echo -e "${yellow}Validating JSON files...${nc}"
echo ""

# Apps configs
if validateJsonFile "$configsPath/macosApps.json" "macosApps.json"; then
    validateAppsJson "$configsPath/macosApps.json" "macos"
fi

if validateJsonFile "$configsPath/ubuntuApps.json" "ubuntuApps.json"; then
    validateAppsJson "$configsPath/ubuntuApps.json" "ubuntu"
fi

# Other configs
if validateJsonFile "$configsPath/fonts.json" "fonts.json"; then
    local font_count=$(jq '.googleFonts | length' "$configsPath/fonts.json" 2>/dev/null || echo "0")
    if [ "$font_count" = "0" ]; then
        warnings+=("fonts: No fonts specified")
    fi
fi

if validateJsonFile "$configsPath/repositories.json" "repositories.json"; then
    validateRepositoriesJson "$configsPath/repositories.json"
fi

if validateJsonFile "$configsPath/gitConfig.json" "gitConfig.json"; then
    validateGitConfigJson "$configsPath/gitConfig.json"
fi

if validateJsonFile "$configsPath/cursorSettings.json" "cursorSettings.json"; then
    echo -e "  ${green}✓ cursorSettings.json structure valid${nc}"
fi

echo ""

# Report results
if [ ${#errors[@]} -eq 0 ] && [ ${#warnings[@]} -eq 0 ]; then
    echo -e "${green}✓ All configuration files are valid!${nc}"
    exit 0
else
    if [ ${#warnings[@]} -gt 0 ]; then
        echo -e "${yellow}Warnings:${nc}"
        for warning in "${warnings[@]}"; do
            echo -e "  ⚠ $warning"
        done
        echo ""
    fi
    
    if [ ${#errors[@]} -gt 0 ]; then
        echo -e "${red}Errors:${nc}"
        for error in "${errors[@]}"; do
            echo -e "  ✗ $error"
        done
        echo ""
        echo -e "${red}✗ Validation failed. Please fix errors before running setup.${nc}"
        exit 1
    else
        echo -e "${green}✓ Validation passed with warnings.${nc}"
        exit 0
    fi
fi

