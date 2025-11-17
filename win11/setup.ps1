# Master setup script for Windows 11
# Runs all configuration and installation scripts in the correct order

param(
    [switch]$skipFonts,
    [switch]$skipApps,
    [switch]$skipGit,
    [switch]$skipCursor,
    [switch]$skipRepos,
    [switch]$skipSsh,
    [switch]$appsOnly,
    [switch]$dryRun,
    [switch]$noBackup
)

$ErrorActionPreference = "Stop"

# Get script directory
$scriptRoot = $PSScriptRoot

# Load logging module
. "$scriptRoot\logging.ps1"

# Initialize logging
$logFile = initLogging
logInfo "=== jrl_env Setup for Windows 11 ==="
logInfo "Log file: $logFile"

# Parse flags
$runFonts = -not $skipFonts -and -not $appsOnly
$runApps = -not $skipApps -or $appsOnly
$runGit = -not $skipGit -and -not $appsOnly
$runCursor = -not $skipCursor -and -not $appsOnly
$runRepos = -not $skipRepos -and -not $appsOnly
$runSsh = -not $skipSsh -and -not $appsOnly

$configPath = Join-Path (Join-Path $scriptRoot "..\configs") "win11.json"
$osConfig = Get-Content $configPath -Raw | ConvertFrom-Json

function Invoke-OsCommands {
    param(
        [Parameter()]
        [ValidateSet("preInstall", "postInstall")]
        [string]$Phase
    )

    if ($null -eq $osConfig.commands) { return }
    $commands = $osConfig.commands.$Phase
    if (-not $commands) { return }

    foreach ($cmd in $commands)
    {
        $name = $cmd.name
        $shell = $cmd.shell
        $command = $cmd.command
        $runOnce = $cmd.runOnce
        $flagFile = Join-Path $env:LOCALAPPDATA ("jrl_env_" + $name + ".flag")

        if ($runOnce -and (Test-Path $flagFile))
        {
            logInfo "Skipping $name (already executed)"
            continue
        }

        if ($dryRun)
        {
            logInfo "DRY RUN: would execute command '$name'"
            continue
        }

        logInfo "Running command: $name"
        try
        {
            switch ($shell.ToLower())
            {
                "powershell"
                {
                    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command $command
                }
                default
                {
                    cmd.exe /c $command
                }
            }

            if ($runOnce)
            {
                New-Item -ItemType File -Path $flagFile -Force | Out-Null
            }
        }
        catch
        {
            logWarn "Command $name failed: $_"
        }
    }
}

if ($dryRun)
{
    logWarn "=== DRY RUN MODE ==="
    logWarn "No changes will be made. This is a preview."
}

logInfo "=== jrl_env Setup for Windows 11 ==="

# Validate configs first
logInfo "Validating configuration files..."
& "$scriptRoot\validate.ps1"
if ($LASTEXITCODE -ne 0)
{
    logWarn "Validation had issues. Continuing anyway..."
}

Invoke-OsCommands -Phase "preInstall"

# Backup function
function backupConfigs
{
    if ($noBackup -or $dryRun)
    {
        logInfo "Backup skipped (noBackup or dryRun flag set)"
        return
    }

    $backupDir = Join-Path $env:TEMP "jrl_env_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

    logInfo "Creating backup..."

    # Backup Git config
    $gitConfigPath = "$env:USERPROFILE\.gitconfig"
    if (Test-Path $gitConfigPath)
    {
        Copy-Item $gitConfigPath "$backupDir\gitconfig" -ErrorAction SilentlyContinue
        logSuccess "Backed up Git config"
    }

    # Backup Cursor settings
    $cursorSettingsPath = "$env:APPDATA\Cursor\User\settings.json"
    if (Test-Path $cursorSettingsPath)
    {
        $cursorBackupDir = Join-Path $backupDir "Cursor"
        New-Item -ItemType Directory -Path $cursorBackupDir -Force | Out-Null
        Copy-Item $cursorSettingsPath "$cursorBackupDir\settings.json" -ErrorAction SilentlyContinue
        logSuccess "Backed up Cursor settings"
    }

    logSuccess "Backup created: $backupDir"
}

# Check dependencies
function testDependencies
{
    logInfo "Checking dependencies..."
    $missing = @()

    if (-not (isGitInstalled))
    {
        $missing += "Git"
        logWarn "Git is not installed"
    }
    else
    {
        logSuccess "Git is installed"
    }

    if (-not (isWingetInstalled))
    {
        $missing += "winget (Windows Package Manager)"
        logWarn "winget is not installed"
    }
    else
    {
        logSuccess "winget is installed"
    }

    if ($missing.Count -gt 0)
    {
        logWarn "Missing dependencies: $($missing -join ', ')"
        Write-Host "Some features may not work. Continue anyway? (Y/N): " -NoNewline -ForegroundColor Yellow
        $response = Read-Host
        if ($response -notmatch '^[Yy]')
        {
            logError "Setup cancelled by user due to missing dependencies"
            exit 1
        }
        logInfo "User chose to continue despite missing dependencies"
    }
    else
    {
        logSuccess "All dependencies are installed"
    }
}

if (-not $dryRun)
{
    testDependencies
    backupConfigs
}

# Dot-source all required scripts
. "$scriptRoot\updateStore.ps1"
. "$scriptRoot\configureWin11.ps1"
. "$scriptRoot\installFonts.ps1"
. "$scriptRoot\installApps.ps1"
. "$scriptRoot\configureGit.ps1"
. "$scriptRoot\configureCursor.ps1"
. "$scriptRoot\configureGithubSsh.ps1"
. "$scriptRoot\cloneRepositories.ps1"

logInfo "Starting complete environment setup..."

