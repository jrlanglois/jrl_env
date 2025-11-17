# Script to check status of installed applications, configurations, and repositories

$ErrorActionPreference = "Continue"

$scriptRoot = $PSScriptRoot
$configsPath = Join-Path $scriptRoot "..\configs"

Write-Host "=== jrl_env Status Check ===" -ForegroundColor Cyan
Write-Host ""

# Dot-source required scripts
. "$scriptRoot\updateStore.ps1"
. "$scriptRoot\configureGit.ps1"

# Check Git
Write-Host "Git:" -ForegroundColor Yellow
if (isGitInstalled)
{
    $gitVersion = git --version 2>$null
    Write-Host "  ✓ Installed: $gitVersion" -ForegroundColor Green
    
    $gitName = git config --global user.name 2>$null
    $gitEmail = git config --global user.email 2>$null
    if ($gitName -and $gitEmail)
    {
        Write-Host "  ✓ Configured: $gitName <$gitEmail>" -ForegroundColor Green
    }
    else
    {
        Write-Host "  ⚠ Not configured" -ForegroundColor Yellow
    }
}
else
{
    Write-Host "  ✗ Not installed" -ForegroundColor Red
}
Write-Host ""

# Check winget
Write-Host "Windows Package Manager (winget):" -ForegroundColor Yellow
if (isWingetInstalled)
{
    $wingetVersion = winget --version 2>$null
    Write-Host "  ✓ Installed: $wingetVersion" -ForegroundColor Green
}
else
{
    Write-Host "  ✗ Not installed" -ForegroundColor Red
}
Write-Host ""

# Check installed apps
if (Test-Path (Join-Path $configsPath "win11Apps.json"))
{
    Write-Host "Installed Applications:" -ForegroundColor Yellow
    try
    {
        $apps = Get-Content (Join-Path $configsPath "win11Apps.json") -Raw | ConvertFrom-Json
        $installed = 0
        $notInstalled = 0
        
        if ($apps.winget)
        {
            foreach ($app in $apps.winget)
            {
                if (isAppInstalled $app)
                {
                    $installed++
                }
                else
                {
                    $notInstalled++
                    Write-Host "  ✗ $app" -ForegroundColor Red
                }
            }
        }
        
        if ($installed -gt 0)
        {
            Write-Host "  ✓ $installed winget app(s) installed" -ForegroundColor Green
        }
        if ($notInstalled -gt 0)
        {
            Write-Host "  ⚠ $notInstalled app(s) not installed" -ForegroundColor Yellow
        }
    }
    catch
    {
        Write-Host "  ⚠ Could not check apps: $_" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Check repositories
if (Test-Path (Join-Path $configsPath "repositories.json"))
{
    Write-Host "Repositories:" -ForegroundColor Yellow
    try
    {
        $repos = Get-Content (Join-Path $configsPath "repositories.json") -Raw | ConvertFrom-Json
        $workPath = $repos.workPathWindows
        
        if (Test-Path $workPath)
        {
            $ownerDirs = Get-ChildItem -Path $workPath -Directory -ErrorAction SilentlyContinue
            Write-Host "  ✓ Work directory exists: $workPath" -ForegroundColor Green
            Write-Host "  ✓ $($ownerDirs.Count) owner directory/directories found" -ForegroundColor Green
            
            $totalRepos = 0
            foreach ($dir in $ownerDirs)
            {
                $repoCount = (Get-ChildItem -Path $dir.FullName -Directory -ErrorAction SilentlyContinue | Where-Object { Test-Path (Join-Path $_.FullName ".git") }).Count
                $totalRepos += $repoCount
            }
            Write-Host "  ✓ $totalRepos repository/repositories cloned" -ForegroundColor Green
        }
        else
        {
            Write-Host "  ⚠ Work directory does not exist: $workPath" -ForegroundColor Yellow
        }
    }
    catch
    {
        Write-Host "  ⚠ Could not check repositories: $_" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Check Cursor
Write-Host "Cursor:" -ForegroundColor Yellow
$cursorSettingsPath = "$env:APPDATA\Cursor\User\settings.json"
if (Test-Path $cursorSettingsPath)
{
    Write-Host "  ✓ Settings file exists" -ForegroundColor Green
}
else
{
    Write-Host "  ⚠ Settings file not found" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "=== Status Check Complete ===" -ForegroundColor Cyan
