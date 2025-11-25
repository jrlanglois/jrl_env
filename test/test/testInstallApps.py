#!/usr/bin/env python3
"""
Unit tests for app installation logic.
Tests package installation, result tracking, and command execution.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
scriptDir = Path(__file__).parent.absolute()
sys.path.insert(0, str(scriptDir.parent.parent))

from common.core.utilities import getProjectRoot
projectRoot = getProjectRoot()

from common.install.installApps import InstallResult


class TestInstallResult(unittest.TestCase):
    """Tests for InstallResult dataclass."""

    def testDefaultValues(self):
        """Test InstallResult initialises with zeros."""
        result = InstallResult()

        self.assertEqual(result.installedCount, 0)
        self.assertEqual(result.updatedCount, 0)
        self.assertEqual(result.failedCount, 0)
        self.assertEqual(result.installedPackages, [])
        self.assertEqual(result.updatedPackages, [])

    def testWithValues(self):
        """Test InstallResult with values."""
        result = InstallResult(
            installedCount=5,
            updatedCount=3,
            failedCount=1,
            installedPackages=["pkg1", "pkg2"],
            updatedPackages=["pkg3"]
        )

        self.assertEqual(result.installedCount, 5)
        self.assertEqual(result.updatedCount, 3)
        self.assertEqual(result.failedCount, 1)
        self.assertEqual(len(result.installedPackages), 2)
        self.assertEqual(len(result.updatedPackages), 1)


if __name__ == "__main__":
    unittest.main()