# 1. Update Windows Store and winget
if ($dryRun)
{
    logInfo "=== Step 1: Updating package managers (DRY RUN) ==="
    logInfo "Would update winget and Microsoft Store"
}
else
{
    logInfo "=== Step 1: Updating package managers ==="
    if (-not (updateWinget))
    {
        logWarn "winget update failed, continuing..."
    }
    else
    {
        logSuccess "winget updated successfully"
    }
    if (-not (updateMicrosoftStore))
    {
        logWarn "Microsoft Store update failed, continuing..."
    }
    else
    {
        logSuccess "Microsoft Store updated successfully"
    }
}

# 2. Configure Windows 11 settings
if ($dryRun)
{
    logInfo "=== Step 2: Configuring Windows 11 (DRY RUN) ==="
    logInfo "Would configure Windows 11 settings (regional, time, dark mode, File Explorer, privacy, taskbar, Developer Mode, notifications, WSL2)"
}
else
{
    logInfo "=== Step 2: Configuring Windows 11 ==="
    if (-not (configureWin11))
    {
        logWarn "Windows 11 configuration had some issues, continuing..."
    }
    else
    {
        logSuccess "Windows 11 configuration completed"
    }
}

# 3. Install fonts
if ($runFonts)
{
    if ($dryRun)
    {
        logInfo "=== Step 3: Installing fonts (DRY RUN) ==="
        logInfo "Would install fonts from fonts.json"
    }
    else
    {
        logInfo "=== Step 3: Installing fonts ==="
        if (-not (installGoogleFonts))
        {
            logWarn "Font installation had some issues, continuing..."
        }
        else
        {
            logSuccess "Font installation completed"
        }
    }
}

# 4. Install applications
if ($runApps)
{
    if ($dryRun)
    {
        logInfo "=== Step 4: Installing applications (DRY RUN) ==="
        logInfo "Would install/update apps from win11.json"
    }
    else
    {
        logInfo "=== Step 4: Installing applications ==="
        if (-not (installOrUpdateApps))
        {
            logWarn "Application installation had some issues, continuing..."
        }
        else
        {
            logSuccess "Application installation completed"
        }
    }
}

# 5. Configure Git
if ($runGit)
{
    if ($dryRun)
    {
        logInfo "=== Step 5: Configuring Git (DRY RUN) ==="
        logInfo "Would configure Git from gitConfig.json"
    }
    else
    {
        logInfo "=== Step 5: Configuring Git ==="
        if (-not (configureGit))
        {
            logWarn "Git configuration had some issues, continuing..."
        }
        else
        {
            logSuccess "Git configuration completed"
        }
    }
}

# 6. Configure GitHub SSH
if ($runSsh)
{
    if ($dryRun)
    {
        logInfo "=== Step 6: Configuring GitHub SSH (DRY RUN) ==="
        logInfo "Would generate SSH keys for GitHub."
    }
    else
    {
        logInfo "=== Step 6: Configuring GitHub SSH ==="
        if (-not (Configure-GithubSsh))
        {
            logWarn "GitHub SSH configuration had some issues, continuing..."
        }
        else
        {
            logSuccess "GitHub SSH configuration completed"
        }
    }
}

# 7. Configure Cursor
if ($runCursor)
{
    if ($dryRun)
    {
        logInfo "=== Step 7: Configuring Cursor (DRY RUN) ==="
        logInfo "Would configure Cursor from cursorSettings.json"
    }
    else
    {
        logInfo "=== Step 7: Configuring Cursor ==="
        if (-not (configureCursor))
        {
            logWarn "Cursor configuration had some issues, continuing..."
        }
        else
        {
            logSuccess "Cursor configuration completed"
        }
    }
}

# 8. Clone repositories (only on first run)
if ($runRepos)
{
    if ($dryRun)
    {
        logInfo "=== Step 8: Cloning repositories (DRY RUN) ==="
        logInfo "Would clone repositories from repositories.json"
    }
    else
    {
        logInfo "=== Step 7: Cloning repositories ==="

        # Check if repositories have already been cloned
        $configPath = Join-Path (Join-Path $scriptRoot "..\configs") "repositories.json"
        if (Test-Path $configPath)
        {
            try
            {
                $jsonContent = Get-Content $configPath -Raw | ConvertFrom-Json
                $workPath = $jsonContent.workPathWindows

                # Check if work directory exists and has any owner subdirectories
                if (Test-Path $workPath)
                {
                    $ownerDirs = Get-ChildItem -Path $workPath -Directory -ErrorAction SilentlyContinue
                    if ($ownerDirs.Count -gt 0)
                    {
                        logWarn "Repositories directory already exists with content. Skipping repository cloning."
                        logInfo "To clone repositories manually, run: .\win11\cloneRepositories.ps1"
                    }
                    else
                    {
                        if (-not (cloneRepositories))
                        {
                            logWarn "Repository cloning had some issues, continuing..."
                        }
                        else
                        {
                            logSuccess "Repository cloning completed"
                        }
                    }
                }
                else
                {
                    if (-not (cloneRepositories))
                    {
                        logWarn "Repository cloning had some issues, continuing..."
                    }
                    else
                    {
                        logSuccess "Repository cloning completed"
                    }
                }
            }
            catch
            {
                logWarn "Could not check repository status, skipping clone step."
            }
        }
        else
        {
            logWarn "Repository config not found, skipping clone step."
        }
    }
}

Invoke-OsCommands -Phase "postInstall"

logSuccess "=== Setup Complete ==="
logInfo "All setup tasks have been executed."
logInfo "Log file saved to: $logFile"
Write-Host "Please review any warnings above and restart your computer if prompted." -ForegroundColor Yellow