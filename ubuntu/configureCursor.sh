#!/bin/bash
# Ubuntu wrapper for shared Cursor configuration

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../common/colours.sh
if [ -z "${red:-}" ]; then
    if [ -f "$scriptDir/../common/colours.sh" ]; then
        source "$scriptDir/../common/colours.sh"
    else
        echo "Error: colours.sh not found at $scriptDir/../common/colours.sh" >&2
        exit 1
    fi
fi

cursorConfigPath="${scriptDir}/../configs/cursorSettings.json"
cursorSettingsPath="$HOME/.config/Cursor/User/settings.json"
jqInstallHint="${yellow}  sudo apt-get install -y jq${nc}"

# shellcheck source=../common/configureCursor.sh
source "$scriptDir/../common/configureCursor.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureCursor "$@"
fi
