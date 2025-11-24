#!/usr/bin/env python3
"""
Argcomplete setup for Python-based tab completion.
Provides completers for setup.py and CLI arguments.
"""

try:
    import argcomplete
    argcompleteAvailable = True
except ImportError:
    argcompleteAvailable = False


def getInstallTargetCompleter():
    """Get completer for install targets."""
    return ['all', 'fonts', 'apps', 'git', 'cursor', 'repos', 'ssh']


def getUpdateTargetCompleter():
    """Get completer for update targets."""
    return ['all', 'apps', 'system']


def getPassphraseModeCompleter():
    """Get completer for passphrase modes."""
    return ['require', 'no']


def getPlatformCompleter():
    """Get completer for platforms."""
    return [
        'macos', 'win11',
        'ubuntu', 'debian', 'popos', 'linuxmint', 'elementary', 'zorin', 'mxlinux', 'raspberrypi',
        'fedora', 'redhat',
        'opensuse',
        'archlinux', 'manjaro', 'endeavouros',
        'alpine'
    ]


def getOperationCompleter():
    """Get completer for CLI operations."""
    return ['fonts', 'apps', 'git', 'ssh', 'cursor', 'repos', 'status', 'rollback', 'verify', 'update']


def enableArgcomplete():
    """
    Enable argcomplete if available.
    Call this early in your main() function.

    Returns:
        True if argcomplete is available and enabled, False otherwise
    """
    if not argcompleteAvailable:
        return False

    try:
        # Enable global completion
        argcomplete.autocomplete(None)
        return True
    except Exception:
        return False


__all__ = [
    'argcompleteAvailable',
    'getInstallTargetCompleter',
    'getUpdateTargetCompleter',
    'getPassphraseModeCompleter',
    'getPlatformCompleter',
    'getOperationCompleter',
    'enableArgcomplete',
]
