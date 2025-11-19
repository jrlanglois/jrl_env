#!/usr/bin/env python3
"""
Unified validation script for all platforms.
Validates JSON configuration files for syntax, required fields, and basic validity.

Usage:
    python3 -m common.systems.validate [platform]

If platform is not specified, validates all platform configs.
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Try to import jsonschema, but make it optional
try:
    import jsonschema
    from jsonschema import validate as jsonValidate, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    ValidationError = Exception

# Add project root to path
scriptDir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(scriptDir))

from common.common import (
    getJsonArray,
    getJsonValue,
    printError,
    printInfo,
    printSection,
    printSuccess,
    printWarning,
    safePrint,
)
from common.systems.update import detectPlatform
from common.systems.schemas import getSchemaForConfig


def validateJsonFile(filePath: Path, description: str, schema: Optional[dict] = None) -> tuple[bool, list[str], list[str]]:
    """
    Validate a JSON file for syntax errors and optionally against a schema.

    Args:
        filePath: Path to JSON file
        description: Description of the file
        schema: Optional JSON schema to validate against

    Returns:
        Tuple of (isValid, errors, warnings)
    """
    errors = []
    warnings = []

    if not filePath.exists():
        errors.append(f"{description}: File not found: {filePath}")
        return (False, errors, warnings)

    try:
        with open(filePath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate against schema if provided and jsonschema is available
        if schema and HAS_JSONSCHEMA:
            try:
                jsonValidate(instance=data, schema=schema)
                printSuccess(f"{description} (schema valid)")
            except ValidationError as e:
                errorPath = " -> ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
                errors.append(f"{description}: Schema validation failed at {errorPath}: {e.message}")
                return (False, errors, warnings)
        else:
            if schema and not HAS_JSONSCHEMA:
                warnings.append(f"{description}: jsonschema library not available, skipping schema validation")
            printSuccess(f"{description}")

        return (True, errors, warnings)
    except json.JSONDecodeError as e:
        errors.append(f"{description}: Invalid JSON - {e}")
        return (False, errors, warnings)
    except Exception as e:
        errors.append(f"{description}: Error reading file - {e}")
        return (False, errors, warnings)


def validateAppsJson(filePath: Path, platform: str) -> tuple[list[str], list[str]]:
    """
    Validate apps JSON configuration.

    Args:
        filePath: Path to apps JSON file
        platform: Platform name (win11, macos, ubuntu, raspberrypi, redhat, opensuse, archlinux)

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    try:
        with open(filePath, 'r', encoding='utf-8') as f:
            content = json.load(f)

        if platform == "win11":
            winget = content.get("winget", [])
            windowsStore = content.get("windowsStore", [])
            if not winget and not windowsStore:
                warnings.append(f"{platform} apps: No apps specified")
            if winget and len(winget) == 0:
                warnings.append(f"{platform} apps: winget array is empty")
            if windowsStore and len(windowsStore) == 0:
                warnings.append(f"{platform} apps: windowsStore array is empty")
        elif platform == "macos":
            brew = content.get("brew", [])
            brewCask = content.get("brewCask", [])
            if not brew and not brewCask:
                warnings.append(f"{platform} apps: No apps specified")
            if brew and len(brew) == 0:
                warnings.append(f"{platform} apps: brew array is empty")
            if brewCask and len(brewCask) == 0:
                warnings.append(f"{platform} apps: brewCask array is empty")
        elif platform in ("ubuntu", "raspberrypi"):
            apt = content.get("apt", [])
            snap = content.get("snap", [])
            if not apt and not snap:
                warnings.append(f"{platform} apps: No apps specified")
            if apt and len(apt) == 0:
                warnings.append(f"{platform} apps: apt array is empty")
            if snap and len(snap) == 0:
                warnings.append(f"{platform} apps: snap array is empty")
        elif platform == "redhat":
            dnf = content.get("dnf", [])
            if not dnf:
                warnings.append(f"{platform} apps: No apps specified")
            if dnf and len(dnf) == 0:
                warnings.append(f"{platform} apps: dnf array is empty")
        elif platform == "opensuse":
            zypper = content.get("zypper", [])
            if not zypper:
                warnings.append(f"{platform} apps: No apps specified")
            if zypper and len(zypper) == 0:
                warnings.append(f"{platform} apps: zypper array is empty")
        elif platform == "archlinux":
            pacman = content.get("pacman", [])
            if not pacman:
                warnings.append(f"{platform} apps: No apps specified")
            if pacman and len(pacman) == 0:
                warnings.append(f"{platform} apps: pacman array is empty")
    except Exception as e:
        errors.append(f"{platform} apps: Validation failed - {e}")

    return (errors, warnings)


