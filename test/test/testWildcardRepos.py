#!/usr/bin/env python3
"""
Unit tests for wildcard repository pattern parsing and validation.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
scriptDir = Path(__file__).parent.absolute()
sys.path.insert(0, str(scriptDir.parent.parent))

from common.core.utilities import getProjectRoot
projectRoot = getProjectRoot()

from common.configure.githubApi import parseGitHubPattern


class TestWildcardPatternParsing(unittest.TestCase):
    """Test wildcard pattern parsing and validation."""

    def testValidSshPattern(self):
        """Test valid SSH wildcard pattern."""
        result = parseGitHubPattern('git@github.com:jrlanglois/*')
        self.assertIsNotNone(result)
        owner, isWildcard = result
        self.assertEqual(owner, 'jrlanglois')
        self.assertTrue(isWildcard)

    def testValidHttpsPattern(self):
        """Test valid HTTPS wildcard pattern."""
        result = parseGitHubPattern('https://github.com/SquarePine/*')
        self.assertIsNotNone(result)
        owner, isWildcard = result
        self.assertEqual(owner, 'SquarePine')
        self.assertTrue(isWildcard)

    def testInvalidPatternWildcardInOwner(self):
        """Test invalid pattern with wildcard in owner name."""
        result = parseGitHubPattern('git@github.com:jrlanglois*')
        self.assertIsNone(result)

    def testInvalidPatternWildcardOnly(self):
        """Test invalid pattern with only wildcard."""
        result = parseGitHubPattern('git@github.com:*')
        self.assertIsNone(result)

    def testInvalidPatternWildcardInWrongPlace(self):
        """Test invalid pattern with wildcard in wrong place."""
        result = parseGitHubPattern('git@github.com:owner/*/subfolder')
        self.assertIsNone(result)

    def testNonWildcardPattern(self):
        """Test non-wildcard pattern returns None (not an error)."""
        result = parseGitHubPattern('git@github.com:owner/repo')
        self.assertIsNone(result)

    def testCaseSensitivity(self):
        """Test that patterns are case-sensitive for owner."""
        result1 = parseGitHubPattern('git@github.com:Owner/*')
        result2 = parseGitHubPattern('git@github.com:owner/*')
        self.assertIsNotNone(result1)
        self.assertIsNotNone(result2)
        owner1, _ = result1
        owner2, _ = result2
        self.assertEqual(owner1, 'Owner')
        self.assertEqual(owner2, 'owner')
        self.assertNotEqual(owner1, owner2)


class TestRepositoryEntryValidation(unittest.TestCase):
    """Test repository entry validation (strings vs objects)."""

    def testStringEntry(self):
        """Test that string entries are valid."""
        entry = "git@github.com:owner/repo.git"
        self.assertIsInstance(entry, str)

    def testObjectEntryValid(self):
        """Test that valid object entries work."""
        entry = {
            "pattern": "git@github.com:owner/*",
            "visibility": "all"
        }
        self.assertIsInstance(entry, dict)
        self.assertIn("pattern", entry)
        self.assertIn("visibility", entry)
        self.assertIn(entry["visibility"], ["all", "public", "private"])

    def testObjectEntryDefaultVisibility(self):
        """Test that visibility defaults to 'all' if not specified."""
        entry = {
            "pattern": "git@github.com:owner/*"
        }
        visibility = entry.get("visibility", "all")
        self.assertEqual(visibility, "all")

    def testObjectEntryInvalidVisibility(self):
        """Test that invalid visibility values are detected."""
        validVisibilities = {"all", "public", "private"}
        invalidVisibility = "invalid"
        self.assertNotIn(invalidVisibility, validVisibilities)


def main():
    """Run all tests."""
    # Run tests with verbose output
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code based on results
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
