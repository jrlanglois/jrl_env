# Script to tidy all files in a repository
# Uses tidy.ps1 functions to process multiple files

param(
    [string]$path = (Join-Path $PSScriptRoot ".."),
    [switch]$dryRun
)

$ErrorActionPreference = "Stop"

# Source the tidy script to get the function
$tidyScriptPath = Join-Path $PSScriptRoot "tidy.ps1"
. $tidyScriptPath

# Find all relevant files
$files = Get-ChildItem -Path $path -Recurse -Include *.ps1,*.sh,*.json,*.md -ErrorAction SilentlyContinue

if ($files.Count -eq 0)
{
    Write-Host "No files found to process." -ForegroundColor Yellow
    exit 0
}

$modifiedCount = 0
$totalTabCount = 0
$totalWhitespaceCount = 0

foreach ($file in $files)
{
    $result = tidyFile -path $file.FullName -isDryRun $dryRun

    if ($result.Modified)
    {
        $modifiedCount++
    }

    $totalTabCount += $result.TabCount
    $totalWhitespaceCount += $result.WhitespaceCount
}

# Summary
if ($dryRun)
{
    Write-Host ""
    Write-Host "DRY RUN: Would process $($files.Count) file(s)" -ForegroundColor Yellow
    if ($totalTabCount -gt 0)
    {
        Write-Host "  Would convert $totalTabCount tab(s) to spaces" -ForegroundColor Yellow
    }
    if ($totalWhitespaceCount -gt 0)
    {
        Write-Host "  Would trim trailing whitespace from $totalWhitespaceCount line(s)" -ForegroundColor Yellow
    }
}
else
{
    Write-Host ""
    Write-Host "Processed $($files.Count) file(s)" -ForegroundColor Cyan
    if ($modifiedCount -gt 0)
    {
        Write-Host "Modified $modifiedCount file(s)" -ForegroundColor Green
        if ($totalTabCount -gt 0)
        {
            Write-Host "  Converted $totalTabCount tab(s) to spaces" -ForegroundColor Green
        }
        if ($totalWhitespaceCount -gt 0)
        {
            Write-Host "  Trimmed trailing whitespace from $totalWhitespaceCount line(s)" -ForegroundColor Green
        }
    }
    else
    {
        Write-Host "No files needed tidying. All files are clean!" -ForegroundColor Green
    }
}

