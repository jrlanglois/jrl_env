#!/bin/bash
# Update script for macOS
# Pulls latest changes and re-runs setup

set -e

# Source all core tools (singular entry point)
# shellcheck source=../common/core/tools.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/core/tools.sh"

# Get repository root (parent of macos directory)
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repoRoot="$(cd "$scriptDir/.." && pwd)"
macosDir="$scriptDir"

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
