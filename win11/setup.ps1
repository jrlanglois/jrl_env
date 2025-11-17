# Master setup script for Windows 11
# Runs all configuration and installation scripts in the correct order

$ErrorActionPreference = "Stop"

Write-Host "=== jrl_env Setup for Windows 11 ===" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptRoot = $PSScriptRoot

# Dot-source all required scripts
. "$ScriptRoot\updateStore.ps1"
. "$ScriptRoot\configureWin11.ps1"
. "$ScriptRoot\installFonts.ps1"
. "$ScriptRoot\installApps.ps1"
. "$ScriptRoot\configureGit.ps1"
. "$ScriptRoot\configureCursor.ps1"
. "$ScriptRoot\cloneRepositories.ps1"

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
Write-Host "=== Step 3: Installing fonts ===" -ForegroundColor Yellow
Write-Host ""
if (-not (installGoogleFonts)) {
    Write-Warning "Font installation had some issues, continuing..."
}
Write-Host ""

# 4. Install applications
Write-Host "=== Step 4: Installing applications ===" -ForegroundColor Yellow
Write-Host ""
if (-not (installOrUpdateApps)) {
    Write-Warning "Application installation had some issues, continuing..."
}
Write-Host ""

# 5. Configure Git
Write-Host "=== Step 5: Configuring Git ===" -ForegroundColor Yellow
Write-Host ""
if (-not (configureGit)) {
    Write-Warning "Git configuration had some issues, continuing..."
}
Write-Host ""

# 6. Configure Cursor
Write-Host "=== Step 6: Configuring Cursor ===" -ForegroundColor Yellow
Write-Host ""
if (-not (configureCursor)) {
    Write-Warning "Cursor configuration had some issues, continuing..."
}
Write-Host ""

# 7. Clone repositories (only on first run)
Write-Host "=== Step 7: Cloning repositories ===" -ForegroundColor Yellow
Write-Host ""

# Check if repositories have already been cloned
$configPath = Join-Path (Join-Path $ScriptRoot "..\configs") "repositories.json"
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

Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "All setup tasks have been executed." -ForegroundColor Green
Write-Host "Please review any warnings above and restart your computer if prompted." -ForegroundColor Yellow

