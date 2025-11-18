#!/bin/bash
# Script to set up Ubuntu development environment
# Installs zsh, Oh My Zsh, and essential development tools

set -e

# Source all core tools (singular entry point)
# shellcheck source=../common/core/tools.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/core/tools.sh"

osConfigPath="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../configs/ubuntu.json"

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
    logInfo "Installing zsh..."

    if isZshInstalled; then
        logSuccess "zsh is already installed"
        zsh --version
        return 0
    fi

    logNote "Installing zsh via apt..."
    sudo apt-get update
    if sudo apt-get install -y zsh; then
        if isZshInstalled; then
            logSuccess "zsh installed successfully"
            return 0
        else
            logError "Failed to install zsh"
            return 1
        fi
    else
        logError "Failed to install zsh"
        return 1
    fi
}

# Function to install Oh My Zsh
installOhMyZsh()
{
    logInfo "Installing Oh My Zsh..."

    if isOhMyZshInstalled; then
        logSuccess "Oh My Zsh is already installed"
        return 0
    fi

    logNote "Installing Oh My Zsh..."
    if sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended; then
        logSuccess "Oh My Zsh installed successfully"
        return 0
    else
        logError "Failed to install Oh My Zsh"
        return 1
    fi
}

configureOhMyZshTheme()
{
    local theme=${1:-"agnoster"}
    local zshrc="$HOME/.zshrc"

    if [ ! -f "$zshrc" ]; then
        logWarning "~/.zshrc not found. Skipping theme update."
        return 0
    fi

    if grep -q '^ZSH_THEME=' "$zshrc"; then
        sed -i "s/^ZSH_THEME=.*/ZSH_THEME=\"$theme\"/" "$zshrc"
    else
        printf '\nZSH_THEME="%s"\n' "$theme" >> "$zshrc"
    fi

    logSuccess "Set Oh My Zsh theme to $theme"
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
    logInfo "Ensuring essential tools are installed..."

    local needsUpdate=false

    if ! commandExists curl; then
        logNote "Installing curl..."
        sudo apt-get install -y curl
        needsUpdate=true
    fi

    if ! commandExists wget; then
        logNote "Installing wget..."
        sudo apt-get install -y wget
        needsUpdate=true
    fi

    if [ "$needsUpdate" = false ]; then
        logSuccess "Essential tools already installed"
    fi
}

# Function to set zsh as default shell
setZshAsDefault()
{
    logInfo "Setting zsh as default shell..."
    if ! isZshInstalled; then
        logError "zsh is not installed. Please install it first."
        return 1
    fi

    local zshPath
    local currentShell

    zshPath=$(which zsh)
    currentShell="$SHELL"

    if [ "$currentShell" = "$zshPath" ]; then
        logSuccess "zsh is already the default shell"
        return 0
    fi

    logNote "Changing default shell to zsh..."
    logNote "You may be prompted for your password."

    if sudo chsh -s "$zshPath" "$USER"; then
        logSuccess "Default shell changed to zsh"
        logNote "Note: This change will take effect after you log out and log back in."
        return 0
    else
        logError "Failed to change default shell"
        return 1
    fi
}

# Main setup function
setupDevEnv()
{
    logSection "Ubuntu Development Environment Setup"
    echo ""

    local success=true

    # Update package list
    logInfo "Updating package list..."
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

    logSection "Setup Complete"
    if [ "$success" = true ]; then
        logSuccess "Development environment setup completed successfully!"
        logNote "Note: You may need to restart your terminal for all changes to take effect."
    else
        logNote "Some steps may not have completed successfully. Please review the output above."
    fi

    return 0
}

# Run setup if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setupDevEnv
fi
