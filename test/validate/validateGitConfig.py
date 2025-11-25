#!/usr/bin/env python3
"""
Enhanced validation for Git config
Validates aliases, defaults, name (UTF-8 and web-compatible), email, and GitHub username
"""

import json
import re
import sys
import time
import urllib.error
import urllib.request
from email.utils import parseaddr
from pathlib import Path
from typing import Optional

# Add project root to path so we can import from common
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent.parent
sys.path.insert(0, str(projectRoot))

from common.common import (
    printError,
    printInfo,
    printH2,
    printSuccess,
    printWarning,
    safePrint,
)


def isValidUtf8(text: str) -> bool:
    """Check if text is valid UTF-8"""
    try:
        text.encode('utf-8')
        return True
    except UnicodeEncodeError:
        return False


def isWebFormCompatible(text: str) -> bool:
    """Check if text is compatible with web forms (GitHub, etc.)
    Allows letters, numbers, spaces, hyphens, apostrophes, and common Unicode characters
    """
    # GitHub allows most Unicode characters in names, but we'll be conservative
    # Allow letters, numbers, spaces, hyphens, apostrophes, and common punctuation
    pattern = r'^[\p{L}\p{N}\s\-\'\.]+$'
    try:
        return bool(re.match(pattern, text, re.UNICODE))
    except Exception:
        # Fallback: check for control characters and problematic characters
        return not any(ord(c) < 32 or c in '<>{}[]|\\`' for c in text)


def isValidEmail(email: str) -> bool:
    """Check if email is valid"""
    if not email:
        return False

    # Basic email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False

    # Use email.utils.parseaddr for additional validation
    name, addr = parseaddr(email)
    return bool(addr and '@' in addr)


def githubUsernameExists(username: str) -> tuple[Optional[bool], str]:
    """Check if GitHub username exists"""
    import os

    if not username:
        return False, "Username is empty"

    # GitHub username validation: alphanumeric and hyphens, 1-39 chars
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$', username):
        return False, "Invalid GitHub username format"

    isCi = os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'

    try:
        url = f"https://api.github.com/users/{username}"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'jrl_env-validator')

        # Use GITHUB_TOKEN if available (automatically provided in GitHub Actions)
        githubToken = os.getenv('GITHUB_TOKEN')
        if githubToken:
            req.add_header('Authorization', f'token {githubToken}')

        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                return True, "Username exists"
            else:
                return False, f"GitHub API returned status {response.status}"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, "Username does not exist on GitHub"
        elif e.code == 403:
            # 403 can mean rate limiting, private account, or API restrictions
            # In CI, this is common and shouldn't fail validation
            if isCi:
                return None, "Could not verify (rate limited or API restricted)"
            return None, "Could not verify (403 - may be rate limited or API restricted)"
        else:
            return None, f"GitHub API error: {e.code}"
    except (urllib.error.URLError, TimeoutError):
        return None, "Could not reach GitHub API - network issue or timeout"
    except Exception as e:
        return None, f"Error checking GitHub: {str(e)}"


def validateGitAlias(alias: str) -> tuple[bool, str]:
    """Validate a git alias command"""
    if not alias:
        return False, "Alias is empty"

    # Basic validation: should be a valid git command
    # This is a simple check - actual validation would require parsing the full command
    if len(alias) > 1000:  # Reasonable limit
        return False, "Alias too long"

    return True, "Valid"


