#!/bin/bash
# Shared logging functions for consistent output formatting
# Requires colours.sh to be sourced first

# shellcheck disable=SC2154 # colour variables provided by callers

logInfo()
{
    local message="$1"
    echo -e "${cyan}${message}${nc}"
}

logSuccess()
{
    local message="$1"
    echo -e "${green}✓ ${message}${nc}"
}

logError()
{
    local message="$1"
    echo -e "${red}✗ ${message}${nc}"
}

logWarning()
{
    local message="$1"
    echo -e "${yellow}⚠ ${message}${nc}"
}

logNote()
{
    local message="$1"
    echo -e "${yellow}${message}${nc}"
}

logSection()
{
    local message="$1"
    echo -e "${cyan}=== ${message} ===${nc}"
}
