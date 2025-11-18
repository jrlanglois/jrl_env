#!/bin/bash
# Enhanced validation for Windows packages
# Checks if winget packages actually exist
# Note: This script requires winget to be available (typically on Windows)

# Source all core tools (singular entry point)
# shellcheck source=../common/core/tools.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/core/tools.sh"

validateWindowsPackages()
{
    local configPath=$1
    local errors=0

    if [ ! -f "$configPath" ]; then
        logError "Config file not found: $configPath"
        return 1
    fi

    logSection "Validating Windows Packages"
    echo ""

    # Check if winget is available
    if ! command -v winget >/dev/null 2>&1; then
        logError "winget is not available. Cannot validate packages."
        logNote "winget is typically available on Windows 10/11"
        return 1
    fi

    # Validate winget packages
    local wingetPackages
    wingetPackages=$(jq -r '.winget[]?' "$configPath" 2>/dev/null || echo "")

    if [ -n "$wingetPackages" ]; then
        logNote "Validating winget packages..."
        while IFS= read -r package; do
            if [ -z "$package" ]; then
                continue
            fi

            # Check if package exists in winget
            # Try multiple methods for better reliability across different environments
            local found=false

            # Method 1: winget show (most reliable, but may fail in CI if sources aren't updated)
            if winget show --id "$package" &>/dev/null 2>&1; then
                found=true
            # Method 2: winget search with exact ID match (fallback - works even if sources need update)
            elif winget search --id "$package" --exact 2>/dev/null | grep -qE "[[:space:]]${package}[[:space:]]"; then
                found=true
            # Method 3: winget search without exact flag (last resort - may match similar packages)
            elif winget search "$package" 2>/dev/null | head -5 | grep -qE "[[:space:]]${package}[[:space:]]"; then
                found=true
            fi

            if [ "$found" = true ]; then
                logSuccess "  $package"
            else
                logError "  $package (not found in winget)"
                ((errors++))
            fi
        done <<< "$wingetPackages"
        echo ""
    fi

    if [ $errors -eq 0 ]; then
        logSuccess "All Windows packages are valid!"
        return 0
    else
        logError "Found $errors invalid package(s)"
        return 1
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [ $# -eq 0 ]; then
        logError "Usage: $0 <path-to-win11.json>"
        exit 1
    fi
    validateWindowsPackages "$1"
    exit $?
fi
