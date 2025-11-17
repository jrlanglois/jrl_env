#!/bin/bash
# Ubuntu wrapper for shared Git configuration

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
gitInstallHint="${yellow}  sudo apt-get install -y git${nc}"

# shellcheck source=../common/colors.sh
source "$scriptDir/../common/colors.sh"

# shellcheck source=../common/configureGit.sh
source "$scriptDir/../common/configureGit.sh"

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureGit "$@"
fi
