#!/bin/bash
# macOS wrapper for shared repository cloning

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../helpers/utilities.sh
source "$scriptDir/../helpers/utilities.sh"
# shellcheck source=../common/colours.sh
sourceIfExists "$scriptDir/../common/colours.sh"
repoConfigPath="${scriptDir}/../configs/repositories.json"
jqInstallHint="${yellow}  brew install jq${nc}"

# shellcheck source=../common/cloneRepositories.sh
sourceIfExists "$scriptDir/../common/cloneRepositories.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    cloneRepositories "$@"
fi
