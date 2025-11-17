#!/bin/bash
# Script to tidy all files in a repository via the Python implementation

set -euo pipefail

# Allow CRLF scripts to run under Git Bash on Windows
set -o igncr 2>/dev/null || true

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tidyPy="$scriptDir/tidy.py"

defaultPath="$(cd "$scriptDir/.." && pwd)"
dryRunFlag=""
targetPath="$defaultPath"
extraArgs=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run|--dryRun|-d)
        {
            dryRunFlag="--dry-run"
            shift
        }
        ;;
        --path|-p)
        {
            targetPath="$2"
            shift 2
        }
        ;;
        *)
        {
            if [[ ! "$1" =~ ^- ]]; then
                targetPath="$1"
            else
                extraArgs+=("$1")
            fi
            shift
        }
        ;;
    esac
done

cmd=(python3 "$tidyPy")
if [[ -n "$dryRunFlag" ]]; then
    cmd+=("$dryRunFlag")
fi
cmd+=("--path" "$targetPath")
if [[ ${#extraArgs[@]} -gt 0 ]]; then
    cmd+=("${extraArgs[@]}")
fi

"${cmd[@]}"
