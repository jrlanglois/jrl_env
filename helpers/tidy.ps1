# Script to tidy a single file
# Trims trailing whitespace and converts tabs to 4 spaces
# Works on Windows and PowerShell Core on *nix

param(
    [Parameter(Mandatory=$true)]
    [string]$filePath,
    [switch]$dryRun
)

$ErrorActionPreference = "Stop"

# Function to tidy a single file
function tidyFile
{
    param(
        [string]$path,
        [bool]$isDryRun
    )

    if (-not (Test-Path $path))
    {
        Write-Error "File not found: $path"
        return @{
            Modified = $false
            TabCount = 0
            WhitespaceCount = 0
            HasTrailingBlanks = $false
        }
    }

    $originalContent = Get-Content $path -Raw
    if (-not $originalContent)
    {
        return @{
            Modified = $false
            TabCount = 0
            WhitespaceCount = 0
            HasTrailingBlanks = $false
        }
    }

    $modified = $false
    $content = $originalContent
    $tabCount = 0
    $whitespaceCount = 0
    $hasTrailingBlanks = $false

    # Check for tabs
    if ($content -match "`t")
    {
        $tabCount = ([regex]::Matches($content, "`t")).Count
        if (-not $isDryRun)
        {
            $content = $content -replace "`t", '    '
            $modified = $true
        }
    }

    # Trim trailing whitespace and trailing blank lines
    $lines = $content -split "`r?`n"
    $trimmed = $lines | ForEach-Object {
        $line = $_
        $originalLine = $line
        $trimmedLine = $line.TrimEnd()
        if ($originalLine -ne $trimmedLine)
        {
            $script:whitespaceCount++
            if (-not $isDryRun)
            {
                $script:modified = $true
            }
        }
        $trimmedLine
    }

    # Check for trailing blank lines
    $blankLineCount = 0
    for ($i = $trimmed.Count - 1; $i -ge 0; $i--)
    {
        if ($trimmed[$i] -eq '')
        {
            $blankLineCount++
        }
        else
        {
            break
        }
    }

    if ($blankLineCount -gt 0)
    {
        $hasTrailingBlanks = $true
        if (-not $isDryRun)
        {
            $trimmed = $trimmed[0..($trimmed.Count - $blankLineCount - 1)]
            $modified = $true
        }
    }

    if ($modified -and -not $isDryRun)
    {
        $result = ($trimmed -join "`r`n").TrimEnd()
        Set-Content -Path $path -Value $result -NoNewline
    }

    return @{
        Modified = $modified
        TabCount = $tabCount
        WhitespaceCount = $whitespaceCount
        HasTrailingBlanks = $hasTrailingBlanks
    }
}

# If script is called directly (not sourced), execute the function
if ($MyInvocation.InvocationName -ne '.' -and $PSCommandPath -eq $MyInvocation.PSCommandPath)
{
    if (-not $filePath)
    {
        Write-Error "filePath parameter is required when calling this script directly."
        Write-Host "Usage: .\tidy.ps1 -filePath <path> [-dryRun]"
        exit 1
    }

    $result = tidyFile -path $filePath -isDryRun $dryRun

    if ($dryRun)
    {
        if ($result.TabCount -gt 0 -or $result.WhitespaceCount -gt 0 -or $result.HasTrailingBlanks)
        {
            Write-Host "Would tidy: $filePath" -ForegroundColor Cyan
            if ($result.TabCount -gt 0)
            {
                Write-Host "  Would convert $($result.TabCount) tab(s) to spaces" -ForegroundColor Yellow
            }
            if ($result.WhitespaceCount -gt 0)
            {
                Write-Host "  Would trim trailing whitespace from $($result.WhitespaceCount) line(s)" -ForegroundColor Yellow
            }
            if ($result.HasTrailingBlanks)
            {
                Write-Host "  Would remove trailing blank lines" -ForegroundColor Yellow
            }
        }
        else
        {
            Write-Host "File is already tidy: $filePath" -ForegroundColor Green
        }
    }
    else
    {
        if ($result.Modified)
        {
            Write-Host "Tidied: $filePath" -ForegroundColor Green
            if ($result.TabCount -gt 0)
            {
                Write-Host "  Converted $($result.TabCount) tab(s) to spaces" -ForegroundColor Green
            }
            if ($result.WhitespaceCount -gt 0)
            {
                Write-Host "  Trimmed trailing whitespace from $($result.WhitespaceCount) line(s)" -ForegroundColor Green
            }
            if ($result.HasTrailingBlanks)
            {
                Write-Host "  Removed trailing blank lines" -ForegroundColor Green
            }
        }
        else
        {
            Write-Host "File is already tidy: $filePath" -ForegroundColor Green
        }
    }

    exit 0
}
