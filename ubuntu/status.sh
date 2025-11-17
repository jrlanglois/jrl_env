#!/bin/bash
# Script to check status of installed applications, configurations, and repositories

set -e

# Colours for output
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[1;33m'
cyan='\033[0;36m'
nc='\033[0m' # No Colour

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
configsPath="$scriptDir/../configs"

echo -e "${cyan}=== jrl_env Status Check ===${nc}"
echo ""

# Check Git
echo -e "${yellow}Git:${nc}"
if command -v git >/dev/null 2>&1; then
    gitVersion=$(git --version 2>/dev/null)
    echo -e "  ${green}✓ Installed: $gitVersion${nc}"

    gitName=$(git config --global user.name 2>/dev/null || echo "")
    gitEmail=$(git config --global user.email 2>/dev/null || echo "")
    if [ -n "$gitName" ] && [ -n "$gitEmail" ]; then
        echo -e "  ${green}✓ Configured: $gitName <$gitEmail>${nc}"
    else
        echo -e "  ${yellow}⚠ Not configured${nc}"
    fi
else
    echo -e "  ${red}✗ Not installed${nc}"
fi
echo ""

# Check zsh
echo -e "${yellow}zsh:${nc}"
if command -v zsh >/dev/null 2>&1; then
    zshVersion=$(zsh --version 2>/dev/null)
    echo -e "  ${green}✓ Installed: $zshVersion${nc}"

    if [ -d "$HOME/.oh-my-zsh" ]; then
        echo -e "  ${green}✓ Oh My Zsh installed${nc}"
    else
        echo -e "  ${yellow}⚠ Oh My Zsh not installed${nc}"
    fi
else
    echo -e "  ${red}✗ Not installed${nc}"
fi
echo ""

# Check installed apps
if [ -f "$configsPath/ubuntuApps.json" ]; then
    echo -e "${yellow}Installed Applications:${nc}"
    if command -v jq >/dev/null 2>&1; then
        installed=0
        notInstalled=0

        # Check apt packages
        aptApps=$(jq -r '.apt[]?' "$configsPath/ubuntuApps.json" 2>/dev/null || echo "")
        while IFS= read -r app; do
            if [ -n "$app" ]; then
                if dpkg -l | grep -q "^ii  $app "; then
                    ((installed++))
                else
                    ((notInstalled++))
                    echo -e "  ${red}✗ $app${nc}"
                fi
            fi
        done <<< "$aptApps"

        if [ $installed -gt 0 ]; then
            echo -e "  ${green}✓ $installed apt package(s) installed${nc}"
        fi
        if [ $notInstalled -gt 0 ]; then
            echo -e "  ${yellow}⚠ $notInstalled package(s) not installed${nc}"
        fi
    else
        echo -e "  ${yellow}⚠ Could not check apps (jq not available)${nc}"
    fi
    echo ""
fi

# Check repositories
if [ -f "$configsPath/repositories.json" ]; then
    echo -e "${yellow}Repositories:${nc}"
    if command -v jq >/dev/null 2>&1; then
        workPath=$(jq -r '.workPathUnix' "$configsPath/repositories.json" 2>/dev/null)
        if [ -n "$workPath" ] && [ "$workPath" != "null" ]; then
            workPath=$(echo "$workPath" | sed "s|\$HOME|$HOME|g" | sed "s|\$USER|$USER|g")

            if [ -d "$workPath" ]; then
                echo -e "  ${green}✓ Work directory exists: $workPath${nc}"
                ownerDirs=$(find "$workPath" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
                echo -e "  ${green}✓ $ownerDirs owner directory/directories found${nc}"

                totalRepos=0
                for dir in "$workPath"/*; do
                    if [ -d "$dir" ]; then
                        repoCount=$(find "$dir" -mindepth 1 -maxdepth 1 -type d -name ".git" -o -type d -exec test -d {}/.git \; -print 2>/dev/null | wc -l | tr -d ' ')
                        totalRepos=$((totalRepos + repoCount))
                    fi
                done
                echo -e "  ${green}✓ $totalRepos repository/repositories cloned${nc}"
            else
                echo -e "  ${yellow}⚠ Work directory does not exist: $workPath${nc}"
            fi
        fi
    else
        echo -e "  ${yellow}⚠ Could not check repositories (jq not available)${nc}"
    fi
    echo ""
fi

# Check Cursor
echo -e "${yellow}Cursor:${nc}"
cursorSettingsPath="$HOME/.config/Cursor/User/settings.json"
if [ -f "$cursorSettingsPath" ]; then
    echo -e "  ${green}✓ Settings file exists${nc}"
else
    echo -e "  ${yellow}⚠ Settings file not found${nc}"
fi
echo ""

echo -e "${cyan}=== Status Check Complete ===${nc}"