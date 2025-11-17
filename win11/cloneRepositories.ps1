# Script to clone Git repositories from repositories.json
# Clones repositories recursively (including submodules) to a configured work directory

# Dot-source configureGit.ps1 to get Git utility functions
. "$PSScriptRoot\configureGit.ps1"

# Function to check if a repository is already cloned
function isRepositoryCloned
{
    param(
        [Parameter(Mandatory=$true)]
        [string]$repoUrl,

        [Parameter(Mandatory=$true)]
        [string]$workPath
    )

    try
    {
        # Extract username and repository name from URL
        $owner = getRepositoryOwner -repoUrl $repoUrl
        $repoName = getRepositoryName -repoUrl $repoUrl

        if ([string]::IsNullOrWhiteSpace($owner) -or [string]::IsNullOrWhiteSpace($repoName))
        {
            return $false
        }

        $ownerPath = Join-Path $workPath $owner
        $repoPath = Join-Path $ownerPath $repoName

        if (Test-Path $repoPath)
        {
            # Check if it's actually a Git repository
            $gitPath = Join-Path $repoPath ".git"
            if (Test-Path $gitPath)
            {
                return $true
            }
        }
    }
    catch
    {
        # If we can't determine, assume not cloned
    }

    return $false
}

# Function to get username/organization from URL
function getRepositoryOwner
{
    param(
        [Parameter(Mandatory=$true)]
        [string]$repoUrl
    )

    try
    {
        # Extract username/organization from URL (handles both HTTPS and SSH)
        # Pattern: github.com/username/ or :username/
        if ($repoUrl -match '(?:github\.com/|:)([^/]+)/')
        {
            return $matches[1]
        }
        return $null
    }
    catch
    {
        return $null
    }
}

# Function to get repository name from URL
function getRepositoryName
{
    param(
        [Parameter(Mandatory=$true)]
        [string]$repoUrl
    )

    try
    {
        # Extract repository name from URL (handles both HTTPS and SSH)
        $repoName = $repoUrl -replace '.*[:/]([^/]+?)(?:\.git)?$', '$1'
        return $repoName
    }
    catch
    {
        return $null
    }
}

# Function to clone a single repository recursively
function cloneRepository
{
    param(
        [Parameter(Mandatory=$true)]
        [string]$repoUrl,

        [Parameter(Mandatory=$true)]
        [string]$workPath
    )

    try
    {
        $owner = getRepositoryOwner -repoUrl $repoUrl
        $repoName = getRepositoryName -repoUrl $repoUrl

        if ([string]::IsNullOrWhiteSpace($owner) -or [string]::IsNullOrWhiteSpace($repoName))
        {
            Write-Host "  ✗ Failed to extract owner or repository name from URL" -ForegroundColor Red
            return $false
        }

        # Create owner directory if it doesn't exist
        $ownerPath = Join-Path $workPath $owner
        if (-not (Test-Path $ownerPath))
        {
            New-Item -ItemType Directory -Path $ownerPath -Force | Out-Null
        }

        $repoPath = Join-Path $ownerPath $repoName

        # Check if already cloned
        if (isRepositoryCloned -repoUrl $repoUrl -workPath $workPath)
        {
            Write-Host "  ⚠ Repository already exists: $owner/$repoName" -ForegroundColor Yellow
            Write-Host "    Skipping clone. Use 'git pull' to update if needed." -ForegroundColor Gray
            return $true
        }

        Write-Host "  Cloning $owner/$repoName..." -ForegroundColor Yellow

        # Clone with recursive flag to include submodules
        $cloneOutput = git clone --recursive $repoUrl $repoPath 2>&1

        if ($LASTEXITCODE -eq 0)
        {
            Write-Host "    ✓ Cloned successfully" -ForegroundColor Green

            # Check if submodules were initialised
            $submodulePath = Join-Path $repoPath ".gitmodules"
            if (Test-Path $submodulePath)
            {
                Write-Host "    ✓ Submodules initialised" -ForegroundColor Green
            }

            return $true
        }
        else
        {
            Write-Host "    ✗ Clone failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
            if ($cloneOutput)
            {
                Write-Host "    Error: $cloneOutput" -ForegroundColor Red
            }
            return $false
        }
    }
    catch
    {
        Write-Host "    ✗ Clone failed: $_" -ForegroundColor Red
        return $false
    }
}

# Function to clone all repositories from JSON configuration
function cloneRepositories
{
    param(
        [Parameter(Mandatory=$false)]
        [string]$configPath = (Join-Path (Join-Path $PSScriptRoot "..\configs") "repositories.json")
    )

    Write-Host "=== Repository Cloning ===" -ForegroundColor Cyan
    Write-Host ""

    # Check if Git is installed
    if (-not (isGitInstalled))
    {
        Write-Error "Git is not installed. Please install Git first."
        Write-Host "You can install Git using: winget install Git.Git" -ForegroundColor Yellow
        return $false
    }

    # Check if config file exists
    if (-not (Test-Path $configPath))
    {
        Write-Error "Configuration file not found: $configPath"
        return $false
    }

    # Parse JSON configuration
    try
    {
        $jsonContent = Get-Content $configPath -Raw | ConvertFrom-Json

        if (-not $jsonContent.PSObject.Properties.Name -contains "repositories")
        {
            Write-Error "JSON file must contain a 'repositories' array."
            return $false
        }

        if (-not $jsonContent.PSObject.Properties.Name -contains "workPathWindows")
        {
            Write-Error "JSON file must contain a 'workPathWindows' property."
            return $false
        }

        $workPath = $jsonContent.workPathWindows
        $repositories = $jsonContent.repositories

        if ($repositories.Count -eq 0)
        {
            Write-Host "No repositories specified in configuration file." -ForegroundColor Yellow
            return $true
        }

        Write-Host "Work directory: $workPath" -ForegroundColor Cyan
        Write-Host "Found $($repositories.Count) repository/repositories in configuration file." -ForegroundColor Cyan
        Write-Host ""

    }
    catch
    {
        Write-Error "Failed to parse JSON file: $_"
        return $false
    }

    # Create work directory if it doesn't exist
    if (-not (Test-Path $workPath))
    {
        Write-Host "Creating work directory: $workPath" -ForegroundColor Yellow
        try
        {
            New-Item -ItemType Directory -Path $workPath -Force | Out-Null
            Write-Host "✓ Work directory created" -ForegroundColor Green
            Write-Host ""
        }
        catch
        {
            Write-Error "Failed to create work directory: $_"
            return $false
        }
    }

    $clonedCount = 0
    $skippedCount = 0
    $failedCount = 0

    # Process each repository
    foreach ($repoUrl in $repositories)
    {
        Write-Host "Processing: $repoUrl" -ForegroundColor Yellow

        if (cloneRepository -repoUrl $repoUrl -workPath $workPath)
        {
            $clonedCount++
        }
        elseif (isRepositoryCloned -repoUrl $repoUrl -workPath $workPath)
        {
            $skippedCount++
        }
        else
        {
            $failedCount++
        }

        Write-Host ""
    }

    Write-Host "Summary:" -ForegroundColor Cyan
    Write-Host "  Cloned: $clonedCount repository/repositories" -ForegroundColor Green
    if ($skippedCount -gt 0)
    {
        Write-Host "  Skipped: $skippedCount repository/repositories (already exist)" -ForegroundColor Yellow
    }
    if ($failedCount -gt 0)
    {
        Write-Host "  Failed: $failedCount repository/repositories" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "Repository cloning complete!" -ForegroundColor Green

    return ($failedCount -eq 0)
}