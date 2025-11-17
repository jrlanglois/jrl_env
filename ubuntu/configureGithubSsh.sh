#!/bin/bash
# Ubuntu wrapper for shared GitHub SSH configuration
# shellcheck disable=SC2034,SC2154 # Variables are used by sourced common scripts; colours come from colours.sh

set -e

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../helpers/utilities.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$scriptDir/../helpers/utilities.sh"
# shellcheck source=../common/colours.sh
sourceIfExists "$scriptDir/../common/colours.sh"

# shellcheck disable=SC2034 # Used by sourced common script
gitConfigPath="$scriptDir/../configs/gitConfig.json"
# shellcheck disable=SC2034,SC2154 # Used by sourced common script; colours from colours.sh
jqInstallHint="${yellow}  sudo apt-get install -y jq${nc}"

# shellcheck source=../common/configureGithubSsh.sh
sourceIfExists "$scriptDir/../common/configureGithubSsh.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureGithubSsh "$@"
fi
