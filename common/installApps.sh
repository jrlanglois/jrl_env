#!/bin/bash
# Shared application installation logic

# shellcheck disable=SC2154 # colours supplied by wrappers

# Source utilities and logging functions (utilities must be direct source)
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../helpers/utilities.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$scriptDir/../helpers/utilities.sh"
# shellcheck source=../helpers/logging.sh
sourceIfExists "$scriptDir/../helpers/logging.sh"

installPackages()
{
    local packageList=$1
    local checkFunction=$2
    local installFunction=$3
    local updateFunction=$4
    local label=$5
    local installedCount=0
    local updatedCount=0
    local failedCount=0

    if [ -z "$packageList" ]; then
        return 0
    fi

    logSection "Processing ${label}"
    echo ""

    while IFS= read -r packageName; do
        if [ -z "$packageName" ]; then
            continue
        fi

        logNote "Processing: $packageName"

        if "$checkFunction" "$packageName"; then
            logInfo "  Already installed. Updating..."
            if "$updateFunction" "$packageName"; then
                logSuccess "  Updated successfully"
                ((updatedCount++))
            else
                logWarning "  Update check completed (may already be up to date)"
                ((updatedCount++))
            fi
        else
            logInfo "  Not installed. Installing..."
            if "$installFunction" "$packageName"; then
                logSuccess "  Installed successfully"
                ((installedCount++))
            else
                logError "  Installation failed"
                ((failedCount++))
            fi
        fi
        echo ""
    done <<< "$packageList"

    installPackages_installedCount=$installedCount
    installPackages_updatedCount=$updatedCount
    installPackages_failedCount=$failedCount
}

installFromConfig()
{
    local configPath=${1:-$appsConfigPath}
    local packageExtractor=$2
    local packageLabel=$3
    local checkFunction=$4
    local installFunction=$5
    local updateFunction=$6

    local packages
    packages=$(getJsonArray "$configPath" "$packageExtractor")

    installPackages "$packages" "$checkFunction" "$installFunction" "$updateFunction" "$packageLabel"

    local installed=$installPackages_installedCount
    local updated=$installPackages_updatedCount
    local failed=$installPackages_failedCount

    installFromConfig_installed=$installed
    installFromConfig_updated=$updated
    installFromConfig_failed=$failed
}

installApps()
{
    local configPath=${1:-$appsConfigPath}
    local jqHint="${jqInstallHint:-Please install jq via your package manager.}"

    if [ ! -f "$configPath" ]; then
        logError "Configuration file not found: $configPath"
        return 1
    fi

    if ! requireJq "$jqHint"; then
        return 1
    fi

    logSection "Application Installation"
    echo ""

    local totalInstalled=0
    local totalUpdated=0
    local totalFailed=0

    installFromConfig "$configPath" "${installApps_extractPrimary:-.brew[]?}" "Primary packages" installApps_checkPrimary installApps_installPrimary installApps_updatePrimary
    totalInstalled=$((totalInstalled + installFromConfig_installed))
    totalUpdated=$((totalUpdated + installFromConfig_updated))
    totalFailed=$((totalFailed + installFromConfig_failed))

    installFromConfig "$configPath" "${installApps_extractSecondary:-.brewCask[]?}" "Secondary packages" installApps_checkSecondary installApps_installSecondary installApps_updateSecondary
    totalInstalled=$((totalInstalled + installFromConfig_installed))
    totalUpdated=$((totalUpdated + installFromConfig_updated))
    totalFailed=$((totalFailed + installFromConfig_failed))

    logInfo "Summary:"
    logSuccess "  Installed: $totalInstalled"
    logSuccess "  Updated: $totalUpdated"
    if [ $totalFailed -gt 0 ]; then
        logError "  Failed: $totalFailed"
    fi

    return 0
}

# Parse a command JSON object into variables
# Sets: cmdName, cmdShell, cmdCommand, cmdRunOnce
parseCommandJson()
{
    local cmdJson="$1"
    cmdName=$(echo "$cmdJson" | jq -r '.name // "command"' 2>/dev/null)
    cmdShell=$(echo "$cmdJson" | jq -r '.shell // "bash"' 2>/dev/null)
    cmdCommand=$(echo "$cmdJson" | jq -r '.command // ""' 2>/dev/null)
    cmdRunOnce=$(echo "$cmdJson" | jq -r '.runOnce // false' 2>/dev/null)
}

# Get the flag file path for a run-once command
getCommandFlagFile()
{
    local phase="$1"
    local name="$2"
    local cacheDir="$HOME/.cache/jrl_env/commands"
    mkdir -p "$cacheDir"
    local safeName
    safeName=$(echo "${phase}_${name}" | tr -cs '[:alnum:]_' '_')
    echo "${cacheDir}/${safeName}.flag"
}

# Check if a run-once command has already been executed
isCommandAlreadyRun()
{
    local flagFile="$1"
    [ -f "$flagFile" ]
}

# Mark a run-once command as executed
markCommandAsRun()
{
    local flagFile="$1"
    touch "$flagFile"
}

# Execute a single command from the config
executeConfigCommand()
{
    local phase="$1"
    local cmdJson="$2"
    local configPath="${3:-$appsConfigPath}"

    [ -z "$cmdJson" ] && return 0

    local cmdName cmdShell cmdCommand cmdRunOnce
    parseCommandJson "$cmdJson"

    if [ -z "$cmdCommand" ] || [ "$cmdCommand" = "null" ]; then
        return 0
    fi

    local flagFile
    flagFile=$(getCommandFlagFile "$phase" "$cmdName")

    if [ "$cmdRunOnce" = "true" ] && isCommandAlreadyRun "$flagFile"; then
        logWarning "Skipping $cmdName (run once already executed)."
        return 0
    fi

    if ! commandExists "$cmdShell"; then
        logError "Command shell '$cmdShell' not available for $cmdName."
        return 1
    fi

    logInfo "Running $cmdName..."
    if "$cmdShell" -lc "$cmdCommand"; then
        logSuccess "$cmdName completed"
        if [ "$cmdRunOnce" = "true" ]; then
            markCommandAsRun "$flagFile"
        fi
        return 0
    else
        logError "$cmdName failed"
        return 1
    fi
}

# Run commands from a specific phase (preInstall/postInstall)
runConfigCommands()
{
    local phase="$1"
    local configPath="${2:-$appsConfigPath}"
    local jqHint="${jqInstallHint:-Please install jq via your package manager.}"

    if [ ! -f "$configPath" ]; then
        return 0
    fi

    if ! requireJq "$jqHint"; then
        logWarning "jq is not available; skipping ${phase} commands."
        return 0
    fi

    local cmdJsonList
    cmdJsonList=$(jq -c --arg phase "$phase" '.commands[$phase] // [] | .[]' "$configPath" 2>/dev/null)

    if [ -z "$cmdJsonList" ]; then
        return 0
    fi

    while IFS= read -r cmdJson; do
        executeConfigCommand "$phase" "$cmdJson" "$configPath"
    done <<< "$cmdJsonList"
}
