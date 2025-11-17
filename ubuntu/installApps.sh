#!/bin/bash
# Ubuntu wrapper for shared application installation logic

set -e

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
appsConfigPath="${scriptDir}/../configs/ubuntuApps.json"
jqInstallHint="${yellow}  sudo apt-get install -y jq${nc}"

# shellcheck source=../common/colors.sh
source "$scriptDir/../common/colors.sh"

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
source "$scriptDir/../common/installApps.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    installApps "$@"
fi
