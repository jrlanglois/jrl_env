#!/usr/bin/env python3
"""
Sudo management for elevated permissions.
Prompts once upfront with security warning.
"""

import subprocess
from common.core.logging import printInfo, printWarning, printError, safePrint
from common.systems.platform import isWindows


class SudoManager:
    """Manages sudo credentials and caching."""

    def __init__(self, dryRun: bool = False):
        """
        Initialise sudo manager.

        Args:
            dryRun: If True, skip actual sudo operations
        """
        self.dryRun = dryRun
        self.validated = False

    def isNeeded(self) -> bool:
        """
        Determine if sudo is needed for this platform.

        Returns:
            True if sudo may be needed, False otherwise
        """
        # Windows doesn't use sudo
        return not isWindows()

    def validate(self) -> bool:
        """
        Validate and cache sudo credentials upfront.
        Shows security warning and prompts for password once.

        Returns:
            True if sudo is available or not needed, False if sudo failed
        """
        if not self.isNeeded():
            return True

        if self.validated:
            return True  # Already validated

        if self.dryRun:
            printInfo("[DRY RUN] Would validate sudo credentials")
            self.validated = True
            return True

        safePrint()
        printWarning("SECURITY NOTICE:")
        printInfo(
            "This setup requires elevated permissions (sudo) for:\n"
            "  • Installing packages via system package managers\n"
            "  • Configuring system-level settings\n"
            "  • Managing system directories and files\n"
            "\n"
            "You will be prompted for your password once.\n"
            "Your credentials will be cached for the duration of this setup."
        )
        safePrint()

        printInfo("Validating sudo access...")
        try:
            # Run sudo -v to validate and cache credentials
            result = subprocess.run(
                ["sudo", "-v"],
                check=False,
                capture_output=False  # Let password prompt show
            )

            if result.returncode == 0:
                printInfo("✓ Sudo access validated")
                safePrint()
                self.validated = True
                return True

            # User refused or sudo failed
            printWarning("Sudo validation failed or was cancelled")
            printInfo(
                "Without sudo access, the following operations will fail:\n"
                "  • Package installation via system package managers\n"
                "  • System configuration changes\n"
                "\n"
                "You can continue, but expect errors during installation steps."
            )
            safePrint()

            # Ask user if they want to continue
            try:
                response = input("Continue without sudo? (y/N): ").strip().lower()
                if response in ('y', 'yes'):
                    printInfo("Continuing without sudo - expect limited functionality")
                    safePrint()
                    return True  # User chooses to continue
                else:
                    printError("Setup cancelled - sudo is required for package installation")
                    return False
            except (EOFError, KeyboardInterrupt):
                printError("\nSetup cancelled by user")
                return False

        except KeyboardInterrupt:
            printError("\nSudo validation cancelled by user")
            printInfo("Setup cannot proceed without sudo access for package installation.")
            return False
        except Exception as e:
            printWarning(f"Could not validate sudo: {e}")
            printInfo("Continuing anyway - operations will prompt for password as needed.")
            safePrint()
            return True  # Non-fatal

    def keepAlive(self) -> None:
        """
        Refresh sudo timestamp to keep credentials cached.
        Call this periodically during long-running operations.
        """
        if not self.isNeeded() or self.dryRun or not self.validated:
            return

        try:
            subprocess.run(
                ["sudo", "-v"],
                check=False,
                capture_output=True,
                timeout=1
            )
        except Exception:
            pass  # Non-fatal if refresh fails


__all__ = [
    'SudoManager',
]
