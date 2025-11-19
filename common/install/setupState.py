#!/usr/bin/env python3
"""
Setup state tracking for resuming failed setups.
Tracks completed steps to allow resuming from the last successful step.
"""

import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Set

# Add project root to path
scriptDir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(scriptDir))

from common.core.logging import printError, printInfo, printWarning


@dataclass
class SetupState:
    """State tracking for setup progress."""
    platformName: str
    sessionId: str
    timestamp: str
    completedSteps: Set[str] = None
    failedAtStep: Optional[str] = None

    def __post_init__(self):
        if self.completedSteps is None:
            self.completedSteps = set()


def getStateDir() -> Path:
    """Get the directory for storing setup state files."""
    if sys.platform == "win32":
        baseDir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        baseDir = Path.home() / ".cache"
    stateDir = baseDir / "jrl_env" / "setup_state"
    stateDir.mkdir(parents=True, exist_ok=True)
    return stateDir


def createState(platformName: str) -> SetupState:
    """
    Create a new setup state.

    Args:
        platformName: Platform name (e.g., "ubuntu", "macos", "win11")

    Returns:
        SetupState instance
    """
    sessionId = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp = datetime.now().isoformat()

    state = SetupState(
        platformName=platformName,
        sessionId=sessionId,
        timestamp=timestamp,
    )
    return state


def saveState(state: SetupState) -> Path:
    """
    Save setup state to a file.

    Args:
        state: SetupState to save

    Returns:
        Path to the saved state file
    """
    stateDir = getStateDir()
    stateFile = stateDir / f"{state.platformName}_{state.sessionId}.json"

    # Convert set to list for JSON serialisation
    stateDict = asdict(state)
    stateDict["completedSteps"] = list(state.completedSteps)

    with open(stateFile, 'w', encoding='utf-8') as f:
        json.dump(stateDict, f, indent=4)

    return stateFile


def loadState(platformName: str) -> Optional[SetupState]:
    """
    Load the most recent setup state for a platform.

    Args:
        platformName: Platform name

    Returns:
        SetupState if found, None otherwise
    """
    stateDir = getStateDir()
    stateFiles = sorted(stateDir.glob(f"{platformName}_*.json"), reverse=True)

    if not stateFiles:
        return None

    # Load the most recent state file
    stateFile = stateFiles[0]
    try:
        with open(stateFile, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert list back to set
        if "completedSteps" in data:
            data["completedSteps"] = set(data["completedSteps"])

        return SetupState(**data)
    except Exception as e:
        printWarning(f"Failed to load setup state from {stateFile}: {e}")
        return None


def clearState(platformName: str) -> bool:
    """
    Clear setup state for a platform.

    Args:
        platformName: Platform name

    Returns:
        True if state was cleared, False otherwise
    """
    stateDir = getStateDir()
    stateFiles = list(stateDir.glob(f"{platformName}_*.json"))

    if not stateFiles:
        return False

    try:
        for stateFile in stateFiles:
            stateFile.unlink()
        return True
    except Exception as e:
        printError(f"Failed to clear setup state: {e}")
        return False


def markStepComplete(state: SetupState, stepName: str) -> None:
    """
    Mark a setup step as completed.

    Args:
        state: SetupState instance
        stepName: Name of the completed step
    """
    state.completedSteps.add(stepName)
    saveState(state)


def isStepComplete(state: Optional[SetupState], stepName: str) -> bool:
    """
    Check if a setup step has been completed.

    Args:
        state: SetupState instance (can be None)
        stepName: Name of the step to check

    Returns:
        True if step is completed, False otherwise
    """
    if state is None:
        return False
    return stepName in state.completedSteps


def markStepFailed(state: SetupState, stepName: str) -> None:
    """
    Mark a setup step as failed.

    Args:
        state: SetupState instance
        stepName: Name of the failed step
    """
    state.failedAtStep = stepName
    saveState(state)
