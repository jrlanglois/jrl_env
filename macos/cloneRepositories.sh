#!/bin/bash
# macOS wrapper for shared repository cloning
# shellcheck disable=SC2034,SC2154 # Variables are used by sourced common scripts; colours come from colours.sh

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../helpers/utilities.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$scriptDir/../helpers/utilities.sh"
# shellcheck source=../common/colours.sh
sourceIfExists "$scriptDir/../common/colours.sh"
# shellcheck disable=SC2034 # Used by sourced common script
repoConfigPath="${scriptDir}/../configs/repositories.json"
# shellcheck disable=SC2034,SC2154 # Used by sourced common script; colours from colours.sh
jqInstallHint="${yellow}  brew install jq${nc}"

# shellcheck source=../common/cloneRepositories.sh
sourceIfExists "$scriptDir/../common/cloneRepositories.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    cloneRepositories "$@"
fi
