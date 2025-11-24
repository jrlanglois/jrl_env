#!/usr/bin/env python3
"""
Documentation generation script for jrl_env using Sphinx.
Automatically sets up and builds comprehensive documentation.
"""

import os
import subprocess
import sys
from pathlib import Path

# Add project root to path
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent
sys.path.insert(0, str(projectRoot))

from common.common import (
    printError,
    printInfo,
    printHeading,
    printSuccess,
    printWarning,
    safePrint,
)
from common.core.logging import setVerbosityFromArgs, getVerbosity, Verbosity, printHelpText


def printHelp() -> None:
    """Print help information."""
    printHelpText(
        title="generateDocs.py",
        intent=[
            "Generate comprehensive documentation for jrl_env using Sphinx.",
            "Creates API documentation from docstrings, including call graphs and module structure.",
        ],
        usage="python3 docs/generateDocs.py [options]",
        options=[
            ("--help, -h", "Show this help message and exit"),
            ("--clean", "Clean existing documentation (remove _build directory)"),
            ("--noOpen", "Skip opening browser after building (default: auto-open)"),
            ("--quiet, -q", "Only show final success/failure message"),
        ],
        examples=[
            "python3 docs/generateDocs.py",
            "python3 docs/generateDocs.py --clean",
            "python3 docs/generateDocs.py --noOpen",
        ],
    )


