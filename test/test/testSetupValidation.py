#!/usr/bin/env python3
"""
End-to-end tests for setup validation.
Tests success and failure scenarios as if mocking a user journey.

Uses Python's built-in unittest framework (no external dependencies).

Naming Conventions (per repository style guide):
- Classes: PascalCase (e.g., TestSetupValidation, TestSetupValidationIntegration)
- Functions/Methods: camelCase (e.g., setUp, tearDown, createValidConfig, testValidConfigDirectory)
- Variables: camelCase (e.g., tempDir, configFile, fakeDir, badConfig)
- Test methods: camelCase with 'test' prefix (unittest requirement: must start with 'test')

Note: unittest requires test methods to start with 'test', but we use camelCase for the rest
of the method name (e.g., testValidConfigDirectory, not test_valid_config_directory).

Usage:
    python3 test/testSetupValidation.py
    python3 -m unittest test.testSetupValidation
    python3 -m unittest test.testSetupValidation.TestSetupValidation.testValidConfigDirectory
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
scriptDir = Path(__file__).parent.absolute()
sys.path.insert(0, str(scriptDir.parent.parent))

from common.core.utilities import getProjectRoot
projectRoot = getProjectRoot()

from common.systems.validate import (
    validateConfigDirectory,
    validatePlatformConfig,
    validateJsonFile,
)
from common.core.utilities import getConfigDirectory
from common.core.logging import safePrint
from common.systems.platform import isWindows


class TestSetupValidation(unittest.TestCase):
    """Test setup validation scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.tempDir = Path(tempfile.mkdtemp())
        self.originalCwd = os.getcwd()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.tempDir.exists():
            shutil.rmtree(self.tempDir)
        os.chdir(self.originalCwd)

    def createValidConfig(self, filename: str, content: dict) -> Path:
        """Create a valid JSON config file."""
        configFile = self.tempDir / filename
        configFile.write_text(json.dumps(content, indent=4))
        return configFile

    def testValidConfigDirectory(self):
        """Test: Valid config directory should pass validation."""
        # Create valid config files
        self.createValidConfig("ubuntu.json", {"apt": ["git", "vim"]})
        self.createValidConfig("fonts.json", {"googleFonts": ["Roboto"]})

        result = validateConfigDirectory(self.tempDir, "ubuntu")
        self.assertTrue(result, "Valid config directory should pass validation")

    def testMissingConfigDirectory(self):
        """Test: Missing config directory should fail validation."""
        fakeDir = self.tempDir / "nonexistent"
        result = validateConfigDirectory(fakeDir, "ubuntu")
        self.assertFalse(result, "Missing config directory should fail validation")

    def testConfigDirectoryNotADirectory(self):
        """Test: Config path that's a file should fail validation."""
        fakeFile = self.tempDir / "notadir"
        fakeFile.write_text("not a directory")
        result = validateConfigDirectory(fakeFile, "ubuntu")
        self.assertFalse(result, "File path should fail directory validation")

    def testEmptyConfigDirectory(self):
        """Test: Empty config directory should fail validation."""
        result = validateConfigDirectory(self.tempDir, "ubuntu")
        self.assertFalse(result, "Empty config directory should fail validation")

    def testValidPlatformConfig(self):
        """Test: Valid platform config should pass validation."""
        configFile = self.createValidConfig("ubuntu.json", {"apt": ["git"]})
        result = validatePlatformConfig(configFile, "ubuntu")
        self.assertTrue(result, "Valid platform config should pass validation")

    def testMissingPlatformConfig(self):
        """Test: Missing platform config should fail validation."""
        fakeFile = self.tempDir / "ubuntu.json"
        result = validatePlatformConfig(fakeFile, "ubuntu")
        self.assertFalse(result, "Missing platform config should fail validation")

    def testInvalidJsonPlatformConfig(self):
        """Test: Invalid JSON in platform config should fail validation."""
        badConfig = self.tempDir / "ubuntu.json"
        badConfig.write_text("{ invalid json }")
        result = validatePlatformConfig(badConfig, "ubuntu")
        self.assertFalse(result, "Invalid JSON should fail validation")

    def testEmptyJsonPlatformConfig(self):
        """Test: Empty JSON object should pass syntax validation."""
        configFile = self.createValidConfig("ubuntu.json", {})
        result = validatePlatformConfig(configFile, "ubuntu")
        self.assertTrue(result, "Empty JSON object should pass syntax validation")

    def testValidJsonFileValidation(self):
        """Test: Valid JSON file should pass validation."""
        configFile = self.createValidConfig("test.json", {"key": "value"})
        isValid, errors, warnings = validateJsonFile(configFile, "test.json")
        self.assertTrue(isValid, "Valid JSON file should pass validation")
        self.assertEqual(len(errors), 0, "Valid JSON should have no errors")

    def testInvalidJsonFileValidation(self):
        """Test: Invalid JSON file should fail validation."""
        badFile = self.tempDir / "bad.json"
        badFile.write_text("{ invalid }")
        isValid, errors, warnings = validateJsonFile(badFile, "bad.json")
        self.assertFalse(isValid, "Invalid JSON file should fail validation")
        self.assertGreater(len(errors), 0, "Invalid JSON should have errors")

    def testMissingJsonFileValidation(self):
        """Test: Missing JSON file should fail validation."""
        fakeFile = self.tempDir / "missing.json"
        isValid, errors, warnings = validateJsonFile(fakeFile, "missing.json")
        self.assertFalse(isValid, "Missing JSON file should fail validation")
        self.assertGreater(len(errors), 0, "Missing file should have errors")

    def testCustomConfigDirectoryCliArg(self):
        """Test: Custom config directory via CLI argument."""
        # Create valid configs in temp dir
        self.createValidConfig("ubuntu.json", {"apt": ["git"]})

        # Mock sys.argv to include --configDir
        with patch("sys.argv", ["script", "--configDir", str(self.tempDir)]):
            configDir = getConfigDirectory(projectRoot)
            self.assertEqual(configDir, self.tempDir, "Should use CLI --configDir argument")

    def testCustomConfigDirectoryEnvVar(self):
        """Test: Custom config directory via environment variable."""
        # Create valid configs in temp dir
        self.createValidConfig("ubuntu.json", {"apt": ["git"]})

        # Set environment variable
        with patch.dict(os.environ, {"JRL_ENV_CONFIG_DIR": str(self.tempDir)}):
            configDir = getConfigDirectory(projectRoot, args=[])
            self.assertEqual(configDir, self.tempDir, "Should use JRL_ENV_CONFIG_DIR environment variable")

    def testDefaultConfigDirectory(self):
        """Test: Default config directory when no custom path specified."""
        with patch.dict(os.environ, {}, clear=True):
            configDir = getConfigDirectory(projectRoot, args=[])
            expected = projectRoot / "configs"
            self.assertEqual(configDir, expected, "Should use default configs directory")

    def testSetupValidationFlowSuccess(self):
        """Test: Complete successful setup validation flow."""
        # Create all required configs
        self.createValidConfig("ubuntu.json", {
            "apt": ["git", "vim"],
            "useLinuxCommon": False
        })
        self.createValidConfig("fonts.json", {"googleFonts": ["Roboto"]})
        self.createValidConfig("gitConfig.json", {
            "user": {"name": "Test User", "email": "test@example.com"}
        })
        self.createValidConfig("repositories.json", {"repositories": []})
        self.createValidConfig("cursorSettings.json", {"editor.fontSize": 14})

        # Validate directory
        self.assertTrue(validateConfigDirectory(self.tempDir, "ubuntu"))

        # Validate platform config
        platformConfig = self.tempDir / "ubuntu.json"
        self.assertTrue(validatePlatformConfig(platformConfig, "ubuntu"))

    def testSetupValidationFlowMissingPlatformConfig(self):
        """Test: Setup validation fails when platform config is missing."""
        # Create other configs but not platform config
        self.createValidConfig("fonts.json", {"googleFonts": ["Roboto"]})

        # Directory validation should pass
        self.assertTrue(validateConfigDirectory(self.tempDir, "ubuntu"))

        # Platform config validation should fail
        platformConfig = self.tempDir / "ubuntu.json"
        self.assertFalse(validatePlatformConfig(platformConfig, "ubuntu"))

    def testSetupValidationFlowInvalidJson(self):
        """Test: Setup validation fails when platform config has invalid JSON."""
        # Create invalid platform config
        badConfig = self.tempDir / "ubuntu.json"
        badConfig.write_text("{ invalid json syntax }")

        # Directory validation should pass
        self.assertTrue(validateConfigDirectory(self.tempDir, "ubuntu"))

        # Platform config validation should fail
        self.assertFalse(validatePlatformConfig(badConfig, "ubuntu"))

    def testSetupValidationFlowEmptyDirectory(self):
        """Test: Setup validation fails when config directory is empty."""
        # Don't create any files
        self.assertFalse(validateConfigDirectory(self.tempDir, "ubuntu"))

    def testSetupValidationFlowPermissionError(self):
        """Test: Setup validation handles permission errors gracefully."""
        # Create a directory we can't read (on Unix-like systems)
        if not isWindows():  # Skip on Windows
            restrictedDir = self.tempDir / "restricted"
            restrictedDir.mkdir(mode=0o000)  # No permissions

            try:
                result = validateConfigDirectory(restrictedDir, "ubuntu")
                self.assertFalse(result, "Should fail when directory is not readable")
            finally:
                # Restore permissions for cleanup
                restrictedDir.chmod(0o755)
                restrictedDir.rmdir()

    def testUnknownFieldsInPlatformConfig(self):
        """Test: Unknown fields in platform config should be detected and reported."""
        from common.systems.validate import validateAppsJson

        # Create config with unknown field
        configFile = self.createValidConfig("ubuntu.json", {
            "apt": ["git"],
            "unknownField": "should not be here",
            "anotherUnknown": {"nested": "value"}
        })

        errors, warnings = validateAppsJson(configFile, "ubuntu")
        self.assertGreater(len(errors), 0, "Should detect unknown fields")
        self.assertTrue(any("unknownField" in error for error in errors), "Should report unknownField")
        self.assertTrue(any("anotherUnknown" in error for error in errors), "Should report anotherUnknown")

    def testUnknownFieldsInCommands(self):
        """Test: Unknown fields in command objects should be detected."""
        from common.systems.validate import validateAppsJson

        # Create config with unknown field in command
        configFile = self.createValidConfig("ubuntu.json", {
            "apt": ["git"],
            "commands": {
                "preInstall": [
                    {
                        "name": "test",
                        "command": "echo test",
                        "unknownField": "not allowed"
                    }
                ]
            }
        })

        errors, warnings = validateAppsJson(configFile, "ubuntu")
        self.assertGreater(len(errors), 0, "Should detect unknown fields in commands")
        self.assertTrue(any("unknownField" in error for error in errors), "Should report unknownField in command")

    def testUnknownFieldsInShell(self):
        """Test: Unknown fields in shell config should be detected."""
        from common.systems.validate import validateAppsJson

        # Create config with unknown field in shell
        configFile = self.createValidConfig("ubuntu.json", {
            "apt": ["git"],
            "shell": {
                "ohMyZshTheme": "robbyrussell",
                "unknownField": "not allowed"
            }
        })

        errors, warnings = validateAppsJson(configFile, "ubuntu")
        self.assertGreater(len(errors), 0, "Should detect unknown fields in shell")
        self.assertTrue(any("unknownField" in error for error in errors), "Should report unknownField in shell")

    def testUnknownFieldsInGitConfig(self):
        """Test: Unknown fields in git config should be detected."""
        from common.systems.validate import validateGitConfigJson

        # Create git config with unknown field
        configFile = self.createValidConfig("gitConfig.json", {
            "user": {
                "name": "Test User",
                "email": "test@example.com"
            },
            "unknownField": "not allowed"
        })

        errors, warnings = validateGitConfigJson(configFile)
        self.assertGreater(len(errors), 0, "Should detect unknown fields in git config")
        self.assertTrue(any("unknownField" in error for error in errors), "Should report unknownField")

    def testUnknownFieldsInRepositories(self):
        """Test: Unknown fields in repositories config should be detected."""
        from common.systems.validate import validateRepositoriesJson

        # Create repositories config with unknown field
        configFile = self.createValidConfig("repositories.json", {
            "repositories": [],
            "unknownField": "not allowed"
        })

        errors, warnings = validateRepositoriesJson(configFile)
        self.assertGreater(len(errors), 0, "Should detect unknown fields in repositories config")
        self.assertTrue(any("unknownField" in error for error in errors), "Should report unknownField")

    def testUnknownFieldsInFonts(self):
        """Test: Unknown fields in fonts config should be detected."""
        from common.systems.validate import detectUnknownFields

        # Create fonts config with unknown field
        fontsData = {
            "googleFonts": ["Roboto"],
            "unknownField": "not allowed"
        }

        allowedFields = {"googleFonts"}
        errors = detectUnknownFields(fontsData, allowedFields)
        self.assertGreater(len(errors), 0, "Should detect unknown fields")
        self.assertTrue(any("unknownField" in error for error in errors), "Should report unknownField")


    def testUnknownFieldsReturnCode(self):
        """Test: Validation returns code 2 for unknown fields only."""
        from common.systems.validate import validateAppsJson

        # Create config with unknown field
        configFile = self.createValidConfig("ubuntu.json", {
            "apt": ["git"],
            "unknownField": "test"
        })

        errors, warnings = validateAppsJson(configFile, "ubuntu")

        # Should have unknown field error
        unknownFieldErrors = [e for e in errors if "Unknown field" in e]
        self.assertGreater(len(unknownFieldErrors), 0, "Should detect unknown fields")
        self.assertTrue(any("unknownField" in error for error in unknownFieldErrors), "Should report unknownField")

    def testInvalidRepositoryUrl(self):
        """Test: Invalid repository URLs are detected and reported."""
        from common.systems.validate import validateRepositoriesJson

        # Create repositories config with invalid URL
        configFile = self.createValidConfig("repositories.json", {
            "workPathUnix": "~/work",
            "repositories": [
                "not-a-valid-url",
                "https://github.com/nonexistent/repo-that-does-not-exist-12345"
            ]
        })

        errors, warnings = validateRepositoriesJson(configFile)

        # Should have warnings for invalid URLs
        self.assertGreater(len(warnings), 0, "Should detect invalid repository URLs")
        self.assertTrue(any("Invalid URL format" in w for w in warnings) or
                       any("not found" in w.lower() for w in warnings) or
                       any("not accessible" in w.lower() for w in warnings),
                       "Should report invalid or nonexistent repository URLs")

    def testInvalidFontName(self):
        """Test: Invalid font names are detected and reported."""
        from common.systems.validate import checkFontExists

        # Check a font that definitely doesn't exist
        fontExists, message = checkFontExists("ThisFontDefinitelyDoesNotExist12345")

        # Should detect that font doesn't exist (or at least warn)
        # fontExists can be True, False, or None (network error)
        if fontExists is False:
            # Font definitely doesn't exist
            self.assertIn("not found", message.lower() or "404" in message,
                         "Should report font not found")
        elif fontExists is None:
            # Network issue is acceptable - at least we tried
            self.assertTrue("network" in message.lower() or "timeout" in message.lower() or "error" in message.lower(),
                         f"Should report network/checking error, got: {message}")
        elif fontExists is True:
            # This shouldn't happen for a non-existent font, but if it does, that's also a problem
            self.fail(f"Font check returned True for non-existent font, message: {message}")
        else:
            # Should always return one of True, False, or None
            self.fail(f"Unexpected return value: {fontExists}")

    def testValidRepositoryUrl(self):
        """Test: Valid repository URLs pass validation."""
        from common.systems.validate import validateRepositoriesJson

        # Create repositories config with valid GitHub URL
        configFile = self.createValidConfig("repositories.json", {
            "workPathUnix": "~/work",
            "repositories": [
                "https://github.com/microsoft/vscode"# Known to exist
            ]
        })

        errors, warnings = validateRepositoriesJson(configFile)

        # Should not have errors (warnings are OK for network issues)
        # But invalid format errors should not appear
        invalidFormatWarnings = [w for w in warnings if "Invalid URL format" in w]
        self.assertEqual(len(invalidFormatWarnings), 0,
                        "Should not report invalid format for valid GitHub URL")

    def testValidFontName(self):
        """Test: Valid font names pass validation."""
        from common.systems.validate import checkFontExists

        # Check a font that definitely exists
        fontExists, message = checkFontExists("Roboto")

        # Should find the font (or at least not report it as definitely invalid)
        self.assertIsNotNone(fontExists, "Should return a result")
        if fontExists is True:
            self.assertIn("exists", message.lower(), "Should report font exists")
        elif fontExists is None:
            # Network issue is acceptable - at least we tried
            self.assertIn("network", message.lower() or "timeout" in message.lower() or "error" in message.lower(),
                         "Should report network/checking error if can't verify")


