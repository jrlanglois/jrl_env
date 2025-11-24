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
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    printH2,
    printSuccess,
    printWarning,
    safePrint,
)
from common.systems.update import detectPlatform
from common.systems.schemas import getSchemaForConfig


def validateConfigDirectory(configsDir: Path, platformName: str) -> bool:
    """
    Validate that the config directory exists and is accessible.

    Args:
        configsDir: Path to config directory
        platformName: Platform name for error messages

    Returns:
        True if valid, False otherwise
    """
    from common.common import printError, printInfo

    if not configsDir.exists():
        printError(
            f"Configuration directory does not exist: {configsDir}\n"
            "Please ensure the config directory path is correct."
        )
        return False

    if not configsDir.is_dir():
        printError(f"Configuration path is not a directory: {configsDir}")
        return False

    # Check if directory is readable
    try:
        list(configsDir.iterdir())
    except PermissionError:
        printError(f"Permission denied accessing configuration directory: {configsDir}")
        return False
    except Exception as e:
        printError(f"Error accessing configuration directory: {e}")
        return False

    # Check if directory is empty
    files = list(configsDir.glob("*.json"))
    if not files:
        printError(
            f"Configuration directory is empty: {configsDir}\n"
            "No JSON configuration files found."
        )
        return False

    printInfo(f"Configuration directory validated: {configsDir}")
    return True


def validatePlatformConfig(platformConfigPath: Path, platformName: str) -> bool:
    """
    Validate that the platform config file exists and is valid JSON.

    Args:
        platformConfigPath: Path to platform config file
        platformName: Platform name for error messages

    Returns:
        True if valid, False otherwise
    """
    from common.common import printError, printInfo

    if not platformConfigPath.exists():
        printError(
            f"Platform configuration file not found: {platformConfigPath}\n"
            f"Required file for platform '{platformName}' is missing.\n"
            "Please create this file or ensure you're using the correct config directory."
        )
        return False

    # Validate JSON syntax
    try:
        with open(platformConfigPath, 'r', encoding='utf-8') as f:
            json.load(f)
    except json.JSONDecodeError as e:
        printError(
            f"Invalid JSON in platform configuration file: {platformConfigPath}\n"
            f"JSON error: {e}\n"
            "Please fix the JSON syntax errors before continuing."
        )
        return False
    except Exception as e:
        printError(f"Error reading platform configuration file: {e}")
        return False

    printInfo(f"Platform configuration file validated: {platformConfigPath.name}")
    return True


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


def detectUnknownFields(data: dict, allowedFields: set, path: str = "root") -> list[str]:
    """
    Detect unknown fields in a JSON object.

    Args:
        data: JSON data dictionary
        allowedFields: Set of allowed field names
        path: Current path in the JSON structure (for error messages)

    Returns:
        List of error messages for unknown fields
    """
    errors = []

    if not isinstance(data, dict):
        return errors

    for key in data.keys():
        currentPath = f"{path}.{key}" if path != "root" else key
        if key not in allowedFields:
            errors.append(f"Unknown field '{currentPath}' is not supported")
        elif isinstance(data[key], dict):
            # Recursively check nested objects
            # Note: We don't validate nested objects here as they have their own schemas
            pass

    return errors


