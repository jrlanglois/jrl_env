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
validateJsonFile()
{
    local filePath=$1
    local description=$2

    if [ ! -f "$filePath" ]; then
        errors+=("$description: File not found: $filePath")
        return 1
    fi

    if jq empty "$filePath" 2>/dev/null; then
        echo -e "${green}✓ $description${nc}"
        return 0
    else
        errors+=("$description: Invalid JSON")
        return 1
    fi
}

# Function to validate apps JSON
validateAppsJson()
{
    local filePath=$1
    local platform=$2
    local brewCount
    local caskCount
    local aptCount
    local snapCount

    if [ "$platform" = "macos" ]; then
        brewCount=$(jq '.brew | length' "$filePath" 2>/dev/null || echo "0")
        caskCount=$(jq '.brewCask | length' "$filePath" 2>/dev/null || echo "0")

        if [ "$brewCount" = "0" ] && [ "$caskCount" = "0" ]; then
            warnings+=("$platform apps: No apps specified")
        fi
    elif [ "$platform" = "ubuntu" ]; then
        aptCount=$(jq '.apt | length' "$filePath" 2>/dev/null || echo "0")
        snapCount=$(jq '.snap | length' "$filePath" 2>/dev/null || echo "0")

        if [ "$aptCount" = "0" ] && [ "$snapCount" = "0" ]; then
            warnings+=("$platform apps: No apps specified")
        fi
    fi
}

# Function to validate repositories JSON
validateRepositoriesJson()
{
    local filePath=$1
    local workPathWin
    local workPathUnix
    local repoCount

    workPathWin=$(jq -r '.workPathWindows' "$filePath" 2>/dev/null)
    workPathUnix=$(jq -r '.workPathUnix' "$filePath" 2>/dev/null)

    if [ -z "$workPathWin" ] || [ "$workPathWin" = "null" ]; then
        if [ -z "$workPathUnix" ] || [ "$workPathUnix" = "null" ]; then
            errors+=("repositories: Missing workPathWindows or workPathUnix")
        fi
    fi

    repoCount=$(jq '.repositories | length' "$filePath" 2>/dev/null || echo "0")
    if [ "$repoCount" = "0" ]; then
        warnings+=("repositories: No repositories specified")
    fi
}

# Function to validate Git config JSON
validateGitConfigJson()
{
    local filePath=$1
    local hasUser
    local userName
    local userEmail

    hasUser=$(jq 'has("user")' "$filePath" 2>/dev/null)
    if [ "$hasUser" != "true" ]; then
        warnings+=("gitConfig: No user section specified")
    else
        userName=$(jq -r '.user.name' "$filePath" 2>/dev/null)
        userEmail=$(jq -r '.user.email' "$filePath" 2>/dev/null)

        if [ -z "$userName" ] || [ "$userName" = "null" ]; then
            warnings+=("gitConfig: Missing user.name")
        fi
        if [ -z "$userEmail" ] || [ "$userEmail" = "null" ]; then
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
    fontCount=$(jq '.googleFonts | length' "$configsPath/fonts.json" 2>/dev/null || echo "0")
    if [ "$fontCount" = "0" ]; then
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
