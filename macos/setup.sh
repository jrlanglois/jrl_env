#!/bin/bash
# Master setup script for macOS
# Runs all configuration and installation scripts in the correct order

set -e

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Colour

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CYAN}=== jrl_env Setup for macOS ===${NC}"
echo ""

# Source all required scripts
source "$SCRIPT_DIR/setupDevEnv.sh"
source "$SCRIPT_DIR/installFonts.sh"
source "$SCRIPT_DIR/installApps.sh"
source "$SCRIPT_DIR/configureGit.sh"
source "$SCRIPT_DIR/configureCursor.sh"
source "$SCRIPT_DIR/cloneRepositories.sh"

echo -e "${CYAN}Starting complete environment setup...${NC}"
echo ""

# 1. Setup development environment (zsh, Oh My Zsh, Homebrew)
echo -e "${YELLOW}=== Step 1: Setting up development environment ===${NC}"
echo ""
if ! setupDevEnv; then
    echo -e "${YELLOW}⚠ Development environment setup had some issues, continuing...${NC}"
fi
echo ""

# 2. Install fonts
echo -e "${YELLOW}=== Step 2: Installing fonts ===${NC}"
echo ""
if ! installGoogleFonts; then
    echo -e "${YELLOW}⚠ Font installation had some issues, continuing...${NC}"
fi
echo ""

# 3. Install applications
echo -e "${YELLOW}=== Step 3: Installing applications ===${NC}"
echo ""
if ! installOrUpdateApps; then
    echo -e "${YELLOW}⚠ Application installation had some issues, continuing...${NC}"
fi
echo ""

# 4. Configure Git
echo -e "${YELLOW}=== Step 4: Configuring Git ===${NC}"
echo ""
if ! configureGit; then
    echo -e "${YELLOW}⚠ Git configuration had some issues, continuing...${NC}"
fi
echo ""

# 5. Configure Cursor
echo -e "${YELLOW}=== Step 5: Configuring Cursor ===${NC}"
echo ""
if ! configureCursor; then
    echo -e "${YELLOW}⚠ Cursor configuration had some issues, continuing...${NC}"
fi
echo ""

# 6. Clone repositories (only on first run)
echo -e "${YELLOW}=== Step 6: Cloning repositories ===${NC}"
echo ""

# Check if repositories have already been cloned
CONFIG_PATH="$SCRIPT_DIR/../configs/repositories.json"
if [ -f "$CONFIG_PATH" ]; then
    WORK_PATH=$(jq -r '.workPathUnix' "$CONFIG_PATH" 2>/dev/null || echo "")
    if [ -n "$WORK_PATH" ] && [ "$WORK_PATH" != "null" ]; then
        # Expand $HOME if present in path
        WORK_PATH=$(echo "$WORK_PATH" | sed "s|\$HOME|$HOME|g" | sed "s|\$USER|$USER|g")
        
        # Check if work directory exists and has any owner subdirectories
        if [ -d "$WORK_PATH" ]; then
            OWNER_DIRS=$(find "$WORK_PATH" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
            if [ "$OWNER_DIRS" -gt 0 ]; then
                echo -e "${YELLOW}Repositories directory already exists with content. Skipping repository cloning.${NC}"
                echo -e "To clone repositories manually, run: ./macos/cloneRepositories.sh"
                echo ""
            else
                if ! cloneRepositories; then
                    echo -e "${YELLOW}⚠ Repository cloning had some issues, continuing...${NC}"
                fi
                echo ""
            fi
        else
            if ! cloneRepositories; then
                echo -e "${YELLOW}⚠ Repository cloning had some issues, continuing...${NC}"
            fi
            echo ""
        fi
    else
        echo -e "${YELLOW}Could not determine work path, skipping clone step.${NC}"
        echo ""
    fi
else
    echo -e "${YELLOW}Repository config not found, skipping clone step.${NC}"
    echo ""
fi

echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo -e "${GREEN}All setup tasks have been executed.${NC}"
echo -e "${YELLOW}Please review any warnings above and restart your terminal if needed.${NC}"

