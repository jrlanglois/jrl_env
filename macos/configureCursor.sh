#!/bin/bash
# macOS wrapper for shared Cursor configuration

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../common/colors.sh
source "$scriptDir/../common/colors.sh"
cursorConfigPath="${scriptDir}/../configs/cursorSettings.json"
cursorSettingsPath="$HOME/Library/Application Support/Cursor/User/settings.json"
jqInstallHint="${yellow}  brew install jq${nc}"

# shellcheck source=../common/configureCursor.sh
source "$scriptDir/../common/configureCursor.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureCursor "$@"
fi