def collectUnknownFieldErrors(configsPath: Path, targetPlatform: Optional[str] = None) -> list[str]:
    """
    Collect all unknown field errors from config files.

    Args:
        configsPath: Path to configs directory
        targetPlatform: Optional platform to validate (if None, validates all)

    Returns:
        List of unknown field error messages
    """
    unknownFieldErrors = []

    platforms = ["win11", "macos", "ubuntu", "raspberrypi", "redhat", "opensuse", "archlinux"]
    if targetPlatform:
        platforms = [targetPlatform]

    # Check platform configs
    for platform in platforms:
        platformConfigPath = configsPath / f"{platform}.json"
        if platformConfigPath.exists():
            try:
                errors, _ = validateAppsJson(platformConfigPath, platform)
                # Filter for unknown field errors
                unknownFieldErrors.extend([e for e in errors if "Unknown field" in e])
            except Exception:
                pass  # Already handled by main validation

    # Check shared configs
    try:
        reposPath = configsPath / "repositories.json"
        if reposPath.exists():
            errors, _ = validateRepositoriesJson(reposPath)
            unknownFieldErrors.extend([e for e in errors if "Unknown field" in e])
    except Exception:
        pass

    try:
        gitConfigPath = configsPath / "gitConfig.json"
        if gitConfigPath.exists():
            errors, _ = validateGitConfigJson(gitConfigPath)
            unknownFieldErrors.extend([e for e in errors if "Unknown field" in e])
    except Exception:
        pass

    try:
        fontsPath = configsPath / "fonts.json"
        if fontsPath.exists():
            import json
            with open(fontsPath, 'r', encoding='utf-8') as f:
                fontsData = json.load(f)
            allowedFontFields = {"googleFonts"}
            errors = detectUnknownFields(fontsData, allowedFontFields)
            unknownFieldErrors.extend(errors)
    except Exception:
        pass

    try:
        linuxCommonPath = configsPath / "linuxCommon.json"
        if linuxCommonPath.exists():
            import json
            with open(linuxCommonPath, 'r', encoding='utf-8') as f:
                linuxCommonData = json.load(f)
            allowedLinuxCommonFields = {"apt", "dnf", "pacman", "zypper", "snap", "flatpak"}
            errors = detectUnknownFields(linuxCommonData, allowedLinuxCommonFields)
            unknownFieldErrors.extend(errors)
    except Exception:
        pass

    return unknownFieldErrors


def checkGitHubRepositoryViaApi(ownerRepo: str) -> tuple[Optional[bool], str]:
    """
    Check if a GitHub repository exists via API.

    Args:
        ownerRepo: Repository in format "owner/repo"

    Returns:
        Tuple of (exists: bool|None, message: str)
        None means we couldn't determine (network error, private repo, etc.)
    """
    import os

    apiUrl = f"https://api.github.com/repos/{ownerRepo}"
    isCi = os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'

    try:
        req = urllib.request.Request(apiUrl)
        req.add_header('User-Agent', 'jrl_env-validator')

        # Use GITHUB_TOKEN if available (automatically provided in GitHub Actions)
        githubToken = os.getenv('GITHUB_TOKEN')
        if githubToken:
            req.add_header('Authorization', f'token {githubToken}')

        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                return True, "Repository exists"
            else:
                return False, f"Unexpected status {response.status}"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, "Repository not found or is private (404)"
        elif e.code == 403:
            # In CI, 403s are common due to rate limits or private repos - suppress warning
            if isCi:
                return None, None  # Return None message to suppress warning
            return None, "Repository access forbidden (403) - may be private or rate limited"
        else:
            return None, f"HTTP error {e.code}"
    except (urllib.error.URLError, TimeoutError):
        return None, "Could not reach GitHub API - network issue or timeout"
    except Exception:
        return None, "Error checking repository"


