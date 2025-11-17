#!/bin/bash
# Ubuntu wrapper for shared Google Fonts installation

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../helpers/utilities.sh
source "$scriptDir/../helpers/utilities.sh"
# shellcheck source=../common/colours.sh
sourceIfExists "$scriptDir/../common/colours.sh"

fontsConfigPath="${scriptDir}/../configs/fonts.json"
fontInstallDirPath="$HOME/.local/share/fonts"
jqInstallHint="${yellow}  sudo apt-get install -y jq${nc}"
fontCacheCmd="fc-cache -f -v \"$fontInstallDirPath\" &>/dev/null || true"

# shellcheck source=../common/installFonts.sh
sourceIfExists "$scriptDir/../common/installFonts.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    installGoogleFonts "$@"
fi
