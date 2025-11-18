# Enhanced validation for Windows packages
# Checks if winget packages actually exist

param(
    [Parameter(Mandatory=$true)]
    [string]$configPath
)

$ErrorActionPreference = "Stop"

# Simple logging functions (no file logging needed for validation)
function writeSection
{
    param([string]$message)
    Write-Host "=== $message ===" -ForegroundColor Cyan
    Write-Host ""
}

function writeNote
{
    param([string]$message)
    Write-Host $message -ForegroundColor Yellow
}

function writeSuccess
{
    param([string]$message)
    Write-Host $message -ForegroundColor Green
}

function writeError
{
    param([string]$message)
    Write-Host $message -ForegroundColor Red
}

# Validate Windows packages
function validateWindowsPackages
{
    param(
        [string]$configPath
    )

    $errors = 0

    if (-not (Test-Path $configPath))
    {
        writeError "Config file not found: $configPath"
        return 1
    }

    writeSection "Validating Windows Packages"

    # Read and parse JSON config
    try
    {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
    }
    catch
    {
        writeError "Failed to parse JSON config: $_"
        return 1
    }

    # Validate winget packages using winstall.app API (much faster than winget commands)
    if ($config.winget -and $config.winget.Count -gt 0)
    {
        writeNote "Validating winget packages via winstall.app..."
        foreach ($package in $config.winget)
        {
            if ([string]::IsNullOrWhiteSpace($package))
            {
                continue
            }

            $found = $false

            # Check package existence via winstall.app (much faster than winget commands)
            try
            {
                $url = "https://winstall.app/apps/$package"
                $response = Invoke-WebRequest -Uri $url -TimeoutSec 5 -ErrorAction Stop

                # Valid packages return 200 and don't contain the error message
                # Invalid packages return 200 but contain "Sorry! We could not load this app"
                if ($response.StatusCode -eq 200 -and $response.Content -notmatch "Sorry! We could not load this app")
                {
                    $found = $true
                }
            }
            catch
            {
                # 404 or other error means package doesn't exist
                $found = $false
            }

            if ($found)
            {
                writeSuccess "  $package"
            }
            else
            {
                writeError "  $package (not found in winget)"
                $errors++
            }
        }
        Write-Host ""
    }

    if ($errors -eq 0)
    {
        writeSuccess "All Windows packages are valid!"
        return 0
    }
    else
    {
        writeError "Found $errors invalid package(s)"
        return 1
    }
}

# Main execution
# Run if script is executed directly (not sourced/dot-sourced)
if ($MyInvocation.InvocationName -ne '.' -or $PSCommandPath)
{
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $exitCode = validateWindowsPackages -configPath $configPath
    $stopwatch.Stop()
    Write-Host ""
    writeNote "Validation completed in $($stopwatch.Elapsed.TotalSeconds.ToString('F2'))s"
    exit $exitCode
}
