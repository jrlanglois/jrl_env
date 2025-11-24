#!/usr/bin/env python3
"""
Auto-installer for shell completions.
Automatically installs tab completion without user intervention.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional


def detectShell() -> Optional[str]:
    """
    Detect the current shell.

    Returns:
        Shell name ('bash', 'zsh', 'powershell') or None if unknown
    """
    shell = os.environ.get('SHELL', '')

    if 'zsh' in shell:
        return 'zsh'
    elif 'bash' in shell:
        return 'bash'
    elif 'POWERSHELL' in os.environ or 'PSModulePath' in os.environ:
        return 'powershell'

    return None


def getShellConfigFile() -> Optional[Path]:
    """
    Get the shell configuration file path.

    Returns:
        Path to shell config file or None if not found
    """
    shell = detectShell()

    if shell == 'zsh':
        return Path.home() / '.zshrc'
    elif shell == 'bash':
        # Try .bashrc first, then .bash_profile
        bashrc = Path.home() / '.bashrc'
        if bashrc.exists():
            return bashrc
        return Path.home() / '.bash_profile'
    elif shell == 'powershell':
        # PowerShell profile path
        try:
            result = subprocess.run(
                ['pwsh', '-NoProfile', '-Command', 'echo $PROFILE'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                return Path(result.stdout.strip())
        except Exception:
            pass

    return None


def isCompletionInstalled(configFile: Path, marker: str) -> bool:
    """
    Check if completion is already installed.

    Args:
        configFile: Shell configuration file
        marker: Marker string to search for

    Returns:
        True if completion is installed, False otherwise
    """
    if not configFile.exists():
        return False

    try:
        content = configFile.read_text(encoding='utf-8')
        return marker in content
    except Exception:
        return False


def installBashCompletion(projectRoot: Path) -> bool:
    """
    Install bash completion automatically.

    Args:
        projectRoot: Root directory of jrl_env project

    Returns:
        True if successful, False otherwise
    """
    shell = detectShell()
    if shell not in ('bash', 'zsh'):
        return False

    configFile = getShellConfigFile()
    if not configFile:
        return False

    completionScript = projectRoot / 'completions' / 'jrl_env.bash'
    if not completionScript.exists():
        return False

    marker = '# jrl_env completion'

    # Check if already installed
    if isCompletionInstalled(configFile, marker):
        return True

    try:
        # Ensure config file exists
        configFile.parent.mkdir(parents=True, exist_ok=True)
        configFile.touch(exist_ok=True)

        # Add completion source line
        sourceCommand = f'\n{marker}\n'
        if shell == 'zsh':
            sourceCommand += 'autoload -U +X bashcompinit && bashcompinit\n'
        sourceCommand += f'source "{completionScript}"\n'

        with open(configFile, 'a', encoding='utf-8') as f:
            f.write(sourceCommand)

        return True
    except Exception:
        return False


def installPowershellCompletion(projectRoot: Path) -> bool:
    """
    Install PowerShell completion automatically.

    Args:
        projectRoot: Root directory of jrl_env project

    Returns:
        True if successful, False otherwise
    """
    if detectShell() != 'powershell':
        return False

    configFile = getShellConfigFile()
    if not configFile:
        return False

    completionScript = projectRoot / 'completions' / 'jrl_env.ps1'
    if not completionScript.exists():
        return False

    marker = '# jrl_env completion'

    # Check if already installed
    if isCompletionInstalled(configFile, marker):
        return True

    try:
        # Ensure profile exists
        configFile.parent.mkdir(parents=True, exist_ok=True)
        configFile.touch(exist_ok=True)

        # Add completion source line
        sourceCommand = f'\n{marker}\n. "{completionScript}"\n'

        with open(configFile, 'a', encoding='utf-8') as f:
            f.write(sourceCommand)

        return True
    except Exception:
        return False


def autoInstallCompletion(projectRoot: Optional[Path] = None) -> bool:
    """
    Automatically install shell completion based on detected shell.
    Idempotent - safe to call multiple times.

    Args:
        projectRoot: Root directory of jrl_env project (auto-detected if None)

    Returns:
        True if completion was installed or already present, False if failed
    """
    if projectRoot is None:
        # Try to detect project root
        thisFile = Path(__file__).resolve()
        projectRoot = thisFile.parent.parent.parent

    shell = detectShell()

    if shell in ('bash', 'zsh'):
        return installBashCompletion(projectRoot)
    elif shell == 'powershell':
        return installPowershellCompletion(projectRoot)

    # Unknown shell or no completion needed
    return True


__all__ = [
    'detectShell',
    'autoInstallCompletion',
]
