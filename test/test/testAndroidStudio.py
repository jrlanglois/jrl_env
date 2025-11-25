#!/usr/bin/env python3
"""
Unit tests for Android Studio manager.
Tests SDK detection, component management, and updates.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
scriptDir = Path(__file__).parent.absolute()
sys.path.insert(0, str(scriptDir.parent.parent))

from common.core.utilities import getProjectRoot
projectRoot = getProjectRoot()

from common.install.androidStudio import AndroidStudioManager


class TestAndroidStudioManager(unittest.TestCase):
    """Tests for AndroidStudioManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = AndroidStudioManager(dryRun=True)

    def testInitialization(self):
        """Test AndroidStudioManager initialises correctly."""
        self.assertTrue(self.manager.dryRun)
        self.assertIsNone(self.manager.sdkRoot)
        self.assertIsNone(self.manager.sdkManager)

    @patch.dict(os.environ, {'ANDROID_HOME': '/test/android/sdk', 'ANDROID_SDK_ROOT': ''}, clear=False)
    @patch('pathlib.Path.exists')
    def testFindSdkRootFromEnvVar(self, mockExists):
        """Test finding SDK root from ANDROID_HOME env var."""
        mockExists.return_value = True
        # Create fresh manager to pick up env vars
        manager = AndroidStudioManager(dryRun=True)

        result = manager.findSdkRoot()

        self.assertIsNotNone(result)
        self.assertIn('test', str(result))

    @patch.dict(os.environ, {'ANDROID_SDK_ROOT': '/test/sdk/root', 'ANDROID_HOME': ''}, clear=False)
    @patch('pathlib.Path.exists')
    def testFindSdkRootFromSdkRootEnvVar(self, mockExists):
        """Test finding SDK root from ANDROID_SDK_ROOT env var."""
        mockExists.return_value = True
        manager = AndroidStudioManager(dryRun=True)

        result = manager.findSdkRoot()

        self.assertIsNotNone(result)
        self.assertIn('test', str(result))

    @patch.dict(os.environ, {}, clear=True)
    @patch('pathlib.Path.exists')
    def testFindSdkRootNotFound(self, mockExists):
        """Test SDK root not found."""
        mockExists.return_value = False

        result = self.manager.findSdkRoot()

        self.assertIsNone(result)

    @patch.object(AndroidStudioManager, 'findSdkRoot')
    def testFindSdkManagerNotFound(self, mockFindRoot):
        """Test sdkmanager not found when SDK root is None."""
        mockFindRoot.return_value = None
        manager = AndroidStudioManager(dryRun=True)

        result = manager.findSdkManager()

        self.assertIsNone(result)

    @patch.object(AndroidStudioManager, 'findSdkRoot')
    @patch('pathlib.Path.exists')
    def testFindSdkManagerFound(self, mockExists, mockFindRoot):
        """Test finding sdkmanager when it exists."""
        mockFindRoot.return_value = Path('/test/sdk')
        mockExists.return_value = True

        result = self.manager.findSdkManager()

        self.assertIsNotNone(result)

    @patch.object(AndroidStudioManager, 'findSdkRoot')
    def testIsInstalledTrue(self, mockFindRoot):
        """Test isInstalled returns True when SDK found."""
        mockFindRoot.return_value = Path('/test/sdk')

        result = self.manager.isInstalled()

        self.assertTrue(result)

    @patch.object(AndroidStudioManager, 'findSdkRoot')
    def testIsInstalledFalse(self, mockFindRoot):
        """Test isInstalled returns False when SDK not found."""
        mockFindRoot.return_value = None

        result = self.manager.isInstalled()

        self.assertFalse(result)

    @patch.object(AndroidStudioManager, 'findSdkManager')
    def testIsSdkManagerAvailableTrue(self, mockFindManager):
        """Test isSdkManagerAvailable returns True."""
        mockFindManager.return_value = Path('/test/sdk/sdkmanager')

        result = self.manager.isSdkManagerAvailable()

        self.assertTrue(result)

    @patch.object(AndroidStudioManager, 'findSdkManager')
    def testIsSdkManagerAvailableFalse(self, mockFindManager):
        """Test isSdkManagerAvailable returns False."""
        mockFindManager.return_value = None

        result = self.manager.isSdkManagerAvailable()

        self.assertFalse(result)

    @patch.object(AndroidStudioManager, 'isInstalled')
    def testUpdateSdkNotInstalled(self, mockIsInstalled):
        """Test updateSdk skips when SDK not installed."""
        mockIsInstalled.return_value = False

        result = self.manager.updateSdk()

        self.assertTrue(result)  # Non-fatal

    @patch.object(AndroidStudioManager, 'isInstalled')
    @patch.object(AndroidStudioManager, 'findSdkManager')
    def testUpdateSdkManagerNotFound(self, mockFindManager, mockIsInstalled):
        """Test updateSdk skips when sdkmanager not found."""
        mockIsInstalled.return_value = True
        mockFindManager.return_value = None

        result = self.manager.updateSdk()

        self.assertTrue(result)  # Non-fatal

    @patch.object(AndroidStudioManager, 'isInstalled')
    @patch.object(AndroidStudioManager, 'findSdkManager')
    def testUpdateSdkDryRun(self, mockFindManager, mockIsInstalled):
        """Test updateSdk in dry-run mode."""
        mockIsInstalled.return_value = True
        mockFindManager.return_value = Path('/test/sdk/sdkmanager')

        result = self.manager.updateSdk()

        self.assertTrue(result)

    @patch.object(AndroidStudioManager, 'findSdkManager')
    def testListInstalledPackagesManagerNotFound(self, mockFindManager):
        """Test listInstalledPackages when sdkmanager not found."""
        mockFindManager.return_value = None

        result = self.manager.listInstalledPackages()

        self.assertEqual(result, [])

    @patch.object(AndroidStudioManager, 'findSdkManager')
    def testInstallComponentsEmptyList(self, mockFindManager):
        """Test installComponents with empty list."""
        mockFindManager.return_value = Path('/test/sdk/sdkmanager')

        result = self.manager.installComponents([])

        self.assertTrue(result)

    @patch.object(AndroidStudioManager, 'findSdkManager')
    def testInstallComponentsManagerNotFound(self, mockFindManager):
        """Test installComponents when sdkmanager not found."""
        mockFindManager.return_value = None

        result = self.manager.installComponents(["platform-tools"])

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
