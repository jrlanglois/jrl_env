#!/bin/bash
# Script to install applications on macOS using Homebrew
# Reads from macos.json configuration file
# shellcheck disable=SC2034 # Variables are used by sourced common scripts

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../helpers/utilities.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$scriptDir/../helpers/utilities.sh"
# shellcheck source=../common/colours.sh
sourceIfExists "$scriptDir/../common/colours.sh"

appsConfigPath="${scriptDir}/../configs/macos.json"
jqInstallHint="  brew install jq"

installApps_checkPrimary()
{
    brew list "$1" &>/dev/null
}

installApps_installPrimary()
{
    brew install "$1" &>/dev/null
}

installApps_updatePrimary()
{
    brew upgrade "$1" &>/dev/null
}

installApps_checkSecondary()
{
    brew list --cask "$1" &>/dev/null
}

installApps_installSecondary()
{
    brew install --cask "$1" &>/dev/null
}

installApps_updateSecondary()
{
    brew upgrade --cask "$1" &>/dev/null
}

installApps_extractPrimary='.brew[]?'
installApps_extractSecondary='.brewCask[]?'

# shellcheck source=../common/installApps.sh
sourceIfExists "$scriptDir/../common/installApps.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    runConfigCommands "preInstall"
    installApps "$@"
    runConfigCommands "postInstall"
fi
