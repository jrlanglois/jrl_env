#!/bin/bash
# Update script for Ubuntu
# Pulls latest changes and re-runs setup

set -e

# Get repository root (parent of ubuntu directory)
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repoRoot="$(cd "$scriptDir/.." && pwd)"
ubuntuDir="$scriptDir"

# shellcheck source=../helpers/utilities.sh
sourceIfExists "$ubuntuDir/../helpers/utilities.sh"
# shellcheck source=../common/colours.sh
sourceIfExists "$ubuntuDir/../common/colours.sh"
# shellcheck source=../helpers/logging.sh
sourceIfExists "$ubuntuDir/../helpers/logging.sh"

logSection "jrl_env Update"
echo ""

# Check if we're in a git repository
if [ ! -d "$repoRoot/.git" ]; then
    logError "Not a git repository. Please clone the repository first."
    exit 1
fi

logNote "Pulling latest changes..."
cd "$repoRoot"

if ! git pull; then
    logWarning "Git pull had issues. Continuing anyway..."
fi

echo ""
logNote "Re-running setup..."
echo ""

# Run the setup script
bash "$ubuntuDir/setup.sh"
