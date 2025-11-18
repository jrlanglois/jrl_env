#!/bin/bash
# Ubuntu wrapper for shared Cursor configuration
# shellcheck disable=SC2034,SC2154 # Variables are used by sourced common scripts; colours come from colours.sh

set -e

# Source all core tools (singular entry point)
# shellcheck source=../common/core/tools.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/core/tools.sh"

# shellcheck disable=SC2034 # Used by sourced common script
cursorConfigPath="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../configs/cursorSettings.json"
# shellcheck disable=SC2034 # Used by sourced common script
cursorSettingsPath="$HOME/.config/Cursor/User/settings.json"
# shellcheck disable=SC2034 # Used by sourced common script
jqInstallHint="  sudo apt-get install -y jq"

# shellcheck source=../common/configure/configureCursor.sh
sourceIfExists "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/configure/configureCursor.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureCursor "$@"
fi
