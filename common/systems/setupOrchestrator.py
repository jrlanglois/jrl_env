#!/usr/bin/env python3
"""
Setup orchestration for jrl_env.
Manages the complete setup flow, step execution, and state management.
"""

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional

from common.common import (
    RunFlags,
    SetupArgs,
    checkAndroidStudioInConfig,
    cloneRepositories,
    configureAndroid,
    configureCursor,
    configureGit,
    configureGithubSsh,
    isAndroidStudioInstalled,
    printError,
    printInfo,
    printSection,
    printSuccess,
    printWarning,
    safePrint,
)
from common.core.utilities import getJsonObject
from common.install.installApps import runConfigCommands
from common.install.rollback import RollbackSession, createSession, saveSession
from common.install.setupState import SetupState, clearState, createState, isStepComplete, loadState, markStepComplete, markStepFailed
from common.install.setupUtils import backupConfigs, checkDependencies, shouldCloneRepositories
from common.systems.configManager import ConfigManager
from common.systems.validationEngine import ValidationEngine

if TYPE_CHECKING:
    from common.systems.systemBase import SystemBase


class SetupOrchestrator:
    """
    Orchestrates the complete setup process.
    Manages setup flow, step execution, state management, and rollback.
    """

    def __init__(
        self,
        system: "SystemBase",
        setupArgs: SetupArgs,
        runFlags: RunFlags,
        configManager: ConfigManager,
        logFile: str,
    ):
        """
        Initialise the setup orchestrator.

        Args:
            system: System instance (for platform-specific operations)
            setupArgs: Parsed setup arguments
            runFlags: Flags determining which steps to run
            configManager: Config manager for path resolution
            logFile: Path to log file
        """
        self.system = system
        self.setupArgs = setupArgs
        self.runFlags = runFlags
        self.configManager = configManager
        self.logFile = logFile
        self.setupState: Optional[SetupState] = None
        self.rollbackSession: Optional[RollbackSession] = None
        self.validationEngine = ValidationEngine(system.getPlatformName(), setupArgs)

    def run(self) -> int:
        """
        Run the complete setup process.

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        platformName = self.system.getPlatformName()

        # Print header
        printSection(f"jrl_env Setup for {platformName.capitalize()}")
        printInfo(f"Log file: {self.logFile}")

        if self.setupArgs.dryRun:
            printSection("DRY RUN MODE")
            printWarning("No changes will be made. This is a preview.")

        # Handle resume logic
        if not self.initialiseState():
            return 1

        # Validate configs
        paths = self.configManager.getPaths()
        platformConfigPath = Path(paths["platformConfigPath"])
        self.validationEngine.validateAll(platformConfigPath)

        # Run pre-install commands
        runConfigCommands("preInstall", paths["platformConfigPath"])
        safePrint()

        # Check dependencies and backup configs
        if not self.checkDependenciesAndBackup(paths):
            return 1

        # Create rollback session
        if not self.setupArgs.dryRun:
            backupDir = getattr(self, 'backupDir', None)
            self.rollbackSession = createSession(backupDir)

        printInfo("Starting complete environment setup...")
        safePrint()

        # Execute setup steps
        if not self.executeSetupSteps(paths):
            return 1

        # Run post-install commands
        runConfigCommands("postInstall", paths["platformConfigPath"])
        safePrint()

        # Save rollback session
        if self.rollbackSession and not self.setupArgs.dryRun:
            sessionFile = saveSession(self.rollbackSession)
            printInfo(f"Rollback session saved: {sessionFile}")

        # Run verification
        if not self.setupArgs.dryRun:
            safePrint()
            from common.systems.verify import runVerification

            runVerification(self.system)
            safePrint()

        # Clear setup state on successful completion
        if self.setupState and not self.setupArgs.dryRun:
            clearState(platformName)
            printInfo("Setup state cleared (setup completed successfully)")

        # Print completion message
        self.printCompletionMessage()

        return 0

    def initialiseState(self) -> bool:
        """
        Initialise or resume setup state.

        Returns:
            True if initialisation successful, False otherwise
        """
        platformName = self.system.getPlatformName()
        existingState = loadState(platformName) if not self.setupArgs.dryRun else None
        shouldResume = False

        if existingState and not self.setupArgs.noResume:
            if self.setupArgs.resume:
                shouldResume = True
            else:
                shouldResume = self.promptResume(existingState)

        if shouldResume and existingState:
            printSection("Resuming Setup")
            printInfo(
                f"Resuming from session: {existingState.sessionId}\n"
                f"Skipping completed steps: {', '.join(sorted(existingState.completedSteps)) or 'None'}"
            )
            self.setupState = existingState
            safePrint()
        else:
            if existingState and not shouldResume:
                clearState(platformName)
            self.setupState = createState(platformName) if not self.setupArgs.dryRun else None

        return True

    def promptResume(self, existingState: SetupState) -> bool:
        """
        Prompt user if they want to resume from previous setup.

        Args:
            existingState: Previous setup state

        Returns:
            True if user wants to resume, False otherwise
        """
        printSection("Previous Setup Detected")
        printInfo(f"Found incomplete setup from {existingState.timestamp}")
        if existingState.failedAtStep:
            printInfo(f"Setup failed at: {existingState.failedAtStep}")
        printInfo(f"Completed steps: {', '.join(sorted(existingState.completedSteps)) or 'None'}\n")
        safePrint()
        print("Would you like to resume from the last successful step? (y/n): ", end="", flush=True)
        try:
            response = input().strip().lower()
            return response in ('y', 'yes')
        except (EOFError, KeyboardInterrupt):
            return False
        finally:
            safePrint()

    def checkDependenciesAndBackup(self, paths: Dict[str, str]) -> bool:
        """
        Check dependencies and backup config files.

        Args:
            paths: Dictionary of config paths

        Returns:
            True if successful, False otherwise
        """
        if self.setupArgs.dryRun:
            return True

        dependencyCheckers = self.system.getOptionalDependencyCheckers()
        if not checkDependencies(self.system.getRequiredDependencies(), dependencyCheckers):
            return False

        self.backupDir = backupConfigs(
            self.setupArgs.noBackup,
            self.setupArgs.dryRun,
            paths["cursorSettingsPath"]
        )
        safePrint()
        return True

    def executeSetupSteps(self, paths: Dict[str, str]) -> bool:
        """
        Execute all setup steps in sequence.

        Note: This method's step sequence matches the canonical definitions in
        common.systems.stepDefinitions. If you modify steps here, update that module too.

        Args:
            paths: Dictionary of config paths

        Returns:
            True if successful, False otherwise
        """
        # Run pre-setup steps
        if not self.system.runPreSetupSteps():
            printWarning("Pre-setup steps had some issues, continuing...")
        safePrint()

        # Step 1: Setup development environment
        self.executeStep(
            stepName="devEnv",
            stepNumber="1",
            description="Setting up development environment",
            action=lambda: self.system.setupDevEnv(),
        )

        # Step 2: Install fonts
        if self.runFlags.runFonts:
            self.executeStep(
                stepName="fonts",
                stepNumber="2",
                description="Installing fonts",
                action=lambda: self.system.installGoogleFonts(
                    paths["fontsConfigPath"],
                    paths["fontInstallDir"],
                    self.setupArgs.dryRun
                ),
            )

        # Step 3: Install applications
        if self.runFlags.runApps:
            self.executeAppInstallation(paths)

        # Step 3.5: Configure Android (if applicable)
        self.executeAndroidConfiguration(paths)

        # Step 4: Configure Git
        if self.runFlags.runGit:
            self.executeGitConfiguration(paths)

        # Step 5: Configure GitHub SSH
        if self.runFlags.runSsh:
            self.executeSshConfiguration(paths)

        # Step 6: Configure Cursor
        if self.runFlags.runCursor:
            self.executeCursorConfiguration(paths)

        # Step 7: Clone repositories
        if self.runFlags.runRepos:
            self.executeRepositoryCloning(paths)

        # Run post-setup steps
        if not self.system.runPostSetupSteps():
            printWarning("Post-setup steps had some issues, continuing...")
        safePrint()

        return True

    def executeStep(
        self,
        stepName: str,
        stepNumber: str,
        description: str,
        action: callable,
        trackInRollback: Optional[callable] = None,
    ) -> bool:
        """
        Execute a single setup step with state tracking.

        Args:
            stepName: Internal step name for state tracking
            stepNumber: Step number for display
            description: Human-readable step description
            action: Function to execute for this step
            trackInRollback: Optional function to track changes in rollback session

        Returns:
            True if step succeeded, False otherwise
        """
        if isStepComplete(self.setupState, stepName):
            printSection(
                f"Step {stepNumber}: {description} (SKIPPED - already completed)",
                dryRun=self.setupArgs.dryRun
            )
            printInfo(f"{description} was already completed in a previous run.")
            safePrint()
            return True

        printSection(f"Step {stepNumber}: {description}", dryRun=self.setupArgs.dryRun)
        try:
            result = action()
            if not result:
                printWarning(f"{description} had some issues, continuing...")
            else:
                printSuccess(f"{description} completed")
                if self.setupState:
                    markStepComplete(self.setupState, stepName)
                if trackInRollback and self.rollbackSession:
                    trackInRollback()
        except Exception as e:
            if self.setupState:
                markStepFailed(self.setupState, stepName)
            raise
        finally:
            safePrint()

        return True

    def executeAppInstallation(self, paths: Dict[str, str]) -> None:
        """Execute application installation step."""
        stepName = "apps"
        if isStepComplete(self.setupState, stepName):
            printSection(
                "Step 3: Installing applications (SKIPPED - already completed)",
                dryRun=self.setupArgs.dryRun
            )
            printInfo("Application installation was already completed in a previous run.")
            safePrint()
            return

        printSection("Step 3: Installing applications", dryRun=self.setupArgs.dryRun)
        try:
            installResult = self.system.installOrUpdateApps(
                paths["platformConfigPath"],
                self.setupArgs.dryRun
            )
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
        finally:
            safePrint()

    def executeAndroidConfiguration(self, paths: Dict[str, str]) -> None:
        """Execute Android SDK configuration step if applicable."""
        stepName = "android"
        androidConfigPath = paths.get("androidConfigPath")

        if not androidConfigPath or not Path(androidConfigPath).exists():
            return

        shouldConfigureAndroid = self.shouldConfigureAndroid(paths, androidConfigPath)

        if not shouldConfigureAndroid:
            return

        if isStepComplete(self.setupState, stepName):
            printSection(
                "Step 3.5: Configuring Android SDK (SKIPPED - already completed)",
                dryRun=self.setupArgs.dryRun
            )
            printInfo("Android SDK configuration was already completed in a previous run.")
            safePrint()
            return

        printSection("Step 3.5: Configuring Android SDK", dryRun=self.setupArgs.dryRun)
        try:
            platformAndroidConfig = None
            platformAndroid = getJsonObject(paths["platformConfigPath"], ".android")
            if platformAndroid:
                platformAndroidConfig = paths["platformConfigPath"]

            androidSuccess = configureAndroid(
                configPath=androidConfigPath if not platformAndroidConfig else None,
                platformConfigPath=platformAndroidConfig if platformAndroidConfig else paths["platformConfigPath"],
                dryRun=self.setupArgs.dryRun
            )
            if not androidSuccess:
                printWarning("Android SDK configuration had some issues, continuing...")
            else:
                printSuccess("Android SDK configuration completed")
                if self.setupState:
                    markStepComplete(self.setupState, stepName)
        except Exception as e:
            if self.setupState:
                markStepFailed(self.setupState, stepName)
            printWarning(f"Android configuration error: {e}")
        finally:
            safePrint()

    def shouldConfigureAndroid(self, paths: Dict[str, str], androidConfigPath: str) -> bool:
        """
        Determine if Android configuration should run.

        Args:
            paths: Dictionary of config paths
            androidConfigPath: Path to android.json

        Returns:
            True if Android configuration should run, False otherwise
        """
        androidInConfig = checkAndroidStudioInConfig(paths["platformConfigPath"])
        androidInstalled = isAndroidStudioInstalled()

        if androidInConfig or androidInstalled:
            return True

        if self.setupArgs.dryRun:
            printInfo("[DRY RUN] Would check Android Studio installation and prompt for Android configuration")
            return True

        printSection("Android Configuration Check")
        printInfo("Android Studio is not installed and not in your platform config.")
        printInfo("Would you like to configure Android SDK components?")
        printInfo("(Note: You'll need to install Android Studio separately if not already installed)")
        safePrint()
        print("Configure Android SDK? (y/n): ", end="", flush=True)
        try:
            response = input().strip().lower()
            return response in ('y', 'yes')
        except (EOFError, KeyboardInterrupt):
            return False
        finally:
            safePrint()

    def executeGitConfiguration(self, paths: Dict[str, str]) -> None:
        """Execute Git configuration step."""
        stepName = "git"
        if isStepComplete(self.setupState, stepName):
            printSection(
                "Step 4: Configuring Git (SKIPPED - already completed)",
                dryRun=self.setupArgs.dryRun
            )
            printInfo("Git configuration was already completed in a previous run.")
            safePrint()
            return

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
        finally:
            safePrint()

    def executeSshConfiguration(self, paths: Dict[str, str]) -> None:
        """Execute GitHub SSH configuration step."""
        stepName = "ssh"
        if isStepComplete(self.setupState, stepName):
            printSection(
                "Step 5: Configuring GitHub SSH (SKIPPED - already completed)",
                dryRun=self.setupArgs.dryRun
            )
            printInfo("GitHub SSH configuration was already completed in a previous run.")
            safePrint()
            return

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
        finally:
            safePrint()

    def executeCursorConfiguration(self, paths: Dict[str, str]) -> None:
        """Execute Cursor editor configuration step."""
        stepName = "cursor"
        if isStepComplete(self.setupState, stepName):
            printSection(
                "Step 6: Configuring Cursor (SKIPPED - already completed)",
                dryRun=self.setupArgs.dryRun
            )
            printInfo("Cursor configuration was already completed in a previous run.")
            safePrint()
            return

        printSection("Step 6: Configuring Cursor", dryRun=self.setupArgs.dryRun)
        try:
            cursorSuccess = configureCursor(
                paths["cursorConfigPath"],
                paths["cursorSettingsPath"],
                dryRun=self.setupArgs.dryRun
            )
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
        finally:
            safePrint()

    def executeRepositoryCloning(self, paths: Dict[str, str]) -> None:
        """Execute repository cloning step."""
        stepName = "repos"
        if isStepComplete(self.setupState, stepName):
            printSection(
                "Step 7: Cloning repositories (SKIPPED - already completed)",
                dryRun=self.setupArgs.dryRun
            )
            printInfo("Repository cloning was already completed in a previous run.")
            safePrint()
            return

        printSection("Step 7: Cloning repositories", dryRun=self.setupArgs.dryRun)
        try:
            if self.setupArgs.dryRun or shouldCloneRepositories(
                paths["reposConfigPath"],
                self.system.getRepositoryWorkPathKey()
            ):
                if not cloneRepositories(paths["reposConfigPath"], dryRun=self.setupArgs.dryRun):
                    printWarning("Repository cloning had some issues, continuing...")
                else:
                    printSuccess("Repository cloning completed")
                    if self.setupState:
                        markStepComplete(self.setupState, stepName)
            else:
                printWarning("Repositories directory already exists with content. Skipping repository cloning.")
                printInfo(
                    f"To clone repositories manually, run: "
                    f"python3 -m common.systems.cli {self.system.getPlatformName()} repos"
                )
                if self.setupState:
                    markStepComplete(self.setupState, stepName)
        except Exception as e:
            if self.setupState:
                markStepFailed(self.setupState, stepName)
            raise
        finally:
            safePrint()

    def printCompletionMessage(self) -> None:
        """Print setup completion message."""
        printSection("Setup Complete")
        printInfo("All setup tasks have been executed.")
        printInfo(f"Log file saved to: {self.logFile}")
        if self.rollbackSession and not self.setupArgs.dryRun:
            printInfo(
                f"To rollback this setup, run: "
                f"python3 -m common.systems.cli {self.system.getPlatformName()} rollback"
            )
        printInfo("Please review any warnings above and restart your terminal if needed.")
