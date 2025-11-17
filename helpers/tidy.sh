#!/bin/bash
# Thin wrapper to run the Python tidy utility for a single file

set -euo pipefail

# Allow CRLF scripts to run under Git Bash on Windows
set -o igncr 2>/dev/null || true

if [ $# -lt 1 ]; then
    echo "Usage: $0 <filePath> [--dry-run]" >&2
    exit 1
fi

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tidyPy="$scriptDir/tidy.py"

filePath="$1"
shift

python3 "$tidyPy" --file "$filePath" "$@"
