#!/bin/bash
# Ubuntu wrapper for shared Google Fonts installation
# shellcheck disable=SC2034,SC2154 # Variables are used by sourced common scripts; colours come from colours.sh

set -e

# Source all core tools (singular entry point)
# shellcheck source=../common/core/tools.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/core/tools.sh"

# shellcheck disable=SC2034 # Used by sourced common script
fontsConfigPath="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../configs/fonts.json"
# shellcheck disable=SC2034 # Used by sourced common script
fontInstallDirPath="$HOME/.local/share/fonts"
# shellcheck disable=SC2034 # Used by sourced common script
jqInstallHint="  sudo apt-get install -y jq"
# shellcheck disable=SC2034 # Used by sourced common script
fontCacheCmd="fc-cache -f -v \"$fontInstallDirPath\" &>/dev/null || true"

# shellcheck source=../common/install/installFonts.sh
sourceIfExists "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/install/installFonts.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    installGoogleFonts "$@"
fi
