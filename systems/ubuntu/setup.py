#!/usr/bin/env python3
"""
Master setup script for Ubuntu.
Runs all configuration and installation scripts in the correct order.
"""

import sys
from pathlib import Path

# Add project root to path so we can import from common
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent.parent
sys.path.insert(0, str(projectRoot))

from systems.ubuntu.system import UbuntuSystem


def main() -> int:
    """Main setup function."""
    system = UbuntuSystem(projectRoot)
    return system.run()


if __name__ == "__main__":
    sys.exit(main())
