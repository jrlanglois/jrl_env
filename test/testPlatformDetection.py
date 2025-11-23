#!/usr/bin/env python3
"""
Unit tests for platform detection and OS helper functions.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent
sys.path.insert(0, str(projectRoot))

from common.systems.platform import (
    Platform,
    findOperatingSystem,
    getOperatingSystem,
    isOperatingSystem,
    isWindows,
    isMacOS,
    isLinux,
    isUnix,
)


class TestPlatformEnum(unittest.TestCase):
    """Test Platform enum structure and values."""

    def testPlatformEnumValues(self):
        """Test that Platform enum has all expected values."""
        expectedPlatforms = {"macos", "ubuntu", "archlinux", "opensuse", "redhat", "raspberrypi", "win11"}
        actualPlatforms = {p.value for p in Platform}
        self.assertEqual(actualPlatforms, expectedPlatforms)

    def testPlatformEnumStringConversion(self):
        """Test that Platform enum converts to string correctly."""
        self.assertEqual(str(Platform.macos), "macos")
        self.assertEqual(str(Platform.win11), "win11")
        self.assertEqual(str(Platform.ubuntu), "ubuntu")


class TestHelperFunctions(unittest.TestCase):
    """Test OS detection helper functions."""

    def testHelperFunctionsReturnBool(self):
        """Test that all helpers return boolean."""
        self.assertIsInstance(isWindows(), bool)
        self.assertIsInstance(isMacOS(), bool)
        self.assertIsInstance(isLinux(), bool)
        self.assertIsInstance(isUnix(), bool)

    def testOnlyOnePrimaryPlatform(self):
        """Test that only one primary platform is detected."""
        platforms = [isWindows(), isMacOS(), isLinux()]
        activeCount = sum(platforms)
        self.assertEqual(activeCount, 1, "Should detect exactly one primary platform")

    def testUnixConsistency(self):
        """Test that isUnix matches isMacOS or isLinux."""
        self.assertEqual(isUnix(), isMacOS() or isLinux())

    def testWindowsAndUnixMutuallyExclusive(self):
        """Test that Windows and Unix are mutually exclusive."""
        self.assertNotEqual(isWindows(), isUnix())


class TestIsOperatingSystem(unittest.TestCase):
    """Test isOperatingSystem with Platform enum (type-safe)."""

    def testAcceptsPlatformEnum(self):
        """Test that isOperatingSystem accepts Platform enum."""
        for platform in Platform:
            result = isOperatingSystem(platform)
            self.assertIsInstance(result, bool)

    def testRejectsStringParameters(self):
        """Test that string parameters raise TypeError."""
        with self.assertRaises(TypeError):
            isOperatingSystem("windows")
        with self.assertRaises(TypeError):
            isOperatingSystem("win11")
        with self.assertRaises(TypeError):
            isOperatingSystem("macos")
        with self.assertRaises(TypeError):
            isOperatingSystem("linux")

    def testRejectsNone(self):
        """Test that None raises TypeError."""
        with self.assertRaises(TypeError):
            isOperatingSystem(None)

    def testRejectsInteger(self):
        """Test that integers raise TypeError."""
        with self.assertRaises(TypeError):
            isOperatingSystem(0)
        with self.assertRaises(TypeError):
            isOperatingSystem(1)

    def testRejectsBoolean(self):
        """Test that booleans raise TypeError."""
        with self.assertRaises(TypeError):
            isOperatingSystem(True)
        with self.assertRaises(TypeError):
            isOperatingSystem(False)

    def testRejectsList(self):
        """Test that lists raise TypeError."""
        with self.assertRaises(TypeError):
            isOperatingSystem(["macos"])
        with self.assertRaises(TypeError):
            isOperatingSystem([Platform.macos])

    def testRejectsDict(self):
        """Test that dictionaries raise TypeError."""
        with self.assertRaises(TypeError):
            isOperatingSystem({"platform": "macos"})


class TestOSDetectionFunctions(unittest.TestCase):
    """Test low-level OS detection functions."""

    def testFindOperatingSystemReturnsString(self):
        """Test that findOperatingSystem returns a string."""
        result = findOperatingSystem()
        self.assertIsInstance(result, str)
        self.assertIn(result, {"linux", "macos", "windows", "unknown"})

    def testGetOperatingSystemReturnsString(self):
        """Test that getOperatingSystem returns a string."""
        result = getOperatingSystem()
        self.assertIsInstance(result, str)
        self.assertIn(result, {"linux", "macos", "windows", "unknown"})

    def testGetOperatingSystemCaches(self):
        """Test that getOperatingSystem returns same value on repeated calls."""
        result1 = getOperatingSystem()
        result2 = getOperatingSystem()
        self.assertEqual(result1, result2)


def main():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
