#!/bin/bash
# Master setup script for macOS
# Runs all configuration and installation scripts in the correct order

set -e

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../common/colors.sh
source "$scriptDir/../common/colors.sh"

# Parse arguments
skipFonts=false
skipApps=false
skipGit=false
skipCursor=false
skipRepos=false
appsOnly=false
dryRun=false
noBackup=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-fonts) skipFonts=true ;;
        --skip-apps) skipApps=true ;;
        --skip-git) skipGit=true ;;
        --skip-cursor) skipCursor=true ;;
        --skip-repos) skipRepos=true ;;
        --apps-only) appsOnly=true ;;
        --dry-run) dryRun=true ;;
        --no-backup) noBackup=true ;;
        *) echo -e "${red}Unknown option: $1${nc}"; exit 1 ;;
    esac
    shift
done

# Determine what to run
runFonts=false
if [ "$skipFonts" = false ] && [ "$appsOnly" = false ]; then
    runFonts=true
fi
runApps=false
if [ "$skipApps" = false ] || [ "$appsOnly" = true ]; then
    runApps=true
fi
runGit=false
if [ "$skipGit" = false ] && [ "$appsOnly" = false ]; then
    runGit=true
fi
runCursor=false
if [ "$skipCursor" = false ] && [ "$appsOnly" = false ]; then
    runCursor=true
fi
runRepos=false
if [ "$skipRepos" = false ] && [ "$appsOnly" = false ]; then
    runRepos=true
fi

# Load logging functions
# shellcheck source=common/logging.sh
source "$scriptDir/../common/logging.sh"

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
source "$scriptDir/setupDevEnv.sh"
# shellcheck source=macos/installFonts.sh
source "$scriptDir/installFonts.sh"
# shellcheck source=macos/installApps.sh
source "$scriptDir/installApps.sh"
# shellcheck source=macos/configureGit.sh
source "$scriptDir/configureGit.sh"
# shellcheck source=macos/configureCursor.sh
source "$scriptDir/configureCursor.sh"
# shellcheck source=macos/cloneRepositories.sh
source "$scriptDir/cloneRepositories.sh"

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

# 5. Configure Cursor
if [ "$runCursor" = true ]; then
    if [ "$dryRun" = true ]; then
        logInfo "=== Step 5: Configuring Cursor (DRY RUN) ==="
        logInfo "Would configure Cursor from cursorSettings.json"
    else
        logInfo "=== Step 5: Configuring Cursor ==="
        if ! configureCursor; then
            logWarn "Cursor configuration had some issues, continuing..."
        else
            logSuccess "Cursor configuration completed"
        fi
    fi
fi

# 6. Clone repositories (only on first run)
if [ "$runRepos" = true ]; then
    if [ "$dryRun" = true ]; then
        logInfo "=== Step 6: Cloning repositories (DRY RUN) ==="
        logInfo "Would clone repositories from repositories.json"
    else
        logInfo "=== Step 6: Cloning repositories ==="

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
echo -e "${yellow}Please review any warnings above and restart your terminal if needed.${nc}"
