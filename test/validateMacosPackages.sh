#!/bin/bash
# Enhanced validation for macOS packages
# Checks if brew and brewCask packages actually exist

# Source all core tools (singular entry point)
# shellcheck source=../common/core/tools.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/core/tools.sh"

validateMacosPackages()
{
    local configPath=$1
    local errors=0

    if [ ! -f "$configPath" ]; then
        logError "Config file not found: $configPath"
        return 1
    fi

    logSection "Validating macOS Packages"
    echo ""

    # Check if brew is available
    if ! command -v brew >/dev/null 2>&1; then
        logError "Homebrew is not installed. Cannot validate packages."
        logNote "Install with: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        return 1
    fi

    # Validate brew packages
    local brewPackages
    brewPackages=$(jq -r '.brew[]?' "$configPath" 2>/dev/null || echo "")

    if [ -n "$brewPackages" ]; then
        logNote "Validating brew packages..."
        while IFS= read -r package; do
            if [ -z "$package" ]; then
                continue
            fi

            # Check if package exists in brew
            # Suppress brew's informational messages (like "already installed", "already up-to-date")
            # brew info returns 0 if package exists, non-zero if not
            if brew info "$package" 2>&1 | grep -vE "(is already installed|already up-to-date|To reinstall)" | grep -qE "(^$package:|^==>|^From:)"; then
                logSuccess "  $package"
            else
                # Double-check with exit code (brew info returns non-zero if package doesn't exist)
                if brew info "$package" &>/dev/null 2>&1; then
                    logSuccess "  $package"
                else
                    logError "  $package (not found in brew)"
                    ((errors++))
                fi
            fi

        done <<< "$brewPackages"
        echo ""
    fi

    # Validate brewCask packages
    local caskPackages
    caskPackages=$(jq -r '.brewCask[]?' "$configPath" 2>/dev/null || echo "")

    if [ -n "$caskPackages" ]; then
        logNote "Validating brew cask packages..."
        while IFS= read -r package; do
            if [ -z "$package" ]; then
                continue
            fi

            # Check if cask exists in brew
            # Suppress brew's informational messages (like "already installed", "already up-to-date")
            # brew info returns 0 if package exists, non-zero if not
            if brew info --cask "$package" 2>&1 | grep -vE "(is already installed|already up-to-date|To reinstall)" | grep -qE "(^$package:|^==>|^From:)"; then
                logSuccess "  $package"
            else
                # Double-check with exit code (brew info returns non-zero if package doesn't exist)
                if brew info --cask "$package" &>/dev/null 2>&1; then
                    logSuccess "  $package"
                else
                    logError "  $package (not found in brew cask)"
                    ((errors++))
                fi
            fi
        done <<< "$caskPackages"
        echo ""
    fi

    if [ $errors -eq 0 ]; then
        logSuccess "All macOS packages are valid!"
        return 0
    else
        logError "Found $errors invalid package(s)"
        return 1
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [ $# -eq 0 ]; then
        logError "Usage: $0 <path-to-macos.json>"
        exit 1
    fi
    startTime=$SECONDS
    validateMacosPackages "$1"
    exitCode=$?
    elapsed=$((SECONDS - startTime))
    echo ""
    logNote "Validation completed in ${elapsed}s"
    exit $exitCode
fi
