#!/bin/bash
# macOS wrapper for shared repository cloning

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../common/colours.sh
source "$scriptDir/../common/colours.sh"
repoConfigPath="${scriptDir}/../configs/repositories.json"
jqInstallHint="${yellow}  brew install jq${nc}"

# shellcheck source=../common/cloneRepositories.sh
source "$scriptDir/../common/cloneRepositories.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    cloneRepositories "$@"
fi
