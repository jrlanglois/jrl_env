#!/bin/bash
# Ubuntu wrapper for shared GitHub SSH configuration

set -e

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../common/colours.sh
source "$scriptDir/../common/colours.sh"

gitConfigPath="$scriptDir/../configs/gitConfig.json"
jqInstallHint="${yellow}  sudo apt-get install -y jq${nc}"

# shellcheck source=../common/configureGithubSsh.sh
source "$scriptDir/../common/configureGithubSsh.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureGithubSsh "$@"
fi
