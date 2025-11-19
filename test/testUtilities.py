#!/usr/bin/env python3
"""
Unit tests for core utility functions.
Tests package manager checks, JSON parsing, path expansion, and OS detection.
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
projectRoot = scriptDir.parent
sys.path.insert(0, str(projectRoot))

from common.core.utilities import (
    commandExists,
    requireCommand,
    getJsonValue,
    getJsonArray,
    getJsonObject,
    findOperatingSystem,
    getOperatingSystem,
    isOperatingSystem,
)
from common.configure.cloneRepositories import expandPath


class TestCommandExists(unittest.TestCase):
    """Tests for commandExists function."""

    def test_commandExists_existing_command(self):
        """Test that commandExists returns True for existing commands."""
        # 'python' should exist on most systems
        self.assertTrue(commandExists("python") or commandExists("python3"))

    def test_commandExists_nonexistent_command(self):
        """Test that commandExists returns False for non-existent commands."""
        self.assertFalse(commandExists("nonexistent_command_xyz_123"))

    def test_commandExists_empty_string(self):
        """Test that commandExists handles empty string."""
        self.assertFalse(commandExists(""))


class TestRequireCommand(unittest.TestCase):
    """Tests for requireCommand function."""

    @patch("common.core.utilities.commandExists")
    @patch("common.core.utilities.printError")
    @patch("common.core.utilities.printInfo")
    def test_requireCommand_exists(self, mockPrintInfo, mockPrintError, mockCommandExists):
        """Test requireCommand when command exists."""
        mockCommandExists.return_value = True
        result = requireCommand("testcmd")
        self.assertTrue(result)
        mockCommandExists.assert_called_once_with("testcmd")
        mockPrintError.assert_not_called()

    @patch("common.core.utilities.commandExists")
    @patch("common.core.utilities.printError")
    @patch("common.core.utilities.printInfo")
    def test_requireCommand_missing(self, mockPrintInfo, mockPrintError, mockCommandExists):
        """Test requireCommand when command is missing."""
        mockCommandExists.return_value = False
        result = requireCommand("testcmd")
        self.assertFalse(result)
        mockPrintError.assert_called_once()
        mockPrintInfo.assert_not_called()

    @patch("common.core.utilities.commandExists")
    @patch("common.core.utilities.printError")
    @patch("common.core.utilities.printInfo")
    def test_requireCommand_missing_with_hint(self, mockPrintInfo, mockPrintError, mockCommandExists):
        """Test requireCommand when command is missing with install hint."""
        mockCommandExists.return_value = False
        result = requireCommand("testcmd", "Install with: apt install testcmd")
        self.assertFalse(result)
        mockPrintError.assert_called_once()
        mockPrintInfo.assert_called_once()


class TestJsonParsing(unittest.TestCase):
    """Tests for JSON parsing functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary JSON file for testing
        self.tempDir = tempfile.mkdtemp()
        self.testJsonPath = Path(self.tempDir) / "test.json"
        self.testData = {
            "stringValue": "test",
            "numberValue": 42,
            "booleanValue": True,
            "nested": {
                "key": "value",
                "number": 123,
            },
            "array": ["item1", "item2", "item3"],
            "nestedArray": {
                "items": ["a", "b", "c"],
            },
            "mixedArray": [1, "two", True, None],
        }
        with open(self.testJsonPath, "w", encoding="utf-8") as f:
            json.dump(self.testData, f)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.testJsonPath.exists():
            self.testJsonPath.unlink()
        os.rmdir(self.tempDir)

    def test_getJsonValue_simple_key(self):
        """Test getJsonValue with simple key."""
        result = getJsonValue(str(self.testJsonPath), ".stringValue")
        self.assertEqual(result, "test")

    def test_getJsonValue_nested_key(self):
        """Test getJsonValue with nested key."""
        result = getJsonValue(str(self.testJsonPath), ".nested.key")
        self.assertEqual(result, "value")

    def test_getJsonValue_number(self):
        """Test getJsonValue with number."""
        result = getJsonValue(str(self.testJsonPath), ".numberValue")
        self.assertEqual(result, 42)

    def test_getJsonValue_boolean(self):
        """Test getJsonValue with boolean."""
        result = getJsonValue(str(self.testJsonPath), ".booleanValue")
        self.assertTrue(result)

    def test_getJsonValue_array_index(self):
        """Test getJsonValue with array index."""
        result = getJsonValue(str(self.testJsonPath), ".array[0]")
        self.assertEqual(result, "item1")

    def test_getJsonValue_nested_array(self):
        """Test getJsonValue with nested array access."""
        result = getJsonValue(str(self.testJsonPath), ".nestedArray.items[1]")
        self.assertEqual(result, "b")

    def test_getJsonValue_missing_key(self):
        """Test getJsonValue with missing key returns default."""
        result = getJsonValue(str(self.testJsonPath), ".nonexistent", "default")
        self.assertEqual(result, "default")

    def test_getJsonValue_missing_file(self):
        """Test getJsonValue with non-existent file returns default."""
        result = getJsonValue("/nonexistent/file.json", ".key", "default")
        self.assertEqual(result, "default")

    def test_getJsonValue_no_default(self):
        """Test getJsonValue with missing key and no default."""
        result = getJsonValue(str(self.testJsonPath), ".nonexistent")
        self.assertIsNone(result)

    def test_getJsonArray_simple_array(self):
        """Test getJsonArray with simple array."""
        result = getJsonArray(str(self.testJsonPath), ".array")
        self.assertEqual(result, ["item1", "item2", "item3"])

    def test_getJsonArray_array_notation(self):
        """Test getJsonArray with array notation."""
        result = getJsonArray(str(self.testJsonPath), ".array[]")
        self.assertEqual(result, ["item1", "item2", "item3"])

    def test_getJsonArray_nested_array(self):
        """Test getJsonArray with nested array."""
        result = getJsonArray(str(self.testJsonPath), ".nestedArray.items")
        self.assertEqual(result, ["a", "b", "c"])

    def test_getJsonArray_mixed_types(self):
        """Test getJsonArray with mixed types converts to strings."""
        result = getJsonArray(str(self.testJsonPath), ".mixedArray")
        # None values should be filtered out
        self.assertEqual(len(result), 3)
        self.assertIn("1", result)
        self.assertIn("two", result)
        self.assertIn("True", result)

    def test_getJsonArray_missing_key(self):
        """Test getJsonArray with missing key returns empty list."""
        result = getJsonArray(str(self.testJsonPath), ".nonexistent")
        self.assertEqual(result, [])

    def test_getJsonArray_missing_file(self):
        """Test getJsonArray with non-existent file returns empty list."""
        result = getJsonArray("/nonexistent/file.json", ".array")
        self.assertEqual(result, [])

    def test_getJsonObject_simple_object(self):
        """Test getJsonObject with simple object."""
        result = getJsonObject(str(self.testJsonPath), ".nested")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["key"], "value")
        self.assertEqual(result["number"], 123)

    def test_getJsonObject_root(self):
        """Test getJsonObject with root path."""
        result = getJsonObject(str(self.testJsonPath), ".")
        self.assertIsInstance(result, dict)
        self.assertIn("stringValue", result)

    def test_getJsonObject_missing_key(self):
        """Test getJsonObject with missing key returns empty dict."""
        result = getJsonObject(str(self.testJsonPath), ".nonexistent")
        self.assertEqual(result, {})

    def test_getJsonObject_missing_file(self):
        """Test getJsonObject with non-existent file returns empty dict."""
        result = getJsonObject("/nonexistent/file.json", ".object")
        self.assertEqual(result, {})

    def test_getJsonObject_not_an_object(self):
        """Test getJsonObject with non-object value returns empty dict."""
        result = getJsonObject(str(self.testJsonPath), ".stringValue")
        self.assertEqual(result, {})


