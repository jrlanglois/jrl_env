#!/usr/bin/env python3
"""
Base class for system-specific setup implementations.
Provides common setup flow with platform-specific hooks.
"""

import os
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, List, Optional, TypeAlias

DependencyChecker: TypeAlias = Callable[[], bool]

from common.common import (
    configureCursor,
    configureGit,
    configureGithubSsh,
    cloneRepositories,
    determineRunFlags,
    parseSetupArgs,
    printError,
    printInfo,
    printSection,
    printSuccess,
    printWarning,
    safePrint,
    SetupArgs,
    RunFlags,
)
from common.install.installApps import runConfigCommands
from common.install.setupUtils import (
    backupConfigs,
    checkDependencies,
    initLogging,
    shouldCloneRepositories,
)


class SystemBase(ABC):
    """
    Base class for system-specific setup implementations.
    Implements the common setup flow using the Template Method pattern.
    """

    def __init__(self, projectRoot: Path):
        """Initialise the system setup."""
        self.projectRoot = projectRoot
        self.scriptDir = projectRoot / "systems" / self.getPlatformName()
        self.setupArgs: Optional[SetupArgs] = None
        self.runFlags: Optional[RunFlags] = None
        self.logFile: Optional[str] = None
        self.rollbackSession = None

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

    def setupDevEnv(self) -> bool:
        """Set up development environment (optional step). Default implementation tries to import and call setupDevEnv module."""
        try:
            moduleName = f"systems.{self.getPlatformName()}.setupDevEnv"
            setupDevEnvModule = __import__(moduleName, fromlist=["setupDevEnv"])
            return setupDevEnvModule.setupDevEnv()
        except (ImportError, AttributeError):
            return True

    def _installAppsWithPackageManagers(
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

    def validateConfigs(self) -> None:
        """Validate configuration files."""
        printInfo("Validating configuration files...")
        try:
            from common.systems.validate import main as validateMain
            result = validateMain()
            if result != 0:
                printWarning("Validation had issues. Continuing anyway...")
        except Exception as e:
            printWarning(f"Could not run validation script: {e}. Continuing anyway...")

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

        steps = []
        if not self.runFlags.runFonts and not self.runFlags.runApps and not self.runFlags.runGit and not self.runFlags.runCursor and not self.runFlags.runRepos and not self.runFlags.runSsh:
            printWarning("All steps are skipped. Nothing will run.")
            return 0

        # Pre-setup
        steps.append(("Pre-setup", "Run pre-setup steps", True))

        # Step 1: Dev environment
        stepName = "devEnv"
        isComplete = isStepComplete(existingState, stepName) if existingState else False
        steps.append(("Step 1", "Setup development environment", True, isComplete))

        # Step 2: Fonts
        if self.runFlags.runFonts:
            stepName = "fonts"
            isComplete = isStepComplete(existingState, stepName) if existingState else False
            steps.append(("Step 2", "Install fonts", True, isComplete))

        # Step 3: Apps
        if self.runFlags.runApps:
            stepName = "apps"
            isComplete = isStepComplete(existingState, stepName) if existingState else False
            steps.append(("Step 3", "Install/update applications", True, isComplete))

        # Step 4: Git
        if self.runFlags.runGit:
            stepName = "git"
            isComplete = isStepComplete(existingState, stepName) if existingState else False
            steps.append(("Step 4", "Configure Git", True, isComplete))

        # Step 5: SSH
        if self.runFlags.runSsh:
            stepName = "ssh"
            isComplete = isStepComplete(existingState, stepName) if existingState else False
            steps.append(("Step 5", "Configure GitHub SSH", True, isComplete))

        # Step 6: Cursor
        if self.runFlags.runCursor:
            stepName = "cursor"
            isComplete = isStepComplete(existingState, stepName) if existingState else False
            steps.append(("Step 6", "Configure Cursor editor", True, isComplete))

        # Step 7: Repos
        if self.runFlags.runRepos:
            stepName = "repos"
            isComplete = isStepComplete(existingState, stepName) if existingState else False
            steps.append(("Step 7", "Clone repositories", True, isComplete))

        # Post-setup
        steps.append(("Post-setup", "Run post-setup steps", True))

        printInfo("Steps that will be executed:")
        safePrint()
        for step in steps:
            if len(step) == 4:
                stepNum, description, willRun, isComplete = step
                status = "✓ (already completed, will skip)" if isComplete else "→ (will run)"
                printInfo(f"  {stepNum}: {description} - {status}")
            else:
                stepNum, description, willRun = step
                printInfo(f"  {stepNum}: {description}")

        safePrint()
        if existingState:
            printInfo(f"Note: Found incomplete setup from {existingState.timestamp}")
            printInfo("Use --resume to automatically resume, or --noResume to start fresh")
        return 0

    def setupPaths(self) -> dict:
        """
        Set up all configuration and installation paths.

        Returns:
            Dictionary with path keys
        """
        configsDir = self.projectRoot / "configs"
        return {
            "gitConfigPath": str(configsDir / "gitConfig.json"),
            "cursorConfigPath": str(configsDir / "cursorSettings.json"),
            "cursorSettingsPath": self.getCursorSettingsPath(),
            "fontsConfigPath": str(configsDir / "fonts.json"),
            "fontInstallDir": self.getFontInstallDir(),
            "reposConfigPath": str(configsDir / "repositories.json"),
            "platformConfigPath": str(configsDir / self.getConfigFileName()),
        }

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run the complete setup process.

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
        printSection(f"jrl_env Setup for {self.getPlatformName().capitalize()}")
        printInfo(f"Log file: {self.logFile}")

        if self.setupArgs.dryRun:
            printSection("DRY RUN MODE")
            printWarning("No changes will be made. This is a preview.")

        # Check for existing setup state (resume capability)
        from common.install.setupState import (
            loadState,
            createState,
            clearState,
            isStepComplete,
            markStepComplete,
            markStepFailed,
        )
        platformName = self.getPlatformName()
        existingState = loadState(platformName) if not self.setupArgs.dryRun else None
        shouldResume = False

        if existingState and not self.setupArgs.noResume:
            if self.setupArgs.resume:
                shouldResume = True
            else:
                # Prompt user if they want to resume
                printSection("Previous Setup Detected")
                printInfo(f"Found incomplete setup from {existingState.timestamp}")
                if existingState.failedAtStep:
                    printInfo(f"Setup failed at: {existingState.failedAtStep}")
                printInfo(f"Completed steps: {', '.join(sorted(existingState.completedSteps)) or 'None'}")
                safePrint()
                print("Would you like to resume from the last successful step? (y/n): ", end="", flush=True)
                try:
                    response = input().strip().lower()
                    shouldResume = response in ('y', 'yes')
                except (EOFError, KeyboardInterrupt):
                    shouldResume = False
                safePrint()

        if shouldResume and existingState:
            printSection("Resuming Setup")
            printInfo(f"Resuming from session: {existingState.sessionId}")
            printInfo(f"Skipping completed steps: {', '.join(sorted(existingState.completedSteps)) or 'None'}")
            self.setupState = existingState
            safePrint()
        else:
            if existingState and not shouldResume:
                # Clear old state if not resuming
                clearState(platformName)
            self.setupState = createState(platformName) if not self.setupArgs.dryRun else None

        # Validate configs
        self.validateConfigs()

        # Run pre-install commands
        paths = self.setupPaths()
        runConfigCommands("preInstall", paths["platformConfigPath"])
        safePrint()

        # Check dependencies and backup configs
        backupDir = None
        if not self.setupArgs.dryRun:
            dependencyCheckers = self.getOptionalDependencyCheckers()
            if not checkDependencies(self.getRequiredDependencies(), dependencyCheckers):
                return 1
            backupDir = backupConfigs(self.setupArgs.noBackup, self.setupArgs.dryRun, paths["cursorSettingsPath"])
            safePrint()

        # Create rollback session
        from common.install.rollback import createSession, saveSession
        rollbackSession = createSession(backupDir)
        self.rollbackSession = rollbackSession

        printInfo("Starting complete environment setup...")
        safePrint()

        # Run pre-setup steps
        if not self.runPreSetupSteps():
            printWarning("Pre-setup steps had some issues, continuing...")
        safePrint()

        # Step 1: Setup development environment
        stepName = "devEnv"
        if isStepComplete(self.setupState, stepName):
            printSection("Step 1: Setting up development environment (SKIPPED - already completed)")
            printInfo("Development environment setup was already completed in a previous run.")
        else:
            printSection("Step 1: Setting up development environment")
            try:
                if not self.setupDevEnv():
                    printWarning("Development environment setup had some issues, continuing...")
                else:
                    printSuccess("Development environment setup completed")
                    if self.setupState:
                        markStepComplete(self.setupState, stepName)
            except Exception as e:
                if self.setupState:
                    markStepFailed(self.setupState, stepName)
                raise
        safePrint()

        # Step 2: Install fonts
        if self.runFlags.runFonts:
            stepName = "fonts"
            if isStepComplete(self.setupState, stepName):
                printSection("Step 2: Installing fonts (SKIPPED - already completed)", dryRun=self.setupArgs.dryRun)
                printInfo("Font installation was already completed in a previous run.")
            else:
                printSection("Step 2: Installing fonts", dryRun=self.setupArgs.dryRun)
                try:
                    if not self.installGoogleFonts(paths["fontsConfigPath"], paths["fontInstallDir"], self.setupArgs.dryRun):
                        printWarning("Font installation had some issues, continuing...")
                    else:
                        printSuccess("Font installation completed")
                        if self.setupState:
                            markStepComplete(self.setupState, stepName)
                except Exception as e:
                    if self.setupState:
                        markStepFailed(self.setupState, stepName)
                    raise
            safePrint()

        # Step 3: Install applications
        if self.runFlags.runApps:
            stepName = "apps"
            if isStepComplete(self.setupState, stepName):
                printSection("Step 3: Installing applications (SKIPPED - already completed)", dryRun=self.setupArgs.dryRun)
                printInfo("Application installation was already completed in a previous run.")
            else:
                printSection("Step 3: Installing applications", dryRun=self.setupArgs.dryRun)
                try:
                    installResult = self.installOrUpdateApps(paths["platformConfigPath"], self.setupArgs.dryRun)
                    if not installResult or (hasattr(installResult, 'failedCount') and installResult.failedCount > 0):
                        printWarning("Application installation had some issues, continuing...")
                    else:
                        printSuccess("Application installation completed")
                        if self.setupState:
                            markStepComplete(self.setupState, stepName)
                    # Track installed packages for rollback
                    if self.rollbackSession and installResult and hasattr(installResult, 'installedPackages'):
                        self.rollbackSession.installedPackages.extend(installResult.installedPackages)
                        self.rollbackSession.updatedPackages.extend(installResult.updatedPackages)
                except Exception as e:
                    if self.setupState:
                        markStepFailed(self.setupState, stepName)
                    raise
            safePrint()

        # Step 4: Configure Git
        if self.runFlags.runGit:
            stepName = "git"
            if isStepComplete(self.setupState, stepName):
                printSection("Step 4: Configuring Git (SKIPPED - already completed)", dryRun=self.setupArgs.dryRun)
                printInfo("Git configuration was already completed in a previous run.")
            else:
                printSection("Step 4: Configuring Git", dryRun=self.setupArgs.dryRun)
                try:
                    gitSuccess = configureGit(paths["gitConfigPath"], dryRun=self.setupArgs.dryRun)
                    if not gitSuccess:
                        printWarning("Git configuration had some issues, continuing...")
                    else:
                        printSuccess("Git configuration completed")
                        if self.setupState:
                            markStepComplete(self.setupState, stepName)
                        if self.rollbackSession:
                            self.rollbackSession.configuredGit = True
                except Exception as e:
                    if self.setupState:
                        markStepFailed(self.setupState, stepName)
                    raise
            safePrint()

        # Step 5: Configure GitHub SSH
        if self.runFlags.runSsh:
            stepName = "ssh"
            if isStepComplete(self.setupState, stepName):
                printSection("Step 5: Configuring GitHub SSH (SKIPPED - already completed)", dryRun=self.setupArgs.dryRun)
                printInfo("GitHub SSH configuration was already completed in a previous run.")
            else:
                printSection("Step 5: Configuring GitHub SSH", dryRun=self.setupArgs.dryRun)
                try:
                    sshSuccess = configureGithubSsh(paths["gitConfigPath"], dryRun=self.setupArgs.dryRun)
                    if not sshSuccess:
                        printWarning("GitHub SSH configuration had some issues, continuing...")
                    else:
                        printSuccess("GitHub SSH configuration completed")
                        if self.setupState:
                            markStepComplete(self.setupState, stepName)
                        if self.rollbackSession:
                            self.rollbackSession.configuredSsh = True
                except Exception as e:
                    if self.setupState:
                        markStepFailed(self.setupState, stepName)
                    raise
            safePrint()

        # Step 6: Configure Cursor
        if self.runFlags.runCursor:
            stepName = "cursor"
            if isStepComplete(self.setupState, stepName):
                printSection("Step 6: Configuring Cursor (SKIPPED - already completed)", dryRun=self.setupArgs.dryRun)
                printInfo("Cursor configuration was already completed in a previous run.")
            else:
                printSection("Step 6: Configuring Cursor", dryRun=self.setupArgs.dryRun)
                try:
                    cursorSuccess = configureCursor(paths["cursorConfigPath"], paths["cursorSettingsPath"], dryRun=self.setupArgs.dryRun)
                    if not cursorSuccess:
                        printWarning("Cursor configuration had some issues, continuing...")
                    else:
                        printSuccess("Cursor configuration completed")
                        if self.setupState:
                            markStepComplete(self.setupState, stepName)
                        if self.rollbackSession:
                            self.rollbackSession.configuredCursor = True
                except Exception as e:
                    if self.setupState:
                        markStepFailed(self.setupState, stepName)
                    raise
            safePrint()

        # Step 7: Clone repositories
        if self.runFlags.runRepos:
            stepName = "repos"
            if isStepComplete(self.setupState, stepName):
                printSection("Step 7: Cloning repositories (SKIPPED - already completed)", dryRun=self.setupArgs.dryRun)
                printInfo("Repository cloning was already completed in a previous run.")
            else:
                printSection("Step 7: Cloning repositories", dryRun=self.setupArgs.dryRun)
                try:
                    if self.setupArgs.dryRun or shouldCloneRepositories(paths["reposConfigPath"], self.getRepositoryWorkPathKey()):
                        if not cloneRepositories(paths["reposConfigPath"], dryRun=self.setupArgs.dryRun):
                            printWarning("Repository cloning had some issues, continuing...")
                        else:
                            printSuccess("Repository cloning completed")
                            if self.setupState:
                                markStepComplete(self.setupState, stepName)
                    else:
                        printWarning("Repositories directory already exists with content. Skipping repository cloning.")
                        printInfo(f"To clone repositories manually, run: python3 -m common.systems.cli {self.getPlatformName()} repos")
                        if self.setupState:
                            markStepComplete(self.setupState, stepName)
                except Exception as e:
                    if self.setupState:
                        markStepFailed(self.setupState, stepName)
                    raise
            safePrint()

        # Run post-setup steps
        if not self.runPostSetupSteps():
            printWarning("Post-setup steps had some issues, continuing...")
        safePrint()

        # Run post-install commands
        runConfigCommands("postInstall", paths["platformConfigPath"])
        safePrint()

        # Save rollback session
        if self.rollbackSession and not self.setupArgs.dryRun:
            from common.install.rollback import saveSession
            sessionFile = saveSession(self.rollbackSession)
            printInfo(f"Rollback session saved: {sessionFile}")

        # Run verification
        if not self.setupArgs.dryRun:
            safePrint()
            from common.systems.verify import runVerification
            verificationPassed = runVerification(self)
            safePrint()

        # Clear setup state on successful completion
        if self.setupState and not self.setupArgs.dryRun:
            clearState(platformName)
            printInfo("Setup state cleared (setup completed successfully)")

        printSection("Setup Complete")
        printInfo("All setup tasks have been executed.")
        printInfo(f"Log file saved to: {self.logFile}")
        if self.rollbackSession and not self.setupArgs.dryRun:
            printInfo(f"To rollback this setup, run: python3 -m common.systems.cli {self.getPlatformName()} rollback")
        printInfo("Please review any warnings above and restart your terminal if needed.")

        return 0
