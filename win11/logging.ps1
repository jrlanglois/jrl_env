# Logging module for PowerShell scripts
# Provides functions to log messages to both console and log file

$script:logFilePath = $null
$script:logDirectory = $null

# Initialize logging
function initLogging {
    param(
        [Parameter(Mandatory=$false)]
        [string]$logDirectory = (Join-Path $env:TEMP "jrl_env_logs")
    )
    
    # Create log directory if it doesn't exist
    if (-not (Test-Path $logDirectory)) {
        New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    }
    
    $script:logDirectory = $logDirectory
    
    # Create log file with timestamp
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $script:logFilePath = Join-Path $logDirectory "setup_$timestamp.log"
    
    # Write initial log entry
    $initMessage = "=== jrl_env Setup Log - Started at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
    Add-Content -Path $script:logFilePath -Value $initMessage
    
    return $script:logFilePath
}

# Get current log file path
function getLogFile {
    return $script:logFilePath
}

# Write log entry
function writeLog {
    param(
        [Parameter(Mandatory=$true)]
        [ValidateSet("INFO", "SUCCESS", "WARN", "ERROR", "DEBUG")]
        [string]$level,
        
        [Parameter(Mandatory=$true)]
        [string]$message
    )
    
    if (-not $script:logFilePath) {
        # Initialize logging if not already done
        initLogging | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$level] $message"
    
    # Write to log file
    Add-Content -Path $script:logFilePath -Value $logEntry
    
    # Also write to console with appropriate colour
    $color = switch ($level) {
        "INFO"    { "White" }
        "SUCCESS" { "Green" }
        "WARN"    { "Yellow" }
        "ERROR"   { "Red" }
        "DEBUG"   { "Gray" }
    }
    
    Write-Host $logEntry -ForegroundColor $color
}

# Convenience functions
function logInfo {
    param([string]$message)
    writeLog -level "INFO" -message $message
}

function logSuccess {
    param([string]$message)
    writeLog -level "SUCCESS" -message $message
}

function logWarn {
    param([string]$message)
    writeLog -level "WARN" -message $message
}

function logError {
    param([string]$message)
    writeLog -level "ERROR" -message $message
}

function logDebug {
    param([string]$message)
    writeLog -level "DEBUG" -message $message
}

# Export functions
Export-ModuleMember -Function initLogging, getLogFile, writeLog, logInfo, logSuccess, logWarn, logError, logDebug

