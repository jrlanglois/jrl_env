#!/bin/bash
# Script to configure Git settings on Ubuntu
# Sets up user information, defaults, and aliases

set -e

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Colour

# Function to check if Git is installed
isGitInstalled() {
    if command -v git >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Function to configure Git user information
configureGitUser() {
    echo -e "${CYAN}Configuring Git user information...${NC}"
    
    # Check current user name
    local currentName=$(git config --global user.name 2>/dev/null || echo "")
    local currentEmail=$(git config --global user.email 2>/dev/null || echo "")
    
    if [ -n "$currentName" ] && [ -n "$currentEmail" ]; then
        echo -e "${YELLOW}Current Git user configuration:${NC}"
        echo -e "  Name:  $currentName"
        echo -e "  Email: $currentEmail"
        read -p "Keep existing configuration? (Y/N): " keepExisting
        if [[ "$keepExisting" =~ ^[Yy]$ ]]; then
            echo -e "${GREEN}✓ Keeping existing configuration${NC}"
            return 0
        fi
    fi
    
    # Get user name
    if [ -z "$currentName" ]; then
        read -p "Enter your name: " userName
    else
        read -p "Enter your name [$currentName]: " userName
        userName=${userName:-$currentName}
    fi
    
    # Get user email
    if [ -z "$currentEmail" ]; then
        read -p "Enter your email: " userEmail
    else
        read -p "Enter your email [$currentEmail]: " userEmail
        userEmail=${userEmail:-$currentEmail}
    fi
    
    # Set Git user configuration
    git config --global user.name "$userName"
    git config --global user.email "$userEmail"
    
    echo -e "${GREEN}✓ Git user information configured successfully${NC}"
    return 0
}

# Function to configure Git defaults
configureGitDefaults() {
    echo -e "${CYAN}Configuring Git default settings...${NC}"
    
    echo -e "${YELLOW}Setting default branch name to 'main'...${NC}"
    git config --global init.defaultBranch main
    echo -e "  ${GREEN}✓ Default branch set to 'main'${NC}"
    
    echo -e "${YELLOW}Enabling colour output...${NC}"
    git config --global color.ui auto
    echo -e "  ${GREEN}✓ Colour output enabled${NC}"
    
    echo -e "${YELLOW}Configuring pull behaviour...${NC}"
    git config --global pull.rebase false
    echo -e "  ${GREEN}✓ Pull behaviour set to merge (default)${NC}"
    
    echo -e "${YELLOW}Configuring push behaviour...${NC}"
    git config --global push.default simple
    echo -e "  ${GREEN}✓ Push default set to 'simple'${NC}"
    
    echo -e "${YELLOW}Configuring push auto-setup...${NC}"
    git config --global push.autoSetupRemote true
    echo -e "  ${GREEN}✓ Push auto-setup remote enabled${NC}"
    
    echo -e "${YELLOW}Configuring rebase behaviour...${NC}"
    git config --global rebase.autoStash true
    echo -e "  ${GREEN}✓ Rebase auto-stash enabled${NC}"
    
    echo -e "${YELLOW}Configuring merge strategy...${NC}"
    git config --global merge.ff false
    echo -e "  ${GREEN}✓ Merge fast-forward disabled (creates merge commits)${NC}"
    
    echo -e "${GREEN}Git default settings configured successfully!${NC}"
    return 0
}

# Function to configure Git aliases
configureGitAliases() {
    echo -e "${CYAN}Configuring Git aliases...${NC}"
    
    # Common aliases
    local aliases=(
        "st:status"
        "co:checkout"
        "br:branch"
        "ci:commit"
        "unstage:reset HEAD --"
        "last:log -1 HEAD"
        "visual:!code"
        "log1:log --oneline"
        "logg:log --oneline --graph --decorate --all"
        "amend:commit --amend"
        "uncommit:reset --soft HEAD^"
        "stash-all:stash --include-untracked"
        "undo:reset HEAD~1"
    )
    
    for alias in "${aliases[@]}"; do
        local aliasName="${alias%%:*}"
        local aliasCommand="${alias#*:}"
        
        # Check if alias already exists
        if git config --global --get "alias.$aliasName" >/dev/null 2>&1; then
            echo -e "  ${YELLOW}⚠ Alias '$aliasName' already exists, skipping...${NC}"
        else
            git config --global "alias.$aliasName" "$aliasCommand"
            echo -e "  ${GREEN}✓ Added alias: $aliasName${NC}"
        fi
    done
    
    echo -e "${GREEN}Git aliases configured successfully!${NC}"
    return 0
}

# Main configuration function
configureGit() {
    echo -e "${CYAN}=== Git Configuration ===${NC}"
    echo ""
    
    if ! isGitInstalled; then
        echo -e "${RED}✗ Git is not installed.${NC}"
        echo -e "${YELLOW}Please install Git first.${NC}"
        echo -e "${YELLOW}  sudo apt-get install -y git${NC}"
        return 1
    fi
    
    local success=true
    
    if ! configureGitUser; then
        success=false
    fi
    echo ""
    
    if ! configureGitDefaults; then
        success=false
    fi
    echo ""
    
    if ! configureGitAliases; then
        success=false
    fi
    echo ""
    
    echo -e "${CYAN}=== Configuration Complete ===${NC}"
    if [ "$success" = true ]; then
        echo -e "${GREEN}Git has been configured successfully!${NC}"
    else
        echo -e "${YELLOW}Some settings may not have been configured. Please review the output above.${NC}"
    fi
    
    return 0
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureGit
fi
