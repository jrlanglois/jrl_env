#!/bin/bash
# macOS wrapper for shared Git configuration

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../common/colours.sh
source "$scriptDir/../common/colours.sh"
gitInstallHint="${yellow}  brew install git${nc}"
gitConfigPath="${scriptDir}/../configs/gitConfig.json"

# shellcheck source=../common/configureGit.sh
source "$scriptDir/../common/configureGit.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureGit "$@"
fi