def checkRepositoryExists(repoUrl: str) -> tuple[Optional[bool], str]:
    """
    Check if a repository exists.

    Args:
        repoUrl: Repository URL (GitHub SSH/HTTPS or other Git URL)

    Returns:
        Tuple of (exists: bool|None, message: str)
        None means we couldn't determine (network error, private repo, etc.)
    """
    # Convert GitHub SSH URLs to HTTPS for API checking
    githubMatch = re.match(r'^git@github\.com:(.+?)(?:\.git)?$', repoUrl)
    if githubMatch:
        ownerRepo = githubMatch.group(1)
        return checkGitHubRepositoryViaApi(ownerRepo)

    # Check GitHub HTTPS URLs
    if repoUrl.startswith("https://github.com/"):
        ownerRepo = repoUrl.replace("https://github.com/", "").replace(".git", "")
        return checkGitHubRepositoryViaApi(ownerRepo)

    # For other Git URLs, try git ls-remote (if git is available)
    if repoUrl.startswith("git@") or repoUrl.startswith("http://") or repoUrl.startswith("https://"):
        try:
            result = subprocess.run(
                ["git", "ls-remote", repoUrl],
                capture_output=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                return True, "Repository exists"
            else:
                return False, "Repository not accessible or does not exist"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None, "Could not validate (git not available or timeout)"
        except Exception:
            return None, "Error checking repository"

    return None, "Unknown URL format"


def makeHttpRequest(url: str, userAgent: str = 'jrl_env-validator', timeout: int = 5) -> tuple[Optional[int], Optional[str]]:
    """
    Make an HTTP request and return status code and error message.

    Args:
        url: URL to request
        userAgent: User-Agent header value
        timeout: Request timeout in seconds

    Returns:
        Tuple of (statusCode: int|None, errorMessage: str|None)
        If statusCode is not None, request succeeded. If errorMessage is not None, request failed.
    """
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', userAgent)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, None
    except urllib.error.HTTPError as e:
        return None, f"HTTP error {e.code}"
    except (urllib.error.URLError, TimeoutError):
        return None, "Network issue or timeout"
    except Exception:
        return None, "Error making request"


def checkFontExists(fontName: str) -> tuple[Optional[bool], str]:
    """
    Check if a Google Font exists.

    Args:
        fontName: Font name to check

    Returns:
        Tuple of (exists: bool|None, message: str)
        None means we couldn't determine (network error, etc.)
    """
    fontUrlName = fontName.replace(" ", "+")
    cssUrl = f"https://fonts.googleapis.com/css2?family={fontUrlName}:wght@400"

    status, error = makeHttpRequest(cssUrl, 'Mozilla/5.0', 5)

    if status == 200:
        return True, "Font exists"
    elif status is not None:
        return False, f"Unexpected status {status}"
    elif error and "404" in error:
        return False, "Font not found (404)"
    else:
        return None, f"Could not reach Google Fonts API - {error}"


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

        # Define allowed fields for each platform
        baseFields = {"useLinuxCommon", "commands", "shell", "cruft", "android"}

        # APT-based distributions
        aptFields = baseFields | {"apt", "snap", "flatpak"}
        # DNF-based distributions
        dnfFields = baseFields | {"dnf", "snap", "flatpak"}
        # Pacman-based distributions
        pacmanFields = baseFields | {"pacman", "snap", "flatpak"}
        # Zypper-based distributions
        zypperFields = baseFields | {"zypper", "snap", "flatpak"}
        # Alpine (APK-based, no useLinuxCommon)
        alpineFields = {"apk", "commands", "shell", "cruft", "android"}

        platformFields = {
            # macOS and Windows
            "win11": {"winget", "windowsStore", "commands", "cruft", "android"},
            "macos": {"brew", "brewCask", "commands", "shell", "cruft", "android"},
            # APT-based
            "debian": aptFields,
            "ubuntu": aptFields,
            "popos": aptFields,
            "linuxmint": aptFields,
            "elementary": aptFields,
            "zorin": aptFields,
            "mxlinux": aptFields,
            "raspberrypi": aptFields,
            # DNF-based
            "fedora": dnfFields,
            "redhat": dnfFields,
            # Pacman-based
            "archlinux": pacmanFields,
            "manjaro": pacmanFields,
            "endeavouros": pacmanFields,
            # Zypper-based
            "opensuse": zypperFields,
            # Alpine
            "alpine": alpineFields,
        }

        allowedFields = platformFields.get(platform, baseFields)

        # Check for unknown top-level fields
        unknownFieldErrors = detectUnknownFields(content, allowedFields)
        errors.extend(unknownFieldErrors)

        # Check for unknown fields in nested objects
        if "commands" in content and isinstance(content["commands"], dict):
            allowedCommandFields = {"preInstall", "postInstall"}
            commandErrors = detectUnknownFields(content["commands"], allowedCommandFields, "commands")
            errors.extend(commandErrors)

            # Check command objects
            for phase in ["preInstall", "postInstall"]:
                if phase in content["commands"] and isinstance(content["commands"][phase], list):
                    for i, cmd in enumerate(content["commands"][phase]):
                        if isinstance(cmd, dict):
                            allowedCmdFields = {"name", "shell", "command", "runOnce"}
                            cmdErrors = detectUnknownFields(cmd, allowedCmdFields, f"commands.{phase}[{i}]")
                            errors.extend(cmdErrors)

        if "shell" in content and isinstance(content["shell"], dict):
            allowedShellFields = {"ohMyZshTheme"}
            shellErrors = detectUnknownFields(content["shell"], allowedShellFields, "shell")
            errors.extend(shellErrors)

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

        # Check for unknown fields
        allowedFields = {"workPathUnix", "workPathWindows", "repositories"}
        unknownFieldErrors = detectUnknownFields(content, allowedFields)
        errors.extend(unknownFieldErrors)

        if not content.get("workPathWindows") and not content.get("workPathUnix"):
            errors.append("repositories: Missing workPathWindows or workPathUnix")

        repositories = content.get("repositories", [])
        if not repositories:
            warnings.append("repositories: No repositories specified")
        elif len(repositories) == 0:
            warnings.append("repositories: repositories array is empty")
        else:
            # Validate repository URLs in parallel for speed
            def validateSingleRepo(repo):
                """Validate a single repository (string or object format) and return warnings."""
                repoWarnings = []

                # Handle object format
                if isinstance(repo, dict):
                    pattern = repo.get('pattern', '')
                    visibility = repo.get('visibility', 'all')

                    if not pattern:
                        repoWarnings.append("repositories: Object missing 'pattern' field")
                        return repoWarnings

                    # Validate visibility enum
                    if visibility not in ('all', 'public', 'private'):
                        repoWarnings.append(f"repositories: Invalid visibility '{visibility}' (must be all/public/private)")

                    # Validate wildcard pattern format
                    if '*' in pattern:
                        # Check for valid wildcard pattern
                        if not re.match(r'^(https://github\.com/|git@github\.com:)[^/]+/\*$', pattern):
                            repoWarnings.append(f"repositories: Invalid wildcard pattern: {pattern}")
                            repoWarnings.append("repositories: Valid formats: git@github.com:owner/* or https://github.com/owner/*")
                        # Don't validate wildcard existence (will be expanded at runtime)
                    else:
                        # Regular URL in object format
                        if not re.match(r'^(https://|git@|http://|git://)', pattern):
                            repoWarnings.append(f"repositories: Invalid URL format: {pattern}")

                    return repoWarnings

                # Handle string format (backward compatible)
                if not isinstance(repo, str) or not repo.strip():
                    repoWarnings.append(f"repositories: Invalid repository entry: {repo}")
                    return repoWarnings

                repo = repo.strip()
                # Check URL format
                if not re.match(r'^(https://|git@|http://|git://)', repo):
                    repoWarnings.append(f"repositories: Invalid URL format: {repo}")
                    return repoWarnings

                # Try to validate repository existence (non-blocking)
                repoExists, repoMessage = checkRepositoryExists(repo)
                if repoExists is False:
                    # Repository definitely doesn't exist or is inaccessible
                    repoWarnings.append(f"repositories: {repoMessage}: {repo}")
                elif repoExists is None and repoMessage:
                    # Couldn't determine (network issue, private repo, etc.) - just warn
                    # repoMessage may be None in CI to suppress 403 warnings
                    repoWarnings.append(f"repositories: {repoMessage}: {repo}")

                return repoWarnings

            # Use thread pool for parallel validation (max 10 concurrent checks)
            maxWorkers = min(10, len(repositories))
            with ThreadPoolExecutor(max_workers=maxWorkers) as executor:
                futures = {executor.submit(validateSingleRepo, repo): repo for repo in repositories}
                for future in as_completed(futures):
                    try:
                        repoWarnings = future.result()
                        warnings.extend(repoWarnings)
                    except Exception as e:
                        warnings.append(f"repositories: Validation error - {e}")
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

        # Define allowed fields
        allowedTopLevelFields = {"user", "defaults", "aliases", "lfs"}
        unknownFieldErrors = detectUnknownFields(content, allowedTopLevelFields)
        errors.extend(unknownFieldErrors)

        if not content.get("user"):
            warnings.append("gitConfig: No user section specified")
        else:
            user = content["user"]
            if isinstance(user, dict):
                allowedUserFields = {"name", "email", "usernameGitHub"}
                userErrors = detectUnknownFields(content["user"], allowedUserFields, "user")
                errors.extend(userErrors)

            if not user.get("name"):
                warnings.append("gitConfig: Missing user.name")
            if not user.get("email"):
                warnings.append("gitConfig: Missing user.email")

        if not content.get("defaults"):
            warnings.append("gitConfig: No defaults section specified")

        if not content.get("aliases"):
            warnings.append("gitConfig: No aliases section specified")

        if "lfs" in content and isinstance(content["lfs"], dict):
            allowedLfsFields = {"enabled"}
            lfsErrors = detectUnknownFields(content["lfs"], allowedLfsFields, "lfs")
            errors.extend(lfsErrors)
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
                "          If not specified, validates all platform configs",
            ],
            "Valid Platforms": [
                "macos, win11",
                "debian, ubuntu, popos, linuxmint, elementary, zorin, mxlinux, raspberrypi",
                "fedora, redhat, opensuse, archlinux, manjaro, endeavouros, alpine",
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
            ("--configDir DIR", "Use custom configuration directory (default: ./configs)\n"
             "                  Can also be set via JRL_ENV_CONFIG_DIR environment variable"),
        ],
    )


