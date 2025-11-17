#!/bin/bash
# Script to check status of installed applications, configurations, and repositories

set -e

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
configsPath="$scriptDir/../configs"

# shellcheck source=../helpers/utilities.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$scriptDir/../helpers/utilities.sh"
# shellcheck source=../common/colours.sh
sourceIfExists "$scriptDir/../common/colours.sh"
# shellcheck source=../helpers/logging.sh
sourceIfExists "$scriptDir/../helpers/logging.sh"

logSection "jrl_env Status Check"
echo ""

# Check Git
logNote "Git:"
if command -v git >/dev/null 2>&1; then
    gitVersion=$(git --version 2>/dev/null)
    logSuccess "  Installed: $gitVersion"

    gitName=$(git config --global user.name 2>/dev/null || echo "")
    gitEmail=$(git config --global user.email 2>/dev/null || echo "")
    if [ -n "$gitName" ] && [ -n "$gitEmail" ]; then
        logSuccess "  Configured: $gitName <$gitEmail>"
    else
        logWarning "  Not configured"
    fi
else
    logError "  Not installed"
fi
echo ""

# Check zsh
logNote "zsh:"
if command -v zsh >/dev/null 2>&1; then
    zshVersion=$(zsh --version 2>/dev/null)
    logSuccess "  Installed: $zshVersion"

    if [ -d "$HOME/.oh-my-zsh" ]; then
        logSuccess "  Oh My Zsh installed"
    else
        logWarning "  Oh My Zsh not installed"
    fi
else
    logError "  Not installed"
fi
echo ""

# Check installed apps
if [ -f "$configsPath/ubuntu.json" ]; then
    logNote "Installed Applications:"
    if command -v jq >/dev/null 2>&1; then
        installed=0
        notInstalled=0

        # Check apt packages
        aptApps=$(jq -r '.apt[]?' "$configsPath/ubuntu.json" 2>/dev/null || echo "")
        while IFS= read -r app; do
            if [ -n "$app" ]; then
                if dpkg -l | grep -q "^ii  $app "; then
                    ((installed++))
                else
                    ((notInstalled++))
                    logError "  $app"
                fi
            fi
        done <<< "$aptApps"

        if [ $installed -gt 0 ]; then
            logSuccess "  $installed apt package(s) installed"
        fi
        if [ $notInstalled -gt 0 ]; then
            logWarning "  $notInstalled package(s) not installed"
        fi
    else
        logWarning "  Could not check apps (jq not available)"
    fi
    echo ""
fi

# Check repositories
if [ -f "$configsPath/repositories.json" ]; then
    logNote "Repositories:"
    if command -v jq >/dev/null 2>&1; then
        workPath=$(jq -r '.workPathUnix' "$configsPath/repositories.json" 2>/dev/null)
        if [ -n "$workPath" ] && [ "$workPath" != "null" ]; then
            workPath=$(echo "$workPath" | sed "s|\$HOME|$HOME|g" | sed "s|\$USER|$USER|g")

            if [ -d "$workPath" ]; then
                logSuccess "  Work directory exists: $workPath"
                ownerDirs=$(find "$workPath" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
                logSuccess "  $ownerDirs owner directory/directories found"

                totalRepos=0
                for dir in "$workPath"/*; do
                    if [ -d "$dir" ]; then
                        repoCount=$(find "$dir" -mindepth 1 -maxdepth 1 -type d -name ".git" -o -type d -exec test -d {}/.git \; -print 2>/dev/null | wc -l | tr -d ' ')
                        totalRepos=$((totalRepos + repoCount))
                    fi
                done
                logSuccess "  $totalRepos repository/repositories cloned"
            else
                logWarning "  Work directory does not exist: $workPath"
            fi
        fi
    else
        logWarning "  Could not check repositories (jq not available)"
    fi
    echo ""
fi

# Check Cursor
logNote "Cursor:"
cursorSettingsPath="$HOME/.config/Cursor/User/settings.json"
if [ -f "$cursorSettingsPath" ]; then
    logSuccess "  Settings file exists"
else
    logWarning "  Settings file not found"
fi
echo ""

logSection "Status Check Complete"
