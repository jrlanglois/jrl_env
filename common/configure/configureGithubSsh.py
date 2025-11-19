#!/usr/bin/env python3
"""
Shared GitHub SSH configuration logic for macOS, Ubuntu, and Windows.
Generates SSH keys and helps configure them for GitHub.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Import common utilities directly from source modules
from common.core.logging import (
    printError,
    printInfo,
    printSection,
    printSuccess,
    printWarning,
)
from common.core.utilities import (
    commandExists,
    getJsonValue,
    requireCommand,
)


def copyToClipboard(text: str) -> bool:
    """
    Copy text to clipboard using platform-specific command.

    Args:
        text: Text to copy to clipboard

    Returns:
        True if successful, False otherwise
    """
    system = platform.system()

    if system == "Darwin":  # macOS
        if commandExists("pbcopy"):
            try:
                process = subprocess.Popen(
                    ["pbcopy"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                process.communicate(input=text.encode('utf-8'))
                return process.returncode == 0
            except Exception:
                return False
    elif system == "Linux":
        if commandExists("xclip"):
            try:
                process = subprocess.Popen(
                    ["xclip", "-selection", "clipboard"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                process.communicate(input=text.encode('utf-8'))
                return process.returncode == 0
            except Exception:
                pass
        if commandExists("wl-copy"):  # Wayland
            try:
                process = subprocess.Popen(
                    ["wl-copy"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                process.communicate(input=text.encode('utf-8'))
                return process.returncode == 0
            except Exception:
                pass
    elif system == "Windows":
        if commandExists("clip"):
            try:
                process = subprocess.Popen(
                    ["clip"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                process.communicate(input=text.encode('utf-8'))
                return process.returncode == 0
            except Exception:
                pass

    return False


def openUrl(url: str) -> bool:
    """
    Open a URL in the default browser.

    Args:
        url: URL to open

    Returns:
        True if successful, False otherwise
    """
    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", url], check=False, capture_output=True)
            return True
        elif system == "Linux":
            subprocess.run(["xdg-open", url], check=False, capture_output=True)
            return True
        elif system == "Windows":
            subprocess.run(["start", url], check=False, shell=True, capture_output=True)
            return True
    except Exception:
        pass

    return False


def startSshAgent() -> bool:
    """
    Start ssh-agent if available.

    Returns:
        True if successful or not needed, False on error
    """
    if not commandExists("ssh-agent"):
        return True  # Not critical if ssh-agent is not available

    try:
        subprocess.run(
            ["ssh-agent", "-s"],
            check=False,
            capture_output=True,
        )
        return True
    except Exception:
        return True  # Not critical


def addKeyToSshAgent(keyPath: str) -> bool:
    """
    Add SSH key to ssh-agent.

    Args:
        keyPath: Path to private key file

    Returns:
        True if successful, False otherwise
    """
    if not commandExists("ssh-add"):
        return False

    try:
        result = subprocess.run(
            ["ssh-add", keyPath],
            check=False,
            capture_output=True,
        )
        if result.returncode == 0:
            return True

        # Try macOS keychain option
        if platform.system() == "Darwin" and commandExists("ssh-add"):
            result = subprocess.run(
                ["ssh-add", "--apple-use-keychain", keyPath],
                check=False,
                capture_output=True,
            )
            if result.returncode == 0:
                return True
    except Exception:
        pass

    return False


def configureGithubSsh(
    configPath: Optional[str] = None,
    dryRun: bool = False,
) -> bool:
    """
    Configure GitHub SSH key generation and setup.

    Args:
        configPath: Path to gitConfig.json file
        dryRun: If True, don't actually generate keys or configure

    Returns:
        True if successful, False otherwise
    """
    if not configPath:
        printError("Configuration file path not provided")
        return False

    if not requireCommand("ssh-keygen", ""):
        return False

    printSection("GitHub SSH Configuration", dryRun=dryRun)
    print()

    # Read email and username from config
    email = getJsonValue(configPath, ".user.email", "")
    username = getJsonValue(configPath, ".user.usernameGitHub", "")
    githubUrl = "https://github.com/settings/ssh/new"

    if dryRun:
        printInfo("[DRY RUN] Would configure GitHub SSH key generation")
        if email and email != "null":
            printInfo(f"  Would use email: {email}")
        else:
            printInfo("  Would prompt for email")
        if username and username != "null":
            printInfo(f"  Would use GitHub username: {username}")
        else:
            printInfo("  Would prompt for GitHub username")
        printInfo("  Would generate SSH key: id_ed25519_github")
        printInfo("  Would add key to ssh-agent")
        printInfo(f"  Would open GitHub URL: {githubUrl}")
        printSuccess("GitHub SSH configuration complete!")
        return True

    # Prompt for email
    if not email or email == "null":
        emailInput = input("Enter email for SSH key: ").strip()
        email = emailInput
    else:
        emailInput = input(f"Enter email for SSH key [{email}]: ").strip()
        email = emailInput if emailInput else email

    # Prompt for username
    if not username or username == "null":
        usernameInput = input("Enter GitHub username: ").strip()
        username = usernameInput
    else:
        usernameInput = input(f"Enter GitHub username [{username}]: ").strip()
        username = usernameInput if usernameInput else username

    if not email:
        printError("Email is required to generate SSH key.")
        return False

    # Determine key path
    keyDir = Path.home() / ".ssh"
    keyName = "id_ed25519_github"
    keyNameInput = input(f"Key filename [{keyName}]: ").strip()
    keyName = keyNameInput if keyNameInput else keyName
    keyPath = keyDir / keyName

    # Create .ssh directory if it doesn't exist
    keyDir.mkdir(mode=0o700, parents=True, exist_ok=True)

    # Check if key already exists
    if keyPath.exists():
        overwrite = input("Key file exists. Overwrite? (y/N): ").strip()
        if overwrite.upper() != "Y":
            printInfo("Skipping key generation.")
            return True

    # Generate SSH key
    printInfo("Generating SSH key...")
    try:
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-C", email, "-f", str(keyPath), "-N", ""],
            check=True,
            input="",  # Empty passphrase
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        printError("Failed to generate SSH key.")
        return False

    # Start ssh-agent
    startSshAgent()

    # Add key to ssh-agent
    if addKeyToSshAgent(str(keyPath)):
        printSuccess("Added key to ssh-agent")
    else:
        printWarning("Unable to add key to agent automatically.")

    # Display public key
    publicKeyPath = keyPath.with_suffix(keyPath.suffix + ".pub")
    print()
    printInfo("Public key:")
    print()
    try:
        with open(publicKeyPath, 'r', encoding='utf-8') as f:
            publicKey = f.read().strip()
            print(publicKey)
            print()
    except Exception as e:
        printError(f"Failed to read public key: {e}")
        return False

    # Copy to clipboard
    if copyToClipboard(publicKey):
        printSuccess("Copied public key to clipboard")
    else:
        printWarning("Copy the above key manually.")

    # Ask to open GitHub page
    openPage = input("Open GitHub SSH keys page now? (Y/n): ").strip()
    if not openPage or openPage.upper() == "Y":
        if openUrl(githubUrl):
            pass  # Success, no message needed
        else:
            printInfo(f"Open {githubUrl} in your browser to add the key.")
    else:
        printInfo(f"Visit {githubUrl} to add the key when ready.")

    print()
    printSuccess("GitHub SSH configuration complete")
    return True


__all__ = [
    "copyToClipboard",
    "openUrl",
    "startSshAgent",
    "addKeyToSshAgent",
    "configureGithubSsh",
]
