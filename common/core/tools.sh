#!/bin/bash
# Single entry point for all core utilities
# Sources all necessary tools in the correct order

# Get the directory of this script
toolsDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source utilities first (which also sources colours)
# shellcheck source=utilities.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "${toolsDir}/utilities.sh"

# Source logging (which depends on utilities and colours)
# shellcheck source=logging.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "${toolsDir}/logging.sh"