class TestExpandPath(unittest.TestCase):
    """Tests for expandPath function."""

    def test_expandPath_home_variable(self):
        """Test expandPath with $HOME variable."""
        if os.name != "nt":  # Unix-like systems
            result = expandPath("$HOME/test")
            self.assertIn(os.path.expanduser("~"), result)
        else:  # Windows
            result = expandPath("%USERPROFILE%\\test")
            self.assertIn(os.environ.get("USERPROFILE", ""), result)

    def test_expandPath_no_variables(self):
        """Test expandPath with no variables."""
        result = expandPath("/path/to/file")
        self.assertEqual(result, "/path/to/file")

    def test_expandPath_multiple_variables(self):
        """Test expandPath with multiple variables."""
        if os.name != "nt":
            result = expandPath("$HOME/$USER/test")
            self.assertNotIn("$", result)
        else:
            result = expandPath("%USERPROFILE%\\%USERNAME%\\test")
            self.assertNotIn("%", result)


class TestOSDetection(unittest.TestCase):
    """Tests for OS detection functions."""

    @patch("common.core.utilities.platform.system")
    def test_findOperatingSystem_linux(self, mockSystem):
        """Test findOperatingSystem detects Linux."""
        mockSystem.return_value = "Linux"
        result = findOperatingSystem()
        self.assertEqual(result, "linux")

    @patch("common.core.utilities.platform.system")
    def test_findOperatingSystem_macos(self, mockSystem):
        """Test findOperatingSystem detects macOS."""
        mockSystem.return_value = "Darwin"
        result = findOperatingSystem()
        self.assertEqual(result, "macos")

    @patch("common.core.utilities.platform.system")
    def test_findOperatingSystem_windows(self, mockSystem):
        """Test findOperatingSystem detects Windows."""
        mockSystem.return_value = "Windows"
        result = findOperatingSystem()
        self.assertEqual(result, "windows")

    @patch("common.core.utilities.platform.system")
    def test_findOperatingSystem_unknown(self, mockSystem):
        """Test findOperatingSystem handles unknown OS."""
        mockSystem.return_value = "UnknownOS"
        result = findOperatingSystem()
        self.assertEqual(result, "unknown")

    def test_getOperatingSystem_caching(self):
        """Test that getOperatingSystem caches the result."""
        # Reset the cache by importing the module fresh
        import importlib
        import common.core.utilities as utils_module
        importlib.reload(utils_module)

        # First call should detect
        result1 = utils_module.getOperatingSystem()
        # Second call should return cached value
        result2 = utils_module.getOperatingSystem()
        self.assertEqual(result1, result2)

    def test_isOperatingSystem(self):
        """Test isOperatingSystem function."""
        current = getOperatingSystem()
        self.assertTrue(isOperatingSystem(current))
        # Test with wrong OS (assuming we're not on all three at once)
        if current != "linux":
            self.assertFalse(isOperatingSystem("linux"))
        if current != "macos":
            self.assertFalse(isOperatingSystem("macos"))
        if current != "windows":
            self.assertFalse(isOperatingSystem("windows"))


if __name__ == "__main__":
    unittest.main()
