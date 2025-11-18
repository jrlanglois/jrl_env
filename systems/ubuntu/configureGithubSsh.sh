#!/bin/bash
# Ubuntu wrapper for shared GitHub SSH configuration
# shellcheck disable=SC2034,SC2154 # Variables are used by sourced common scripts; colours come from colours.sh

set -e

# Source all core tools (singular entry point)
# shellcheck source=../common/core/tools.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/core/tools.sh"

# shellcheck disable=SC2034 # Used by sourced common script
gitConfigPath="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../configs/gitConfig.json"
# shellcheck disable=SC2034 # Used by sourced common script
jqInstallHint="  sudo apt-get install -y jq"

# shellcheck source=../common/configure/configureGithubSsh.sh
sourceIfExists "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/configure/configureGithubSsh.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureGithubSsh "$@"
fi
