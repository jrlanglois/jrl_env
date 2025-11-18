#!/bin/bash
# Master setup script for macOS
# Runs all configuration and installation scripts in the correct order
# shellcheck disable=SC2154 # Variables are set by sourced setupArgs.sh and colours.sh

set -e

# Source all core tools (singular entry point)
# shellcheck source=../common/core/tools.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/core/tools.sh"

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../common/install/setupArgs.sh
sourceIfExists "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/install/setupArgs.sh"

# Parse arguments
parseSetupArgs "$@"

# Determine what to run
determineRunFlags

# Initialize logging
logFile=$(initLogging)
logInfo "=== jrl_env Setup for macOS ==="
logInfo "Log file: $logFile"

if [ "$dryRun" = true ]; then
    logWarn "=== DRY RUN MODE ==="
    logWarn "No changes will be made. This is a preview."
fi

# Validate configs first
logInfo "Validating configuration files..."
if ! bash "$scriptDir/validate.sh"; then
    logWarn "Validation had issues. Continuing anyway..."
fi

# Backup function
backupConfigs()
{
    local backupDir
    local cursorSettings

    if [ "$noBackup" = true ] || [ "$dryRun" = true ]; then
        logInfo "Backup skipped (noBackup or dryRun flag set)"
        return 0
    fi

    backupDir="$TMPDIR/jrl_env_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backupDir"

    logInfo "Creating backup..."

    # Backup Git config
    if [ -f "$HOME/.gitconfig" ]; then
        cp "$HOME/.gitconfig" "$backupDir/gitconfig" 2>/dev/null || true
        logSuccess "Backed up Git config"
    fi

    # Backup Cursor settings
    cursorSettings="$HOME/Library/Application Support/Cursor/User/settings.json"
    if [ -f "$cursorSettings" ]; then
        mkdir -p "$backupDir/Cursor"
        cp "$cursorSettings" "$backupDir/Cursor/settings.json" 2>/dev/null || true
        logSuccess "Backed up Cursor settings"
    fi

    logSuccess "Backup created: $backupDir"
}

# Check dependencies
checkDependencies()
{
    logInfo "Checking dependencies..."
    local missing=()
    local response

    if ! command -v git >/dev/null 2>&1; then
        missing+=("Git")
        logWarn "Git is not installed"
    else
        logSuccess "Git is installed"
    fi

    if ! command -v brew >/dev/null 2>&1; then
        missing+=("Homebrew")
        logWarn "Homebrew is not installed"
    else
        logSuccess "Homebrew is installed"
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        logWarn "Missing dependencies: ${missing[*]}"
        read -r -p "Some features may not work. Continue anyway? (Y/N): " response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            logError "Setup cancelled by user due to missing dependencies"
            exit 1
        fi
        logInfo "User chose to continue despite missing dependencies"
    else
        logSuccess "All dependencies are installed"
    fi
}

if [ "$dryRun" = false ]; then
    checkDependencies
    backupConfigs
fi

# Source all required scripts
# shellcheck source=macos/setupDevEnv.sh
sourceIfExists "$scriptDir/setupDevEnv.sh"
# shellcheck source=macos/installFonts.sh
sourceIfExists "$scriptDir/installFonts.sh"
# shellcheck source=macos/installApps.sh
sourceIfExists "$scriptDir/installApps.sh"
# shellcheck source=macos/configureGit.sh
sourceIfExists "$scriptDir/configureGit.sh"
# shellcheck source=macos/configureCursor.sh
sourceIfExists "$scriptDir/configureCursor.sh"
# shellcheck source=macos/configureGithubSsh.sh
sourceIfExists "$scriptDir/configureGithubSsh.sh"
# shellcheck source=macos/cloneRepositories.sh
sourceIfExists "$scriptDir/cloneRepositories.sh"

logInfo "Starting complete environment setup..."

# 1. Setup development environment (zsh, Oh My Zsh, Homebrew)
logInfo "=== Step 1: Setting up development environment ==="
if ! setupDevEnv; then
    logWarn "Development environment setup had some issues, continuing..."
else
    logSuccess "Development environment setup completed"
fi