def validateGitConfig(configPath: str) -> int:
    """Main validation function"""
    errors = []
    warnings = []

    printH2("Validating Git Config")
    safePrint()

    # Read config file
    try:
        with open(configPath, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        printError(f"Config file not found: {configPath}")
        return 1
    except json.JSONDecodeError as e:
        printError(f"Invalid JSON: {e}")
        return 1
    except Exception as e:
        printError(f"Error reading config: {e}")
        return 1

    # Validate user section
    if 'user' in config:
        user = config['user']
        printInfo("Validating user section...")

        # Validate name
        if 'name' in user and user['name']:
            name = user['name']
            if not isValidUtf8(name):
                errors.append(f"user.name: Invalid UTF-8 encoding")
            elif not isWebFormCompatible(name):
                errors.append(f"user.name: Not compatible with web forms (contains invalid characters)")
            else:
                printSuccess(f"user.name: {name}")
        else:
            warnings.append("user.name: Not specified")

        # Validate email
        if 'email' in user and user['email']:
            email = user['email']
            if isValidEmail(email):
                printSuccess(f"user.email: {email}")
            else:
                errors.append(f"user.email: Invalid email format: {email}")
        else:
            warnings.append("user.email: Not specified")

        # Validate GitHub username
        if 'usernameGitHub' in user and user['usernameGitHub']:
            username = user['usernameGitHub']
            printInfo(f"Checking GitHub username: {username}...")
            exists, message = githubUsernameExists(username)
            if exists:
                printSuccess(f"user.usernameGitHub: {username} ({message})")
            elif exists is None:
                warnings.append(f"user.usernameGitHub: Could not verify ({message})")
            else:
                errors.append(f"user.usernameGitHub: {message}: {username}")
        else:
            warnings.append("user.usernameGitHub: Not specified")

        safePrint()

    # Validate aliases
    if 'aliases' in config:
        printInfo("Validating aliases...")
        aliases = config['aliases']
        for aliasName, aliasCommand in aliases.items():
            isValid, message = validateGitAlias(aliasCommand)
            if isValid:
                printSuccess(f"alias.{aliasName}")
            else:
                errors.append(f"alias.{aliasName}: {message}")
        safePrint()

    # Validate defaults section
    if 'defaults' in config:
        printInfo("Validating defaults...")
        defaults = config['defaults']

        # Validate init.defaultBranch if present
        if 'init.defaultBranch' in defaults:
            defaultBranch = defaults['init.defaultBranch']
            # Basic validation: should be a valid branch name
            if re.match(r'^[a-zA-Z0-9._/-]+$', defaultBranch):
                printSuccess(f"init.defaultBranch: {defaultBranch}")
            else:
                errors.append(f"init.defaultBranch: Invalid branch name: {defaultBranch}")

        # Validate other defaults (basic checks)
        for key, value in defaults.items():
            if key == 'init.defaultBranch':
                continue  # Already validated above

            # Basic validation: value should be a string or number
            if isinstance(value, (str, int, bool)):
                # Additional validation for specific keys
                if key == 'color.ui' and value not in ['auto', 'always', 'never', 'true', 'false']:
                    errors.append(f"defaults.{key}: Invalid value '{value}' (should be auto, always, never, true, or false)")
                elif key == 'pull.rebase' and value not in ['true', 'false', True, False]:
                    errors.append(f"defaults.{key}: Invalid value '{value}' (should be true or false)")
                elif key == 'push.default' and value not in ['nothing', 'matching', 'upstream', 'simple', 'current']:
                    errors.append(f"defaults.{key}: Invalid value '{value}' (should be nothing, matching, upstream, simple, or current)")
                elif key == 'push.autoSetupRemote' and value not in ['true', 'false', True, False]:
                    errors.append(f"defaults.{key}: Invalid value '{value}' (should be true or false)")
                elif key == 'rebase.autoStash' and value not in ['true', 'false', True, False]:
                    errors.append(f"defaults.{key}: Invalid value '{value}' (should be true or false)")
                elif key == 'merge.ff' and value not in ['true', 'false', 'only', True, False]:
                    errors.append(f"defaults.{key}: Invalid value '{value}' (should be true, false, or only)")
                elif key == 'fetch.parallel':
                    # Handle both string and int values from JSON
                    try:
                        intValue = int(value) if isinstance(value, str) else value
                        if not isinstance(intValue, int) or intValue < 0:
                            errors.append(f"defaults.{key}: Invalid value '{value}' (should be a non-negative integer)")
                        else:
                            printSuccess(f"defaults.{key}: {value}")
                    except (ValueError, TypeError):
                        errors.append(f"defaults.{key}: Invalid value '{value}' (should be a non-negative integer)")
                else:
                    printSuccess(f"defaults.{key}: {value}")
            else:
                errors.append(f"defaults.{key}: Invalid value type (should be string, number, or boolean)")
        safePrint()

    # Report results
    if warnings:
        printWarning("Warnings:")
        for warning in warnings:
            printWarning(f"{warning}")
        safePrint()

    if errors:
        printError("Errors:")
        for error in errors:
            printError(f"{error}")
        safePrint()
        printError("Validation failed")
        return 1
    else:
        printSuccess("All validations passed!")
        if warnings:
            printWarning("(with warnings)")
        return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        printError("Usage: python3 validateGitConfig.py <path-to-gitConfig.json>")
        sys.exit(1)

    configPath = sys.argv[1]
    startTime = time.perf_counter()
    exitCode = validateGitConfig(configPath)
    elapsed = time.perf_counter() - startTime
    safePrint()
    printInfo(f"Validation completed in {elapsed:.2f}s")
    sys.exit(exitCode)
