#!/bin/bash
# Script to set up macOS development environment
# Installs zsh, Oh My Zsh, Homebrew, and other essential tools

set -e  # Exit on error

# Colours for output
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[1;33m'
cyan='\033[0;36m'
nc='\033[0m' # No Colour

# Function to check if a command exists
commandExists()
{
    command -v "$1" >/dev/null 2>&1
}

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

# Function to check if Homebrew is installed
isBrewInstalled()
{
    if commandExists brew; then
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

    if isBrewInstalled; then
        echo -e "${yellow}Installing zsh via Homebrew...${nc}"
        brew install zsh
    else
        echo -e "${yellow}zsh should be pre-installed on macOS. If not, please install Xcode Command Line Tools:${nc}"
        echo -e "${yellow}  xcode-select --install${nc}"
        return 1
    fi

    if isZshInstalled; then
        echo -e "${green}✓ zsh installed successfully${nc}"
        return 0
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

# Function to install Homebrew
installBrew()
{
    echo -e "${cyan}Installing Homebrew...${nc}"

    if isBrewInstalled; then
        echo -e "${green}✓ Homebrew is already installed${nc}"
        brew --version
        return 0
    fi

    echo -e "${yellow}Installing Homebrew...${nc}"
    if /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; then
        # Add Homebrew to PATH for Apple Silicon Macs
        if [[ $(uname -m) == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/usr/local/bin/brew shellenv)"
        fi

        if isBrewInstalled; then
            echo -e "${green}✓ Homebrew installed successfully${nc}"
            return 0
        else
            echo -e "${yellow}⚠ Homebrew installation completed, but may not be available in this session.${nc}"
            echo -e "${yellow}Please restart your terminal or run: eval \"\$(brew shellenv)\"${nc}"
            return 1
        fi
    else
        echo -e "${red}✗ Failed to install Homebrew${nc}"
        return 1
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

    ZSH_PATH=$(which zsh)
    CURRENT_SHELL=$(echo $SHELL)

    if [ "$CURRENT_SHELL" = "$ZSH_PATH" ]; then
        echo -e "${green}✓ zsh is already the default shell${nc}"
        return 0
    fi

    echo -e "${yellow}Changing default shell to zsh...${nc}"
    echo -e "${yellow}You may be prompted for your password.${nc}"

    if sudo chsh -s "$ZSH_PATH" "$USER"; then
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
    echo -e "${cyan}=== macOS Development Environment Setup ===${nc}"
    echo ""

    local success=true

    # Install Homebrew first (needed for zsh if not pre-installed)
    if ! installBrew; then
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