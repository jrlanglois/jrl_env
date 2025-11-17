#!/bin/bash
# Update script for macOS
# Pulls latest changes and re-runs setup

set -e

# Colours for output
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[1;33m'
cyan='\033[0;36m'
nc='\033[0m' # No Colour

echo -e "${cyan}=== jrl_env Update ===${nc}"
echo ""

# Get repository root (parent of macos directory)
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repoRoot="$(cd "$scriptDir/.." && pwd)"
macosDir="$scriptDir"

# Check if we're in a git repository
if [ ! -d "$repoRoot/.git" ]; then
    echo -e "${red}✗ Not a git repository. Please clone the repository first.${nc}"
    exit 1
fi

echo -e "${yellow}Pulling latest changes...${nc}"
cd "$repoRoot"

if ! git pull; then
    echo -e "${yellow}⚠ Git pull had issues. Continuing anyway...${nc}"
fi

echo ""
echo -e "${yellow}Re-running setup...${nc}"
echo ""

# Run the setup script
bash "$macosDir/setup.sh"