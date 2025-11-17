#!/bin/bash
# Script to tidy a single file
# Trims trailing whitespace and converts tabs to 4 spaces
# Works on macOS and Linux

# Colors
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[1;33m'
cyan='\033[0;36m'
nc='\033[0m' # No Color

# Check if sed supports -i flag (GNU vs BSD)
if sed -i '' /dev/null 2>/dev/null
then
    # BSD sed (macOS)
    sedInPlace="sed -i ''"
else
    # GNU sed (Linux)
    sedInPlace="sed -i"
fi

# Function to tidy a single file
tidyFile()
{
    local filePath="$1"
    local isDryRun="$2"

    if [ ! -f "$filePath" ]
    then
        echo -e "${red}Error: File not found: $filePath${nc}" >&2
        return 1
    fi

    local modified=false
    local tabCount=0
    local whitespaceCount=0
    local hasTrailingBlanks=false

    # Check for tabs (before processing)
    if grep -q $'\t' "$filePath" 2>/dev/null
    then
        tabCount=$(grep -o $'\t' "$filePath" | wc -l | tr -d ' ')
        if [ "$isDryRun" != true ]
        then
            $sedInPlace "s/\t/    /g" "$filePath"
            modified=true
        fi
    fi

    # Check for trailing whitespace (before processing)
    if grep -q '[[:space:]]$' "$filePath" 2>/dev/null
    then
        whitespaceCount=$(grep -c '[[:space:]]$' "$filePath" 2>/dev/null || echo "0")
        if [ "$isDryRun" != true ]
        then
            $sedInPlace 's/[[:space:]]*$//' "$filePath"
            modified=true
        fi
    fi

    # Check for trailing blank lines
    if [ -s "$filePath" ]
    then
        trailingNewlines=$(tail -c 100 "$filePath" | tr -cd '\n' | wc -c | tr -d ' ')
        if [ "$trailingNewlines" -gt 1 ]
        then
            hasTrailingBlanks=true
            if [ "$isDryRun" != true ]
            then
                # Remove trailing blank lines using awk
                awk 'BEGIN {blank=0} {if (NF || length($0)) {for(i=0;i<blank;i++) print ""; blank=0; print} else blank++} END {if (blank && !NF && !length($0)) blank--}' "$filePath" > "$filePath.tmp" && mv "$filePath.tmp" "$filePath"
                modified=true
            fi
        fi
    fi

    # Output results to stderr (so stats can be captured from stdout when sourced)
    if [ "$isDryRun" = true ]
    then
        if [ "$tabCount" -gt 0 ] || [ "$whitespaceCount" -gt 0 ] || [ "$hasTrailingBlanks" = true ]
        then
            echo -e "${cyan}Would tidy: $filePath${nc}" >&2
            if [ "$tabCount" -gt 0 ]
            then
                echo -e "${yellow}  Would convert $tabCount tab(s) to spaces${nc}" >&2
            fi
            if [ "$whitespaceCount" -gt 0 ]
            then
                echo -e "${yellow}  Would trim trailing whitespace from $whitespaceCount line(s)${nc}" >&2
            fi
            if [ "$hasTrailingBlanks" = true ]
            then
                echo -e "${yellow}  Would remove trailing blank lines${nc}" >&2
            fi
        else
            echo -e "${green}File is already tidy: $filePath${nc}" >&2
        fi
    else
        if [ "$modified" = true ]
        then
            echo -e "${green}Tidied: $filePath${nc}" >&2
            if [ "$tabCount" -gt 0 ]
            then
                echo -e "${green}  Converted $tabCount tab(s) to spaces${nc}" >&2
            fi
            if [ "$whitespaceCount" -gt 0 ]
            then
                echo -e "${green}  Trimmed trailing whitespace from $whitespaceCount line(s)${nc}" >&2
            fi
            if [ "$hasTrailingBlanks" = true ]
            then
                echo -e "${green}  Removed trailing blank lines${nc}" >&2
            fi
        else
            echo -e "${green}File is already tidy: $filePath${nc}" >&2
        fi
    fi

    # Return stats to stdout (for sourcing) - pipe-delimited
    # Only output stats if sourced (not when called directly)
    if [ "${BASH_SOURCE[0]}" != "${0}" ]
    then
        echo "$modified|$tabCount|$whitespaceCount|$hasTrailingBlanks"
    fi
}

# If script is called directly (not sourced), execute the function
if [ "${BASH_SOURCE[0]}" = "${0}" ]
then
    if [ $# -lt 1 ]
    then
        echo "Usage: $0 <filePath> [--dry-run]" >&2
        exit 1
    fi

    filePath="$1"
    isDryRun=false

    if [ "$2" = "--dry-run" ] || [ "$2" = "--dryRun" ] || [ "$2" = "-d" ]
    then
        isDryRun=true
    fi

    # When called directly, redirect stderr to stdout so user sees output
    tidyFile "$filePath" "$isDryRun" 2>&1
    exit 0
fi
