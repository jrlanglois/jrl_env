#!/usr/bin/env python3
"""
Unit tests for SSH key manager.
Tests SSH key configuration, generation, and passphrase management.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add project root to path
scriptDir = Path(__file__).parent.absolute()
sys.path.insert(0, str(scriptDir.parent.parent))

from common.core.utilities import getProjectRoot
projectRoot = getProjectRoot()

from common.configure.sshKeyManager import (
    SshKeyConfig,
    SshKeyGenerator,
    PassphraseManager,
    promptForEmail,
    promptForUsername,
    promptForKeyFilename,
)


class TestSshKeyConfig(unittest.TestCase):
    """Tests for SshKeyConfig class."""

    def testValidateEd25519(self):
        """Test validating ed25519 configuration."""
        config = SshKeyConfig("configs/gitConfig.json")  # Uses real config
        # Override with test values
        config.algorithm = "ed25519"
        config.keySize = None
        config.keyFilename = "test_key"

        result = config.validate()

        self.assertTrue(result)

    def testValidateRsa4096(self):
        """Test validating RSA 4096 configuration."""
        config = SshKeyConfig("configs/gitConfig.json")
        config.algorithm = "rsa"
        config.keySize = 4096
        config.keyFilename = "test_rsa"

        result = config.validate()

        self.assertTrue(result)

    def testValidateEcdsa521(self):
        """Test validating ECDSA 521 configuration."""
        config = SshKeyConfig("configs/gitConfig.json")
        config.algorithm = "ecdsa"
        config.keySize = 521
        config.keyFilename = "test_ecdsa"

        result = config.validate()

        self.assertTrue(result)

    def testValidateInvalidAlgorithm(self):
        """Test that invalid algorithm fails validation."""
        config = SshKeyConfig("configs/gitConfig.json")
        config.algorithm = "invalid"
        config.keyFilename = "test"

        result = config.validate()

        self.assertFalse(result)

    def testValidateEd25519WithKeySize(self):
        """Test that ed25519 with keySize fails validation."""
        config = SshKeyConfig("configs/gitConfig.json")
        config.algorithm = "ed25519"
        config.keySize = 4096
        config.keyFilename = "test"

        result = config.validate()

        self.assertFalse(result)

    def testValidateRsaTooSmall(self):
        """Test that RSA < 2048 fails validation."""
        config = SshKeyConfig("configs/gitConfig.json")
        config.algorithm = "rsa"
        config.keySize = 1024
        config.keyFilename = "test"

        result = config.validate()

        self.assertFalse(result)

    def testValidateEcdsaInvalidSize(self):
        """Test that ECDSA with invalid size fails validation."""
        config = SshKeyConfig("configs/gitConfig.json")
        config.algorithm = "ecdsa"
        config.keySize = 512
        config.keyFilename = "test"

        result = config.validate()

        self.assertFalse(result)

    def testValidateEmptyFilename(self):
        """Test that empty filename fails validation."""
        config = SshKeyConfig("configs/gitConfig.json")
        config.algorithm = "ed25519"
        config.keyFilename = ""

        result = config.validate()

        self.assertFalse(result)


class TestSshKeyGenerator(unittest.TestCase):
    """Tests for SshKeyGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        mockConfig = MagicMock()
        mockConfig.algorithm = "ed25519"
        mockConfig.keySize = None
        mockConfig.keyFilename = "test_key"

        self.generator = SshKeyGenerator(mockConfig, "test@example.com", dryRun=True)

    def testGetKeyPath(self):
        """Test getting key path."""
        result = self.generator.getKeyPath("test_key")

        self.assertEqual(result, Path.home() / ".ssh" / "test_key")

    def testBuildKeygenCommandEd25519(self):
        """Test building keygen command for ed25519."""
        keyPath = Path("/test/key")
        passphrase = "secret"

        cmd = self.generator.buildKeygenCommand(keyPath, passphrase)

        self.assertIn("ssh-keygen", cmd)
        self.assertIn("-t", cmd)
        self.assertIn("ed25519", cmd)
        self.assertNotIn("-b", cmd)  # ed25519 doesn't use -b

    def testBuildKeygenCommandRsa(self):
        """Test building keygen command for RSA with key size."""
        mockConfig = MagicMock()
        mockConfig.algorithm = "rsa"
        mockConfig.keySize = 4096

        generator = SshKeyGenerator(mockConfig, "test@example.com", dryRun=True)
        cmd = generator.buildKeygenCommand(Path("/test/key"), "secret")

        self.assertIn("-b", cmd)
        self.assertIn("4096", cmd)

    def testGenerateDryRun(self):
        """Test generate in dry-run mode."""
        result = self.generator.generate("test_key", "secret")

        self.assertTrue(result)


class TestPassphraseManager(unittest.TestCase):
    """Tests for PassphraseManager class."""

    def testInitialization(self):
        """Test PassphraseManager initialises correctly."""
        manager = PassphraseManager(requirePassphrase=True, noPassphrase=False)

        self.assertTrue(manager.requirePassphrase)
        self.assertFalse(manager.noPassphrase)

    def testPromptNoPassphrase(self):
        """Test prompt with noPassphrase=True."""
        manager = PassphraseManager(requirePassphrase=False, noPassphrase=True)

        result = manager.prompt()

        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
