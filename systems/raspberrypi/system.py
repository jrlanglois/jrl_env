#!/usr/bin/env python3
"""
Raspberry Pi system setup implementation.
"""

import sys
from pathlib import Path

# Add project root to path so we can import from common
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent.parent
sys.path.insert(0, str(projectRoot))

from common.systems.genericSystem import GenericSystem
from common.systems.platform import Platform


def main() -> int:
    """Main entry point for Raspberry Pi setup."""
    system = GenericSystem(projectRoot, Platform.raspberrypi)
    return system.run()


if __name__ == "__main__":
    sys.exit(main())
