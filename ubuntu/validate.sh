#!/bin/bash
# Script to validate JSON configuration files
# Checks syntax, required fields, and basic validity
# shellcheck disable=SC2154 # Colour variables come from sourced colours.sh

set -e

# Source all core tools (singular entry point)
# shellcheck source=../common/core/tools.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/core/tools.sh"

configsPath="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../configs"

errors=()
warnings=()

logSection "Validating Configuration Files"
echo ""

# Check if jq is available
if ! command -v jq >/dev/null 2>&1; then
    logError "jq is required for validation. Please install it first."
    logNote "  sudo apt-get install -y jq"
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
        logSuccess "$description"
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
logNote "Validating JSON files..."
echo ""

# Apps configs
if validateJsonFile "$configsPath/macos.json" "macos.json"; then
    validateAppsJson "$configsPath/macos.json" "macos"
fi

if validateJsonFile "$configsPath/ubuntu.json" "ubuntu.json"; then
    validateAppsJson "$configsPath/ubuntu.json" "ubuntu"
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
    logSuccess "cursorSettings.json structure valid"
fi

echo ""

# Report results
if [ ${#errors[@]} -eq 0 ] && [ ${#warnings[@]} -eq 0 ]; then
    logSuccess "All configuration files are valid!"
    exit 0
else
    if [ ${#warnings[@]} -gt 0 ]; then
        logWarning "Warnings:"
        for warning in "${warnings[@]}"; do
            echo "  ⚠ $warning"
        done
        echo ""
    fi

    if [ ${#errors[@]} -gt 0 ]; then
        logError "Errors:"
        for error in "${errors[@]}"; do
            echo "  ✗ $error"
        done
        echo ""
        logError "Validation failed. Please fix errors before running setup."
        exit 1
    else
        logSuccess "Validation passed with warnings."
        exit 0
    fi
fi
