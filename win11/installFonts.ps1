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

        # Map common variant names to possible file name patterns
        $variantPatterns = @()
        switch ($variant)
        {
            "Regular" {
                $variantPatterns = @("Regular", "400", "normal", "regular")
            }
            "Bold" {
                $variantPatterns = @("Bold", "700", "bold", "BoldRegular")
            }
            "Italic" {
                $variantPatterns = @("Italic", "400italic", "italic", "RegularItalic")
            }
            "BoldItalic" {
                $variantPatterns = @("BoldItalic", "700italic", "bolditalic", "Bold-Italic")
            }
            default {
                $variantPatterns = @($variant -replace '\s+', '', $variant)
            }
        }

        # Try different variant patterns and URL formats
        foreach ($variantPattern in $variantPatterns)
        {
            $testVariant = $variantPattern -replace '\s+', ''

            # Try different repository paths and naming conventions
            $urlPatterns = @(
                "https://github.com/google/fonts/raw/main/ofl/$normalisedName/$normalisedName-$testVariant.ttf",
                "https://github.com/google/fonts/raw/main/ofl/$normalisedName/$testVariant.ttf",
                "https://github.com/google/fonts/raw/main/apache/$normalisedName/$normalisedName-$testVariant.ttf",
                "https://github.com/google/fonts/raw/main/apache/$normalisedName/$testVariant.ttf",
                "https://github.com/google/fonts/raw/main/ufl/$normalisedName/$normalisedName-$testVariant.ttf",
                "https://github.com/google/fonts/raw/main/ufl/$normalisedName/$testVariant.ttf"
            )

            $fileName = "$normalisedName-$testVariant.ttf"
            $filePath = Join-Path $outputPath $fileName

            foreach ($fontUrl in $urlPatterns)
            {
                try
                {
                    # Try to download the file
                    Invoke-WebRequest -Uri $fontUrl -OutFile $filePath -UseBasicParsing -ErrorAction Stop

                    # Verify it's actually a font file (check file size)
                    if (Test-Path $filePath -and (Get-Item $filePath).Length -gt 1000)
                    {
                        Write-Host "    ✓ Downloaded $variant successfully" -ForegroundColor Green
                        return $filePath
                    }
                    else
                    {
                        # File too small, probably not a valid font
                        Remove-Item $filePath -Force -ErrorAction SilentlyContinue
                    }
                }
                catch
                {
                    # Try next URL pattern
                    if (Test-Path $filePath)
                    {
                        Remove-Item $filePath -Force -ErrorAction SilentlyContinue
                    }
                    continue
                }
            }
        }

        # Fallback: Try to get font URL from Google Fonts CSS API
        # This works for fonts like Bungee Spice that might not be in the GitHub repo structure
        if ($variant -eq "Regular")
        {
            $apiFontName = $fontName -replace '\s+', '+'
            $cssUrl = "https://fonts.googleapis.com/css2?family=$apiFontName&display=swap"

            try
            {
                $cssContent = Invoke-WebRequest -Uri $cssUrl -UseBasicParsing -ErrorAction Stop | Select-Object -ExpandProperty Content

                if ($cssContent)
                {
                    $fontUrl = $null
                    $fileExt = "ttf"

                    # Try to find TTF first (more compatible across OS)
                    if ($cssContent -match 'url\(https://fonts\.gstatic\.com/[^)]+\.ttf\)')
                    {
                        $fontUrl = $matches[0] -replace 'url\(([^)]+)\)', '$1'
                    }
                    # If no TTF found, try WOFF2 (web font format)
                    elseif ($cssContent -match 'url\(https://fonts\.gstatic\.com/[^)]+\.woff2\)')
                    {
                        $fontUrl = $matches[0] -replace 'url\(([^)]+)\)', '$1'
                        $fileExt = "woff2"
                    }

                    if ($fontUrl)
                    {
                        $fileName = "$normalisedName-$variant.$fileExt"
                        $filePath = Join-Path $outputPath $fileName

                        try
                        {
                            Invoke-WebRequest -Uri $fontUrl -OutFile $filePath -UseBasicParsing -ErrorAction Stop

                            if (Test-Path $filePath -and (Get-Item $filePath).Length -gt 1000)
                            {
                                # If we got WOFF2, try to convert to TTF
                                if ($fileExt -eq "woff2")
                                {
                                    $ttfPath = Join-Path $outputPath "$normalisedName-$variant.ttf"
                                    $converted = $false

                                    # Try Node.js with woff2 package
                                    if (Get-Command node -ErrorAction SilentlyContinue)
                                    {
                                        try
                                        {
                                            # Check if woff2 package is available, install if needed
                                            $woff2Module = npm list -g woff2 2>$null
                                            if (-not $woff2Module)
                                            {
                                                Write-Host "    Installing woff2 npm package..." -ForegroundColor Cyan
                                                npm install -g woff2 2>$null | Out-Null
                                            }

                                            # Try to convert using woff2
                                            $convertResult = node -e "const woff2 = require('woff2'); const fs = require('fs'); const input = fs.readFileSync('$filePath'); const output = woff2.decompress(input); fs.writeFileSync('$ttfPath', output);" 2>$null

                                            if (Test-Path $ttfPath -and (Get-Item $ttfPath).Length -gt 1000)
                                            {
                                                Remove-Item $filePath -Force -ErrorAction SilentlyContinue
                                                $filePath = $ttfPath
                                                $converted = $true
                                                Write-Host "    ✓ Downloaded and converted $variant successfully (via Google Fonts API)" -ForegroundColor Green
                                            }
                                        }
                                        catch
                                        {
                                            # Conversion failed, continue to warning
                                        }
                                    }

                                    if (-not $converted)
                                    {
                                        Write-Host "    ⚠ Downloaded WOFF2 format (Windows cannot install WOFF2 directly)" -ForegroundColor Yellow
                                        Write-Host "    ⚠ File saved at: $filePath" -ForegroundColor Yellow
                                        Write-Host "    ⚠ Convert to TTF using:" -ForegroundColor Yellow
                                        Write-Host "      - Online: https://cloudconvert.com/woff2-converter" -ForegroundColor Yellow
                                        Write-Host "      - Node.js: npm install -g woff2" -ForegroundColor Yellow
                                    }
                                }
                                else
                                {
                                    Write-Host "    ✓ Downloaded $variant successfully (via Google Fonts API)" -ForegroundColor Green
                                }
                                return $filePath
                            }
                            else
                            {
                                Remove-Item $filePath -Force -ErrorAction SilentlyContinue
                            }
                        }
                        catch
                        {
                            if (Test-Path $filePath)
                            {
                                Remove-Item $filePath -Force -ErrorAction SilentlyContinue
                            }
                        }
                    }
                }
            }
            catch
            {
                # CSS API failed, continue
            }
        }

        # No variant found
        return $null
    }
    catch
    {
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

        # Check if file is WOFF2 (web font format, Windows cannot install directly)
        $fileExt = [System.IO.Path]::GetExtension($fontPath).ToLower()
        if ($fileExt -eq ".woff2")
        {
            Write-Host "    ⚠ WOFF2 format cannot be directly installed on Windows" -ForegroundColor Yellow
            Write-Host "    ⚠ File saved at: $fontPath" -ForegroundColor Yellow
            Write-Host "    ⚠ Convert to TTF first using an online tool or woff2 tools" -ForegroundColor Yellow
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

    # Check if config file exists
    if (-not (Test-Path $configPath))
    {
        Write-Error "Configuration file not found: $configPath"
        return $false
    }

    # Use Python script for parallel processing
    $pythonScript = Join-Path (Join-Path $PSScriptRoot "..\helpers") "installFonts.py"

    if (-not (Test-Path $pythonScript))
    {
        Write-Error "Python script not found: $pythonScript"
        return $false
    }

    # Check for Python
    if (-not (Get-Command python -ErrorAction SilentlyContinue) -and -not (Get-Command python3 -ErrorAction SilentlyContinue))
    {
        Write-Error "Python is required for font installation. Please install it first."
        return $false
    }

    $pythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "python3" }

    # Build arguments
    $installDir = "$env:WINDIR\Fonts"  # Windows uses system font folder
    $args = @($configPath, $installDir) + $variants

    # Call Python script
    & $pythonCmd $pythonScript $args
    return $LASTEXITCODE -eq 0
}
