#!/usr/bin/env python3
"""
ArchLinux system setup implementation.
"""

import sys
from pathlib import Path

# Add project root to path so we can import from common
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent.parent
sys.path.insert(0, str(projectRoot))

from common.systems.systemBase import SystemBase


class ArchlinuxSystem(SystemBase):
    """ArchLinux system setup implementation."""

    def getPlatformName(self) -> str:
        return "archlinux"

    def getConfigFileName(self) -> str:
        return "archlinux.json"

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
        """Install or update applications on ArchLinux."""
        from common.core.utilities import getJsonValue
        from common.install.packageManagers import PacmanPackageManager

        pacman = PacmanPackageManager()
        useLinuxCommon = getJsonValue(configPath, ".useLinuxCommon", False)

        return self._installAppsWithPackageManagers(
            configPath=configPath,
            dryRun=dryRun,
            primaryExtractor=".pacman[]?",
            secondaryExtractor=None,
            primaryLabel="Pacman packages",
            secondaryLabel=None,
            checkPrimary=pacman.check,
            installPrimary=pacman.install,
            updatePrimary=pacman.update,
            useLinuxCommon=useLinuxCommon,
        )


def main() -> int:
    """Main entry point for ArchLinux setup."""
    from pathlib import Path
    projectRoot = Path(__file__).parent.parent.parent
    system = ArchlinuxSystem(projectRoot)
    return system.run()


if __name__ == "__main__":
    sys.exit(main())
