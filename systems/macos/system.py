#!/usr/bin/env python3
"""
macOS system setup implementation.
"""

import sys
from pathlib import Path

# Add project root to path so we can import from common
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent.parent
sys.path.insert(0, str(projectRoot))

from common.systems.systemBase import SystemBase


class MacosSystem(SystemBase):
    """macOS system setup implementation."""

    def getPlatformName(self) -> str:
        return "macos"

    def getConfigFileName(self) -> str:
        return "macos.json"

    def getFontInstallDir(self) -> str:
        return str(Path.home() / "Library/Fonts")

    def getCursorSettingsPath(self) -> str:
        return str(Path.home() / "Library/Application Support/Cursor/User/settings.json")

    def getRepositoryWorkPathKey(self) -> str:
        return ".workPathUnix"

    def getRequiredDependencies(self) -> list:
        return ["git", "brew"]

    def getOptionalDependencyCheckers(self) -> list:
        return []

    def installOrUpdateApps(self, configPath: str, dryRun: bool) -> bool:
        """Install or update applications on macOS."""
        from common.install.packageManagers import BrewPackageManager, BrewCaskPackageManager

        brew = BrewPackageManager()
        brewCask = BrewCaskPackageManager()

        return self._installAppsWithPackageManagers(
            configPath=configPath,
            dryRun=dryRun,
            primaryExtractor=".brew[]?",
            secondaryExtractor=".brewCask[]?",
            primaryLabel="Brew packages",
            secondaryLabel="Brew Cask packages",
            checkPrimary=brew.check,
            installPrimary=brew.install,
            updatePrimary=brew.update,
            checkSecondary=brewCask.check,
            installSecondary=brewCask.install,
            updateSecondary=brewCask.update,
            useLinuxCommon=False,
        )


def main() -> int:
    """Main entry point for macOS setup."""
    from pathlib import Path
    projectRoot = Path(__file__).parent.parent.parent
    system = MacosSystem(projectRoot)
    return system.run()


if __name__ == "__main__":
    sys.exit(main())
