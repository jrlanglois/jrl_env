#!/bin/bash
# Update script for macOS
# Pulls latest changes and re-runs setup

set -e

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Colour

echo -e "${CYAN}=== jrl_env Update ===${NC}"
echo ""

# Get repository root (parent of macos directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MACOS_DIR="$SCRIPT_DIR"

# Check if we're in a git repository
if [ ! -d "$REPO_ROOT/.git" ]; then
    echo -e "${RED}✗ Not a git repository. Please clone the repository first.${NC}"
    exit 1
fi

echo -e "${YELLOW}Pulling latest changes...${NC}"
cd "$REPO_ROOT"

if ! git pull; then
    echo -e "${YELLOW}⚠ Git pull had issues. Continuing anyway...${NC}"
fi

echo ""
echo -e "${YELLOW}Re-running setup...${NC}"
echo ""

# Run the setup script
bash "$MACOS_DIR/setup.sh"

