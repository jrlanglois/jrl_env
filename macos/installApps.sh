#!/bin/bash
# Script to install applications on macOS using Homebrew
# Reads from macosApps.json configuration file

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../common/colors.sh
source "$scriptDir/../common/colors.sh"
configPath="${scriptDir}/../configs/macosApps.json"

# Function to check if a command exists
commandExists()
{
    command -v "$1" >/dev/null 2>&1
}

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
appsConfigPath="${scriptDir}/../configs/macosApps.json"
jqInstallHint="${yellow}  brew install jq${nc}"

# shellcheck source=../common/colors.sh
source "$scriptDir/../common/colors.sh"

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
source "$scriptDir/../common/installApps.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    installApps "$@"
fi
