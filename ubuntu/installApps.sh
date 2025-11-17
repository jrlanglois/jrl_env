#!/bin/bash
# Ubuntu wrapper for shared application installation logic
# Reads from ubuntu.json configuration file

set -e

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../common/colors.sh
source "$scriptDir/../common/colors.sh"

appsConfigPath="${scriptDir}/../configs/ubuntu.json"
jqInstallHint="${yellow}  sudo apt-get install -y jq${nc}"

commandExists()
{
    command -v "$1" >/dev/null 2>&1
}

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

removeCruftPackages()
{
    if [ ! -f "$appsConfigPath" ]; then
        return 0
    fi

    if ! commandExists jq; then
        echo -e "${yellow}⚠ jq not available; skipping cruft removal.${nc}"
        return 0
    fi

    local cruftPackages
    cruftPackages=$(jq -r '.cruft[]?' "$appsConfigPath" 2>/dev/null || echo "")

    if [ -z "$cruftPackages" ]; then
        return 0
    fi

    echo -e "${yellow}Removing unwanted packages...${nc}"
    local removedCount=0
    local skippedCount=0

    while IFS= read -r packagePattern; do
        if [ -z "$packagePattern" ]; then
            continue
        fi

        if sudo apt-get remove -y --purge "$packagePattern" &>/dev/null; then
            echo -e "  ${green}✓ Removed: $packagePattern${nc}"
            ((removedCount++))
        else
            echo -e "  ${yellow}⚠ Could not remove (maybe absent): $packagePattern${nc}"
            ((skippedCount++))
        fi
    done <<< "$cruftPackages"

    if [ $removedCount -gt 0 ]; then
        sudo apt-get autoremove -y &>/dev/null || true
        sudo apt-get autoclean -y &>/dev/null || true
    fi

    echo -e "${cyan}Removal summary:${nc}"
    echo -e "  ${green}Removed: $removedCount pattern(s)${nc}"
    if [ $skippedCount -gt 0 ]; then
        echo -e "  ${yellow}Skipped (missing): $skippedCount pattern(s)${nc}"
    fi
    echo ""
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    installApps "$@"
    removeCruftPackages
fi
