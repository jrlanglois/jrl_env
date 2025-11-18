#!/usr/bin/env python3
"""
Enhanced validation for Git config
Validates aliases, defaults, name (UTF-8 and web-compatible), email, and GitHub username
"""

import json
import re
import sys
import urllib.request
import urllib.error
from email.utils import parseaddr
from pathlib import Path


def is_valid_utf8(text):
    """Check if text is valid UTF-8"""
    try:
        text.encode('utf-8')
        return True
    except UnicodeEncodeError:
        return False


def is_web_form_compatible(text):
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


def is_valid_email(email):
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


def github_username_exists(username):
    """Check if GitHub username exists"""
    if not username:
        return False, "Username is empty"
    
    # GitHub username validation: alphanumeric and hyphens, 1-39 chars
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$', username):
        return False, "Invalid GitHub username format"
    
    try:
        url = f"https://api.github.com/users/{username}"
        req = urllib.request.Request(url, headers={'User-Agent': 'jrl_env-validator'})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                return True, "Username exists"
            else:
                return False, f"GitHub API returned status {response.status}"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, "Username does not exist on GitHub"
        return False, f"GitHub API error: {e.code}"
    except Exception as e:
        return None, f"Error checking GitHub: {str(e)}"


def validate_git_alias(alias):
    """Validate a git alias command"""
    if not alias:
        return False, "Alias is empty"
    
    # Basic validation: should be a valid git command
    # This is a simple check - actual validation would require parsing the full command
    if len(alias) > 1000:  # Reasonable limit
        return False, "Alias too long"
    
    return True, "Valid"


def validate_git_config(config_path):
    """Main validation function"""
    errors = []
    warnings = []
    
    print("=== Validating Git Config ===\n")
    
    # Read config file
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"✗ Error: Config file not found: {config_path}")
        return 1
    except json.JSONDecodeError as e:
        print(f"✗ Error: Invalid JSON: {e}")
        return 1
    except Exception as e:
        print(f"✗ Error reading config: {e}")
        return 1
    
    # Validate user section
    if 'user' in config:
        user = config['user']
        print("Validating user section...")
        
        # Validate name
        if 'name' in user and user['name']:
            name = user['name']
            if not is_valid_utf8(name):
                errors.append(f"user.name: Invalid UTF-8 encoding")
            elif not is_web_form_compatible(name):
                errors.append(f"user.name: Not compatible with web forms (contains invalid characters)")
            else:
                print(f"  ✓ user.name: {name}")
        else:
            warnings.append("user.name: Not specified")
        
        # Validate email
        if 'email' in user and user['email']:
            email = user['email']
            if is_valid_email(email):
                print(f"  ✓ user.email: {email}")
            else:
                errors.append(f"user.email: Invalid email format: {email}")
        else:
            warnings.append("user.email: Not specified")
        
        # Validate GitHub username
        if 'usernameGitHub' in user and user['usernameGitHub']:
            username = user['usernameGitHub']
            print(f"  Checking GitHub username: {username}...")
            exists, message = github_username_exists(username)
            if exists:
                print(f"  ✓ user.usernameGitHub: {username} ({message})")
            elif exists is None:
                warnings.append(f"user.usernameGitHub: Could not verify ({message})")
            else:
                errors.append(f"user.usernameGitHub: {message}: {username}")
        else:
            warnings.append("user.usernameGitHub: Not specified")
        
        print()
    
    # Validate aliases
    if 'aliases' in config:
        print("Validating aliases...")
        aliases = config['aliases']
        for alias_name, alias_command in aliases.items():
            is_valid, message = validate_git_alias(alias_command)
            if is_valid:
                print(f"  ✓ alias.{alias_name}")
            else:
                errors.append(f"alias.{alias_name}: {message}")
        print()
    
    # Validate defaults section
    if 'defaults' in config:
        print("Validating defaults...")
        defaults = config['defaults']
        
        # Validate init.defaultBranch if present
        if 'init.defaultBranch' in defaults:
            default_branch = defaults['init.defaultBranch']
            # Basic validation: should be a valid branch name
            if re.match(r'^[a-zA-Z0-9._/-]+$', default_branch):
                print(f"  ✓ init.defaultBranch: {default_branch}")
            else:
                errors.append(f"init.defaultBranch: Invalid branch name: {default_branch}")
        
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
                        int_value = int(value) if isinstance(value, str) else value
                        if not isinstance(int_value, int) or int_value < 0:
                            errors.append(f"defaults.{key}: Invalid value '{value}' (should be a non-negative integer)")
                        else:
                            print(f"  ✓ defaults.{key}: {value}")
                    except (ValueError, TypeError):
                        errors.append(f"defaults.{key}: Invalid value '{value}' (should be a non-negative integer)")
                else:
                    print(f"  ✓ defaults.{key}: {value}")
            else:
                errors.append(f"defaults.{key}: Invalid value type (should be string, number, or boolean)")
        print()
    
    # Report results
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  ⚠ {warning}")
        print()
    
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  ✗ {error}")
        print()
        print("✗ Validation failed")
        return 1
    else:
        print("✓ All validations passed!")
        if warnings:
            print("(with warnings)")
        return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 validateGitConfig.py <path-to-gitConfig.json>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    sys.exit(validate_git_config(config_path))

