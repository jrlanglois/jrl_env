#!/usr/bin/env python3
"""
Unit tests for setup argument parsing.
Tests CLI argument parsing, target validation, and run flag determination.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
scriptDir = Path(__file__).parent.absolute()
sys.path.insert(0, str(scriptDir.parent.parent))

from common.core.utilities import getProjectRoot
projectRoot = getProjectRoot()

from common.install.setupArgs import (
    SetupArgs,
    RunFlags,
    parseTargets,
    parseSetupArgs,
    determineRunFlags,
    VALID_INSTALL_TARGETS,
    VALID_UPDATE_TARGETS,
)


class TestParseTargets(unittest.TestCase):
    """Tests for parseTargets function."""

    def testParseTargetsEmpty(self):
        """Test parsing empty string defaults to 'all'."""
        result = parseTargets("", VALID_INSTALL_TARGETS)
        self.assertEqual(result, ['all'])

    def testParseSingleTarget(self):
        """Test parsing single target."""
        result = parseTargets("apps", VALID_INSTALL_TARGETS)
        self.assertEqual(result, ['apps'])

    def testParseMultipleTargets(self):
        """Test parsing comma-separated targets."""
        result = parseTargets("fonts,apps,git", VALID_INSTALL_TARGETS)
        self.assertEqual(result, ['fonts', 'apps', 'git'])

    def testParseTargetsInvalidTarget(self):
        """Test that invalid target raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            parseTargets("invalid", VALID_INSTALL_TARGETS)
        self.assertIn("Invalid target", str(cm.exception))

    def testParseTargetsWhitespace(self):
        """Test that whitespace is stripped."""
        result = parseTargets(" fonts , apps , git ", VALID_INSTALL_TARGETS)
        self.assertEqual(result, ['fonts', 'apps', 'git'])


class TestParseSetupArgs(unittest.TestCase):
    """Tests for parseSetupArgs function."""

    def testDefaultArgs(self):
        """Test parsing with no arguments."""
        args = parseSetupArgs([])
        self.assertEqual(args.installTargets, ['all'])
        self.assertEqual(args.updateTargets, [])
        self.assertEqual(args.passphraseMode, 'require')

    def testInstallFlag(self):
        """Test parsing --install flag."""
        args = parseSetupArgs(['--install'])
        self.assertEqual(args.installTargets, ['all'])

    def testInstallWithTargets(self):
        """Test parsing --install=targets."""
        args = parseSetupArgs(['--install=fonts,apps'])
        self.assertEqual(args.installTargets, ['fonts', 'apps'])

    def testUpdateFlag(self):
        """Test parsing --update flag."""
        args = parseSetupArgs(['--update'])
        self.assertEqual(args.updateTargets, ['all'])

    def testUpdateWithTargets(self):
        """Test parsing --update=targets."""
        args = parseSetupArgs(['--update=apps'])
        self.assertEqual(args.updateTargets, ['apps'])

    def testPassphraseMode(self):
        """Test parsing --passphrase flag."""
        args = parseSetupArgs(['--passphrase=no'])
        self.assertEqual(args.passphraseMode, 'no')

    def testDryRunFlag(self):
        """Test parsing --dryRun flag."""
        args = parseSetupArgs(['--dryRun'])
        self.assertTrue(args.dryRun)

    def testVerboseFlag(self):
        """Test parsing --verbose flag."""
        args = parseSetupArgs(['--verbose'])
        self.assertTrue(args.verbose)

    def testQuietFlag(self):
        """Test parsing --quiet flag."""
        args = parseSetupArgs(['--quiet'])
        self.assertTrue(args.quiet)

    def testConfigDirFlag(self):
        """Test parsing --configDir flag."""
        args = parseSetupArgs(['--configDir', '/custom/path'])
        self.assertEqual(args.configDir, '/custom/path')

    def testConfigDirEquals(self):
        """Test parsing --configDir= flag."""
        args = parseSetupArgs(['--configDir=/custom/path'])
        self.assertEqual(args.configDir, '/custom/path')


class TestDetermineRunFlags(unittest.TestCase):
    """Tests for determineRunFlags function."""

    def testUpdateModeSkipsInstall(self):
        """Test that update mode skips installation steps."""
        args = SetupArgs(updateTargets=['all'])
        flags = determineRunFlags(args)

        self.assertTrue(flags.runUpdate)
        self.assertFalse(flags.runFonts)
        self.assertFalse(flags.runApps)

    def testInstallAllMode(self):
        """Test that install=all enables everything."""
        args = SetupArgs(installTargets=['all'])
        flags = determineRunFlags(args)

        self.assertTrue(flags.runFonts)
        self.assertTrue(flags.runApps)
        self.assertTrue(flags.runGit)
        self.assertTrue(flags.runCursor)
        self.assertTrue(flags.runRepos)
        self.assertTrue(flags.runSsh)

    def testInstallSpecificTargets(self):
        """Test that specific install targets work."""
        args = SetupArgs(installTargets=['fonts', 'git'])
        flags = determineRunFlags(args)

        self.assertTrue(flags.runFonts)
        self.assertTrue(flags.runGit)
        self.assertFalse(flags.runApps)
        self.assertFalse(flags.runCursor)

    def testInstallAppsOnly(self):
        """Test install=apps mode."""
        args = SetupArgs(installTargets=['apps'])
        flags = determineRunFlags(args)

        self.assertTrue(flags.runApps)
        self.assertFalse(flags.runFonts)
        self.assertFalse(flags.runGit)


if __name__ == "__main__":
    unittest.main()
