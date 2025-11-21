#!/usr/bin/env python3
"""
Signal handling utilities for graceful shutdown.
Handles CTRL+C and other termination signals cleanly.
"""

import signal
import sys


def setupSignalHandlers(resumeMessage: bool = True) -> None:
    """
    Set up signal handlers for graceful shutdown on CTRL+C and SIGTERM.

    Args:
        resumeMessage: If True, show resume message on interrupt
    """
    def signalHandler(signum, frame):
        """Handle CTRL+C and other signals gracefully."""
        from common.core.logging import printWarning, printInfo, safePrint

        safePrint()
        safePrint()
        printWarning("Process interrupted by user (CTRL+C)")

        if resumeMessage:
            printInfo("Operation was not completed. You can resume later with: python3 setup.py --resume")

        safePrint()
        sys.exit(130)  # Standard exit code for SIGINT

    # Register handlers
    signal.signal(signal.SIGINT, signalHandler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signalHandler)


__all__ = [
    "setupSignalHandlers",
]
