#!/usr/bin/env python3
"""
Unit tests for step definitions.
Tests setup step configuration and execution order.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
scriptDir = Path(__file__).parent.absolute()
sys.path.insert(0, str(scriptDir.parent.parent))

from common.core.utilities import getProjectRoot
projectRoot = getProjectRoot()

from common.systems.stepDefinitions import getStepsToRun, willAnyStepsRun
from common.install.setupArgs import RunFlags


class TestStepDefinitions(unittest.TestCase):
    """Tests for step definition functions."""

    def testGetStepsToRunAll(self):
        """Test getting all steps when all flags are True."""
        flags = RunFlags(
            runFonts=True,
            runApps=True,
            runGit=True,
            runCursor=True,
            runRepos=True,
            runSsh=True,
        )

        steps = getStepsToRun(flags)

        self.assertGreater(len(steps), 0)
        # Should have fonts, apps, git, ssh, cursor, repos
        self.assertGreaterEqual(len(steps), 6)

    def testGetStepsToRunNone(self):
        """Test getting steps when all flags are False."""
        flags = RunFlags()

        steps = getStepsToRun(flags)

        # Should still have devEnv step
        self.assertGreater(len(steps), 0)

    def testGetStepsToRunAppsOnly(self):
        """Test getting steps for apps only."""
        flags = RunFlags(runApps=True)

        steps = getStepsToRun(flags)

        stepNames = [s.stepName for s in steps]
        self.assertIn("apps", stepNames)
        self.assertIn("devEnv", stepNames)  # Always included

    def testWillAnyStepsRunTrue(self):
        """Test willAnyStepsRun returns True when steps exist."""
        flags = RunFlags(runApps=True)

        result = willAnyStepsRun(flags)

        self.assertTrue(result)

    def testWillAnyStepsRunFalse(self):
        """Test willAnyStepsRun returns False when no steps."""
        flags = RunFlags()

        result = willAnyStepsRun(flags)

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
