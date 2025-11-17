#!/bin/bash
# Script to configure Git settings on macOS
# Sets up user information, defaults, and aliases

set -e

# Colours for output
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[1;33m'
cyan='\033[0;36m'
nc='\033[0m' # No Colour

# Function to check if Git is installed
isGitInstalled()
{
    if command -v git >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Function to configure Git user information
configureGitUser()
{
    echo -e "${cyan}Configuring Git user information...${nc}"

    # Check current user name
    local currentName=$(git config --global user.name 2>/dev/null || echo "")
    local currentEmail=$(git config --global user.email 2>/dev/null || echo "")

    if [ -n "$currentName" ] && [ -n "$currentEmail" ]; then
        echo -e "${yellow}Current Git user configuration:${nc}"
        echo -e "  Name:  $currentName"
        echo -e "  Email: $currentEmail"
        read -p "Keep existing configuration? (Y/N): " keepExisting
        if [[ "$keepExisting" =~ ^[Yy]$ ]]; then
            echo -e "${green}✓ Keeping existing configuration${nc}"
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

    echo -e "${green}✓ Git user information configured successfully${nc}"
    return 0
}

# Function to configure Git defaults
configureGitDefaults()
{
    echo -e "${cyan}Configuring Git default settings...${nc}"

    echo -e "${yellow}Setting default branch name to 'main'...${nc}"
    git config --global init.defaultBranch main
    echo -e "  ${green}✓ Default branch set to 'main'${nc}"

    echo -e "${yellow}Enabling colour output...${nc}"
    git config --global color.ui auto
    echo -e "  ${green}✓ Colour output enabled${nc}"

    echo -e "${yellow}Configuring pull behaviour...${nc}"
    git config --global pull.rebase false
    echo -e "  ${green}✓ Pull behaviour set to merge (default)${nc}"

    echo -e "${yellow}Configuring push behaviour...${nc}"
    git config --global push.default simple
    echo -e "  ${green}✓ Push default set to 'simple'${nc}"

    echo -e "${yellow}Configuring push auto-setup...${nc}"
    git config --global push.autoSetupRemote true
    echo -e "  ${green}✓ Push auto-setup remote enabled${nc}"

    echo -e "${yellow}Configuring rebase behaviour...${nc}"
    git config --global rebase.autoStash true
    echo -e "  ${green}✓ Rebase auto-stash enabled${nc}"

    echo -e "${yellow}Configuring merge strategy...${nc}"
    git config --global merge.ff false
    echo -e "  ${green}✓ Merge fast-forward disabled (creates merge commits)${nc}"

    echo -e "${green}Git default settings configured successfully!${nc}"
    return 0
}

# Function to configure Git aliases
configureGitAliases()
{
    echo -e "${cyan}Configuring Git aliases...${nc}"

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
            echo -e "  ${yellow}⚠ Alias '$aliasName' already exists, skipping...${nc}"
        else
            git config --global "alias.$aliasName" "$aliasCommand"
            echo -e "  ${green}✓ Added alias: $aliasName${nc}"
        fi
    done

    echo -e "${green}Git aliases configured successfully!${nc}"
    return 0
}

# Main configuration function
configureGit()
{
    echo -e "${cyan}=== Git Configuration ===${nc}"
    echo ""

    if ! isGitInstalled; then
        echo -e "${red}✗ Git is not installed.${nc}"
        echo -e "${yellow}Please install Git first.${nc}"
        echo -e "${yellow}  brew install git${nc}"
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

    echo -e "${cyan}=== Configuration Complete ===${nc}"
    if [ "$success" = true ]; then
        echo -e "${green}Git has been configured successfully!${nc}"
    else
        echo -e "${yellow}Some settings may not have been configured. Please review the output above.${nc}"
    fi

    return 0
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    configureGit
fi
