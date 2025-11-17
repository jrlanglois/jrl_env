#!/bin/bash
# Helper script to run Allman brace conversion and whitespace tidying

set -e

scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repoRoot="$(cd "$scriptDir/.." && pwd)"

echo "=== Running convertToAllman.py ==="
python "$scriptDir/convertToAllman.py"

echo ""
echo "=== Running tidyRepo.sh ==="
bash "$scriptDir/tidyRepo.sh" "$repoRoot"

echo ""
echo "Formatting complete."

