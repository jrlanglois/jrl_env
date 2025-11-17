#!/bin/bash
# Ubuntu wrapper for shared Google Fonts installation

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fontsConfigPath="${scriptDir}/../configs/fonts.json"
fontInstallDirPath="$HOME/.local/share/fonts"
jqInstallHint="${yellow}  sudo apt-get install -y jq${nc}"
fontCacheCmd="fc-cache -f -v \"$fontInstallDirPath\" &>/dev/null || true"

# shellcheck source=../common/colors.sh
source "$scriptDir/../common/colors.sh"

# shellcheck source=../common/installFonts.sh
source "$scriptDir/../common/installFonts.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    installGoogleFonts "$@"
fi
