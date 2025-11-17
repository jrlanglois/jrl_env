#!/bin/bash
# Helper script to run Allman brace conversion and whitespace tidying

set -e

# Allow CRLF scripts to run under Git Bash on Windows
set -o igncr 2>/dev/null || true

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repoRoot="$(cd "$scriptDir/.." && pwd)"

# Always use a non-interactive pager so automation doesn't hang
export PAGER="${PAGER:-cat}"
if [ "$PAGER" != "cat" ]; then
    export PAGER=cat
fi

echo "=== Running convertToAllman.py ==="
python3 "$scriptDir/convertToAllman.py"

echo ""
echo "=== Running tidyRepo.sh ==="
bash "$scriptDir/tidyRepo.sh" "$repoRoot"

echo ""
echo "Formatting complete."
