#!/usr/bin/env python3
"""
Platform enumeration for jrl_env.
Provides type-safe platform identifiers.
"""

from enum import Enum


class Platform(Enum):
    """Supported platform identifiers."""
    macos = "macos"
    ubuntu = "ubuntu"
    archlinux = "archlinux"
    opensuse = "opensuse"
    redhat = "redhat"
    raspberrypi = "raspberrypi"
    win11 = "win11"

    def __str__(self) -> str:
        """Return the string value of the platform."""
        return self.value


__all__ = [
    "Platform",
]
