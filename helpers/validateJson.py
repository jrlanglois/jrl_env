#!/usr/bin/env python3
"""
Simple JSON validation script for CI workflows.
Validates JSON syntax and optionally checks for required fields.

Usage:
    python3 helpers/validateJson.py <json_file> [--required-field <field>]
"""

import json
import sys
from pathlib import Path

# Import shared logging utilities from common
scriptDir = Path(__file__).parent.absolute()
commonDir = scriptDir.parent / "common"
sys.path.insert(0, str(commonDir.parent))
from common.core.logging import printHelpText, setVerbosityFromArgs, getVerbosity, Verbosity, printError


def validateJsonFile(jsonPath: str, requiredField: str = None, quiet: bool = False) -> int:
    """
    Validate JSON file syntax and optionally check for required field.

    Args:
        jsonPath: Path to JSON file
        requiredField: Optional JSONPath to required field (e.g., ".workPathUnix")
        quiet: If True, suppress error messages

    Returns:
        0 if valid, 1 if invalid
    """
    jsonFile = Path(jsonPath)

    if not jsonFile.exists():
        if not quiet:
            print(f"Error: File not found: {jsonPath}", file=sys.stderr)
        return 1

    try:
        with open(jsonFile, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check for required field if specified
        if requiredField:
            field = requiredField.lstrip('.')
            parts = field.split('.')
            current = data
            for part in parts:
                if part not in current:
                    if not quiet:
                        print(f"Error: Required field '{requiredField}' not found in {jsonPath}", file=sys.stderr)
                    return 1
                current = current[part]

        return 0
    except json.JSONDecodeError as e:
        if not quiet:
            print(f"Error: Invalid JSON syntax in {jsonPath}: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        if not quiet:
            print(f"Error: Failed to validate {jsonPath}: {e}", file=sys.stderr)
        return 1


def printHelp() -> None:
    """Print help information for validateJson.py."""
    printHelpText(
        title="validateJson.py",
        intent=[
            "Validate JSON files for syntax errors and optionally check for required fields.",
            "Useful for CI workflows and pre-commit validation.",
        ],
        usage="python3 helpers/validateJson.py <json_file> [--required-field <field>]",
        options=[
            ("--help, -h", "Show this help message and exit"),
            ("--required-field <field>", "JSONPath to a required field (e.g., '.workPathUnix')"),
            ("--quiet, -q", "Only show final success/failure message"),
        ],
        examples=[
            "python3 helpers/validateJson.py configs/ubuntu.json",
            "python3 helpers/validateJson.py configs/repositories.json --required-field .workPathUnix",
        ],
    )


def main() -> int:
    """Main function."""
    # Check for --help flag
    if "--help" in sys.argv or "-h" in sys.argv:
        printHelp()
        return 0

    # Parse arguments
    quiet = "--quiet" in sys.argv or "-q" in sys.argv
    setVerbosityFromArgs(quiet=quiet, verbose=False)

    if len(sys.argv) < 2:
        if getVerbosity() == Verbosity.quiet:
            print("Failure")
        else:
            print("Usage: python3 helpers/validateJson.py <json_file> [--required-field <field>]", file=sys.stderr)
            print("Use --help for more information.", file=sys.stderr)
        return 1

    jsonPath = sys.argv[1]
    requiredField = None

    # Parse optional --required-field argument
    if len(sys.argv) >= 4 and sys.argv[2] == "--required-field":
        requiredField = sys.argv[3]

    result = validateJsonFile(jsonPath, requiredField, quiet=quiet)

    # Final success/failure message (always show in quiet mode)
    if getVerbosity() == Verbosity.quiet:
        if result == 0:
            print("Success")
        else:
            print("Failure")

    return result


if __name__ == "__main__":
    sys.exit(main())
