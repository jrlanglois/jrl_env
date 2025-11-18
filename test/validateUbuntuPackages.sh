#!/bin/bash
# Enhanced validation for Ubuntu packages
# Checks if apt and snap packages actually exist

# Source all core tools (singular entry point)
# shellcheck source=../common/core/tools.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/core/tools.sh"

validateUbuntuPackages()
{
    local configPath=$1
    local errors=0

    if [ ! -f "$configPath" ]; then
        logError "Config file not found: $configPath"
        return 1
    fi

    logSection "Validating Ubuntu Packages"
    echo ""

    # Validate apt packages
    local aptPackages
    aptPackages=$(jq -r '.apt[]?' "$configPath" 2>/dev/null || echo "")

    if [ -n "$aptPackages" ]; then
        logNote "Validating apt packages..."
        # Update package list first (non-interactive)
        if command -v apt-cache >/dev/null 2>&1; then
            while IFS= read -r package; do
                if [ -z "$package" ]; then
                    continue
                fi

                # Check if package exists in apt
                if apt-cache show "$package" &>/dev/null; then
                    logSuccess "  ✓ $package"
                else
                    logError "  ✗ $package (not found in apt)"
                    ((errors++))
                fi
            done <<< "$aptPackages"
        else
            logWarning "apt-cache not available, skipping apt package validation"
        fi
        echo ""
    fi

    # Validate snap packages
    local snapPackages
    snapPackages=$(jq -r '.snap[]?' "$configPath" 2>/dev/null || echo "")

    if [ -n "$snapPackages" ]; then
        logNote "Validating snap packages..."
        if command -v snap >/dev/null 2>&1; then
            while IFS= read -r package; do
                if [ -z "$package" ]; then
                    continue
                fi

                # Check if package exists in snap
                if snap info "$package" &>/dev/null; then
                    logSuccess "  ✓ $package"
                else
                    logError "  ✗ $package (not found in snap)"
                    ((errors++))
                fi
            done <<< "$snapPackages"
        else
            logWarning "snap not available, skipping snap package validation"
        fi
        echo ""
    fi

    if [ $errors -eq 0 ]; then
        logSuccess "All Ubuntu packages are valid!"
        return 0
    else
        logError "Found $errors invalid package(s)"
        return 1
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [ $# -eq 0 ]; then
        logError "Usage: $0 <path-to-ubuntu.json>"
        exit 1
    fi
    validateUbuntuPackages "$1"
    exit $?
fi
