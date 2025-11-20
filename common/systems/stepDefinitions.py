#!/usr/bin/env python3
"""
Centralised step definitions for jrl_env setup.
Defines the canonical sequence of setup steps used by both listSteps and orchestrator.
"""

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class SetupStep:
    """Defines a single setup step."""
    stepName: str  # Internal name for state tracking (e.g., "devEnv", "fonts")
    stepNumber: str  # Display number (e.g., "1", "2", "3.5")
    description: str  # Human-readable description
    isConditional: bool = False  # If True, step may be skipped based on runFlags
    flagAttribute: Optional[str] = None  # RunFlags attribute to check (e.g., "runFonts")


# Canonical step definitions
# This is the single source of truth for setup step sequence
setupSteps = [
    SetupStep("preSetup", "Pre-setup", "Run pre-setup steps", isConditional=False),
    SetupStep("devEnv", "1", "Setup development environment", isConditional=False),
    SetupStep("fonts", "2", "Install fonts", isConditional=True, flagAttribute="runFonts"),
    SetupStep("apps", "3", "Install/update applications", isConditional=True, flagAttribute="runApps"),
    SetupStep("android", "3.5", "Configure Android SDK", isConditional=True, flagAttribute="runApps"),  # Special: runs conditionally within apps
    SetupStep("git", "4", "Configure Git", isConditional=True, flagAttribute="runGit"),
    SetupStep("ssh", "5", "Configure GitHub SSH", isConditional=True, flagAttribute="runSsh"),
    SetupStep("cursor", "6", "Configure Cursor editor", isConditional=True, flagAttribute="runCursor"),
    SetupStep("repos", "7", "Clone repositories", isConditional=True, flagAttribute="runRepos"),
    SetupStep("postSetup", "Post-setup", "Run post-setup steps", isConditional=False),
]


def getStepsToRun(runFlags) -> list[SetupStep]:
    """
    Get the list of steps that will run based on runFlags.

    Args:
        runFlags: RunFlags instance with boolean flags

    Returns:
        List of SetupStep objects that will be executed
    """
    stepsToRun = []

    for step in setupSteps:
        if not step.isConditional:
            stepsToRun.append(step)
        elif step.flagAttribute and hasattr(runFlags, step.flagAttribute):
            if getattr(runFlags, step.flagAttribute):
                stepsToRun.append(step)

    return stepsToRun


def willAnyStepsRun(runFlags) -> bool:
    """
    Check if any conditional steps will run.

    Args:
        runFlags: RunFlags instance

    Returns:
        True if at least one conditional step will run
    """
    return any(
        step.flagAttribute and hasattr(runFlags, step.flagAttribute) and getattr(runFlags, step.flagAttribute)
        for step in setupSteps
        if step.isConditional
    )


__all__ = [
    "SetupStep",
    "setupSteps",
    "getStepsToRun",
    "willAnyStepsRun",
]
