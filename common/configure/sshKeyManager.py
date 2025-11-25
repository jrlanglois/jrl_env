#!/usr/bin/env python3
"""
SSH Key management for GitHub configuration.
Refactored into focused, single-responsibility classes and methods.
"""

import getpass
import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from common.core.logging import printError, printInfo, printSuccess, printWarning
from common.core.utilities import getJsonValue


class SshKeyConfig:
    """SSH key configuration from gitConfig.json."""

    def __init__(self, configPath: str):
        """
        Load and validate SSH key configuration.

        Args:
            configPath: Path to gitConfig.json file
        """
        self.algorithm = getJsonValue(configPath, ".ssh.algorithm", "ed25519")
        self.keySize = getJsonValue(configPath, ".ssh.keySize", None)
        self.keyFilename = getJsonValue(configPath, ".ssh.keyFilename", f"id_{self.algorithm}_github")

    def validate(self) -> bool:
        """
        Validate SSH key configuration.

        Returns:
            True if valid, False otherwise
        """
        # Validate algorithm
        validAlgorithms = ["rsa", "dsa", "ecdsa", "ed25519"]
        if self.algorithm not in validAlgorithms:
            printError(f"Invalid SSH algorithm '{self.algorithm}' in config.")
            printError(f"Valid algorithms: {', '.join(validAlgorithms)}")
            printError("Recommended: ed25519 (modern, secure, fast)")
            return False

        # Validate key size
        if self.keySize is not None:
            try:
                self.keySize = int(self.keySize)
            except (ValueError, TypeError):
                printError(f"Invalid SSH key size '{self.keySize}'. Must be an integer or null.")
                return False

            # Algorithm-specific validation
            if self.algorithm == "ed25519":
                printError("ed25519 algorithm does not support custom key size.")
                printError("Remove 'keySize' from config or set it to null.")
                return False
            elif self.algorithm == "dsa":
                printError("dsa algorithm does not support custom key size.")
                printError("Remove 'keySize' from config or set it to null.")
                return False
            elif self.algorithm == "rsa":
                if self.keySize < 2048:
                    printError(f"RSA key size {self.keySize} is too small (minimum 2048 bits).")
                    printError("Recommended: 4096 bits for RSA keys.")
                    return False
                if self.keySize not in (2048, 3072, 4096):
                    printWarning(f"Non-standard RSA key size {self.keySize}. Common sizes: 2048, 3072, 4096.")
            elif self.algorithm == "ecdsa":
                if self.keySize not in (256, 384, 521):
                    printError(f"Invalid ECDSA key size {self.keySize}.")
                    printError("ECDSA only supports 256, 384, or 521 bits.")
                    printError("Recommended: 521 bits.")
                    return False

        # Validate filename
        if not self.keyFilename or self.keyFilename == "null":
            printError("SSH key filename cannot be empty.")
            return False

        return True


class SshKeyGenerator:
    """Handles SSH key generation."""

    def __init__(self, keyConfig: SshKeyConfig, email: str, dryRun: bool = False):
        """
        Initialise SSH key generator.

        Args:
            keyConfig: SSH key configuration
            email: Email for key comment
            dryRun: If True, don't actually generate
        """
        self.keyConfig = keyConfig
        self.email = email
        self.dryRun = dryRun
        self.keyDir = Path.home() / ".ssh"

    def getKeyPath(self, keyName: str) -> Path:
        """Get full path to key file."""
        return self.keyDir / keyName

    def buildKeygenCommand(self, keyPath: Path, passphrase: str) -> list:
        """
        Build ssh-keygen command with appropriate flags.

        Args:
            keyPath: Path to key file
            passphrase: Passphrase for key

        Returns:
            Command list for subprocess
        """
        cmd = [
            "ssh-keygen",
            "-t", self.keyConfig.algorithm,
            "-C", self.email,
            "-f", str(keyPath),
            "-N", passphrase
        ]

        # Add key size if applicable
        if self.keyConfig.keySize and self.keyConfig.algorithm not in ("ed25519", "dsa"):
            cmd.insert(3, "-b")
            cmd.insert(4, str(self.keyConfig.keySize))

        return cmd

    def generate(self, keyName: str, passphrase: str) -> bool:
        """
        Generate SSH key.

        Args:
            keyName: Name of key file
            passphrase: Passphrase for key

        Returns:
            True if successful, False otherwise
        """
        keyPath = self.getKeyPath(keyName)

        if self.dryRun:
            printInfo(f"[DRY RUN] Would generate SSH key: {keyName}")
            return True

        # Create .ssh directory if needed
        self.keyDir.mkdir(mode=0o700, parents=True, exist_ok=True)

        # Check if key already exists
        if keyPath.exists():
            overwrite = input("Key file exists. Overwrite? (y/N): ").strip()
            if overwrite.upper() != "Y":
                printInfo("Skipping key generation.")
                return True

        printInfo(f"Generating SSH key ({self.keyConfig.algorithm})...")
        try:
            cmd = self.buildKeygenCommand(keyPath, passphrase)
            subprocess.run(cmd, check=True, input="", capture_output=True)
            printSuccess(f"SSH key generated: {keyName}")
            return True
        except subprocess.CalledProcessError:
            printError(f"Failed to generate SSH key using {self.keyConfig.algorithm}.")
            return False


