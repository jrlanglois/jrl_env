# Unified setup wrapper for Windows
# Auto-detects OS and runs the appropriate setup script

$ErrorActionPreference = "Stop"

# Get the directory where this script is located
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if Python 3 is available
$pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $pythonCmd)
{
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd)
    {
        Write-Host "Error: python3 or python is required but not found in PATH" -ForegroundColor Red
        Write-Host ""

        # Prompt user to install Python3
        $response = Read-Host "Would you like to install Python3? (y/N)"
        if ($response -notmatch "^[Yy]$")
        {
            Write-Host "Setup cancelled. Python3 is required to continue." -ForegroundColor Red
            exit 1
        }

        # Attempt to install Python3 via winget
        Write-Host "Installing Python3 via winget..."
        $installSuccess = $false

        if (Get-Command winget -ErrorAction SilentlyContinue)
        {
            try
            {
                winget install --id Python.Python.3 --accept-package-agreements --accept-source-agreements
                if ($LASTEXITCODE -eq 0)
                {
                    $installSuccess = $true
                    # Refresh PATH
                    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
                }
            }
            catch
            {
                Write-Host "Error: Failed to install Python3 via winget: $_" -ForegroundColor Red
            }
        }
        else
        {
            Write-Host "Error: winget not found. Please install Python3 manually:" -ForegroundColor Red
            Write-Host "  winget install Python.Python.3" -ForegroundColor Yellow
            Write-Host "Or download from: https://www.python.org/downloads/" -ForegroundColor Yellow
        }

        if (-not $installSuccess)
        {
            Write-Host "Failed to install Python3. Setup cancelled." -ForegroundColor Red
            exit 1
        }

        # Verify Python3 is now available
        $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
        if (-not $pythonCmd)
        {
            $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
            if (-not $pythonCmd)
            {
                Write-Host "Error: Python3 installation completed but python3 command not found in PATH." -ForegroundColor Red
                Write-Host "Please restart your terminal and try again." -ForegroundColor Yellow
                exit 1
            }
        }

        Write-Host "Python3 installed successfully!" -ForegroundColor Green
        Write-Host ""
    }
}

# Run the unified Python setup script
$setupScript = Join-Path $scriptDir "setup.py"
& $pythonCmd.Source $setupScript $args
