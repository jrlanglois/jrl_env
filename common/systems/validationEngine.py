#!/usr/bin/env python3
"""
Configuration validation engine for jrl_env setup.
Centralises all validation logic and user prompts.
"""

from pathlib import Path
from typing import Optional

from common.common import printError, printInfo, printSection, printSuccess, printWarning, safePrint
from common.install.setupArgs import SetupArgs


class ValidationEngine:
    """
    Handles all configuration validation logic.
    Validates config files, directories, and prompts user for unknown fields.
    """

    def __init__(self, platformName: str, setupArgs: Optional[SetupArgs] = None):
        """
        Initialise the validation engine.

        Args:
            platformName: Platform name (e.g., "macos", "ubuntu")
            setupArgs: Optional setup arguments (for dry-run mode)
        """
        self.platformName = platformName
        self.setupArgs = setupArgs

    def validateAll(self, platformConfigPath: Path) -> bool:
        """
        Validate all configuration files.

        Args:
            platformConfigPath: Path to platform-specific config file

        Returns:
            True if validation passed, False otherwise

        Raises:
            SystemExit: If validation fails with errors
        """
        printSection("Validating Configuration Files")
        safePrint()

        # Validate config directory exists and is accessible
        configsDir = platformConfigPath.parent

        if not self.validateConfigDirectory(configsDir):
            printError(
                "Configuration directory validation failed!\n"
                "Please fix the issues above before continuing."
            )
            safePrint()
            raise SystemExit(1)

        # Validate platform config file exists and is valid
        if not self.validatePlatformConfig(platformConfigPath):
            printError(
                "Platform configuration validation failed!\n"
                "Please fix the issues above before continuing."
            )
            safePrint()
            raise SystemExit(1)

        # Run full validation (includes shared configs)
        printInfo("Running full configuration validation...")
        safePrint()
        try:
            import sys
            from common.systems.validate import main as validateMain, collectUnknownFieldErrors

            # Save original sys.argv and temporarily replace it
            originalArgv = sys.argv
            try:
                # Call validation with just the platform name
                sys.argv = ['validate', self.platformName]
                result = validateMain()
            finally:
                # Restore original sys.argv
                sys.argv = originalArgv

            if result == 1:
                # Critical errors (not unknown fields)
                printError(
                    "Configuration validation failed!\n"
                    "Please fix the errors above before continuing.\n"
                    "Run 'python3 -m common.systems.validate' for detailed validation."
                )
                safePrint()
                raise SystemExit(1)
            elif result == 2:
                # Unknown fields detected - prompt user
                unknownFieldErrors = collectUnknownFieldErrors(configsDir, self.platformName)

                printWarning("Unknown fields detected in your configuration files:")
                for error in unknownFieldErrors:
                    printWarning(f"  - {error}")
                safePrint()
                printWarning("These fields are not recognised by jrl_env and will be ignored.")
                printInfo(
                    "If you continue, setup will proceed but these fields will have no effect.\n"
                )
                safePrint()

                # Prompt user
                if self.setupArgs and self.setupArgs.dryRun:
                    printInfo(
                        "Dry-run mode: Would prompt to continue (y/n)\n"
                        "Proceeding with dry-run..."
                    )
                else:
                    if not self.promptUserToContinue():
                        printError(
                            "Setup cancelled by user due to unknown configuration fields.\n"
                            "Please remove or fix the unknown fields and try again."
                        )
                        safePrint()
                        raise SystemExit(1)
                    printInfo("User chose to continue despite unknown fields.")
                safePrint()

        except SystemExit:
            raise
        except Exception as e:
            printError(
                f"Could not run validation script: {e}\n"
                "This is a critical error. Please report this issue."
            )
            safePrint()
            raise SystemExit(1)

        printSuccess("All configuration files validated successfully!")
        safePrint()
        return True

    def validateConfigDirectory(self, configsDir: Path) -> bool:
        """
        Validate that config directory exists and is accessible.

        Args:
            configsDir: Path to configs directory

        Returns:
            True if validation passed, False otherwise
        """
        from common.systems.validate import validateConfigDirectory

        return validateConfigDirectory(configsDir, self.platformName)

    def validatePlatformConfig(self, platformConfigPath: Path) -> bool:
        """
        Validate that platform config file exists and is valid.

        Args:
            platformConfigPath: Path to platform-specific config file

        Returns:
            True if validation passed, False otherwise
        """
        from common.systems.validate import validatePlatformConfig

        return validatePlatformConfig(platformConfigPath, self.platformName)

    def promptUserToContinue(self) -> bool:
        """
        Prompt user to continue despite unknown fields.

        Returns:
            True if user wants to continue, False otherwise
        """
        print("Do you want to continue anyway? (y/n): ", end="", flush=True)
        try:
            response = input().strip().lower()
            return response in ('y', 'yes')
        except (EOFError, KeyboardInterrupt):
            printError("\nSetup cancelled by user.")
            return False
