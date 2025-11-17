#!/bin/bash
# Ubuntu wrapper for shared Google Fonts installation
# shellcheck disable=SC2034,SC2154 # Variables are used by sourced common scripts; colours come from colours.sh

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../helpers/utilities.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$scriptDir/../helpers/utilities.sh"
# shellcheck source=../common/colours.sh
sourceIfExists "$scriptDir/../common/colours.sh"

# shellcheck disable=SC2034 # Used by sourced common script
fontsConfigPath="${scriptDir}/../configs/fonts.json"
# shellcheck disable=SC2034 # Used by sourced common script
fontInstallDirPath="$HOME/.local/share/fonts"
# shellcheck disable=SC2034,SC2154 # Used by sourced common script; colours from colours.sh
jqInstallHint="${yellow}  sudo apt-get install -y jq${nc}"
# shellcheck disable=SC2034 # Used by sourced common script
fontCacheCmd="fc-cache -f -v \"$fontInstallDirPath\" &>/dev/null || true"

# shellcheck source=../common/installFonts.sh
sourceIfExists "$scriptDir/../common/installFonts.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    installGoogleFonts "$@"
fi
