# Update script for Windows 11
# Pulls latest changes and re-runs setup

$ErrorActionPreference = "Stop"

Write-Host "=== jrl_env Update ===" -ForegroundColor Cyan
Write-Host ""

# Get repository root (parent of win11 directory)
$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$win11Dir = $PSScriptRoot

# Check if we're in a git repository
if (-not (Test-Path (Join-Path $repoRoot ".git")))
{
    Write-Error "Not a git repository. Please clone the repository first."
    exit 1
}

Write-Host "Pulling latest changes..." -ForegroundColor Yellow
Set-Location $repoRoot

try
{
    git pull
    if ($LASTEXITCODE -ne 0)
    {
        Write-Warning "Git pull had issues. Continuing anyway..."
    }
}
catch
{
    Write-Warning "Failed to pull latest changes: $_"
    Write-Host "Continuing with current version..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Re-running setup..." -ForegroundColor Yellow
Write-Host ""

# Run the setup script
& "$win11Dir\setup.ps1"

