#!/usr/bin/env python3
"""
Windows 11 system setup implementation.
"""

import os
import sys
from pathlib import Path

# Add project root to path so we can import from common
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent.parent
sys.path.insert(0, str(projectRoot))

from common.common import (
    isWingetInstalled,
    printInfo,
    printSection,
    printSuccess,
    printWarning,
    safePrint,
    updateMicrosoftStore,
    updateWinget,
)
from common.systems.systemBase import SystemBase


class Win11System(SystemBase):
    """Windows 11 system setup implementation."""

    def getPlatformName(self) -> str:
        return "win11"

    def getConfigFileName(self) -> str:
        return "win11.json"

    def getFontInstallDir(self) -> str:
        return str(Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts")

    def getCursorSettingsPath(self) -> str:
        return str(Path(os.environ.get("APPDATA", "")) / "Cursor" / "User" / "settings.json")

    def getRepositoryWorkPathKey(self) -> str:
        return ".workPathWindows"

    def getRequiredDependencies(self) -> list:
        return ["git"]

    def getOptionalDependencyCheckers(self) -> list:
        return [isWingetInstalled]

    def installOrUpdateApps(self, configPath: str, dryRun: bool) -> bool:
        """Install or update applications on Windows 11."""
        from common.install.packageManagers import WingetPackageManager, StorePackageManager

        winget = WingetPackageManager()
        store = StorePackageManager()

        return self._installAppsWithPackageManagers(
            configPath=configPath,
            dryRun=dryRun,
            primaryExtractor=".winget[]?",
            secondaryExtractor=".store[]?",
            primaryLabel="Winget packages",
            secondaryLabel="Windows Store packages",
            checkPrimary=winget.check,
            installPrimary=winget.install,
            updatePrimary=winget.update,
            checkSecondary=store.check,
            installSecondary=store.install,
            updateSecondary=store.update,
            useLinuxCommon=False,
        )

    def runPreSetupSteps(self) -> bool:
        """Update Windows Store and winget."""
        if self.setupArgs.dryRun:
            printSection("Step 1: Updating package managers", dryRun=True)
            printInfo("Would update winget and Microsoft Store")
        else:
            printSection("Step 1: Updating package managers")
            if not updateWinget():
                printWarning("winget update failed, continuing...")
            else:
                printSuccess("winget updated successfully")
            if not updateMicrosoftStore():
                printWarning("Microsoft Store update failed, continuing...")
            else:
                printSuccess("Microsoft Store updated successfully")
        safePrint()
        return True

    def setupDevEnv(self) -> bool:
        """Configure Windows 11 settings (Windows doesn't have a traditional dev env setup)."""
        if self.setupArgs.dryRun:
            printSection("Step 2: Configuring Windows 11", dryRun=True)
            printInfo("Would configure Windows 11 settings (regional, time, dark mode, File Explorer, privacy, taskbar, Developer Mode, notifications, WSL2)")
        else:
            printSection("Step 2: Configuring Windows 11")
            try:
                from systems.win11.configureWin11 import configureWin11
                if not configureWin11():
                    printWarning("Windows 11 configuration had some issues, continuing...")
                else:
                    printSuccess("Windows 11 configuration completed")
            except ImportError:
                printWarning("configureWin11 module not available. Skipping Windows 11 configuration.")
            except Exception as e:
                printWarning(f"Windows 11 configuration error: {e}")
        safePrint()
        return True

    def runPostSetupSteps(self) -> bool:
        """Windows doesn't have post-setup steps."""
        return True


def main() -> int:
    """Main entry point for Windows 11 setup."""
    from pathlib import Path
    projectRoot = Path(__file__).parent.parent.parent
    system = Win11System(projectRoot)
    return system.run()


if __name__ == "__main__":
    sys.exit(main())