# 2. Install fonts
if [ "$runFonts" = true ]; then
    if [ "$dryRun" = true ]; then
        logInfo "=== Step 2: Installing fonts (DRY RUN) ==="
        logInfo "Would install fonts from fonts.json"
    else
        logInfo "=== Step 2: Installing fonts ==="
        if ! installGoogleFonts; then
            logWarn "Font installation had some issues, continuing..."
        else
            logSuccess "Font installation completed"
        fi
    fi
fi

# 3. Install applications
if [ "$runApps" = true ]; then
    if [ "$dryRun" = true ]; then
        logInfo "=== Step 3: Installing applications (DRY RUN) ==="
        logInfo "Would install/update apps from macos.json"
    else
        logInfo "=== Step 3: Installing applications ==="
        if ! installOrUpdateApps; then
            logWarn "Application installation had some issues, continuing..."
        else
            logSuccess "Application installation completed"
        fi
    fi
fi

# 4. Configure Git
if [ "$runGit" = true ]; then
    if [ "$dryRun" = true ]; then
        logInfo "=== Step 4: Configuring Git (DRY RUN) ==="
        logInfo "Would configure Git from gitConfig.json"
    else
        logInfo "=== Step 4: Configuring Git ==="
        if ! configureGit; then
            logWarn "Git configuration had some issues, continuing..."
        else
            logSuccess "Git configuration completed"
        fi
    fi
fi

# 5. Configure GitHub SSH
if [ "$runSsh" = true ]; then
    if [ "$dryRun" = true ]; then
        logInfo "=== Step 5: Configuring GitHub SSH (DRY RUN) ==="
        logInfo "Would generate SSH keys for GitHub."
    else
        logInfo "=== Step 5: Configuring GitHub SSH ==="
        if ! configureGithubSsh; then
            logWarn "GitHub SSH configuration had some issues, continuing..."
        else
            logSuccess "GitHub SSH configuration completed"
        fi
    fi
fi

# 6. Configure Cursor
if [ "$runCursor" = true ]; then
    if [ "$dryRun" = true ]; then
        logInfo "=== Step 6: Configuring Cursor (DRY RUN) ==="
        logInfo "Would configure Cursor from cursorSettings.json"
    else
        logInfo "=== Step 6: Configuring Cursor ==="
        if ! configureCursor; then
            logWarn "Cursor configuration had some issues, continuing..."
        else
            logSuccess "Cursor configuration completed"
        fi
    fi
fi

# 7. Clone repositories (only on first run)
if [ "$runRepos" = true ]; then
    if [ "$dryRun" = true ]; then
        logInfo "=== Step 7: Cloning repositories (DRY RUN) ==="
        logInfo "Would clone repositories from repositories.json"
    else
        logInfo "=== Step 7: Cloning repositories ==="

        # Check if repositories have already been cloned
        configPath="$scriptDir/../configs/repositories.json"
        if [ -f "$configPath" ]; then
            workPath=$(jq -r '.workPathUnix' "$configPath" 2>/dev/null || echo "")
            if [ -n "$workPath" ] && [ "$workPath" != "null" ]; then
                # Expand $HOME if present in path
                workPath=$(echo "$workPath" | sed "s|\$HOME|$HOME|g" | sed "s|\$USER|$USER|g")

                # Check if work directory exists and has any owner subdirectories
                if [ -d "$workPath" ]; then
                    ownerDirs=$(find "$workPath" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
                    if [ "$ownerDirs" -gt 0 ]; then
                        logWarn "Repositories directory already exists with content. Skipping repository cloning."
                        logInfo "To clone repositories manually, run: ./macos/cloneRepositories.sh"
                    else
                        if ! cloneRepositories; then
                            logWarn "Repository cloning had some issues, continuing..."
                        else
                            logSuccess "Repository cloning completed"
                        fi
                    fi
                else
                    if ! cloneRepositories; then
                        logWarn "Repository cloning had some issues, continuing..."
                    else
                        logSuccess "Repository cloning completed"
                    fi
                fi
            else
                logWarn "Could not determine work path, skipping clone step."
            fi
        else
            logWarn "Repository config not found, skipping clone step."
        fi
    fi
fi

logSuccess "=== Setup Complete ==="
logInfo "All setup tasks have been executed."
logInfo "Log file saved to: $logFile"
logNote "Please review any warnings above and restart your terminal if needed."
