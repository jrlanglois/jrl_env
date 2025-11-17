# Script to download and install Google Fonts from fonts.json
# Downloads fonts from Google Fonts GitHub repository, installs them to Windows, and cleans up

# Function to check if a font is already installed
function isFontInstalled
{
    param(
        [Parameter(Mandatory=$true)]
        [string]$fontName
    )

    try
    {
        $installedFonts = Get-ChildItem -Path "$env:WINDIR\Fonts" -Filter "*.ttf","*.otf" -ErrorAction SilentlyContinue
        foreach ($font in $installedFonts)
        {
            $fontObj = New-Object -ComObject Shell.Application
            $fontFolder = $fontObj.Namespace($font.DirectoryName)
            $fontFile = $fontFolder.ParseName($font.Name)
            $fontTitle = $fontFolder.GetDetailsOf($fontFile, 21) # 21 is the property index for "Title"

            if ($fontTitle -like "*$fontName*" -or $font.Name -like "*$fontName*")
            {
                return $true
            }
        }
    }
    catch
    {
        # Fallback: check by filename
        $fontFiles = Get-ChildItem -Path "$env:WINDIR\Fonts" -Filter "*$fontName*" -ErrorAction SilentlyContinue
        if ($fontFiles.Count -gt 0)
        {
            return $true
        }
    }

    return $false
}

# Function to download a font file from Google Fonts GitHub
function downloadGoogleFont
{
    param(
        [Parameter(Mandatory=$true)]
        [string]$fontName,

        [Parameter(Mandatory=$false)]
        [string]$variant = "Regular",

        [Parameter(Mandatory=$false)]
        [string]$outputPath = $env:TEMP
    )

    try
    {
        # Normalise font name for URL (lowercase, spaces to hyphens)
        $normalisedName = $fontName.ToLower() -replace '\s+', '-'
        $normalisedVariant = $variant -replace '\s+', ''

        # Try different URL formats (some fonts use different naming)
        $urlPatterns = @(
            "https://github.com/google/fonts/raw/main/ofl/$normalisedName/$normalisedName-$normalisedVariant.ttf",
            "https://github.com/google/fonts/raw/main/ofl/$normalisedName/$normalisedVariant.ttf",
            "https://github.com/google/fonts/raw/main/apache/$normalisedName/$normalisedName-$normalisedVariant.ttf",
            "https://github.com/google/fonts/raw/main/apache/$normalisedName/$normalisedVariant.ttf"
        )

        $fileName = "$normalisedName-$normalisedVariant.ttf"
        $filePath = Join-Path $outputPath $fileName

        Write-Host "  Downloading $fontName $variant..." -ForegroundColor Yellow

        $downloadSuccess = $false
        foreach ($fontUrl in $urlPatterns)
        {
            try
            {
                # Try to download with HEAD request first to check if file exists
                $response = Invoke-WebRequest -Uri $fontUrl -Method Head -UseBasicParsing -ErrorAction Stop

                if ($response.StatusCode -eq 200)
                {
                    # File exists, download it
                    Invoke-WebRequest -Uri $fontUrl -OutFile $filePath -UseBasicParsing -ErrorAction Stop

                    if (Test-Path $filePath -and (Get-Item $filePath).Length -gt 0)
                    {
                        Write-Host "    ✓ Downloaded successfully" -ForegroundColor Green
                        $downloadSuccess = $true
                        break
                    }
                }
            }
            catch
            {
                # Try next URL pattern
                continue
            }
        }

        if (-not $downloadSuccess)
        {
            Write-Host "    ✗ Download failed: font variant not found" -ForegroundColor Red
            return $null
        }

        return $filePath
    }
    catch
    {
        Write-Host "    ✗ Download failed: $_" -ForegroundColor Red
        return $null
    }
}

