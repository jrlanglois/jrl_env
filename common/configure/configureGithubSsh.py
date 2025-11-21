#!/usr/bin/env python3
"""
Shared GitHub SSH configuration logic for macOS, Ubuntu, and Windows.
Generates SSH keys and helps configure them for GitHub.
"""

import getpass
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

# Import common utilities directly from source modules
from common.core.logging import (
    printError,
    printInfo,
    printH2,
    printSuccess,
    printWarning,
    safePrint,
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


def storePassphrase(keyName: str, passphrase: str) -> bool:
    """
    Store SSH key passphrase securely in system keychain.

    Args:
        keyName: Name of the SSH key
        passphrase: Passphrase to store

    Returns:
        True if successful, False otherwise
    """
    if not KEYRING_AVAILABLE:
        printWarning("keyring library not available. Passphrase will not be stored.")
        return False

    try:
        keyring.set_password("jrl_env_ssh", keyName, passphrase)
        return True
    except Exception as e:
        printWarning(f"Failed to store passphrase in keychain: {e}")
        return False


def getStoredPassphrase(keyName: str) -> Optional[str]:
    """
    Retrieve SSH key passphrase from system keychain.

    Args:
        keyName: Name of the SSH key

    Returns:
        Passphrase if found, None otherwise
    """
    if not KEYRING_AVAILABLE:
        return None

    try:
        return keyring.get_password("jrl_env_ssh", keyName)
    except Exception:
        return None


def deleteStoredPassphrase(keyName: str) -> bool:
    """
    Delete SSH key passphrase from system keychain.

    Args:
        keyName: Name of the SSH key

    Returns:
        True if successful or not found, False on error
    """
    if not KEYRING_AVAILABLE:
        return True

    try:
        keyring.delete_password("jrl_env_ssh", keyName)
        return True
    except keyring.errors.PasswordDeleteError:
        return True  # Password not found, that's ok
    except Exception:
        return False


def addKeyToSshAgent(keyPath: str, passphrase: Optional[str] = None) -> bool:
    """
    Add SSH key to ssh-agent.

    Args:
        keyPath: Path to private key file
        passphrase: Optional passphrase for the key

    Returns:
        True if successful, False otherwise
    """
    if not commandExists("ssh-add"):
        return False

    try:
        # Prepare input for ssh-add (passphrase if provided)
        inputData = f"{passphrase}\n".encode('utf-8') if passphrase else None

        result = subprocess.run(
            ["ssh-add", keyPath],
            check=False,
            capture_output=True,
            input=inputData,
        )
        if result.returncode == 0:
            return True

        # Try macOS keychain option
        if platform.system() == "Darwin" and commandExists("ssh-add"):
            result = subprocess.run(
                ["ssh-add", "--apple-use-keychain", keyPath],
                check=False,
                capture_output=True,
                input=inputData,
            )
            if result.returncode == 0:
                return True
    except Exception:
        pass

    return False


def configureGithubSsh(
    configPath: Optional[str] = None,
    dryRun: bool = False,
    requirePassphrase: bool = False,
    noPassphrase: bool = False,
) -> bool:
    """
    Configure GitHub SSH key generation and setup.

    Args:
        configPath: Path to gitConfig.json file
        dryRun: If True, don't actually generate keys or configure
        requirePassphrase: If True, require a passphrase for the SSH key
        noPassphrase: If True, skip passphrase prompt and use no passphrase

    Returns:
        True if successful, False otherwise
    """
    if not configPath:
        printError("Configuration file path not provided")
        return False

    if not requireCommand("ssh-keygen", ""):
        return False

    printH2("GitHub SSH Configuration", dryRun=dryRun)
    safePrint()

    # Read email and username from config
    email = getJsonValue(configPath, ".user.email", "")
    username = getJsonValue(configPath, ".user.usernameGitHub", "")
    githubUrl = "https://github.com/settings/ssh/new"

    if dryRun:
        printInfo("[DRY RUN] Would configure GitHub SSH key generation")
        if email and email != "null":
            printInfo(f"Would use email: {email}")
        else:
            printInfo("Would prompt for email")
        if username and username != "null":
            printInfo(f"Would use GitHub username: {username}")
        else:
            printInfo("Would prompt for GitHub username")
        printInfo("Would generate SSH key: id_ed25519_github")
        if requirePassphrase:
            printInfo("Would require passphrase for SSH key")
        elif noPassphrase:
            printInfo("Would use no passphrase for SSH key")
        else:
            printInfo("Would optionally prompt for passphrase")
        printInfo("Would add key to ssh-agent")
        printInfo(f"Would open GitHub URL: {githubUrl}")
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

    # Prompt for passphrase
    passphrase = ""
    if not noPassphrase:
        safePrint()
        if requirePassphrase:
            printInfo("A passphrase is required for this SSH key.")
        else:
            printInfo("You can optionally add a passphrase to protect your SSH key.")
            printInfo("Press Enter to skip passphrase (less secure but more convenient).")

        while True:
            passphrase1 = getpass.getpass("Enter passphrase (empty for no passphrase): ")

            if not passphrase1:
                if requirePassphrase:
                    printWarning("Passphrase is required. Please enter a passphrase.")
                    continue
                else:
                    printInfo("Using no passphrase.")
                    passphrase = ""
                    break

            passphrase2 = getpass.getpass("Enter same passphrase again: ")

            if passphrase1 == passphrase2:
                passphrase = passphrase1
                printSuccess("Passphrase confirmed.")
                break
            else:
                printWarning("Passphrases do not match. Please try again.")

    # Generate SSH key
    printInfo("Generating SSH key...")
    try:
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-C", email, "-f", str(keyPath), "-N", passphrase],
            check=True,
            input="",
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        printError("Failed to generate SSH key.")
        return False

    # Store passphrase securely if provided
    if passphrase and KEYRING_AVAILABLE:
        printInfo("Storing passphrase in system keychain...")
        if storePassphrase(keyName, passphrase):
            printSuccess("Passphrase stored securely in system keychain.")
            printInfo("The passphrase will be retrieved automatically when needed.")
        else:
            printWarning("Failed to store passphrase. You'll need to enter it manually when using the key.")
    elif passphrase and not KEYRING_AVAILABLE:
        printWarning("keyring library not available. Install with: pip install keyring")
        printWarning("Passphrase will not be stored. You'll need to enter it manually when using the key.")

    # Start ssh-agent
    startSshAgent()

    # Add key to ssh-agent
    if addKeyToSshAgent(str(keyPath), passphrase if passphrase else None):
        printSuccess("Added key to ssh-agent")
    else:
        printWarning("Unable to add key to agent automatically.")

    # Display public key
    publicKeyPath = keyPath.with_suffix(keyPath.suffix + ".pub")
    safePrint()
    printInfo("Public key:")
    safePrint()
    try:
        with open(publicKeyPath, 'r', encoding='utf-8') as f:
            publicKey = f.read().strip()
            safePrint(publicKey)  # Don't timestamp the actual key
            safePrint()
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

    safePrint()
    printSuccess("GitHub SSH configuration complete")
    return True


__all__ = [
    "copyToClipboard",
    "openUrl",
    "startSshAgent",
    "addKeyToSshAgent",
    "storePassphrase",
    "getStoredPassphrase",
    "deleteStoredPassphrase",
    "configureGithubSsh",
]
