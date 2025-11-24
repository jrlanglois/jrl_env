#!/bin/bash
# Run tests with coverage analysis
# Generates HTML coverage report

set -euo pipefail

cd "$(dirname "$0")/.."

echo "================================================================"
echo "           Running Tests with Coverage Analysis"
echo "================================================================"
echo ""

# Clear any existing coverage data
python3 -m coverage erase

# Run all tests with coverage
echo "Running tests..."
python3 -m coverage run --source=common test/testUtilities.py
python3 -m coverage run --source=common -a test/testPlatformDetection.py
python3 -m coverage run --source=common -a test/testSetupValidation.py

echo ""
echo "================================================================"
echo "           Coverage Report"
echo "================================================================"
echo ""

# Generate coverage report
python3 -m coverage report --show-missing

echo ""
echo "================================================================"
echo "           Generating HTML Coverage Report"
echo "================================================================"
echo ""

# Generate HTML report
python3 -m coverage html

echo "✓ HTML coverage report generated: htmlcov/index.html"
echo ""
echo "To view:"
echo "  open htmlcov/index.html"

