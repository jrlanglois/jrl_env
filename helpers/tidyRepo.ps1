# Script to tidy all files in a repository via the Python implementation

param(
    [string]$path = (Join-Path $PSScriptRoot ".."),
    [switch]$dryRun
)

$ErrorActionPreference = "Stop"

$pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $pythonCmd)
{
    $pythonCmd = Get-Command python -ErrorAction Stop
}

$tidyScript = Join-Path $PSScriptRoot "tidy.py"
$resolvedPath = Resolve-Path -Path $path
$arguments = @($tidyScript, "--path", $resolvedPath)
if ($dryRun)
{
    $arguments += "--dry-run"
}

& $pythonCmd.Source $arguments
