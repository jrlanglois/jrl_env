#!/bin/bash
# Generic utility functions for Bash scripts

# Source a file if it exists, otherwise echo an error
sourceIfExists()
{
    local filePath="$1"
    if [ -f "$filePath" ]; then
        # shellcheck source=/dev/null
        source "$filePath"
        return 0
    else
        echo "Error: File not found: $filePath" >&2
        return 1
    fi
}

# Check if a command exists
commandExists()
{
    command -v "$1" >/dev/null 2>&1
}

# Require a command to be available, show install hint if missing
# Returns 0 if command exists, 1 otherwise
requireCommand()
{
    local cmd=$1
    local installHint=$2

    if commandExists "$cmd"; then
        return 0
    fi

    # Use logging functions if available, otherwise use echo
    if commandExists logError; then
        logError "Required command '$cmd' not found."
        if [ -n "$installHint" ]; then
            logNote "  $installHint"
        fi
    else
        echo "Error: Required command '$cmd' not found." >&2
        if [ -n "$installHint" ]; then
            echo "  $installHint" >&2
        fi
    fi
    return 1
}

# Get a JSON value from a file
# Usage: getJsonValue configPath jsonPath defaultValue
getJsonValue()
{
    local configPath="$1"
    local jsonPath="$2"
    local defaultValue="${3:-}"

    if [ ! -f "$configPath" ]; then
        echo "$defaultValue"
        return 1
    fi

    if ! commandExists jq; then
        echo "$defaultValue"
        return 1
    fi

    jq -r "$jsonPath // \"$defaultValue\"" "$configPath" 2>/dev/null || echo "$defaultValue"
}

# Get a JSON array from a file
# Usage: getJsonArray configPath jsonPath
getJsonArray()
{
    local configPath="$1"
    local jsonPath="$2"

    if [ ! -f "$configPath" ]; then
        return 1
    fi

    if ! commandExists jq; then
        return 1
    fi

    jq -r "$jsonPath // [] | .[]?" "$configPath" 2>/dev/null || echo ""
}

# Get a JSON object as compact JSON
# Usage: getJsonObject configPath jsonPath
getJsonObject()
{
    local configPath="$1"
    local jsonPath="$2"

    if [ ! -f "$configPath" ]; then
        return 1
    fi

    if ! commandExists jq; then
        return 1
    fi

    jq -c "$jsonPath // {}" "$configPath" 2>/dev/null || echo "{}"
}

# Require jq to be available, show install hint if missing
# Returns 0 if jq exists, 1 otherwise
requireJq()
{
    local installHint="${1:-Please install jq via your package manager.}"
    requireCommand jq "$installHint"
}

# Add colours to the script
sourceIfExists "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/colours.sh"
