#!/bin/bash
# Update script for Ubuntu
# Pulls latest changes and re-runs setup

set -e

# Get repository root (parent of ubuntu directory)
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repoRoot="$(cd "$scriptDir/.." && pwd)"
ubuntuDir="$scriptDir"

# shellcheck source=../common/colors.sh
source "$ubuntuDir/../common/colors.sh"

echo -e "${cyan}=== jrl_env Update ===${nc}"
echo ""

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
bash "$ubuntuDir/setup.sh"
