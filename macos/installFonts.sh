#!/bin/bash
# macOS wrapper for shared Google Fonts installation

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../helpers/utilities.sh
source "$scriptDir/../helpers/utilities.sh"
# shellcheck source=../common/colours.sh
sourceIfExists "$scriptDir/../common/colours.sh"
fontsConfigPath="${scriptDir}/../configs/fonts.json"
fontInstallDirPath="$HOME/Library/Fonts"
jqInstallHint="${yellow}  brew install jq${nc}"
fontCacheCmd=""

# shellcheck source=../common/installFonts.sh
sourceIfExists "$scriptDir/../common/installFonts.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    installGoogleFonts "$@"
fi
