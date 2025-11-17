#!/bin/bash
# macOS wrapper for shared Cursor configuration

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../helpers/utilities.sh
source "$scriptDir/../helpers/utilities.sh"
# shellcheck source=../common/colours.sh
sourceIfExists "$scriptDir/../common/colours.sh"
cursorConfigPath="${scriptDir}/../configs/cursorSettings.json"
cursorSettingsPath="$HOME/Library/Application Support/Cursor/User/settings.json"
jqInstallHint="${yellow}  brew install jq${nc}"

# shellcheck source=../common/configureCursor.sh
sourceIfExists "$scriptDir/../common/configureCursor.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureCursor "$@"
fi
