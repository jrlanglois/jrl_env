#!/usr/bin/env python3
"""
Unit tests for sudo manager.
Tests sudo validation and credential caching.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
scriptDir = Path(__file__).parent.absolute()
sys.path.insert(0, str(scriptDir.parent.parent))

from common.core.utilities import getProjectRoot
projectRoot = getProjectRoot()

from common.core.sudoHelper import SudoManager


class TestSudoManager(unittest.TestCase):
    """Tests for SudoManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = SudoManager(dryRun=True)

    def testInitialization(self):
        """Test SudoManager initialises correctly."""
        self.assertTrue(self.manager.dryRun)
        self.assertFalse(self.manager.validated)

    @patch('common.core.sudoHelper.isWindows')
    def testIsNeededOnWindows(self, mockIsWindows):
        """Test isNeeded returns False on Windows."""
        mockIsWindows.return_value = True
        manager = SudoManager(dryRun=True)

        result = manager.isNeeded()

        self.assertFalse(result)

    @patch('common.core.sudoHelper.isWindows')
    def testIsNeededOnUnix(self, mockIsWindows):
        """Test isNeeded returns True on Unix."""
        mockIsWindows.return_value = False
        manager = SudoManager(dryRun=True)

        result = manager.isNeeded()

        self.assertTrue(result)

    @patch.object(SudoManager, 'isNeeded')
    def testValidateNotNeeded(self, mockIsNeeded):
        """Test validate returns True when sudo not needed."""
        mockIsNeeded.return_value = False

        result = self.manager.validate()

        self.assertTrue(result)

    @patch.object(SudoManager, 'isNeeded')
    def testValidateAlreadyValidated(self, mockIsNeeded):
        """Test validate skips when already validated."""
        mockIsNeeded.return_value = True
        self.manager.validated = True

        result = self.manager.validate()

        self.assertTrue(result)

    @patch.object(SudoManager, 'isNeeded')
    def testValidateDryRun(self, mockIsNeeded):
        """Test validate in dry-run mode."""
        mockIsNeeded.return_value = True

        result = self.manager.validate()

        self.assertTrue(result)
        self.assertTrue(self.manager.validated)

    @patch.object(SudoManager, 'isNeeded')
    def testKeepAliveWhenNotNeeded(self, mockIsNeeded):
        """Test keepAlive does nothing when not needed."""
        mockIsNeeded.return_value = False

        # Should not raise
        self.manager.keepAlive()

    @patch.object(SudoManager, 'isNeeded')
    def testKeepAliveWhenNotValidated(self, mockIsNeeded):
        """Test keepAlive does nothing when not validated."""
        mockIsNeeded.return_value = True
        self.manager.validated = False

        # Should not raise
        self.manager.keepAlive()

    @patch.object(SudoManager, 'isNeeded')
    def testKeepAliveInDryRun(self, mockIsNeeded):
        """Test keepAlive does nothing in dry-run."""
        mockIsNeeded.return_value = True
        self.manager.validated = True

        # Should not raise
        self.manager.keepAlive()


if __name__ == "__main__":
    unittest.main()
