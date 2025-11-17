#!/bin/bash
# Update script for macOS
# Pulls latest changes and re-runs setup

set -e

# Get repository root (parent of macos directory)
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repoRoot="$(cd "$scriptDir/.." && pwd)"
macosDir="$scriptDir"

# shellcheck source=../helpers/utilities.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
sourceIfExists "$macosDir/../helpers/utilities.sh"
# shellcheck source=../common/colours.sh
sourceIfExists "$macosDir/../common/colours.sh"
# shellcheck source=../helpers/logging.sh
sourceIfExists "$macosDir/../helpers/logging.sh"

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
bash "$macosDir/setup.sh"
