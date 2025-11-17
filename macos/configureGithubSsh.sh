#!/bin/bash
# macOS wrapper for shared GitHub SSH configuration

set -e

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../common/colors.sh
source "$scriptDir/../common/colors.sh"

gitConfigPath="$scriptDir/../configs/gitConfig.json"
jqInstallHint="${yellow}  brew install jq${nc}"

# shellcheck source=../common/configureGithubSsh.sh
source "$scriptDir/../common/configureGithubSsh.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureGithubSsh "$@"
fi

