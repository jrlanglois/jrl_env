# Dot-source the updateStore.ps1 file to get shared winget functions
. "$PSScriptRoot\updateStore.ps1"

# Function to check if an app is installed via winget
function isAppInstalled
{
    <#
    .SYNOPSIS
    Checks if a specific application is installed via winget.

    .DESCRIPTION
    Uses winget list command to check if an application with the given identifier is installed.

    .PARAMETER appId
    The winget package identifier (e.g., "Microsoft.VisualStudioCode")

    .OUTPUTS
    Boolean. Returns $true if the app is installed, $false otherwise.

    .EXAMPLE
    if (isAppInstalled "Microsoft.VisualStudioCode")
    {
        Write-Host "VS Code is installed"
    }
    #>
    param(
        [Parameter(Mandatory=$true)]
        [string]$appId
    )

    try
    {
        $result = winget list --id $appId --accept-source-agreements 2>$null
        if ($LASTEXITCODE -eq 0)
        {
            # Check if the output contains the app ID (winget list returns 0 even if not found in some cases)
            $listOutput = winget list --id $appId --accept-source-agreements 2>$null | Out-String
            if ($listOutput -match $appId)
            {
                return $true
            }
        }
    }
    catch
    {
        Write-Error "Failed to check if app is installed: $_"
    }
    return $false
}

# Function to install or update apps from JSON config file
function installOrUpdateApps
{
    <#
    .SYNOPSIS
    Installs or updates applications listed in a JSON configuration file.

    .DESCRIPTION
    Reads a JSON file containing winget and/or Windows Store app identifiers and installs
    or updates each application. The JSON file should have an object with "winget" and "windowsStore"
    arrays. If an app is not installed, it will be installed. If it's already installed, it will be
    updated to the latest version (winget apps only; Store apps are installed only).

    .PARAMETER configPath
    Path to the JSON configuration file. Defaults to "win11Apps.json" in the same directory as the script.

    .OUTPUTS
    Boolean. Returns $true if all operations completed (some may have failed), $false if critical error occurred.

    .EXAMPLE
        installOrUpdateApps -configPath "C:\path\to\win11Apps.json"

    .EXAMPLE
    installOrUpdateApps
    #>
    param(
        [Parameter(Mandatory=$false)]
        [string]$configPath = (Join-Path (Join-Path $PSScriptRoot "..\configs") "win11Apps.json")
    )

    # Check if winget is installed, prompt user to install if not available
    if (-not (isWingetInstalled))
    {
        Write-Host "winget (Windows Package Manager) is not installed." -ForegroundColor Yellow
        $response = Read-Host "Would you like to install winget now? (Y/N)"
        if ($response -match '^[Yy]')
        {
            if (-not (installWinget))
            {
                Write-Error "Failed to install winget. Please install Windows Package Manager manually or run as Administrator."
                return $false
            }
        }
        else
        {
            Write-Error "winget is required to install/update apps. Please install it manually or run this script again and choose 'Y' when prompted."
            return $false
        }
    }

    # Check if config file exists
    if (-not (Test-Path $configPath))
    {
        Write-Error "Configuration file not found: $configPath"
        return $false
    }

    # Read and parse JSON file
    try
    {
        $jsonContent = Get-Content $configPath -Raw | ConvertFrom-Json
        
        # Handle both object format (with winget/windowsStore) and array format (legacy)
        $wingetApps = @()
        $storeApps = @()
        
        if ($jsonContent.PSObject.Properties.Name -contains "winget")
        {
            # New format with separate arrays
            $wingetApps = $jsonContent.winget
            $storeApps = $jsonContent.windowsStore
        }
        elseif ($jsonContent -is [Array])
        {
            # Legacy format - treat as winget apps
            $wingetApps = $jsonContent
        }
        else
        {
            Write-Error "JSON file must contain either an object with 'winget' and 'windowsStore' arrays, or a simple array of app identifiers."
            return $false
        }
    }
    catch
    {
        Write-Error "Failed to parse JSON file: $_"
        return $false
    }

    $totalApps = $wingetApps.Count + $storeApps.Count
    Write-Host "Found $totalApps app(s) in configuration file ($($wingetApps.Count) winget, $($storeApps.Count) Windows Store)." -ForegroundColor Cyan
    Write-Host ""

    $installedCount = 0
    $updatedCount = 0
    $failedCount = 0

    # Process winget apps
    if ($wingetApps.Count -gt 0)
    {
        Write-Host "=== Processing winget apps ===" -ForegroundColor Cyan
        Write-Host ""
        
        foreach ($appId in $wingetApps)
        {
            Write-Host "Processing: $appId" -ForegroundColor Yellow

            if (isAppInstalled $appId)
            {
                Write-Host "  App is installed. Updating..." -ForegroundColor Cyan
                try
                {
                    winget upgrade --id $appId --accept-package-agreements --accept-source-agreements --silent 2>&1 | Out-Null
                    if ($LASTEXITCODE -eq 0)
                    {
                        Write-Host "  ✓ Updated successfully" -ForegroundColor Green
                        $updatedCount++
                    }
                    else
                    {
                        Write-Host "  ⚠ Update check completed (may already be up to date)" -ForegroundColor Yellow
                        $updatedCount++
                    }
                }
                catch
                {
                    Write-Host "  ✗ Update failed: $_" -ForegroundColor Red
                    $failedCount++
                }
            }
            else
            {
                Write-Host "  App is not installed. Installing..." -ForegroundColor Cyan
                try
                {
                    winget install --id $appId --accept-package-agreements --accept-source-agreements --silent 2>&1 | Out-Null
                    if ($LASTEXITCODE -eq 0)
                    {
                        Write-Host "  ✓ Installed successfully" -ForegroundColor Green
                        $installedCount++
                    }
                    else
                    {
                        Write-Host "  ✗ Installation failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
                        $failedCount++
                    }
                }
                catch
                {
                    Write-Host "  ✗ Installation failed: $_" -ForegroundColor Red
                    $failedCount++
                }
            }
            Write-Host ""
        }
    }

    # Process Windows Store apps
    if ($storeApps.Count -gt 0)
    {
        Write-Host "=== Processing Windows Store apps ===" -ForegroundColor Cyan
        Write-Host ""
        
        foreach ($appId in $storeApps)
        {
            Write-Host "Processing: $appId" -ForegroundColor Yellow
            Write-Host "  Installing from Windows Store..." -ForegroundColor Cyan
            
            try
            {
                winget install --id $appId --source msstore --accept-package-agreements --accept-source-agreements --silent 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0)
                {
                    Write-Host "  ✓ Installed successfully" -ForegroundColor Green
                    $installedCount++
                }
                else
                {
                    Write-Host "  ✗ Installation failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
                    $failedCount++
                }
            }
            catch
            {
                Write-Host "  ✗ Installation failed: $_" -ForegroundColor Red
                $failedCount++
            }
            Write-Host ""
        }
    }

    # Summary
    Write-Host "Summary:" -ForegroundColor Cyan
    Write-Host "  Installed: $installedCount" -ForegroundColor Green
    Write-Host "  Updated: $updatedCount" -ForegroundColor Green
    if ($failedCount -gt 0)
    {
        Write-Host "  Failed: $failedCount" -ForegroundColor Red
    }

    return $true
}
