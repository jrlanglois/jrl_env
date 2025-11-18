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
            # shellcheck disable=SC2016 # We want to match literal $HOME/$USER, not expand variables
            if echo "$workPathUnix" | grep -qE '^[~/]|^\$HOME|^\$USER'; then
                logSuccess "  workPathUnix: $workPathUnix"
            else
                logError "  workPathUnix: $workPathUnix (should start with ~, /, \$HOME, or \$USER)"
                ((errors++))
            fi
        fi

        # Validate Windows path syntax
        if [ -n "$workPathWindows" ] && [ "$workPathWindows" != "null" ]; then
            # Check for valid Windows path (drive letter or UNC)
            # shellcheck disable=SC2016 # We want to match literal $USERPROFILE/$HOME, not expand variables
            if echo "$workPathWindows" | grep -qE '^[A-Za-z]:|^\\\\|^\$USERPROFILE|^\$HOME'; then
                logSuccess "  workPathWindows: $workPathWindows"
            else
                logError "  workPathWindows: $workPathWindows (should start with drive letter, \\\\, \$USERPROFILE, or \$HOME)"
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
        echo "  Checking: $repoUrl"

        # Validate URL format
        if echo "$repoUrl" | grep -qE '^(https?|git)://|^git@'; then
            # Convert SSH URL to HTTPS for validation (if it's a GitHub URL)
            local checkUrl="$repoUrl"
            if echo "$repoUrl" | grep -qE '^git@github\.com:'; then
                # Convert git@github.com:owner/repo.git to https://github.com/owner/repo.git
                checkUrl=$(echo "$repoUrl" | sed 's|git@github\.com:|https://github.com/|' | sed 's|\.git$||')
            elif echo "$repoUrl" | grep -qE '^git@'; then
                # For other SSH URLs, we can't easily validate without SSH keys
                # Just validate the format and skip existence check
                logWarning "    SSH URL detected - cannot validate without SSH keys (format is valid)"
                continue
            fi

            # Try to check if repository exists (with timeout)
            # Use curl to check if the HTTPS URL is accessible
            if echo "$checkUrl" | grep -qE '^https://github\.com/'; then
                # Check GitHub repository via API (no auth needed for public repos)
                local ownerRepo
                ownerRepo="${checkUrl#https://github.com/}"
                local httpCode
                local apiResponse
                apiResponse=$(curl -s --max-time 10 -w "\n%{http_code}" "https://api.github.com/repos/$ownerRepo" 2>/dev/null)
                httpCode=$(echo "$apiResponse" | tail -n1)

                if [ "$httpCode" = "200" ]; then
                    logSuccess "    Repository exists"
                elif [ "$httpCode" = "404" ]; then
                    # Check if it's actually a 404 or if the repo might be private
                    # Private repos also return 404 without auth, so we can't distinguish
                    logWarning "    Repository not found or is private (404) - will be validated at clone time"
                    # Don't count as error since it might be a private repo
                elif [ "$httpCode" = "403" ]; then
                    logWarning "    Repository access forbidden (403) - may be private or rate limited"
                    # Don't count as error
                elif [ -z "$httpCode" ] || [ "$httpCode" = "000" ]; then
                    logWarning "    Could not reach GitHub API - network issue or timeout"
                    # Don't count as error
                else
                    logWarning "    Unexpected response (HTTP $httpCode) - repository may be private"
                    # Don't count as error
                fi
            elif timeout 10 git ls-remote "$checkUrl" &>/dev/null; then
                logSuccess "    Repository exists"
            else
                logError "    Repository not accessible or does not exist"
                ((errors++))
            fi
        else
            logError "    Invalid repository URL format"
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
    startTime=$SECONDS
    validateRepositories "$1"
    exitCode=$?
    elapsed=$((SECONDS - startTime))
    echo ""
    logNote "Validation completed in ${elapsed}s"
    exit $exitCode
fi
