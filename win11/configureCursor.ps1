# Script to configure Cursor editor settings from cursorSettings.json
# Merges settings from config file into Cursor's settings.json

# Function to get Cursor settings path
function getCursorSettingsPath {
    $cursorPath = "$env:APPDATA\Cursor\User\settings.json"
    return $cursorPath
}

# Function to configure Cursor settings
function configureCursor {
    param(
        [Parameter(Mandatory=$false)]
        [string]$configPath = (Join-Path (Join-Path $PSScriptRoot "..\configs") "cursorSettings.json")
    )

    Write-Host "=== Cursor Configuration ===" -ForegroundColor Cyan
    Write-Host ""

    # Check if config file exists
    if (-not (Test-Path $configPath)) {
        Write-Error "Configuration file not found: $configPath"
        return $false
    }

    # Get Cursor settings path
    $cursorSettingsPath = getCursorSettingsPath
    $cursorUserDir = Split-Path $cursorSettingsPath -Parent

    # Create Cursor User directory if it doesn't exist
    if (-not (Test-Path $cursorUserDir)) {
        Write-Host "Creating Cursor User directory..." -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $cursorUserDir -Force | Out-Null
    }

    try {
        # Read config file
        Write-Host "Reading configuration from: $configPath" -ForegroundColor Cyan
        $configContent = Get-Content $configPath -Raw | ConvertFrom-Json

        # Read existing settings if they exist
        $existingSettings = @{}
        if (Test-Path $cursorSettingsPath) {
            Write-Host "Reading existing Cursor settings..." -ForegroundColor Yellow
            try {
                $existingContent = Get-Content $cursorSettingsPath -Raw | ConvertFrom-Json
                $existingContent.PSObject.Properties | ForEach-Object {
                    $existingSettings[$_.Name] = $_.Value
                }
            } catch {
                Write-Warning "Failed to parse existing settings.json. Creating new file."
            }
        }

        # Merge config settings with existing settings (config takes precedence)
        Write-Host "Merging settings..." -ForegroundColor Yellow
        $configContent.PSObject.Properties | ForEach-Object {
            $existingSettings[$_.Name] = $_.Value
        }

        # Convert merged settings back to JSON
        $mergedJson = $existingSettings | ConvertTo-Json -Depth 10

        # Write to Cursor settings file
        Write-Host "Writing settings to: $cursorSettingsPath" -ForegroundColor Yellow
        $mergedJson | Set-Content -Path $cursorSettingsPath -Encoding UTF8

        Write-Host "✓ Cursor settings configured successfully!" -ForegroundColor Green
        Write-Host "Note: You may need to restart Cursor for all changes to take effect." -ForegroundColor Yellow
        return $true
    } catch {
        Write-Error "Failed to configure Cursor settings: $_"
        return $false
    }
}

# Export functions
Export-ModuleMember -Function configureCursor, getCursorSettingsPath