def checkSphinxInstalled() -> bool:
    """Check if Sphinx is installed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "sphinx", "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def installSphinx() -> bool:
    """Install Sphinx and dependencies."""
    printInfo("Installing Sphinx and dependencies...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(projectRoot / "requirements.txt")],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            printSuccess("Sphinx installed successfully")
            return True
        else:
            printError(f"Failed to install Sphinx: {result.stderr}")
            return False
    except Exception as e:
        printError(f"Failed to install Sphinx: {e}")
        return False


def setupSphinxConfig() -> bool:
    """Set up Sphinx configuration if not already present."""
    docsDir = projectRoot / "docs"
    confFile = docsDir / "conf.py"

    if confFile.exists():
        printInfo("Sphinx configuration already exists")
        return True

    printInfo("Setting up Sphinx configuration...")

    # Create docs directory
    docsDir.mkdir(exist_ok=True)

    # Create conf.py
    confContent = '''# Configuration file for Sphinx documentation builder

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# Project information
project = 'jrl_env'
copyright = '2025, Joël R. Langlois'
author = 'Joël R. Langlois'
release = '1.0.0'

# Language and spelling
# Note: This project uses Canadian English spelling conventions:
# - Verbs: -ise (initialise, normalise, customise, organise)
# - Nouns: -our (colour, behaviour, flavour)
# Documentation is generated from docstrings which follow this convention
language = 'en'

# General configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.inheritance_diagram',
    'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# HTML output options
html_theme = 'furo'
# html_static_path = ['_static']  # Uncomment if you add custom CSS/JS

# Furo theme options
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#2980b9",
        "color-brand-content": "#2980b9",
    },
}

# Napoleon settings (for Google/NumPy style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True
napoleon_type_aliases = None

# AutoDoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Intersphinx configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}
'''

    try:
        with open(confFile, 'w', encoding='utf-8') as f:
            f.write(confContent)
        printSuccess("Created conf.py")
    except Exception as e:
        printError(f"Failed to create conf.py: {e}")
        return False

    # Create index.rst
    indexFile = docsDir / "index.rst"
    indexContent = '''jrl_env Documentation
=====================

Welcome to jrl_env's documentation!

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules

Overview
--------

jrl_env is a cross-platform development environment setup and configuration tool.
Supports ArchLinux, macOS, OpenSUSE, Raspberry Pi, RedHat/Fedora/CentOS, Ubuntu, and Windows 11.

Features
--------

* Automated application installation
* Git configuration
* SSH key generation and setup
* Font installation
* Cursor editor configuration
* Repository cloning
* Data-driven architecture
* Comprehensive validation

Modules
-------

.. toctree::
   :maxdepth: 4

   common

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
'''

    try:
        with open(indexFile, 'w', encoding='utf-8') as f:
            f.write(indexContent)
        printSuccess("Created index.rst")
    except Exception as e:
        printError(f"Failed to create index.rst: {e}")
        return False

    return True


def generateModuleDocs() -> bool:
    """Generate .rst files for common modules (helpers and test are standalone scripts)."""
    docsDir = projectRoot / "docs"

    printInfo("Generating module documentation...")

    try:
        # Generate docs for common/
        result = subprocess.run(
            [
                sys.executable, "-m", "sphinx.ext.apidoc",
                "-f",  # Force overwrite
                "-e",  # Separate page for each module (avoids duplicates)
                "-M",  # Put module documentation before submodule documentation
                "-o", str(docsDir),  # Output directory
                str(projectRoot / "common"),  # Source directory
                "**/common/**/__pycache__",  # Exclude
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            printWarning(f"sphinx-apidoc had issues for common/: {result.stderr}")

        # Note: helpers/ are standalone scripts, documented manually in helpers.rst
        # No need to run sphinx-apidoc on them

        printSuccess("Generated module documentation")
        return True
    except Exception as e:
        printError(f"Failed to generate module docs: {e}")
        return False


def cleanDocs() -> bool:
    """Clean existing documentation build."""
    docsDir = projectRoot / "docs"
    buildDir = docsDir / "_build"

    if not buildDir.exists():
        printInfo("No build directory to clean")
        return True

    printInfo("Cleaning documentation build...")
    import shutil
    try:
        shutil.rmtree(buildDir)
        printSuccess("Documentation build cleaned")
        return True
    except Exception as e:
        printError(f"Failed to clean build directory: {e}")
        return False


def buildDocs() -> bool:
    """Build HTML documentation."""
    docsDir = projectRoot / "docs"
    buildDir = docsDir / "_build"

    printInfo("Building HTML documentation...")
    safePrint()

    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "sphinx",
                "-b", "html",  # HTML builder
                str(docsDir),  # Source directory
                str(buildDir / "html"),  # Output directory
            ],
            check=False,
            cwd=str(projectRoot),
        )

        safePrint()

        if result.returncode == 0:
            printSuccess("Documentation built successfully!")
            printInfo(f"Documentation: {buildDir / 'html' / 'index.html'}")
            return True
        else:
            printError("Documentation build had errors")
            return False
    except Exception as e:
        printError(f"Failed to build documentation: {e}")
        return False


def openDocs() -> bool:
    """Open documentation in default browser."""
    docsDir = projectRoot / "docs"
    indexFile = docsDir / "_build" / "html" / "index.html"

    if not indexFile.exists():
        printError("Documentation not found. Build it first.")
        return False

    printInfo("Opening documentation in browser...")

    try:
        import platform
        system = platform.system()

        if system == "Darwin":  # macOS
            subprocess.run(["open", str(indexFile)], check=False)
        elif system == "Linux":
            subprocess.run(["xdg-open", str(indexFile)], check=False)
        elif system == "Windows":
            subprocess.run(["start", str(indexFile)], check=False, shell=True)
        else:
            printWarning(f"Unknown system: {system}. Please open manually:")
            printInfo(f"{indexFile}")
            return False

        printSuccess("Opened documentation in browser")
        return True
    except Exception as e:
        printError(f"Failed to open documentation: {e}")
        printInfo(f"Please open manually: {indexFile}")
        return False


def main() -> int:
    """Main function."""
    # Check for --help flag
    if "--help" in sys.argv or "-h" in sys.argv:
        printHelp()
        return 0

    # Parse arguments
    cleanOnly = "--clean" in sys.argv
    noOpen = "--noOpen" in sys.argv
    quiet = "--quiet" in sys.argv or "-q" in sys.argv
    setVerbosityFromArgs(quiet=quiet, verbose=False)

    # Detect CI environment (skip opening browser in CI)
    import os
    isCi = any(key in os.environ for key in ['CI', 'GITHUB_ACTIONS', 'JENKINS_URL', 'TRAVIS', 'CIRCLECI'])

    # Print title
    if getVerbosity() != Verbosity.quiet:
        printHeading("jrl_env generateDocs.py")

    # Handle --clean flag (clean only, don't build)
    if cleanOnly:
        if not cleanDocs():
            return 1
        if getVerbosity() == Verbosity.quiet:
            safePrint("Success")
        return 0

    # Check if Sphinx is installed
    if not checkSphinxInstalled():
        printWarning("Sphinx is not installed")
        if not installSphinx():
            return 1
    else:
        printInfo("Sphinx is already installed")

    safePrint()

    # Set up Sphinx configuration
    if not setupSphinxConfig():
        return 1

    safePrint()

    # Generate module documentation
    if not generateModuleDocs():
        return 1

    safePrint()

    # Build documentation
    buildSuccess = buildDocs()
    if not buildSuccess:
        return 1

    safePrint()

    # Open browser after successful build
    # Skip if: --noOpen flag, CI environment, quiet mode, or build failed
    shouldOpen = buildSuccess and not noOpen and not isCi and getVerbosity() != Verbosity.quiet

    if shouldOpen:
        # Default: open directly (no prompt)
        if not openDocs():
            return 1

    if getVerbosity() == Verbosity.quiet:
        safePrint("Success")

    return 0


if __name__ == "__main__":
    sys.exit(main())
