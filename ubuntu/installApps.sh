#!/bin/bash
# Ubuntu wrapper for shared application installation logic
# Reads from ubuntu.json configuration file

set -e

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../common/colours.sh
source "$scriptDir/../common/colours.sh"

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

runConfigCommands()
{
    local phase=$1

    if [ ! -f "$appsConfigPath" ]; then
        return
    fi

    if ! commandExists jq; then
        echo -e "${yellow}⚠ jq is not available; skipping ${phase} commands.${nc}"
        return
    fi

    local cmdJsonList
    cmdJsonList=$(jq -c --arg phase "$phase" '.commands[$phase] // [] | .[]' "$appsConfigPath" 2>/dev/null)
    if [ -z "$cmdJsonList" ]; then
        return
    fi

    local cacheDir="$HOME/.cache/jrl_env/commands"
    mkdir -p "$cacheDir"

    while IFS= read -r cmdJson; do
        [ -z "$cmdJson" ] && continue

        local name shell command runOnce
        name=$(echo "$cmdJson" | jq -r '.name // "command"' 2>/dev/null)
        shell=$(echo "$cmdJson" | jq -r '.shell // "bash"' 2>/dev/null)
        command=$(echo "$cmdJson" | jq -r '.command // ""' 2>/dev/null)
        runOnce=$(echo "$cmdJson" | jq -r '.runOnce // false' 2>/dev/null)

        if [ -z "$command" ] || [ "$command" = "null" ]; then
            continue
        fi

        if ! commandExists "$shell"; then
            echo -e "${red}✗ Command shell '$shell' not available for $name.${nc}"
            continue
        fi

        local safeName
        safeName=$(echo "${phase}_${name}" | tr -cs '[:alnum:]_' '_')
        local flagFile="${cacheDir}/${safeName}.flag"

        if [ "$runOnce" = "true" ] && [ -f "$flagFile" ]; then
            echo -e "${yellow}Skipping $name (run once already executed).${nc}"
            continue
        fi

        echo -e "${cyan}Running $name...${nc}"
        if "$shell" -lc "$command"; then
            echo -e "${green}✓ $name completed${nc}"
            if [ "$runOnce" = "true" ]; then
                touch "$flagFile"
            fi
        else
            echo -e "${red}✗ $name failed${nc}"
        fi
    done <<< "$cmdJsonList"
}

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
    runConfigCommands "preInstall"
    installApps "$@"
    runConfigCommands "postInstall"
    removeCruftPackages
fi
