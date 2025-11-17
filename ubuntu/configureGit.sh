#!/bin/bash
# Ubuntu wrapper for shared Git configuration
# shellcheck disable=SC2034,SC2154 # Variables are used by sourced common scripts; colours come from colours.sh

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../helpers/utilities.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$scriptDir/../helpers/utilities.sh"
# shellcheck source=../common/colours.sh
sourceIfExists "$scriptDir/../common/colours.sh"

# shellcheck disable=SC2034,SC2154 # Used by sourced common script; colours from colours.sh
gitInstallHint="${yellow}  sudo apt-get install -y git${nc}"
# shellcheck disable=SC2034 # Used by sourced common script
gitConfigPath="${scriptDir}/../configs/gitConfig.json"

# shellcheck source=../common/configureGit.sh
sourceIfExists "$scriptDir/../common/configureGit.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureGit "$@"
fi