def validateRepositoriesJson(filePath: Path) -> tuple[list[str], list[str]]:
    """
    Validate repositories JSON configuration.

    Args:
        filePath: Path to repositories JSON file

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    try:
        with open(filePath, 'r', encoding='utf-8') as f:
            content = json.load(f)

        if not content.get("workPathWindows") and not content.get("workPathUnix"):
            errors.append("repositories: Missing workPathWindows or workPathUnix")

        repositories = content.get("repositories", [])
        if not repositories:
            warnings.append("repositories: No repositories specified")
        elif len(repositories) == 0:
            warnings.append("repositories: repositories array is empty")
        else:
            # Validate repository URLs
            for repo in repositories:
                if not re.match(r'^(https://|git@)', repo):
                    warnings.append(f"repositories: Invalid URL format: {repo}")
    except Exception as e:
        errors.append(f"repositories: Validation failed - {e}")

    return (errors, warnings)


def validateGitConfigJson(filePath: Path) -> tuple[list[str], list[str]]:
    """
    Validate Git config JSON.

    Args:
        filePath: Path to gitConfig JSON file

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    try:
        with open(filePath, 'r', encoding='utf-8') as f:
            content = json.load(f)

        if not content.get("user"):
            warnings.append("gitConfig: No user section specified")
        else:
            user = content["user"]
            if not user.get("name"):
                warnings.append("gitConfig: Missing user.name")
            if not user.get("email"):
                warnings.append("gitConfig: Missing user.email")

        if not content.get("defaults"):
            warnings.append("gitConfig: No defaults section specified")

        if not content.get("aliases"):
            warnings.append("gitConfig: No aliases section specified")
    except Exception as e:
        errors.append(f"gitConfig: Validation failed - {e}")

    return (errors, warnings)


def printHelp() -> None:
    """Print help information for the validation script."""
    from common.core.logging import printHelpText

    printHelpText(
        title="Configuration Validator",
        intent=[
            "Validate JSON configuration files for syntax errors, required fields,",
            "and schema compliance. Ensures all config files are valid before running setup.",
        ],
        usage="python3 -m common.systems.validate [platform]",
        sections={
            "Arguments": [
                "platform    Optional platform name to validate (ubuntu, macos, win11, etc.)",
                "            If not specified, validates all platform configs",
            ],
            "Valid Platforms": [
                "ubuntu, macos, win11, redhat, opensuse, archlinux, raspberrypi",
            ],
            "Validated Files": [
                "- Platform-specific configs (e.g., ubuntu.json, macos.json)",
                "- fonts.json (Google Fonts configuration)",
                "- repositories.json (repository cloning configuration)",
                "- gitConfig.json (Git configuration)",
                "- cursorSettings.json (Cursor editor settings)",
                "- linuxCommon.json (Linux common packages)",
            ],
        },
        examples=[
            "python3 -m common.systems.validate",
            "python3 -m common.systems.validate ubuntu",
            "python3 -m common.systems.validate macos",
        ],
        options=[
            ("--help, -h", "Show this help message and exit"),
            ("--quiet, -q", "Only show final success/failure message"),
        ],
    )


