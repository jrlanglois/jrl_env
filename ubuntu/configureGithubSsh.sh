#!/bin/bash
# Ubuntu wrapper for shared GitHub SSH configuration

set -e

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../common/colours.sh
if [ -z "${red:-}" ]; then
    if [ -f "$scriptDir/../common/colours.sh" ]; then
        source "$scriptDir/../common/colours.sh"
    else
        echo "Error: colours.sh not found at $scriptDir/../common/colours.sh" >&2
        exit 1
    fi
fi

gitConfigPath="$scriptDir/../configs/gitConfig.json"
jqInstallHint="${yellow}  sudo apt-get install -y jq${nc}"

# shellcheck source=../common/configureGithubSsh.sh
source "$scriptDir/../common/configureGithubSsh.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureGithubSsh "$@"
fi
