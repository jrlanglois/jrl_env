#!/usr/bin/env python3
"""
Raspberry Pi system setup implementation.
"""

import sys
from pathlib import Path

# Add project root to path so we can import from common
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent.parent
sys.path.insert(0, str(projectRoot))

from common.systems.systemBase import SystemBase


class RaspberrypiSystem(SystemBase):
    """Raspberry Pi system setup implementation."""

    def getPlatformName(self) -> str:
        return "raspberrypi"

    def getConfigFileName(self) -> str:
        return "raspberrypi.json"

    def getFontInstallDir(self) -> str:
        return str(Path.home() / ".local/share/fonts")

    def getCursorSettingsPath(self) -> str:
        return str(Path.home() / ".config/Cursor/User/settings.json")

    def getRepositoryWorkPathKey(self) -> str:
        return ".workPathUnix"

    def getRequiredDependencies(self) -> list:
        return ["git"]

    def getOptionalDependencyCheckers(self) -> list:
        return []

    def installOrUpdateApps(self, configPath: str, dryRun: bool) -> bool:
        """Install or update applications on Raspberry Pi."""
        from common.core.utilities import getJsonValue
        from common.install.packageManagers import AptPackageManager, SnapPackageManager

        apt = AptPackageManager()
        snap = SnapPackageManager()
        useLinuxCommon = getJsonValue(configPath, ".useLinuxCommon", False)

        return self._installAppsWithPackageManagers(
            configPath=configPath,
            dryRun=dryRun,
            primaryExtractor=".apt[]?",
            secondaryExtractor=".snap[]?",
            primaryLabel="APT packages",
            secondaryLabel="Snap packages",
            checkPrimary=apt.check,
            installPrimary=apt.install,
            updatePrimary=apt.update,
            checkSecondary=snap.check,
            installSecondary=snap.install,
            updateSecondary=snap.update,
            useLinuxCommon=useLinuxCommon,
        )


def main() -> int:
    """Main entry point for Raspberry Pi setup."""
    from pathlib import Path
    projectRoot = Path(__file__).parent.parent.parent
    system = RaspberrypiSystem(projectRoot)
    return system.run()


if __name__ == "__main__":
    sys.exit(main())
