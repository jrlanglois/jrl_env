#!/bin/bash
# Ubuntu wrapper for shared Git configuration
# shellcheck disable=SC2034,SC2154 # Variables are used by sourced common scripts; colours come from colours.sh

set -e

# Source all core tools (singular entry point)
# shellcheck source=../common/core/tools.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/core/tools.sh"

# shellcheck disable=SC2034 # Used by sourced common script
gitInstallHint="  sudo apt-get install -y git"
# shellcheck disable=SC2034 # Used by sourced common script
gitConfigPath="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../configs/gitConfig.json"

# shellcheck source=../common/configure/configureGit.sh
sourceIfExists "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/configure/configureGit.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureGit "$@"
fi
