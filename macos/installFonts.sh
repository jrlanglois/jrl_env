#!/bin/bash
# macOS wrapper for shared Google Fonts installation

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../common/colors.sh
source "$scriptDir/../common/colors.sh"
fontsConfigPath="${scriptDir}/../configs/fonts.json"
fontInstallDirPath="$HOME/Library/Fonts"
jqInstallHint="${yellow}  brew install jq${nc}"
fontCacheCmd=""

# shellcheck source=../common/installFonts.sh
source "$scriptDir/../common/installFonts.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    installGoogleFonts "$@"
fi
