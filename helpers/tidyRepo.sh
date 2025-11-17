#!/bin/bash
# Script to tidy all files in a repository
# Uses tidy.sh functions to process multiple files

set -e

# Preserve stderr (fd 3) so we can redirect it later
exec 3>&2

# Source the tidy script to get the function
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tidyScriptPath="$scriptDir/tidy.sh"
source "$tidyScriptPath"

# Default path is parent directory of helpers/
defaultPath="$(cd "$scriptDir/.." && pwd)"
path="$defaultPath"
dryRun=false

# Parse arguments
while [[ $# -gt 0 ]]
do
    case $1 in
        --dry-run|--dryRun|-d)
            dryRun=true
            shift
            ;;
        --path|-p)
            path="$2"
            shift 2
            ;;
        *)
            # If first arg doesn't start with -, treat as path
            if [[ ! "$1" =~ ^- ]]
            then
                path="$1"
            fi
            shift
            ;;
    esac
done

# Colors
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[1;33m'
cyan='\033[0;36m'
nc='\033[0m' # No Color

# Find all relevant files
files=$(find "$path" -type f \( -name "*.ps1" -o -name "*.sh" -o -name "*.json" -o -name "*.md" \) 2>/dev/null)

if [ -z "$files" ]
then
    echo -e "${yellow}No files found to process.${nc}"
    exit 0
fi

fileCount=0
modifiedCount=0
totalTabCount=0
totalWhitespaceCount=0

# Process each file
while IFS= read -r file
do
    fileCount=$((fileCount + 1))

    # Call tidyFile function - user output goes to stderr, stats to stdout
    # Capture stats from stdout, redirect stderr to preserved fd 3 (visible output)
    stats=$(tidyFile "$file" "$dryRun" 2>&3)
    modified=$(echo "$stats" | cut -d'|' -f1)
    tabCount=$(echo "$stats" | cut -d'|' -f2)
    whitespaceCount=$(echo "$stats" | cut -d'|' -f3)

    if [ "$modified" = true ]
    then
        modifiedCount=$((modifiedCount + 1))
    fi

    totalTabCount=$((totalTabCount + tabCount))
    totalWhitespaceCount=$((totalWhitespaceCount + whitespaceCount))

done <<< "$files"

# Summary
if [ "$dryRun" = true ]
then
    echo ""
    echo -e "${yellow}DRY RUN: Would process $fileCount file(s)${nc}"
    if [ "$totalTabCount" -gt 0 ]
    then
        echo -e "${yellow}  Would convert $totalTabCount tab(s) to spaces${nc}"
    fi
    if [ "$totalWhitespaceCount" -gt 0 ]
    then
        echo -e "${yellow}  Would trim trailing whitespace from $totalWhitespaceCount line(s)${nc}"
    fi
else
    echo ""
    echo -e "${cyan}Processed $fileCount file(s)${nc}"
    if [ "$modifiedCount" -gt 0 ]
    then
        echo -e "${green}Modified $modifiedCount file(s)${nc}"
        if [ "$totalTabCount" -gt 0 ]
        then
            echo -e "${green}  Converted $totalTabCount tab(s) to spaces${nc}"
        fi
        if [ "$totalWhitespaceCount" -gt 0 ]
        then
            echo -e "${green}  Trimmed trailing whitespace from $totalWhitespaceCount line(s)${nc}"
        fi
    else
        echo -e "${green}No files needed tidying. All files are clean!${nc}"
    fi
fi

