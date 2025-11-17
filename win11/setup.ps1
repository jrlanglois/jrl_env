# Master setup script for Windows 11
# Runs all configuration and installation scripts in the correct order

param(
    [switch]$skipFonts,
    [switch]$skipApps,
    [switch]$skipGit,
    [switch]$skipCursor,
    [switch]$skipRepos,
    [switch]$appsOnly,
    [switch]$dryRun,
    [switch]$noBackup
)

$ErrorActionPreference = "Stop"

# Parse flags
$runFonts = -not $skipFonts -and -not $appsOnly
$runApps = -not $skipApps -or $appsOnly
$runGit = -not $skipGit -and -not $appsOnly
$runCursor = -not $skipCursor -and -not $appsOnly
$runRepos = -not $skipRepos -and -not $appsOnly

if ($dryRun) {
    Write-Host "=== DRY RUN MODE ===" -ForegroundColor Yellow
    Write-Host "No changes will be made. This is a preview." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "=== jrl_env Setup for Windows 11 ===" -ForegroundColor Cyan
Write-Host ""

# Validate configs first
Write-Host "Validating configuration files..." -ForegroundColor Yellow
& "$PSScriptRoot\validate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Validation had issues. Continuing anyway..."
}
Write-Host ""

# Backup function
function backupConfigs {
    if ($noBackup -or $dryRun) { return }
    
    $backupDir = Join-Path $env:TEMP "jrl_env_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    
    Write-Host "Creating backup..." -ForegroundColor Yellow
    
    # Backup Git config
    $gitConfigPath = "$env:USERPROFILE\.gitconfig"
    if (Test-Path $gitConfigPath) {
        Copy-Item $gitConfigPath "$backupDir\gitconfig" -ErrorAction SilentlyContinue
    }
    
    # Backup Cursor settings
    $cursorSettingsPath = "$env:APPDATA\Cursor\User\settings.json"
    if (Test-Path $cursorSettingsPath) {
        $cursorBackupDir = Join-Path $backupDir "Cursor"
        New-Item -ItemType Directory -Path $cursorBackupDir -Force | Out-Null
        Copy-Item $cursorSettingsPath "$cursorBackupDir\settings.json" -ErrorAction SilentlyContinue
    }
    
    Write-Host "  ✓ Backup created: $backupDir" -ForegroundColor Green
    Write-Host ""
}

# Check dependencies
function testDependencies {
    $missing = @()
    
    if (-not (isGitInstalled)) {
        $missing += "Git"
    }
    
    if (-not (isWingetInstalled)) {
        $missing += "winget (Windows Package Manager)"
    }
    
    if ($missing.Count -gt 0) {
        Write-Host "Missing dependencies:" -ForegroundColor Yellow
        foreach ($dep in $missing) {
            Write-Host "  ✗ $dep" -ForegroundColor Red
        }
        Write-Host ""
        Write-Host "Some features may not work. Continue anyway? (Y/N): " -NoNewline -ForegroundColor Yellow
        $response = Read-Host
        if ($response -notmatch '^[Yy]') {
            exit 1
        }
        Write-Host ""
    }
}

if (-not $dryRun) {
    testDependencies
    backupConfigs
}

# Get script directory
$scriptRoot = $PSScriptRoot

# Dot-source all required scripts
. "$scriptRoot\updateStore.ps1"
. "$scriptRoot\configureWin11.ps1"
. "$scriptRoot\installFonts.ps1"
. "$scriptRoot\installApps.ps1"
. "$scriptRoot\configureGit.ps1"
. "$scriptRoot\configureCursor.ps1"
. "$scriptRoot\cloneRepositories.ps1"

Write-Host "Starting complete environment setup..." -ForegroundColor Cyan
Write-Host ""

# 1. Update Windows Store and winget
Write-Host "=== Step 1: Updating package managers ===" -ForegroundColor Yellow
Write-Host ""
if (-not (updateWinget)) {
    Write-Warning "winget update failed, continuing..."
}
Write-Host ""
if (-not (updateMicrosoftStore)) {
    Write-Warning "Microsoft Store update failed, continuing..."
}
Write-Host ""

# 2. Configure Windows 11 settings
Write-Host "=== Step 2: Configuring Windows 11 ===" -ForegroundColor Yellow
Write-Host ""
if (-not (configureWin11)) {
    Write-Warning "Windows 11 configuration had some issues, continuing..."
}
Write-Host ""