def main() -> int:
    """Main validation function."""
    # Check for --help flag
    if "--help" in sys.argv or "-h" in sys.argv:
        printHelp()
        return 0

    # Parse quiet flag
    quiet = "--quiet" in sys.argv or "-q" in sys.argv
    from common.core.logging import setVerbosityFromArgs, getVerbosity, Verbosity
    setVerbosityFromArgs(quiet=quiet, verbose=False)

    configsPath = scriptDir / "configs"

    # Determine which platform to validate (if specified)
    targetPlatform = None
    if len(sys.argv) > 1:
        targetPlatform = sys.argv[1].lower()
        if targetPlatform not in ("win11", "macos", "ubuntu", "raspberrypi", "redhat", "opensuse", "archlinux"):
            printError(f"Unknown platform: {targetPlatform}")
            printInfo("Valid platforms: win11, macos, ubuntu, raspberrypi, redhat, opensuse, archlinux")
            return 1

    allErrors = []
    allWarnings = []

    printSection("Validating Configuration Files")
    safePrint()

    printInfo("Validating JSON files...")
    safePrint()

    # Define all platforms to validate
    platforms = ["win11", "macos", "ubuntu", "raspberrypi", "redhat", "opensuse", "archlinux"]
    if targetPlatform:
        platforms = [targetPlatform]

    # Validate platform-specific app configs
    for platform in platforms:
        platformConfigPath = configsPath / f"{platform}.json"
        schema = getSchemaForConfig("platform", platform)
        isValid, errors, warnings = validateJsonFile(platformConfigPath, f"{platform}.json", schema)
        allErrors.extend(errors)
        allWarnings.extend(warnings)
        if isValid:
            errors, warnings = validateAppsJson(platformConfigPath, platform)
            allErrors.extend(errors)
            allWarnings.extend(warnings)

    # Validate shared configs (only if not validating a specific platform, or always for shared configs)
    fontsPath = configsPath / "fonts.json"
    fontsSchema = getSchemaForConfig("fonts")
    isValid, errors, warnings = validateJsonFile(fontsPath, "fonts.json", fontsSchema)
    allErrors.extend(errors)
    allWarnings.extend(warnings)
    if isValid:
        try:
            fonts = getJsonArray(str(fontsPath), ".googleFonts[]?")
            if not fonts or len(fonts) == 0:
                allWarnings.append("fonts: No fonts specified")
        except Exception as e:
            allErrors.append(f"fonts: Validation failed - {e}")

    reposPath = configsPath / "repositories.json"
    reposSchema = getSchemaForConfig("repositories")
    isValid, errors, warnings = validateJsonFile(reposPath, "repositories.json", reposSchema)
    allErrors.extend(errors)
    allWarnings.extend(warnings)
    if isValid:
        errors, warnings = validateRepositoriesJson(reposPath)
        allErrors.extend(errors)
        allWarnings.extend(warnings)

    gitConfigPath = configsPath / "gitConfig.json"
    gitSchema = getSchemaForConfig("gitConfig")
    isValid, errors, warnings = validateJsonFile(gitConfigPath, "gitConfig.json", gitSchema)
    allErrors.extend(errors)
    allWarnings.extend(warnings)
    if isValid:
        errors, warnings = validateGitConfigJson(gitConfigPath)
        allErrors.extend(errors)
        allWarnings.extend(warnings)

    cursorSettingsPath = configsPath / "cursorSettings.json"
    cursorSchema = getSchemaForConfig("cursorSettings")
    isValid, errors, warnings = validateJsonFile(cursorSettingsPath, "cursorSettings.json", cursorSchema)
    allErrors.extend(errors)
    allWarnings.extend(warnings)
    if isValid:
        printInfo("  ✓ cursorSettings.json structure valid")

    # Validate linuxCommon.json if it exists
    linuxCommonPath = configsPath / "linuxCommon.json"
    if linuxCommonPath.exists():
        linuxCommonSchema = getSchemaForConfig("linuxCommon")
        isValid, errors, warnings = validateJsonFile(linuxCommonPath, "linuxCommon.json", linuxCommonSchema)
        allErrors.extend(errors)
        allWarnings.extend(warnings)

    safePrint()

    # Report results
    if len(allErrors) == 0 and len(allWarnings) == 0:
        result = 0
        if getVerbosity() == Verbosity.quiet:
            print("Success")
        else:
            printSuccess("All configuration files are valid!")
        return result
    else:
        if len(allWarnings) > 0:
            if getVerbosity() != Verbosity.quiet:
                printWarning("Warnings:")
                for warning in allWarnings:
                    printWarning(f"{warning}")
                safePrint()

        if len(allErrors) > 0:
            if getVerbosity() != Verbosity.quiet:
                printError("Errors:")
                for error in allErrors:
                    printError(f"{error}")
                safePrint()
                printError("Validation failed. Please fix errors before running setup.")
            else:
                print("Failure")
            return 1
        else:
            result = 0
            if getVerbosity() == Verbosity.quiet:
                print("Success")
            else:
                printSuccess("Validation passed with warnings.")
            return result


if __name__ == "__main__":
    sys.exit(main())
