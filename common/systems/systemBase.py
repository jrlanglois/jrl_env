#!/usr/bin/env python3
"""
Refactored base class for system-specific setup implementations.
Provides platform abstraction layer using the Template Method pattern.
All orchestration logic has been moved to SetupOrchestrator.
"""

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, List, Optional

# Type alias for dependency checker functions
DependencyChecker = Callable[[], bool]

from common.common import (
    RunFlags,
    SetupArgs,
    determineRunFlags,
    parseSetupArgs,
    printInfo,
    printSection,
    printSuccess,
    printWarning,
    safePrint,
)
from common.install.installApps import runConfigCommands
from common.install.setupUtils import initLogging
from common.systems.configManager import ConfigManager
from common.systems.setupOrchestrator import SetupOrchestrator
from common.systems.stepDefinitions import getStepsToRun, willAnyStepsRun


class SystemBase(ABC):
    """
    Base class for system-specific setup implementations.
    Provides platform abstraction layer with minimal orchestration.
    Uses Template Method pattern for platform-specific behavior.
    """

    def __init__(self, projectRoot: Path):
        """
        Initialise the system setup.

        Args:
            projectRoot: Root directory of jrl_env project
        """
        self.projectRoot = projectRoot
        self.scriptDir = projectRoot / "systems" / self.getPlatformName()
        self.setupArgs: Optional[SetupArgs] = None
        self.runFlags: Optional[RunFlags] = None
        self.logFile: Optional[str] = None
        self.configManager: Optional[ConfigManager] = None

    # ========== Abstract Methods (Platform-Specific) ==========

    @abstractmethod
    def getPlatformName(self) -> str:
        """Get the platform name (e.g., "ubuntu", "macos", "win11")."""
        pass

    @abstractmethod
    def getConfigFileName(self) -> str:
        """Get the config file name (e.g., "ubuntu.json", "macos.json")."""
        pass

    @abstractmethod
    def getFontInstallDir(self) -> str:
        """Get the directory where fonts should be installed."""
        pass

    @abstractmethod
    def getCursorSettingsPath(self) -> str:
        """Get the path to Cursor settings file."""
        pass

    @abstractmethod
    def getRepositoryWorkPathKey(self) -> str:
        """Get the JSON key for repository work path (.workPathUnix or .workPathWindows)."""
        pass

    @abstractmethod
    def getRequiredDependencies(self) -> List[str]:
        """Get list of required command dependencies (e.g., ["git", "brew"])."""
        pass

    @abstractmethod
    def getOptionalDependencyCheckers(self) -> List[DependencyChecker]:
        """Get list of optional dependency checker functions (e.g., [isWingetInstalled])."""
        pass

    @abstractmethod
    def installOrUpdateApps(self, configPath: str, dryRun: bool) -> bool:
        """
        Install or update applications using platform-specific package managers.

        Args:
            configPath: Path to platform config file
            dryRun: If True, don't actually install

        Returns:
            True if successful, False otherwise
        """
        pass

    # ========== Hook Methods (Optional Overrides) ==========

    def setupDevEnv(self) -> bool:
        """
        Set up development environment (optional step).
        Uses unified setupDevEnv implementation from common.install.

        Returns:
            True if successful, False otherwise
        """
        try:
            from common.install.setupDevEnv import setupDevEnv as setupDevEnvFunc
            from common.systems.platform import Platform

            # Convert platform name to Platform enum
            platformName = self.getPlatformName()
            platform = Platform[platformName]

            # Call unified setup function
            dryRun = self.setupArgs.dryRun if self.setupArgs else False
            return setupDevEnvFunc(platform, self.projectRoot, dryRun=dryRun)
        except Exception as e:
            printWarning(f"Development environment setup skipped: {e}")
            return True

    def runPreSetupSteps(self) -> bool:
        """
        Run any pre-setup steps (e.g., update package managers).
        Default implementation does nothing.

        Returns:
            True if successful, False otherwise
        """
        return True

    def runPostSetupSteps(self) -> bool:
        """
        Run any post-setup steps (e.g., system-specific configuration).
        Default implementation does nothing.

        Returns:
            True if successful, False otherwise
        """
        return True

    # ========== Helper Methods ==========

    def installAppsWithPackageManagers(
        self,
        configPath: str,
        dryRun: bool,
        primaryExtractor: str,
        secondaryExtractor: Optional[str],
        primaryLabel: str,
        secondaryLabel: Optional[str],
        checkPrimary: Callable[[str], bool],
        installPrimary: Callable[[str], bool],
        updatePrimary: Callable[[str], bool],
        checkSecondary: Optional[Callable[[str], bool]] = None,
        installSecondary: Optional[Callable[[str], bool]] = None,
        updateSecondary: Optional[Callable[[str], bool]] = None,
        useLinuxCommon: bool = False,
    ) -> bool:
        """
        Helper method to install apps using package manager functions.
        Handles the common pattern of preInstall -> install -> postInstall.

        Args:
            configPath: Path to platform-specific JSON config file
            dryRun: If True, don't actually install
            primaryExtractor: JSONPath for primary package list (e.g., ".apt[]?")
            secondaryExtractor: JSONPath for secondary package list (e.g., ".snap[]?")
            primaryLabel: Label for primary packages (e.g., "APT packages")
            secondaryLabel: Label for secondary packages (e.g., "Snap packages")
            checkPrimary: Function to check if primary package is installed
            installPrimary: Function to install primary package
            updatePrimary: Function to update primary package
            checkSecondary: Function to check if secondary package is installed
            installSecondary: Function to install secondary package
            updateSecondary: Function to update secondary package
            useLinuxCommon: If True, merge with linuxCommon.json

        Returns:
            True if successful, False otherwise
        """
        from common.install.installApps import installApps, installFromConfigWithLinuxCommon

        # Run preInstall commands
        runConfigCommands("preInstall", configPath)

        # Install apps
        if useLinuxCommon:
            # Use linuxCommon merging (for RedHat, OpenSUSE, ArchLinux, Raspberry Pi)
            primaryResult = installFromConfigWithLinuxCommon(
                configPath,
                commonPath=".linuxCommon[]?",
                distroPath=primaryExtractor,
                packageLabel=primaryLabel,
                checkFunction=checkPrimary,
                installFunction=installPrimary,
                updateFunction=updatePrimary,
                dryRun=dryRun,
            )

            # Handle secondary packages if provided (e.g., snap for Raspberry Pi)
            if secondaryExtractor and checkSecondary and installSecondary and updateSecondary:
                secondaryResult = installApps(
                    configPath,
                    primaryExtractor=secondaryExtractor,
                    secondaryExtractor=None,
                    primaryLabel=secondaryLabel or "Secondary packages",
                    secondaryLabel=None,
                    checkPrimary=checkSecondary,
                    installPrimary=installSecondary,
                    updatePrimary=updateSecondary,
                    dryRun=dryRun,
                )
                # Combine results
                from common.install.installApps import InstallResult

                result = InstallResult(
                    installedCount=primaryResult.installedCount + secondaryResult.installedCount,
                    updatedCount=primaryResult.updatedCount + secondaryResult.updatedCount,
                    failedCount=primaryResult.failedCount + secondaryResult.failedCount,
                )
            else:
                result = primaryResult
        else:
            # Use standard installApps (for Ubuntu, macOS, Windows)
            result = installApps(
                configPath,
                primaryExtractor=primaryExtractor,
                secondaryExtractor=secondaryExtractor,
                primaryLabel=primaryLabel,
                secondaryLabel=secondaryLabel,
                checkPrimary=checkPrimary,
                installPrimary=installPrimary,
                updatePrimary=updatePrimary,
                checkSecondary=checkSecondary,
                installSecondary=installSecondary,
                updateSecondary=updateSecondary,
                dryRun=dryRun,
            )

        # Run postInstall commands
        runConfigCommands("postInstall", configPath)

        return result.failedCount == 0

    def installGoogleFonts(self, configPath: str, installDir: str, dryRun: bool) -> bool:
        """
        Install Google Fonts.

        Args:
            configPath: Path to fonts.json config file
            installDir: Directory to install fonts to
            dryRun: If True, don't actually install

        Returns:
            True if successful, False otherwise
        """
        if dryRun:
            return True

        try:
            from common.install.installFonts import installGoogleFonts as installFontsFunc

            installFontsFunc(configPath, installDir)
            return True
        except Exception as e:
            printWarning(f"Font installation error: {e}")
            return False

    # ========== Public Interface ==========

    def listSteps(self) -> int:
        """
        List all steps that will be executed during setup.

        Returns:
            Exit code (0 for success)
        """
        from common.install.setupState import loadState, isStepComplete

        platformName = self.getPlatformName()
        existingState = loadState(platformName) if not self.setupArgs.dryRun else None

        printSection("Setup Steps Preview")
        printInfo(f"Platform: {platformName.capitalize()}")
        safePrint()

        if not willAnyStepsRun(self.runFlags):
            printWarning("All steps are skipped. Nothing will run.")
            return 0

        # Get steps from shared definition
        stepsToRun = getStepsToRun(self.runFlags)

        printInfo("Steps that will be executed:")
        safePrint()

        for step in stepsToRun:
            # Check if step has been completed
            isComplete = isStepComplete(existingState, step.stepName) if existingState else False

            # Format step display
            if step.stepName in ("preSetup", "postSetup"):
                # Pre/post setup steps don't show completion status
                printInfo(f"  {step.stepNumber}: {step.description}")
            else:
                # Regular steps show completion status
                status = "✓ (already completed, will skip)" if isComplete else "→ (will run)"
                printInfo(f"  {step.stepNumber}: {step.description} - {status}")

        safePrint()
        if existingState:
            printInfo(
                f"Note: Found incomplete setup from {existingState.timestamp}\n"
                "Use --resume to automatically resume, or --noResume to start fresh"
            )
        return 0

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run the complete setup process using the refactored orchestrator.

        Args:
            args: Command-line arguments (defaults to sys.argv[1:])

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        if args is None:
            args = sys.argv[1:]

        # Parse arguments
        self.setupArgs = parseSetupArgs(args)
        self.runFlags = determineRunFlags(self.setupArgs)

        # Handle --listSteps flag
        if self.setupArgs.listSteps:
            return self.listSteps()

        # Initialise logging
        self.logFile = initLogging(self.getPlatformName())

        # Create config manager
        self.configManager = ConfigManager(
            projectRoot=self.projectRoot,
            platformName=self.getPlatformName(),
            configFileName=self.getConfigFileName(),
            fontInstallDir=self.getFontInstallDir(),
            cursorSettingsPath=self.getCursorSettingsPath(),
            setupArgs=self.setupArgs,
        )

        # Create and run orchestrator
        orchestrator = SetupOrchestrator(
            system=self,
            setupArgs=self.setupArgs,
            runFlags=self.runFlags,
            configManager=self.configManager,
            logFile=self.logFile,
        )

        return orchestrator.run()
