#!/bin/bash
# Script to install applications on macOS using Homebrew
# Reads from macos.json configuration file

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../common/colors.sh
source "$scriptDir/../common/colors.sh"

appsConfigPath="${scriptDir}/../configs/macos.json"
jqInstallHint="${yellow}  brew install jq${nc}"

commandExists()
{
    command -v "$1" >/dev/null 2>&1
}

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

        local safeName
        safeName=$(echo "${phase}_${name}" | tr -cs '[:alnum:]_' '_')
        local flagFile="${cacheDir}/${safeName}.flag"

        if [ "$runOnce" = "true" ] && [ -f "$flagFile" ]; then
            echo -e "${yellow}Skipping $name (run once already executed).${nc}"
            continue
        fi

        if ! commandExists "$shell"; then
            echo -e "${red}✗ Command shell '$shell' not available for $name.${nc}"
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

# shellcheck source=../common/installApps.sh
source "$scriptDir/../common/installApps.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    runConfigCommands "preInstall"
    installApps "$@"
    runConfigCommands "postInstall"
fi
