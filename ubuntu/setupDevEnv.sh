#!/bin/bash
# Script to set up Ubuntu development environment
# Installs zsh, Oh My Zsh, and essential development tools

set -e

# Colours for output
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[1;33m'
cyan='\033[0;36m'
nc='\033[0m' # No Colour

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
osConfigPath="${scriptDir}/../configs/ubuntu.json"

# shellcheck source=../helpers/utilities.sh
source "$scriptDir/../helpers/utilities.sh"

# Function to check if zsh is installed
isZshInstalled()
{
    if commandExists zsh; then
        return 0
    fi
    return 1
}

# Function to check if Oh My Zsh is installed
isOhMyZshInstalled()
{
    if [ -d "$HOME/.oh-my-zsh" ]; then
        return 0
    fi
    return 1
}

# Function to install zsh
installZsh()
{
    echo -e "${cyan}Installing zsh...${nc}"

    if isZshInstalled; then
        echo -e "${green}✓ zsh is already installed${nc}"
        zsh --version
        return 0
    fi

    echo -e "${yellow}Installing zsh via apt...${nc}"
    sudo apt-get update
    if sudo apt-get install -y zsh; then
        if isZshInstalled; then
            echo -e "${green}✓ zsh installed successfully${nc}"
            return 0
        else
            echo -e "${red}✗ Failed to install zsh${nc}"
            return 1
        fi
    else
        echo -e "${red}✗ Failed to install zsh${nc}"
        return 1
    fi
}

# Function to install Oh My Zsh
installOhMyZsh()
{
    echo -e "${cyan}Installing Oh My Zsh...${nc}"

    if isOhMyZshInstalled; then
        echo -e "${green}✓ Oh My Zsh is already installed${nc}"
        return 0
    fi

    echo -e "${yellow}Installing Oh My Zsh...${nc}"
    if sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended; then
        echo -e "${green}✓ Oh My Zsh installed successfully${nc}"
        return 0
    else
        echo -e "${red}✗ Failed to install Oh My Zsh${nc}"
        return 1
    fi
}

configureOhMyZshTheme()
{
    local theme=${1:-"agnoster"}
    local zshrc="$HOME/.zshrc"

    if [ ! -f "$zshrc" ]; then
        echo -e "${yellow}⚠ ~/.zshrc not found. Skipping theme update.${nc}"
        return 0
    fi

    if grep -q '^ZSH_THEME=' "$zshrc"; then
        sed -i "s/^ZSH_THEME=.*/ZSH_THEME=\"$theme\"/" "$zshrc"
    else
        printf '\nZSH_THEME="%s"\n' "$theme" >> "$zshrc"
    fi

    echo -e "${green}✓ Set Oh My Zsh theme to $theme${nc}"
    return 0
}

getOhMyZshTheme()
{
    local defaultTheme="agnoster"
    local configuredTheme=""

    if [ -f "$osConfigPath" ]; then
        if commandExists jq; then
            configuredTheme=$(jq -r '.shell.ohMyZshTheme // empty' "$osConfigPath" 2>/dev/null || true)
        elif commandExists python3; then
            configuredTheme=$(python3 - "$osConfigPath" <<'PY' 2>/dev/null || true
import json
import sys

path = sys.argv[1]
try:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    theme = data.get("shell", {}).get("ohMyZshTheme") or ""
    print(theme)
except Exception:
    pass
PY
)
        fi
    fi

    if [ -n "$configuredTheme" ] && [ "$configuredTheme" != "null" ]; then
        echo "$configuredTheme"
    else
        echo "$defaultTheme"
    fi
}

# Function to ensure essential tools are installed
ensureEssentialTools()
{
    echo -e "${cyan}Ensuring essential tools are installed...${nc}"

    local needsUpdate=false

    if ! commandExists curl; then
        echo -e "${yellow}Installing curl...${nc}"
        sudo apt-get install -y curl
        needsUpdate=true
    fi

    if ! commandExists wget; then
        echo -e "${yellow}Installing wget...${nc}"
        sudo apt-get install -y wget
        needsUpdate=true
    fi

    if [ "$needsUpdate" = false ]; then
        echo -e "${green}✓ Essential tools already installed${nc}"
    fi
}

# Function to set zsh as default shell
setZshAsDefault()
{
    echo -e "${cyan}Setting zsh as default shell...${nc}"
    if ! isZshInstalled; then
        echo -e "${red}✗ zsh is not installed. Please install it first.${nc}"
        return 1
    fi

    local zshPath
    local currentShell

    zshPath=$(which zsh)
    currentShell="$SHELL"

    if [ "$currentShell" = "$zshPath" ]; then
        echo -e "${green}✓ zsh is already the default shell${nc}"
        return 0
    fi

    echo -e "${yellow}Changing default shell to zsh...${nc}"
    echo -e "${yellow}You may be prompted for your password.${nc}"

    if sudo chsh -s "$zshPath" "$USER"; then
        echo -e "${green}✓ Default shell changed to zsh${nc}"
        echo -e "${yellow}Note: This change will take effect after you log out and log back in.${nc}"
        return 0
    else
        echo -e "${red}✗ Failed to change default shell${nc}"
        return 1
    fi
}

# Main setup function
setupDevEnv()
{
    echo -e "${cyan}=== Ubuntu Development Environment Setup ===${nc}"
    echo ""

    local success=true

    # Update package list
    echo -e "${cyan}Updating package list...${nc}"
    sudo apt-get update
    echo ""

    # Ensure essential tools (curl, wget) are installed
    if ! ensureEssentialTools; then
        success=false
    fi
    echo ""

    # Install zsh
    if ! installZsh; then
        success=false
    fi
    echo ""

    # Install Oh My Zsh
    if ! installOhMyZsh; then
        success=false
    fi
    echo ""

    if ! configureOhMyZshTheme "$(getOhMyZshTheme)"; then
        success=false
    fi
    echo ""

    # Set zsh as default
    if ! setZshAsDefault; then
        success=false
    fi
    echo ""

    echo -e "${cyan}=== Setup Complete ===${nc}"
    if [ "$success" = true ]; then
        echo -e "${green}Development environment setup completed successfully!${nc}"
        echo -e "${yellow}Note: You may need to restart your terminal for all changes to take effect.${nc}"
    else
        echo -e "${yellow}Some steps may not have completed successfully. Please review the output above.${nc}"
    fi

    return 0
}

# Run setup if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setupDevEnv
fi