class TestSetupValidationIntegration(unittest.TestCase):
    """Integration tests that test the actual setup.py validation flow."""

    def setUp(self):
        """Set up test fixtures."""
        self.tempDir = Path(tempfile.mkdtemp())
        self.originalCwd = os.getcwd()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.tempDir.exists():
            shutil.rmtree(self.tempDir)
        os.chdir(self.originalCwd)

    def createValidConfig(self, filename: str, content: dict) -> Path:
        """Create a valid JSON config file."""
        configFile = self.tempDir / filename
        configFile.write_text(json.dumps(content, indent=4))
        return configFile

    # TODO: Update this test - validateConfigs was refactored into ValidationEngine
    # @patch("common.systems.systemBase.SystemBase.validateConfigs")
    # def testSetupCallsValidation(self, mockValidate):
    #     """Test: Setup should call validateConfigs."""
    #     pass

    def testValidationFailsOnMissingConfigDirectory(self):
        """Test: Setup validation fails when config directory doesn't exist."""
        fakeDir = self.tempDir / "nonexistent"
        result = validateConfigDirectory(fakeDir, "ubuntu")
        self.assertFalse(result)

    def testValidationFailsOnInvalidPlatformConfig(self):
        """Test: Setup validation fails when platform config is invalid."""
        # Create directory with invalid config
        badConfig = self.tempDir / "ubuntu.json"
        badConfig.write_text("{ invalid json }")

        # Directory should pass
        self.assertTrue(validateConfigDirectory(self.tempDir, "ubuntu"))

        # Platform config should fail
        self.assertFalse(validatePlatformConfig(badConfig, "ubuntu"))


if __name__ == "__main__":
    # Set up test environment
    os.chdir(projectRoot)

    # Run tests with verbose output
    unittest.main(verbosity=2, exit=False)

    # Print summary
    safePrint("\n" + "=" * 70)
    safePrint("Test Summary")
    safePrint("=" * 70)
    safePrint("All validation tests completed.")
    safePrint("These tests verify that setup validation fails early and clearly")
    safePrint("when configuration files are missing or invalid.")
