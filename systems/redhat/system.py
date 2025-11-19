#!/usr/bin/env python3
"""
RedHat/Fedora/CentOS system setup implementation.
"""

import sys
from pathlib import Path

# Add project root to path so we can import from common
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent.parent
sys.path.insert(0, str(projectRoot))

from common.systems.systemBase import SystemBase


class RedhatSystem(SystemBase):
    """RedHat/Fedora/CentOS system setup implementation."""

    def getPlatformName(self) -> str:
        return "redhat"

    def getConfigFileName(self) -> str:
        return "redhat.json"

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
        """Install or update applications on RedHat/Fedora/CentOS."""
        from common.install.packageManagers import DnfPackageManager

        dnf = DnfPackageManager()

        return self._installAppsWithPackageManagers(
            configPath=configPath,
            dryRun=dryRun,
            primaryExtractor=".dnf[]?",
            secondaryExtractor=None,
            primaryLabel="DNF packages",
            secondaryLabel=None,
            checkPrimary=dnf.check,
            installPrimary=dnf.install,
            updatePrimary=dnf.update,
            useLinuxCommon=True,
        )


def main() -> int:
    """Main entry point for RedHat setup."""
    from pathlib import Path
    projectRoot = Path(__file__).parent.parent.parent
    system = RedhatSystem(projectRoot)
    return system.run()


if __name__ == "__main__":
    sys.exit(main())
