#!/bin/bash
# Ubuntu wrapper for shared application installation logic
# Reads from ubuntu.json configuration file
# shellcheck disable=SC2034 # Variables are used by sourced common scripts

set -e

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../helpers/utilities.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$scriptDir/../helpers/utilities.sh"
# shellcheck source=../common/colours.sh
sourceIfExists "$scriptDir/../common/colours.sh"

appsConfigPath="${scriptDir}/../configs/ubuntu.json"
jqInstallHint="  sudo apt-get install -y jq"

installApps_checkPrimary()
{
    dpkg -l | grep -q "^ii  $1 "
}

installApps_installPrimary()
{
    sudo apt-get install -y "$1" &>/dev/null
}

installApps_updatePrimary()
{
    sudo apt-get install --only-upgrade -y "$1" &>/dev/null
}

installApps_checkSecondary()
{
    snap list "$1" &>/dev/null 2>&1
}

installApps_installSecondary()
{
    sudo snap install "$1" &>/dev/null
}

installApps_updateSecondary()
{
    sudo snap refresh "$1" &>/dev/null
}

installApps_extractPrimary='.apt[]?'
installApps_extractSecondary='.snap[]?'

# shellcheck source=../common/installApps.sh
sourceIfExists "$scriptDir/../common/installApps.sh"

removeCruftPackages()
{
    if [ ! -f "$appsConfigPath" ]; then
        return 0
    fi

    local jqHint="${jqInstallHint:-Please install jq via your package manager.}"
    if ! requireJq "$jqHint"; then
        logWarning "jq not available; skipping cruft removal."
        return 0
    fi

    local cruftPackages
    cruftPackages=$(getJsonArray "$appsConfigPath" ".cruft[]?")

    if [ -z "$cruftPackages" ]; then
        return 0
    fi

    logNote "Removing unwanted packages..."
    local removedCount=0
    local skippedCount=0

    while IFS= read -r packagePattern; do
        if [ -z "$packagePattern" ]; then
            continue
        fi

        if sudo apt-get remove -y --purge "$packagePattern" &>/dev/null; then
            logSuccess "  Removed: $packagePattern"
            ((removedCount++))
        else
            logWarning "  Could not remove (maybe absent): $packagePattern"
            ((skippedCount++))
        fi
    done <<< "$cruftPackages"

    if [ $removedCount -gt 0 ]; then
        sudo apt-get autoremove -y &>/dev/null || true
        sudo apt-get autoclean -y &>/dev/null || true
    fi

    logInfo "Removal summary:"
    logSuccess "  Removed: $removedCount pattern(s)"
    if [ $skippedCount -gt 0 ]; then
        logNote "  Skipped (missing): $skippedCount pattern(s)"
    fi
    echo ""
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    runConfigCommands "preInstall"
    installApps "$@"
    runConfigCommands "postInstall"
    removeCruftPackages
fi
