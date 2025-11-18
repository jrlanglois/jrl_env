# Function to check if winget is installed
function isWingetInstalled
{
    <#
    .SYNOPSIS
    Checks if Windows Package Manager (winget) is installed and available.

    .DESCRIPTION
    Verifies that winget is installed and accessible in the current PowerShell session.

    .OUTPUTS
    Boolean. Returns $true if winget is available, $false otherwise.

    .EXAMPLE
    if (isWingetInstalled)
    {
        Write-Host "winget is available"
    }
    #>
    try
    {
        $wingetVersion = winget --version 2>$null
        if ($LASTEXITCODE -eq 0)
        {
            return $true
        }
        return $false
    }
    catch
    {
        return $false
    }
}

# Function to install winget (Windows Package Manager)
function installWinget
{
    <#
    .SYNOPSIS
    Installs Windows Package Manager (winget) if it's not already installed.

    .DESCRIPTION
    Downloads and installs winget using the official installation script.
    Requires administrative privileges to execute successfully.

    .OUTPUTS
    Boolean. Returns $true if installation was successful or already installed, $false otherwise.

    .EXAMPLE
    installWinget

    .NOTES
    Requires administrative privileges. Run PowerShell as Administrator.
    #>
    param()

    # Check if already installed
    if (isWingetInstalled)
    {
        Write-Host "winget is already installed." -ForegroundColor Green
        return $true
    }

    Write-Host "Installing winget (Windows Package Manager)..." -ForegroundColor Cyan

    try
    {
        # Check if running as administrator
        $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        if (-not $isAdmin)
        {
            Write-Error "Administrative privileges are required to install winget. Please run PowerShell as Administrator."
            return $false
        }

        # Download and execute the winget installation script
        $installScript = 'https://aka.ms/getwinget'
        Write-Host "Downloading winget installation script..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $installScript -OutFile "$env:TEMP\Microsoft.DesktopAppInstaller.msixbundle" -UseBasicParsing

        # Install the MSIX bundle
        Write-Host "Installing winget..." -ForegroundColor Yellow
        Add-AppxPackage -Path "$env:TEMP\Microsoft.DesktopAppInstaller.msixbundle"

        # Clean up
        Remove-Item "$env:TEMP\Microsoft.DesktopAppInstaller.msixbundle" -ErrorAction SilentlyContinue

        # Refresh environment variables to make winget available in current session
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

        # Verify installation
        Start-Sleep -Seconds 2
        if (isWingetInstalled)
        {
            Write-Host "winget installed successfully!" -ForegroundColor Green
            return $true
        }
        else
        {
            Write-Warning "winget installation completed, but it may not be available in this session. Please restart PowerShell."
            return $false
        }
    }
    catch
    {
        Write-Error "Failed to install winget: $_"
        return $false
    }
}

# Function to update Microsoft Store using winget
function updateMicrosoftStore
{
    <#
    .SYNOPSIS
    Updates the Microsoft Store application using winget.

    .DESCRIPTION
    Uses Windows Package Manager (winget) to update the Microsoft Store application.
    This function first checks if winget is installed before attempting the update.

    .OUTPUTS
    Boolean. Returns $true if the update was successful, $false otherwise.

    .EXAMPLE
    updateMicrosoftStore

    .NOTES
    Requires winget to be installed. Run as Administrator for best results.
    #>
    param()

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
            Write-Error "winget is required to update Microsoft Store. Please install it manually or run this script again and choose 'Y' when prompted."
            return $false
        }
    }

    Write-Host "Updating Microsoft Store using winget..." -ForegroundColor Cyan

    try
    {
        # Update Microsoft Store specifically
        winget upgrade "Microsoft.WindowsStore" --accept-package-agreements --accept-source-agreements

        if ($LASTEXITCODE -eq 0)
        {
            Write-Host "Microsoft Store update completed successfully." -ForegroundColor Green
            return $true
        }
        else
        {
            Write-Warning "Microsoft Store update may have failed or no update was available. Exit code: $LASTEXITCODE"
            return $false
        }
    }
    catch
    {
        Write-Error "Failed to update Microsoft Store: $_"
        return $false
    }
}

# Function to update winget (Windows Package Manager) itself
function updateWinget
{
    <#
    .SYNOPSIS
    Updates Windows Package Manager (winget) to the latest version.

    .DESCRIPTION
    Updates winget by upgrading the Microsoft.DesktopAppInstaller package.
    Requires administrative privileges to execute successfully.

    .OUTPUTS
    Boolean. Returns $true if the update was successful, $false otherwise.

    .EXAMPLE
    updateWinget

    .NOTES
    Requires winget to be installed. Run as Administrator for best results.
    #>
    param()

    # Check if winget is installed
    if (-not (isWingetInstalled))
    {
        Write-Error "winget is not installed. Please install it first using installWinget."
        return $false
    }

    Write-Host "Updating winget (Windows Package Manager)..." -ForegroundColor Cyan

    try
    {
        # Check if running as administrator
        $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        if (-not $isAdmin)
        {
            Write-Warning "Administrative privileges are recommended for updating winget. Continuing anyway..."
        }

        # Update winget by upgrading the DesktopAppInstaller
        winget upgrade --id Microsoft.DesktopAppInstaller --accept-package-agreements --accept-source-agreements

        if ($LASTEXITCODE -eq 0)
        {
            Write-Host "winget update completed successfully." -ForegroundColor Green

            # Refresh environment variables
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

            return $true
        }
        else
        {
            Write-Warning "winget update may have failed or no update was available. Exit code: $LASTEXITCODE"
            return $false
        }
    }
    catch
    {
        Write-Error "Failed to update winget: $_"
        return $false
    }
}