def main(setupSignalHandler: bool = True) -> int:
    """
    Main validation function.

    Args:
        setupSignalHandler: If True, set up CTRL+C handler. Set to False when called programmatically.

    Returns:
        Exit code (0=success, 1=errors, 2=unknown fields)
    """
    # Register signal handlers for graceful shutdown (only if running as main script)
    if setupSignalHandler:
        from common.core.signalHandling import setupSignalHandlers
        setupSignalHandlers(resumeMessage=False)

    # Check for --help flag
    if "--help" in sys.argv or "-h" in sys.argv:
        printHelp()
        return 0

    # Parse quiet flag
    quiet = "--quiet" in sys.argv or "-q" in sys.argv
    from common.core.logging import setVerbosityFromArgs, getVerbosity, Verbosity
    setVerbosityFromArgs(quiet=quiet, verbose=False)

    # Get config directory (supports --configDir and JRL_ENV_CONFIG_DIR)
    from common.core.utilities import getConfigDirectory
    scriptDir = Path(__file__).parent.parent.parent
    configsPath = getConfigDirectory(scriptDir)

    # Determine which platform to validate (if specified)
    targetPlatform = None
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--configDir") and arg != "--quiet" and arg != "-q" and arg != "--help" and arg != "-h"]
    if len(args) > 0:
        targetPlatform = args[0].lower()
        validPlatforms = (
            "win11", "macos",
            "debian", "ubuntu", "popos", "linuxmint", "elementary", "zorin", "mxlinux", "raspberrypi",
            "fedora", "redhat", "opensuse", "archlinux", "manjaro", "endeavouros", "alpine"
        )
        if targetPlatform not in validPlatforms:
            printError(f"Unknown platform: {targetPlatform}")
            printInfo(f"Valid platforms: {', '.join(validPlatforms)}")
            return 1

    allErrors = []
    allWarnings = []

    printH2("Validating Configuration Files")
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
            # Check for unknown fields in fonts.json
            with open(fontsPath, 'r', encoding='utf-8') as f:
                fontsData = json.load(f)
            allowedFontFields = {"googleFonts"}
            unknownFontErrors = detectUnknownFields(fontsData, allowedFontFields)
            allErrors.extend(unknownFontErrors)

            fonts = getJsonArray(str(fontsPath), ".googleFonts[]?")
            if not fonts or len(fonts) == 0:
                allWarnings.append("fonts: No fonts specified")
            else:
                # Validate font existence
                for font in fonts:
                    if not isinstance(font, str) or not font.strip():
                        continue
                    font = font.strip()
                    fontExists, fontMessage = checkFontExists(font)
                    if fontExists is False:
                        allWarnings.append(f"fonts: {fontMessage}: {font}")
                    elif fontExists is None:
                        allWarnings.append(f"fonts: {fontMessage}: {font}")
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
        # cursorSettings.json can have any valid Cursor/VSCode settings, so we don't restrict fields
        # Schema validation handles structure validation
        printInfo("✓ cursorSettings.json structure valid")

    # Validate linuxCommon.json if it exists
    linuxCommonPath = configsPath / "linuxCommon.json"
    if linuxCommonPath.exists():
        linuxCommonSchema = getSchemaForConfig("linuxCommon")
        isValid, errors, warnings = validateJsonFile(linuxCommonPath, "linuxCommon.json", linuxCommonSchema)
        allErrors.extend(errors)
        allWarnings.extend(warnings)
        if isValid:
            # Check for unknown fields
            try:
                with open(linuxCommonPath, 'r', encoding='utf-8') as f:
                    linuxCommonData = json.load(f)
                allowedLinuxCommonFields = {"apt", "dnf", "pacman", "zypper", "snap", "flatpak"}
                unknownLinuxCommonErrors = detectUnknownFields(linuxCommonData, allowedLinuxCommonFields)
                allErrors.extend(unknownLinuxCommonErrors)
            except Exception:
                pass  # Already handled by schema validation

    safePrint()

    # Separate unknown field errors from other errors
    unknownFieldErrors = [e for e in allErrors if "Unknown field" in e]
    otherErrors = [e for e in allErrors if "Unknown field" not in e]

    # Report results
    if len(otherErrors) == 0 and len(allWarnings) == 0 and len(unknownFieldErrors) == 0:
        result = 0
        if getVerbosity() == Verbosity.quiet:
            safePrint("Success")
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

        if len(otherErrors) > 0:
            # Critical errors (not unknown fields)
            if getVerbosity() != Verbosity.quiet:
                printError("Errors:")
                for error in otherErrors:
                    printError(f"{error}")
                if len(unknownFieldErrors) > 0:
                    printWarning("Unknown fields detected:")
                    for error in unknownFieldErrors:
                        printWarning(f"{error}")
                safePrint()
                printError("Validation failed. Please fix errors before running setup.")
            else:
                safePrint("Failure")
            return 1
        elif len(unknownFieldErrors) > 0:
            # Only unknown field errors - these are non-fatal
            if getVerbosity() != Verbosity.quiet:
                printWarning("Unknown fields detected in configuration files:")
                for error in unknownFieldErrors:
                    printWarning(f"{error}")
                if len(allWarnings) > 0:
                    printWarning("Other warnings:")
                    for warning in allWarnings:
                        printWarning(f"{warning}")
            # Return special code for unknown fields (2 instead of 1)
            return 2
        else:
            # Only warnings, no errors
            result = 0
            if getVerbosity() == Verbosity.quiet:
                safePrint("Success")
            else:
                printSuccess("Validation passed with warnings.")
            return result


__all__ = [
    "validateConfigDirectory",
    "validatePlatformConfig",
    "validateJsonFile",
    "detectUnknownFields",
    "checkGitHubRepositoryViaApi",
    "checkRepositoryExists",
    "checkFontExists",
    "makeHttpRequest",
    "validateAppsJson",
    "validateRepositoriesJson",
    "validateGitConfigJson",
    "collectUnknownFieldErrors",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
