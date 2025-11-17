#!/bin/bash
# Ubuntu wrapper for shared Cursor configuration

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cursorConfigPath="${scriptDir}/../configs/cursorSettings.json"
cursorSettingsPath="$HOME/.config/Cursor/User/settings.json"
jqInstallHint="${yellow}  sudo apt-get install -y jq${nc}"

# shellcheck source=../common/colours.sh
source "$scriptDir/../common/colours.sh"

# shellcheck source=../common/configureCursor.sh
source "$scriptDir/../common/configureCursor.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureCursor "$@"
fi
