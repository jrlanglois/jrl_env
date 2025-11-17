#!/bin/bash
# macOS wrapper for shared GitHub SSH configuration

set -e

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../helpers/utilities.sh
source "$scriptDir/../helpers/utilities.sh"
# shellcheck source=../common/colours.sh
sourceIfExists "$scriptDir/../common/colours.sh"

gitConfigPath="$scriptDir/../configs/gitConfig.json"
jqInstallHint="${yellow}  brew install jq${nc}"

# shellcheck source=../common/configureGithubSsh.sh
sourceIfExists "$scriptDir/../common/configureGithubSsh.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureGithubSsh "$@"
fi
