#!/bin/bash
# Master setup script for macOS
# Runs all configuration and installation scripts in the correct order

set -e

# Colours for output
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[1;33m'
cyan='\033[0;36m'
nc='\033[0m' # No Colour

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
runFonts=false && [ "$skipFonts" = false ] && [ "$appsOnly" = false ] && runFonts=true
runApps=false && ([ "$skipApps" = false ] || [ "$appsOnly" = true ]) && runApps=true
runGit=false && [ "$skipGit" = false ] && [ "$appsOnly" = false ] && runGit=true
runCursor=false && [ "$skipCursor" = false ] && [ "$appsOnly" = false ] && runCursor=true
runRepos=false && [ "$skipRepos" = false ] && [ "$appsOnly" = false ] && runRepos=true

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$dryRun" = true ]; then
    echo -e "${yellow}=== DRY RUN MODE ===${nc}"
    echo -e "${yellow}No changes will be made. This is a preview.${nc}"
    echo ""
fi

echo -e "${cyan}=== jrl_env Setup for macOS ===${nc}"
echo ""

# Validate configs first
echo -e "${yellow}Validating configuration files...${nc}"
if ! bash "$scriptDir/validate.sh"; then
    echo -e "${yellow}⚠ Validation had issues. Continuing anyway...${nc}"
fi
echo ""

# Backup function
backupConfigs() {
    if [ "$noBackup" = true ] || [ "$dryRun" = true ]; then
        return 0
    fi
    
    backupDir="$TMPDIR/jrl_env_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backupDir"
    
    echo -e "${yellow}Creating backup...${nc}"
    
    # Backup Git config
    if [ -f "$HOME/.gitconfig" ]; then
        cp "$HOME/.gitconfig" "$backupDir/gitconfig" 2>/dev/null || true
    fi
    
    # Backup Cursor settings
    cursorSettings="$HOME/Library/Application Support/Cursor/User/settings.json"
    if [ -f "$cursorSettings" ]; then
        mkdir -p "$backupDir/Cursor"
        cp "$cursorSettings" "$backupDir/Cursor/settings.json" 2>/dev/null || true
    fi
    
    echo -e "  ${green}✓ Backup created: $backupDir${nc}"
    echo ""
}

# Check dependencies
checkDependencies() {
    missing=()
    
    if ! command -v git >/dev/null 2>&1; then
        missing+=("Git")
    fi
    
    if ! command -v brew >/dev/null 2>&1; then
        missing+=("Homebrew")
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo -e "${yellow}Missing dependencies:${nc}"
        for dep in "${missing[@]}"; do
            echo -e "  ${red}✗ $dep${nc}"
        done
        echo ""
        read -p "Some features may not work. Continue anyway? (Y/N): " response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
        echo ""
    fi
}

if [ "$dryRun" = false ]; then
    checkDependencies
    backupConfigs
fi

# Source all required scripts
source "$scriptDir/setupDevEnv.sh"
source "$scriptDir/installFonts.sh"
source "$scriptDir/installApps.sh"
source "$scriptDir/configureGit.sh"
source "$scriptDir/configureCursor.sh"
source "$scriptDir/cloneRepositories.sh"

echo -e "${cyan}Starting complete environment setup...${nc}"
echo ""

# 1. Setup development environment (zsh, Oh My Zsh, Homebrew)
echo -e "${yellow}=== Step 1: Setting up development environment ===${nc}"
echo ""
if ! setupDevEnv; then
    echo -e "${yellow}⚠ Development environment setup had some issues, continuing...${nc}"
fi
echo ""

# 2. Install fonts
if [ "$runFonts" = true ]; then
    if [ "$dryRun" = true ]; then
        echo -e "${yellow}=== Step 2: Installing fonts (DRY RUN) ===${nc}"
        echo -e "Would install fonts from fonts.json"
    else
        echo -e "${yellow}=== Step 2: Installing fonts ===${nc}"
        echo ""
        if ! installGoogleFonts; then
            echo -e "${yellow}⚠ Font installation had some issues, continuing...${nc}"
        fi
    fi
    echo ""
fi

# 3. Install applications
if [ "$runApps" = true ]; then
    if [ "$dryRun" = true ]; then
        echo -e "${yellow}=== Step 3: Installing applications (DRY RUN) ===${nc}"
        echo -e "Would install/update apps from macosApps.json"
    else
        echo -e "${yellow}=== Step 3: Installing applications ===${nc}"
        echo ""
        if ! installOrUpdateApps; then
            echo -e "${yellow}⚠ Application installation had some issues, continuing...${nc}"
        fi
    fi
    echo ""
fi

# 4. Configure Git
if [ "$runGit" = true ]; then
    if [ "$dryRun" = true ]; then
        echo -e "${yellow}=== Step 4: Configuring Git (DRY RUN) ===${nc}"
        echo -e "Would configure Git from gitConfig.json"
    else
        echo -e "${yellow}=== Step 4: Configuring Git ===${nc}"
        echo ""
        if ! configureGit; then
            echo -e "${yellow}⚠ Git configuration had some issues, continuing...${nc}"
        fi
    fi
    echo ""
fi

# 5. Configure Cursor
if [ "$runCursor" = true ]; then
    if [ "$dryRun" = true ]; then
        echo -e "${yellow}=== Step 5: Configuring Cursor (DRY RUN) ===${nc}"
        echo -e "Would configure Cursor from cursorSettings.json"
    else
        echo -e "${yellow}=== Step 5: Configuring Cursor ===${nc}"
        echo ""
        if ! configureCursor; then
            echo -e "${yellow}⚠ Cursor configuration had some issues, continuing...${nc}"
        fi
    fi
    echo ""
fi

# 6. Clone repositories (only on first run)
if [ "$runRepos" = true ]; then
    if [ "$dryRun" = true ]; then
        echo -e "${yellow}=== Step 6: Cloning repositories (DRY RUN) ===${nc}"
        echo -e "Would clone repositories from repositories.json"
    else
        echo -e "${yellow}=== Step 6: Cloning repositories ===${nc}"
        echo ""
        
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
                        echo -e "${yellow}Repositories directory already exists with content. Skipping repository cloning.${nc}"
                        echo -e "To clone repositories manually, run: ./macos/cloneRepositories.sh"
                        echo ""
                    else
                        if ! cloneRepositories; then
                            echo -e "${yellow}⚠ Repository cloning had some issues, continuing...${nc}"
                        fi
                        echo ""
                    fi
                else
                    if ! cloneRepositories; then
                        echo -e "${yellow}⚠ Repository cloning had some issues, continuing...${nc}"
                    fi
                    echo ""
                fi
            else
                echo -e "${yellow}Could not determine work path, skipping clone step.${nc}"
                echo ""
            fi
        else
            echo -e "${yellow}Repository config not found, skipping clone step.${nc}"
            echo ""
        fi
    fi
    echo ""
fi

echo -e "${green}=== Setup Complete ===${nc}"
echo ""
echo -e "${green}All setup tasks have been executed.${nc}"
echo -e "${yellow}Please review any warnings above and restart your terminal if needed.${nc}"

