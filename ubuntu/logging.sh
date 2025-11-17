#!/bin/bash
# Logging functions for Bash scripts
# Provides functions to log messages to both console and log file

# Global variables
logFilePath=""
logDirectory=""

# Initialize logging
initLogging()
{
    local logDirDefault="${LOG_DIR:-/tmp/jrl_env_logs}"
    local logDir="$logDirDefault"
    local timestamp
    local initMessage

    if [ $# -gt 0 ] && [ -n "$1" ]; then
        logDir="$1"
    fi

    # Create log directory if it doesn't exist
    mkdir -p "$logDir"

    logDirectory="$logDir"

    # Create log file with timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    logFilePath="$logDirectory/setup_$timestamp.log"

    # Write initial log entry
    initMessage="=== jrl_env Setup Log - Started at $(date '+%Y-%m-%d %H:%M:%S') ==="
    echo "$initMessage" >> "$logFilePath"

    echo "$logFilePath"
}

# Get current log file path
getLogFile()
{
    echo "$logFilePath"
}

# Write log entry
writeLog()
{
    local level="$1"
    shift
    local message="$*"
    local timestamp
    local logEntry

    if [ -z "$logFilePath" ]; then
        # Initialize logging if not already done
        initLogging >/dev/null
    fi

    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    logEntry="[$timestamp] [$level] $message"

    # Write to log file
    echo "$logEntry" >> "$logFilePath"

    # Also write to console with appropriate colour
    case "$level" in
        "INFO")
            echo -e "\033[0m$logEntry\033[0m"
            ;;
        "SUCCESS")
            echo -e "\033[0;32m$logEntry\033[0m"
            ;;
        "WARN")
            echo -e "\033[1;33m$logEntry\033[0m"
            ;;
        "ERROR")
            echo -e "\033[0;31m$logEntry\033[0m"
            ;;
        "DEBUG")
            echo -e "\033[0;90m$logEntry\033[0m"
            ;;
        *)
            echo -e "\033[0m$logEntry\033[0m"
            ;;
    esac
}

# Convenience functions
logInfo()
{
    writeLog "INFO" "$@"
}

logSuccess()
{
    writeLog "SUCCESS" "$@"
}

logWarn()
{
    writeLog "WARN" "$@"
}

logError()
{
    writeLog "ERROR" "$@"
}

logDebug()
{
    writeLog "DEBUG" "$@"
}