# 3. Install fonts
if ($runFonts) {
    if ($dryRun) {
        Write-Host "=== Step 3: Installing fonts (DRY RUN) ===" -ForegroundColor Yellow
        Write-Host "Would install fonts from fonts.json" -ForegroundColor Gray
    } else {
        Write-Host "=== Step 3: Installing fonts ===" -ForegroundColor Yellow
        Write-Host ""
        if (-not (installGoogleFonts)) {
            Write-Warning "Font installation had some issues, continuing..."
        }
    }
    Write-Host ""
}

# 4. Install applications
if ($runApps) {
    if ($dryRun) {
        Write-Host "=== Step 4: Installing applications (DRY RUN) ===" -ForegroundColor Yellow
        Write-Host "Would install/update apps from win11Apps.json" -ForegroundColor Gray
    } else {
        Write-Host "=== Step 4: Installing applications ===" -ForegroundColor Yellow
        Write-Host ""
        if (-not (installOrUpdateApps)) {
            Write-Warning "Application installation had some issues, continuing..."
        }
    }
    Write-Host ""
}

# 5. Configure Git
if ($runGit) {
    if ($dryRun) {
        Write-Host "=== Step 5: Configuring Git (DRY RUN) ===" -ForegroundColor Yellow
        Write-Host "Would configure Git from gitConfig.json" -ForegroundColor Gray
    } else {
        Write-Host "=== Step 5: Configuring Git ===" -ForegroundColor Yellow
        Write-Host ""
        if (-not (configureGit)) {
            Write-Warning "Git configuration had some issues, continuing..."
        }
    }
    Write-Host ""
}

# 6. Configure Cursor
if ($runCursor) {
    if ($dryRun) {
        Write-Host "=== Step 6: Configuring Cursor (DRY RUN) ===" -ForegroundColor Yellow
        Write-Host "Would configure Cursor from cursorSettings.json" -ForegroundColor Gray
    } else {
        Write-Host "=== Step 6: Configuring Cursor ===" -ForegroundColor Yellow
        Write-Host ""
        if (-not (configureCursor)) {
            Write-Warning "Cursor configuration had some issues, continuing..."
        }
    }
    Write-Host ""
}

# 7. Clone repositories (only on first run)
if ($runRepos) {
    if ($dryRun) {
        Write-Host "=== Step 7: Cloning repositories (DRY RUN) ===" -ForegroundColor Yellow
        Write-Host "Would clone repositories from repositories.json" -ForegroundColor Gray
    } else {
        Write-Host "=== Step 7: Cloning repositories ===" -ForegroundColor Yellow
        Write-Host ""
        
        # Check if repositories have already been cloned
        $configPath = Join-Path (Join-Path $scriptRoot "..\configs") "repositories.json"
        if (Test-Path $configPath) {
            try {
                $jsonContent = Get-Content $configPath -Raw | ConvertFrom-Json
                $workPath = $jsonContent.workPathWindows
                
                # Check if work directory exists and has any owner subdirectories
                if (Test-Path $workPath) {
                    $ownerDirs = Get-ChildItem -Path $workPath -Directory -ErrorAction SilentlyContinue
                    if ($ownerDirs.Count -gt 0) {
                        Write-Host "Repositories directory already exists with content. Skipping repository cloning." -ForegroundColor Yellow
                        Write-Host "To clone repositories manually, run: .\win11\cloneRepositories.ps1" -ForegroundColor Gray
                        Write-Host ""
                    } else {
                        if (-not (cloneRepositories)) {
                            Write-Warning "Repository cloning had some issues, continuing..."
                        }
                        Write-Host ""
                    }
                } else {
                    if (-not (cloneRepositories)) {
                        Write-Warning "Repository cloning had some issues, continuing..."
                    }
                    Write-Host ""
                }
            } catch {
                Write-Warning "Could not check repository status, skipping clone step."
                Write-Host ""
            }
        } else {
            Write-Host "Repository config not found, skipping clone step." -ForegroundColor Yellow
            Write-Host ""
        }
    }
    Write-Host ""
}

Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "All setup tasks have been executed." -ForegroundColor Green
Write-Host "Please review any warnings above and restart your computer if prompted." -ForegroundColor Yellow