# Function to install a font file to Windows
function installFont
{
    param(
        [Parameter(Mandatory=$true)]
        [string]$fontPath
    )

    try
    {
        if (-not (Test-Path $fontPath))
        {
            Write-Host "    ✗ Font file not found: $fontPath" -ForegroundColor Red
            return $false
        }

        $fontName = Split-Path $fontPath -Leaf
        $fontsFolder = "$env:WINDIR\Fonts"
        $destinationPath = Join-Path $fontsFolder $fontName

        # Check if font is already installed (by filename)
        if (Test-Path $destinationPath)
        {
            Write-Host "    ⚠ Font already installed, skipping..." -ForegroundColor Yellow
            return $true
        }

        # Get font family name from the file (for registry entry)
        $fontRegistryName = $null
        $fontRegistryValue = $fontName

        try
        {
            # Try to extract font name from file using Shell COM object
            $shell = New-Object -ComObject Shell.Application
            $folder = $shell.Namespace((Split-Path $fontPath))
            $file = $folder.ParseName((Split-Path $fontPath -Leaf))
            $fontRegistryName = $folder.GetDetailsOf($file, 21) # Title property (font name)

            if ([string]::IsNullOrWhiteSpace($fontRegistryName))
            {
                # Fallback: try property index 2 (Type) or construct from filename
                $fontRegistryName = $folder.GetDetailsOf($file, 2)
                if ([string]::IsNullOrWhiteSpace($fontRegistryName))
                {
                    # Last resort: construct from filename
                    $fontRegistryName = $fontName -replace '\.ttf$|\.otf$', '' -replace '-', ' '
                }
            }
        }
        catch
        {
            # If COM object fails, construct registry name from filename
            $fontRegistryName = $fontName -replace '\.ttf$|\.otf$', '' -replace '-', ' '
        }

        # Copy font to Fonts folder (this automatically registers it in Windows 10/11)
        Copy-Item -Path $fontPath -Destination $destinationPath -Force -ErrorAction Stop

        # Also register in registry for compatibility
        $registryPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
        if (-not (Test-Path $registryPath))
        {
            Write-Warning "Font registry path not found: $registryPath"
        }
        else
        {
            # Check if registry entry already exists
            $existingValue = Get-ItemProperty -Path $registryPath -Name $fontRegistryName -ErrorAction SilentlyContinue
            if (-not $existingValue)
            {
                New-ItemProperty -Path $registryPath -Name $fontRegistryName -Value $fontRegistryValue -PropertyType String -Force | Out-Null
            }
        }

        Write-Host "    ✓ Installed successfully" -ForegroundColor Green
        return $true
    }
    catch
    {
        Write-Host "    ✗ Installation failed: $_" -ForegroundColor Red
        return $false
    }
}

# Function to install Google Fonts from JSON configuration
function installGoogleFonts
{
    param(
        [Parameter(Mandatory=$false)]
        [string]$configPath = (Join-Path (Join-Path $PSScriptRoot "..\configs") "fonts.json"),

        [Parameter(Mandatory=$false)]
        [string[]]$variants = @("Regular", "Bold", "Italic", "BoldItalic")
    )

    Write-Host "=== Google Fonts Installation ===" -ForegroundColor Cyan
    Write-Host ""

    # Check if config file exists
    if (-not (Test-Path $configPath))
    {
        Write-Error "Configuration file not found: $configPath"
        return $false
    }

    # Check for admin privileges (needed for font installation)
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin)
    {
        Write-Error "Administrative privileges are required to install fonts. Please run PowerShell as Administrator."
        return $false
    }

    # Parse JSON configuration
    try
    {
        $jsonContent = Get-Content $configPath -Raw | ConvertFrom-Json

        if (-not $jsonContent.PSObject.Properties.Name -contains "googleFonts")
        {
            Write-Error "JSON file must contain a 'googleFonts' array."
            return $false
        }

        $fontNames = $jsonContent.googleFonts

        if ($fontNames.Count -eq 0)
        {
            Write-Host "No fonts specified in configuration file." -ForegroundColor Yellow
            return $true
        }

        Write-Host "Found $($fontNames.Count) font(s) in configuration file." -ForegroundColor Cyan
        Write-Host ""

    }
    catch
    {
        Write-Error "Failed to parse JSON file: $_"
        return $false
    }

    # Create temporary directory for downloads
    $tempDir = Join-Path $env:TEMP "GoogleFonts_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    $installedCount = 0
    $skippedCount = 0
    $failedCount = 0
    $downloadedFiles = @()

    # Process each font
    foreach ($fontName in $fontNames)
    {
        Write-Host "Processing: $fontName" -ForegroundColor Yellow

        $fontInstalled = $false

        # Try to download and install each variant
        foreach ($variant in $variants)
        {
            $fontPath = downloadGoogleFont -fontName $fontName -variant $variant -outputPath $tempDir

            if ($fontPath -and (Test-Path $fontPath))
            {
                $downloadedFiles += $fontPath

                if (installFont -fontPath $fontPath)
                {
                    $installedCount++
                    $fontInstalled = $true
                }
                else
                {
                    $failedCount++
                }
            }
            else
            {
                # Some fonts may not have all variants, which is fine
                Write-Host "    ⚠ Variant '$variant' not available, skipping..." -ForegroundColor Yellow
            }
        }

        if (-not $fontInstalled)
        {
            $skippedCount++
        }

        Write-Host ""
    }

    # Clean up downloaded files
    Write-Host "Cleaning up downloaded files..." -ForegroundColor Cyan
    try
    {
        if (Test-Path $tempDir)
        {
            Remove-Item -Path $tempDir -Recurse -Force -ErrorAction Stop
            Write-Host "✓ Temporary files removed successfully" -ForegroundColor Green
        }
    }
    catch
    {
        Write-Warning "Failed to clean up temporary files: $_"
        Write-Host "You may need to manually delete: $tempDir" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "Summary:" -ForegroundColor Cyan
    Write-Host "  Installed: $installedCount font file(s)" -ForegroundColor Green
    if ($skippedCount -gt 0)
    {
        Write-Host "  Skipped: $skippedCount font(s)" -ForegroundColor Yellow
    }
    if ($failedCount -gt 0)
    {
        Write-Host "  Failed: $failedCount font file(s)" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "Font installation complete!" -ForegroundColor Green
    Write-Host "Note: You may need to restart applications for new fonts to appear." -ForegroundColor Yellow

    return $true
}