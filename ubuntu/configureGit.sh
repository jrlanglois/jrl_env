#!/bin/bash
# Ubuntu wrapper for shared Git configuration

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

gitInstallHint="${yellow}  sudo apt-get install -y git${nc}"
gitConfigPath="${scriptDir}/../configs/gitConfig.json"

# shellcheck source=../common/configureGit.sh
source "$scriptDir/../common/configureGit.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureGit "$@"
fi
