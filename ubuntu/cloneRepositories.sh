#!/bin/bash
# Ubuntu wrapper for shared repository cloning

set -e

# Get script directory
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

repoConfigPath="${scriptDir}/../configs/repositories.json"
jqInstallHint="${yellow}  sudo apt-get install -y jq${nc}"

# shellcheck source=../common/cloneRepositories.sh
source "$scriptDir/../common/cloneRepositories.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    cloneRepositories "$@"
fi
