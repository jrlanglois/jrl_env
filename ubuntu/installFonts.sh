#!/bin/bash
# Ubuntu wrapper for shared Google Fonts installation

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

fontsConfigPath="${scriptDir}/../configs/fonts.json"
fontInstallDirPath="$HOME/.local/share/fonts"
jqInstallHint="${yellow}  sudo apt-get install -y jq${nc}"
fontCacheCmd="fc-cache -f -v \"$fontInstallDirPath\" &>/dev/null || true"

# shellcheck source=../common/installFonts.sh
source "$scriptDir/../common/installFonts.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    installGoogleFonts "$@"
fi
