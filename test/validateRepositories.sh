#!/bin/bash
# Enhanced validation for repositories config
# Checks if repositories exist and validates work paths

# Source all core tools (singular entry point)
# shellcheck source=../common/core/tools.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/core/tools.sh"

validateRepositories()
{
    local configPath=$1
    local errors=0

    if [ ! -f "$configPath" ]; then
        logError "Config file not found: $configPath"
        return 1
    fi

    logSection "Validating Repositories Config"
    echo ""

    # Check if jq is available
    if ! command -v jq >/dev/null 2>&1; then
        logError "jq is required for validation"
        return 1
    fi

    # Validate JSON syntax
    if ! jq empty "$configPath" 2>/dev/null; then
        logError "Invalid JSON syntax"
        return 1
    fi

    # Validate work paths
    logNote "Validating work paths..."
    local workPathUnix
    local workPathWindows

    workPathUnix=$(jq -r '.workPathUnix // empty' "$configPath" 2>/dev/null)
    workPathWindows=$(jq -r '.workPathWindows // empty' "$configPath" 2>/dev/null)

    if [ -z "$workPathUnix" ] && [ -z "$workPathWindows" ]; then
        logError "Missing workPathUnix or workPathWindows"
        ((errors++))
    else
        # Validate Unix path syntax
        if [ -n "$workPathUnix" ] && [ "$workPathUnix" != "null" ]; then
            # Check for valid path characters (basic validation)
            if echo "$workPathUnix" | grep -qE '^[~/]|^\$HOME|^\$USER'; then
                logSuccess "  ✓ workPathUnix: $workPathUnix"
            else
                logError "  ✗ workPathUnix: $workPathUnix (should start with ~, /, \$HOME, or \$USER)"
                ((errors++))
            fi
        fi

        # Validate Windows path syntax
        if [ -n "$workPathWindows" ] && [ "$workPathWindows" != "null" ]; then
            # Check for valid Windows path (drive letter or UNC)
            if echo "$workPathWindows" | grep -qE '^[A-Za-z]:|^\\\\|^\$USERPROFILE|^\$HOME'; then
                logSuccess "  ✓ workPathWindows: $workPathWindows"
            else
                logError "  ✗ workPathWindows: $workPathWindows (should start with drive letter, \\\\, \$USERPROFILE, or \$HOME)"
                ((errors++))
            fi
        fi
    fi
    echo ""

    # Validate repositories
    logNote "Validating repositories..."
    local repositories
    repositories=$(jq -r '.repositories[]?' "$configPath" 2>/dev/null || echo "")

    if [ -z "$repositories" ]; then
        logWarning "No repositories specified"
        return 0
    fi

    # Check if git is available
    if ! command -v git >/dev/null 2>&1; then
        logWarning "git is not available. Cannot validate repository existence."
        logNote "Repositories will be validated at clone time."
        return 0
    fi

    local repoCount=0
    while IFS= read -r repoUrl; do
        if [ -z "$repoUrl" ]; then
            continue
        fi

        ((repoCount++))
        logNote "  Checking: $repoUrl"

        # Validate URL format
        if echo "$repoUrl" | grep -qE '^(https?|git)://|^git@'; then
            # Try to check if repository exists (with timeout)
            if timeout 10 git ls-remote "$repoUrl" &>/dev/null; then
                logSuccess "    ✓ Repository exists"
            else
                logError "    ✗ Repository not accessible or does not exist"
                ((errors++))
            fi
        else
            logError "    ✗ Invalid repository URL format"
            ((errors++))
        fi
    done <<< "$repositories"

    echo ""
    logInfo "Checked $repoCount repository/repositories"

    if [ $errors -eq 0 ]; then
        logSuccess "All repositories are valid!"
        return 0
    else
        logError "Found $errors validation error(s)"
        return 1
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [ $# -eq 0 ]; then
        logError "Usage: $0 <path-to-repositories.json>"
        exit 1
    fi
    validateRepositories "$1"
    exit $?
fi
