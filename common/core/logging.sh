#!/bin/bash
# Shared logging functions for Bash scripts across platforms
# shellcheck disable=SC2154 # Colour variables come from sourced colours.sh

# shellcheck source=utilities.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/utilities.sh"

# Global variables
logFilePath=""
logDirectory=""

# Initialize logging
initLogging()
{
    local tmpBase="${TMPDIR:-/tmp}"
    local logDir="${logDirOverride:-$tmpBase/jrl_env_logs}"
    local timestamp
    local initMessage

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

logInfo()
{
    local message="$1"
    # shellcheck disable=SC2154 # cyan and nc come from colours.sh
    echo -e "${cyan}${message}${nc}"
}

logSuccess()
{
    local message="$1"
    # shellcheck disable=SC2154 # green and nc come from colours.sh
    echo -e "${green}✓ ${message}${nc}"
}

logError()
{
    local message="$1"
    # shellcheck disable=SC2154 # red and nc come from colours.sh
    echo -e "${red}✗ ${message}${nc}"
}

logWarning()
{
    local message="$1"
    # shellcheck disable=SC2154 # yellow and nc come from colours.sh
    echo -e "${yellow}⚠ ${message}${nc}"
}

logNote()
{
    local message="$1"
    # shellcheck disable=SC2154 # yellow and nc come from colours.sh
    echo -e "${yellow}${message}${nc}"
}

logSection()
{
    local message="$1"
    # shellcheck disable=SC2154 # cyan and nc come from colours.sh
    echo -e "${cyan}=== ${message} ===${nc}"
}
