# Script to validate JSON configuration files
# Checks syntax, required fields, and basic validity

$ErrorActionPreference = "Stop"

$scriptRoot = $PSScriptRoot
$configsPath = Join-Path $scriptRoot "..\configs"

$errors = @()
$warnings = @()

Write-Host "=== Validating Configuration Files ===" -ForegroundColor Cyan
Write-Host ""

# Function to validate JSON file
function validateJsonFile
{
    param(
        [string]$filePath,
        [string]$description
    )
    
    if (-not (Test-Path $filePath))
    {
        $script:errors += "${description}: File not found: $filePath"
        return $false
    }
    
    try
    {
        $content = Get-Content $filePath -Raw
        $json = $content | ConvertFrom-Json
        
        Write-Host "✓ $description" -ForegroundColor Green
        return $true
    }
    catch
    {
        $script:errors += "${description}: Invalid JSON - $_"
        return $false
    }
}

# Function to validate apps JSON
function validateAppsJson
{
    param([string]$filePath, [string]$platform)
    
    try
    {
        $content = Get-Content $filePath -Raw | ConvertFrom-Json
        
        if ($platform -eq "win11")
        {
            if (-not $content.winget -and -not $content.windowsStore)
            {
                $script:warnings += "${platform} apps: No apps specified"
            }
            if ($content.winget -and $content.winget.Count -eq 0)
            {
                $script:warnings += "${platform} apps: winget array is empty"
            }
            if ($content.windowsStore -and $content.windowsStore.Count -eq 0)
            {
                $script:warnings += "${platform} apps: windowsStore array is empty"
            }
        }
        elseif ($platform -eq "macos")
        {
            if (-not $content.brew -and -not $content.brewCask)
            {
                $script:warnings += "${platform} apps: No apps specified"
            }
        }
        elseif ($platform -eq "ubuntu")
        {
            if (-not $content.apt -and -not $content.snap)
            {
                $script:warnings += "${platform} apps: No apps specified"
            }
        }
    }
    catch
    {
        $script:errors += "${platform} apps: Validation failed - $_"
    }
}

# Function to validate repositories JSON
function validateRepositoriesJson
{
    param([string]$filePath)
    
    try
    {
        $content = Get-Content $filePath -Raw | ConvertFrom-Json
        
        if (-not $content.workPathWindows -and -not $content.workPathUnix)
        {
            $script:errors += "repositories: Missing workPathWindows or workPathUnix"
        }
        
        if (-not $content.repositories)
        {
            $script:warnings += "repositories: No repositories specified"
        }
        elseif ($content.repositories.Count -eq 0)
        {
            $script:warnings += "repositories: repositories array is empty"
        }
        
        # Validate repository URLs
        foreach ($repo in $content.repositories)
        {
            if ($repo -notmatch '^(https://|git@)')
            {
                $script:warnings += "repositories: Invalid URL format: $repo"
            }
        }
    }
    catch
    {
        $script:errors += "repositories: Validation failed - $_"
    }
}

# Function to validate Git config JSON
function validateGitConfigJson
{
    param([string]$filePath)
    
    try
    {
        $content = Get-Content $filePath -Raw | ConvertFrom-Json
        
        if (-not $content.user)
        {
            $script:warnings += "gitConfig: No user section specified"
        }
        else
        {
            if (-not $content.user.name)
            {
                $script:warnings += "gitConfig: Missing user.name"
            }
            if (-not $content.user.email)
            {
                $script:warnings += "gitConfig: Missing user.email"
            }
        }
        
        if (-not $content.defaults)
        {
            $script:warnings += "gitConfig: No defaults section specified"
        }
        
        if (-not $content.aliases)
        {
            $script:warnings += "gitConfig: No aliases section specified"
        }
    }
    catch
    {
        $script:errors += "gitConfig: Validation failed - $_"
    }
}

# Validate all config files
Write-Host "Validating JSON files..." -ForegroundColor Yellow
Write-Host ""

# Apps configs
if (validateJsonFile (Join-Path $configsPath "win11Apps.json") "win11Apps.json")
{
    validateAppsJson (Join-Path $configsPath "win11Apps.json") "win11"
}
if (validateJsonFile (Join-Path $configsPath "macosApps.json") "macosApps.json")
{
    validateAppsJson (Join-Path $configsPath "macosApps.json") "macos"
}
if (validateJsonFile (Join-Path $configsPath "ubuntuApps.json") "ubuntuApps.json")
{
    validateAppsJson (Join-Path $configsPath "ubuntuApps.json") "ubuntu"
}

# Other configs
if (validateJsonFile (Join-Path $configsPath "fonts.json") "fonts.json")
{
    try
    {
        $fonts = Get-Content (Join-Path $configsPath "fonts.json") -Raw | ConvertFrom-Json
        if (-not $fonts.googleFonts -or $fonts.googleFonts.Count -eq 0)
        {
            $warnings += "fonts: No fonts specified"
        }
    }
    catch
    {
        $errors += "fonts: Validation failed - $_"
    }
}

if (validateJsonFile (Join-Path $configsPath "repositories.json") "repositories.json")
{
    validateRepositoriesJson (Join-Path $configsPath "repositories.json")
}

if (validateJsonFile (Join-Path $configsPath "gitConfig.json") "gitConfig.json")
{
    validateGitConfigJson (Join-Path $configsPath "gitConfig.json")
}

if (validateJsonFile (Join-Path $configsPath "cursorSettings.json") "cursorSettings.json")
{
    Write-Host "  ✓ cursorSettings.json structure valid" -ForegroundColor Gray
}

Write-Host ""

# Report results
if ($errors.Count -eq 0 -and $warnings.Count -eq 0)
{
    Write-Host "✓ All configuration files are valid!" -ForegroundColor Green
    exit 0
}
else
{
    if ($warnings.Count -gt 0)
    {
        Write-Host "Warnings:" -ForegroundColor Yellow
        foreach ($warning in $warnings)
        {
            Write-Host "  ⚠ $warning" -ForegroundColor Yellow
        }
        Write-Host ""
    }
    
    if ($errors.Count -gt 0)
    {
        Write-Host "Errors:" -ForegroundColor Red
        foreach ($error in $errors)
        {
            Write-Host "  ✗ $error" -ForegroundColor Red
        }
        Write-Host ""
        Write-Host "✗ Validation failed. Please fix errors before running setup." -ForegroundColor Red
        exit 1
    }
    else
    {
        Write-Host "✓ Validation passed with warnings." -ForegroundColor Green
        exit 0
    }
}