class PassphraseManager:
    """Handles SSH key passphrase prompting and validation."""

    def __init__(self, requirePassphrase: bool = False, noPassphrase: bool = False):
        """
        Initialise passphrase manager.

        Args:
            requirePassphrase: If True, passphrase is required
            noPassphrase: If True, skip passphrase entirely
        """
        self.requirePassphrase = requirePassphrase
        self.noPassphrase = noPassphrase

    def prompt(self) -> str:
        """
        Prompt user for passphrase.

        Returns:
            Passphrase string (empty if no passphrase)
        """
        if self.noPassphrase:
            printInfo("Using no passphrase.")
            return ""

        if self.requirePassphrase:
            printInfo("A passphrase is required for this SSH key.")
        else:
            printInfo("You can optionally add a passphrase to protect your SSH key.")
            printInfo("Press Enter to skip passphrase (less secure but more convenient).")

        maxAttempts = 3
        attempts = 0

        while attempts < maxAttempts:
            passphrase1 = getpass.getpass("Enter passphrase (empty for no passphrase): ")

            if not passphrase1:
                attempts += 1
                if self.requirePassphrase:
                    if attempts >= maxAttempts:
                        printWarning(f"Empty passphrase entered {maxAttempts} times. Using no passphrase.")
                        return ""
                    printWarning(f"Passphrase is required. Please enter a passphrase. (Attempt {attempts}/{maxAttempts})")
                    continue
                else:
                    printInfo("Using no passphrase.")
                    return ""

            passphrase2 = getpass.getpass("Enter same passphrase again: ")

            if passphrase1 == passphrase2:
                printSuccess("Passphrase confirmed.")
                return passphrase1
            else:
                printWarning("Passphrases do not match. Please try again.")


def promptForEmail(configPath: str) -> str:
    """
    Prompt user for email with config default.

    Args:
        configPath: Path to gitConfig.json

    Returns:
        Email address
    """
    email = getJsonValue(configPath, ".user.email", "")

    if not email or email == "null":
        emailInput = input("Enter email for SSH key: ").strip()
        return emailInput
    else:
        emailInput = input(f"Enter email for SSH key [{email}]: ").strip()
        return emailInput if emailInput else email


def promptForUsername(configPath: str) -> str:
    """
    Prompt user for GitHub username with config default.

    Args:
        configPath: Path to gitConfig.json

    Returns:
        GitHub username
    """
    username = getJsonValue(configPath, ".user.usernameGitHub", "")

    if not username or username == "null":
        usernameInput = input("Enter GitHub username: ").strip()
        return usernameInput
    else:
        usernameInput = input(f"Enter GitHub username [{username}]: ").strip()
        return usernameInput if usernameInput else username


def promptForKeyFilename(defaultFilename: str) -> str:
    """
    Prompt user for key filename.

    Args:
        defaultFilename: Default filename from config

    Returns:
        Chosen filename
    """
    keyNameInput = input(f"Key filename [{defaultFilename}]: ").strip()
    return keyNameInput if keyNameInput else defaultFilename


__all__ = [
    'SshKeyConfig',
    'SshKeyGenerator',
    'PassphraseManager',
    'promptForEmail',
    'promptForUsername',
    'promptForKeyFilename',
]
