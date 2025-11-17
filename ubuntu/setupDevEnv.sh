#!/bin/bash
# Script to set up Ubuntu development environment
# Installs zsh, Oh My Zsh, and essential development tools

set -e

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Colour

# Function to check if a command exists
commandExists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if zsh is installed
isZshInstalled() {
    if commandExists zsh; then
        return 0
    fi
    return 1
}

# Function to check if Oh My Zsh is installed
isOhMyZshInstalled() {
    if [ -d "$HOME/.oh-my-zsh" ]; then
        return 0
    fi
    return 1
}

# Function to install zsh
installZsh() {
    echo -e "${CYAN}Installing zsh...${NC}"
    
    if isZshInstalled; then
        echo -e "${GREEN}✓ zsh is already installed${NC}"
        zsh --version
        return 0
    fi
    
    echo -e "${YELLOW}Installing zsh via apt...${NC}"
    sudo apt-get update
    if sudo apt-get install -y zsh; then
        if isZshInstalled; then
            echo -e "${GREEN}✓ zsh installed successfully${NC}"
            return 0
        else
            echo -e "${RED}✗ Failed to install zsh${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Failed to install zsh${NC}"
        return 1
    fi
}

# Function to install Oh My Zsh
installOhMyZsh() {
    echo -e "${CYAN}Installing Oh My Zsh...${NC}"
    
    if isOhMyZshInstalled; then
        echo -e "${GREEN}✓ Oh My Zsh is already installed${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}Installing Oh My Zsh...${NC}"
    if sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended; then
        echo -e "${GREEN}✓ Oh My Zsh installed successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to install Oh My Zsh${NC}"
        return 1
    fi
}

# Function to set zsh as default shell
setZshAsDefault() {
    echo -e "${CYAN}Setting zsh as default shell...${NC}"
    
    if ! isZshInstalled; then
        echo -e "${RED}✗ zsh is not installed. Please install it first.${NC}"
        return 1
    fi
    
    ZSH_PATH=$(which zsh)
    CURRENT_SHELL=$(echo $SHELL)
    
    if [ "$CURRENT_SHELL" = "$ZSH_PATH" ]; then
        echo -e "${GREEN}✓ zsh is already the default shell${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}Changing default shell to zsh...${NC}"
    echo -e "${YELLOW}You may be prompted for your password.${NC}"
    
    if sudo chsh -s "$ZSH_PATH" "$USER"; then
        echo -e "${GREEN}✓ Default shell changed to zsh${NC}"
        echo -e "${YELLOW}Note: This change will take effect after you log out and log back in.${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to change default shell${NC}"
        return 1
    fi
}

# Main setup function
setupDevEnv() {
    echo -e "${CYAN}=== Ubuntu Development Environment Setup ===${NC}"
    echo ""
    
    local success=true
    
    # Update package list
    echo -e "${CYAN}Updating package list...${NC}"
    sudo apt-get update
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
    
    # Set zsh as default
    if ! setZshAsDefault; then
        success=false
    fi
    echo ""
    
    echo -e "${CYAN}=== Setup Complete ===${NC}"
    if [ "$success" = true ]; then
        echo -e "${GREEN}Development environment setup completed successfully!${NC}"
        echo -e "${YELLOW}Note: You may need to restart your terminal for all changes to take effect.${NC}"
    else
        echo -e "${YELLOW}Some steps may not have completed successfully. Please review the output above.${NC}"
    fi
    
    return 0
}

# Run setup if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setupDevEnv
fi
