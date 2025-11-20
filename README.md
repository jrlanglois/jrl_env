# jrl_env

[![CI](https://github.com/jrlanglois/jrl_env/actions/workflows/ci.yml/badge.svg)](https://github.com/jrlanglois/jrl_env/actions/workflows/ci.yml)
[![Validate Configs](https://github.com/jrlanglois/jrl_env/actions/workflows/validateConfigs.yml/badge.svg)](https://github.com/jrlanglois/jrl_env/actions/workflows/validateConfigs.yml)

Cross-platform development environment setup and configuration.

Helper tooling enforces Allman braces, camelCase for functions/variables, PascalCase for classes, and CRLF for `.ps1/.json/.md` while keeping `.sh/.py` LF.

## Overview

Automated setup scripts for ArchLinux, macOS, OpenSUSE, Raspberry Pi, RedHat/Fedora/CentOS, Ubuntu, and Windows 11. Manages application installation, system configuration, Git setup, Cursor editor settings, font installation, and repository cloning.

### Purpose

This repository is designed for configuring my own development machines. The scripts and configurations are tailored to my personal preferences and workflow.

Obviously this is a public repository to make things easier for myself. You can use it, but do so at your own risk! See the license for details.

## Structure

```text
jrl_env/
├── common/           # Shared logic (Python modules)
│   ├── configure/    # Configuration modules
│   │   ├── cloneRepositories.py
│   │   ├── configureCursor.py
│   │   ├── configureGit.py
│   │   └── configureGithubSsh.py
│   ├── core/         # Core utilities (colours, logging, utilities)
│   │   ├── logging.py
│   │   └── utilities.py  # Includes OS detection functions
│   ├── install/      # Installation modules
│   │   ├── installApps.py
│   │   ├── installFonts.py
│   │   ├── setupArgs.py
│   │   └── setupUtils.py
│   ├── linux/        # Linux-specific helpers (package managers, etc.)
│   │   └── packageManager.py
│   ├── systems/      # System base classes
│   │   ├── cli.py         # Unified CLI for individual operations
│   │   └── systemBase.py  # Base class for all system setups
│   ├── windows/      # Windows-specific helpers
│   │   └── packageManager.py
│   └── common.py     # Single entry point for Python - imports all common utilities
├── configs/          # JSON configuration files
│   ├── archlinux.json
│   ├── cursorSettings.json
│   ├── fonts.json
│   ├── gitConfig.json
│   ├── linuxCommon.json
│   ├── macos.json
│   ├── opensuse.json
│   ├── raspberrypi.json
│   ├── redhat.json
│   ├── repositories.json
│   ├── ubuntu.json
│   └── win11.json
├── helpers/          # Utility scripts and shared modules
│   ├── convertToAllman.py
│   ├── formatRepo.py
│   └── tidy.py
├── systems/          # Platform-specific scripts (Python)
│   ├── archlinux/    # Python scripts for ArchLinux
│   ├── macos/        # Python scripts for macOS
│   ├── opensuse/     # Python scripts for OpenSUSE
│   ├── raspberrypi/  # Python scripts for Raspberry Pi
│   ├── redhat/       # Python scripts for RedHat/Fedora/CentOS
│   ├── ubuntu/       # Python scripts for Ubuntu
│   └── win11/        # Python scripts for Windows
└── test/             # Validation scripts for configuration files (Python)
    ├── validateFonts.py
    ├── validateGitConfig.py
    ├── validateLinuxCommonPackages.py  # Comprehensive Linux common validation
    ├── validatePackages.py          # Unified package validation (all platforms)
    └── validateRepositories.py
```

## Quick Start

### Unified Setup (Recommended)

The easiest way to get started is using the unified setup script at the root, which auto-detects your operating system:

**Windows 11:**

```powershell
git clone https://github.com/jrlanglois/jrl_env.git
cd jrl_env
python3 setup.py
```

**ArchLinux / macOS / OpenSUSE / Raspberry Pi / RedHat / Ubuntu:**

```bash
git clone https://github.com/jrlanglois/jrl_env.git
cd jrl_env
python3 setup.py
```

The unified setup script will:

- **Automatically install Python dependencies** from `requirements.txt` (e.g., `jsonschema` for config validation)
- Auto-detect your operating system
- Route to the appropriate platform-specific setup script
- Detect if setup has already been run (first-time vs. update mode)
- Execute all configuration and installation tasks automatically
- Run verification checks after setup completes

**Options:**

- `--help, -h`: Show help message
- `--version, -v`: Show version information
- `--quiet, -q`: Only show final success/failure message
- `--verbose`: Enable verbose output (show debug messages)
- `--resume`: Automatically resume from last successful step if setup was interrupted
- `--noResume`: Do not resume from previous setup (start fresh)
- `--listSteps`: Preview what steps will be executed without running setup
- `--skipFonts`, `--skipApps`, `--skipGit`, `--skipCursor`, `--skipRepos`, `--skipSsh`: Skip specific steps
- `--appsOnly`: Only install/update applications
- `--dryRun`: Preview changes without making them
- `--noBackup`: Skip backing up existing configuration files

**Note:** The setup script will automatically install required Python packages. If you prefer to install them manually:

```bash
pip install -r requirements.txt
```

### Platform-Specific Setup

Alternatively, you can run the platform-specific setup scripts directly:

**Windows 11:**

```powershell
python3 systems/win11/setup.py
```

**macOS:**

```bash
python3 systems/macos/setup.py
```

**Ubuntu:**

```bash
python3 systems/ubuntu/setup.py
```

**Raspberry Pi:**

```bash
python3 systems/raspberrypi/setup.py
```

**RedHat/Fedora/CentOS:**

```bash
python3 systems/redhat/setup.py
```

**OpenSUSE:**

```bash
python3 systems/opensuse/setup.py
```

**ArchLinux:**

```bash
python3 systems/archlinux/setup.py
```

### Individual Operations

Run specific operations without running the full setup:

```bash
python3 -m common.systems.cli <platform> <operation> [options]
```

**Available operations:**

- `status`: Check environment status (installed packages, Git config, fonts, repos)
- `fonts`: Install Google Fonts
- `apps`: Install/update applications
- `git`: Configure Git
- `ssh`: Configure GitHub SSH
- `cursor`: Configure Cursor editor
- `repos`: Clone repositories
- `verify`: Run post-setup verification checks
- `rollback`: Rollback a failed setup session

**Examples:**

```bash
# Check status
python3 -m common.systems.cli ubuntu status

# Install fonts only
python3 -m common.systems.cli macos fonts

# Verify setup
python3 -m common.systems.cli win11 verify

# Rollback failed setup
python3 -m common.systems.cli ubuntu rollback
```

All operations support `--help`, `--quiet`, `--verbose`, and `--dryRun` flags.

## Configuration

Edit JSON files in `configs/` to customise:

- **Apps**: Application packages to install via winget/brew/apt/snap
- **Fonts**: Google Fonts to download and install
- **Repositories**: Git repositories to clone (organised by owner)
- **Git**: User info, defaults, aliases, and GitHub username/email for SSH
- **Cursor**: Editor settings and preferences
- **Shell**: Per-OS shell preferences (e.g., `ohMyZshTheme`)
- **Cruft**: Packages to uninstall (e.g., Ubuntu `apt` wildcard patterns)
- **Commands**: Optional `preInstall`/`postInstall` command objects (name, shell, command, runOnce)
- **Linux Common**: Shared packages for all Linux distributions (merged with distro-specific packages)

See [`configs/README.md`](configs/README.md) for detailed configuration documentation.

### Validation

Configuration files are automatically validated via CI on every push and pull request. The validation checks:

- **JSON Syntax**: Valid JSON structure
- **Schema Validation**: JSON schema validation for required fields and value types
- **Package Existence**: Verifies packages exist in their respective package managers
- **Font Availability**: Validates Google Fonts exist via the Google Fonts API
- **Repository Accessibility**: Checks if Git repositories are accessible
- **Git Configuration**: Validates Git aliases, defaults, user name, email format, and GitHub username
- **Work Paths**: Validates repository work path syntax for Unix and Windows
- **Linux Common Packages**: Validates packages exist across all supported Linux package managers

**Unified validation:**

```bash
# Validate all configs
python3 -m common.systems.validate

# Validate specific platform
python3 -m common.systems.validate ubuntu
```

**Individual validation scripts:**

```bash
# Package validation
python3 test/validatePackages.py configs/macos.json
python3 test/validateLinuxCommonPackages.py configs/linuxCommon.json

# Other configs
python3 test/validateFonts.py configs/fonts.json
python3 test/validateRepositories.py configs/repositories.json
python3 test/validateGitConfig.py configs/gitConfig.json
```

All validation scripts support `--help` and `--quiet` flags. See [`test/README.md`](test/README.md) for details.

## Using This Repository

To adapt this setup for your own machines:

1. **Use your own config directory** (recommended): Point the setup to your own config directory without modifying the repository:
   ```bash
   python3 setup.py --configDir /path/to/your/configs
   # Or set environment variable:
   export JRL_ENV_CONFIG_DIR=/path/to/your/configs
   python3 setup.py
   ```

2. **Fork the repository** and modify the config files with your preferences

3. **Copy the structure** and create your own scripts based on these examples

4. **Use as a template** for building your own environment setup system

The scripts are designed to be modular and configurable. You can use your own configuration files without modifying the repository code, making it easy to maintain your personal configs separately from the tool itself.

### Status Checking

Check the current state of your environment:

```bash
python3 -m common.systems.status
```

Verifies installed packages, Git config, fonts, repositories, and Cursor settings. Supports `--quiet` and `--verbose` flags.

### Rollback

If setup fails, you can rollback changes:

```bash
python3 -m common.systems.cli <platform> rollback
```

This restores backed-up configurations and uninstalls packages installed during the failed session.

## Architecture

This repository follows DRY (Don't Repeat Yourself) and SOLID principles:

- **Single Entry Point**:
  - `common/common.py` is the single entry point that all Python scripts import from. It exposes all common utilities and modules.
- **Shared Logic**: Common Python functionality is centralised in `common/` (e.g., Git configuration, app installation, font installation)
- **Thin Wrappers**: Platform-specific scripts (`systems/archlinux/`, `systems/macos/`, `systems/opensuse/`, `systems/raspberrypi/`, `systems/redhat/`, `systems/ubuntu/`, `systems/win11/`) are thin wrappers that set platform-specific variables and import from `common/common.py`
- **OS Detection**: `common/core/utilities.py` provides OS detection functions (`findOperatingSystem()`, `getOperatingSystem()`, `isOperatingSystem()`) to identify the current platform
- **Shared Utilities**: Core utilities are in `common/core/`:
  - `common/core/utilities.py`: Generic Python utilities (e.g., `commandExists()`, JSON helpers, OS detection)
  - `common/core/logging.py`: Consistent logging functions with verbosity levels (`printInfo`, `printSuccess`, `printError`, `printWarning`, `printSection`, `printVerbose`, `safePrint`, `colourise`)
  - `common/core/logging.py`: Verbosity levels (`quiet`, `normal`, `verbose`) and ISO8601 timestamps
- **Linux Package Helpers**: `common/linux/packageManager.py` provides distro-agnostic OOP abstractions so any Linux system can use its package manager (`apt`, `yum`, `dnf`, `rpm`) and reuse install/update logic
- **Windows Package Helpers**: `common/windows/packageManager.py` provides Windows-specific package management utilities for winget and Microsoft Store
- **Setup Utilities**: `common/install/setupUtils.py` provides shared setup functions (`initLogging`, `backupConfigs`, `checkDependencies`, `shouldCloneRepositories`) used across all platform setup scripts
- **Setup State**: `common/install/setupState.py` tracks setup progress to enable resuming from interrupted setups
- **Rollback**: `common/install/rollback.py` provides rollback capability for failed setups
- **Verification**: `common/systems/verify.py` performs post-setup verification checks
- **Schema Validation**: `common/systems/schemas.py` and `common/systems/validate.py` provide JSON schema validation
- **Helper Scripts**: Utility scripts are in `helpers/`:
  - All helper scripts import from `common/common.py` for consistent logging and utilities
- **Python Migration**: The codebase has been migrated from Bash to Python3 for improved readability, maintainability, and reduced context switching. All platform-specific scripts and test scripts are now Python-based.

See [`common/README.md`](common/README.md) for detailed documentation on the common modules.

## Style Guide

This repository follows a consistent and intentionally opinionated coding style. I'm particular about my environment and I like things the way I like them.

If you find something that causes a real technical issue, I'm happy to adjust it.

If it's a style debate, I have zero interest in entertaining it.

- **Naming**:
  - **Classes/Structs**: PascalCase (e.g., `PackageManager`, `TidyStats`, `Colours`)
  - **Functions/Variables/Macros**: camelCase (e.g., `printInfo`, `backupConfigs`, `isWingetInstalled`, `packageMappings`)
- **Indentation**: 4 spaces, no tabs.
- **Braces**: Allman style (opening brace/bracket on its own line) where possible. Applies to code blocks, objects, and arrays.
- **Boolean functions**: Use `is/was/{verb}` prefixes for clarity (e.g., `isGitInstalled`, `isRepositoryCloned`).
- **Spelling**: Canadian English conventions (`-ise` for verbs, `-our` for nouns like `colour`, `behaviour`).
- **Line endings**:
  - **Python scripts (`.py`)**: LF (Unix-style) line endings (required for shebang compatibility)
  - **Bash scripts (`.sh`)**: LF (Unix-style) line endings
  - **JSON files**: CRLF (Windows-style) line endings
  - **PowerShell (`.ps1`)**: CRLF (Windows-style) line endings
- **Timestamps**: ISO8601.

These conventions apply to all Python (`.py`) and PowerShell (`.ps1`) scripts in this repository.

Note: PowerShell has some syntax quirks that may prevent Allman braces in certain cases (e.g., pipeline operations), but I use them wherever possible.

## Requirements

- **Python 3**: Python 3.6 or higher
- **Dependencies**: Automatically installed from `requirements.txt` (includes `jsonschema` for validation)
- **Platform-specific**:
  - **ArchLinux**: pacman, zsh
  - **macOS**: Homebrew, zsh
  - **OpenSUSE**: zypper, zsh
  - **Raspberry Pi**: apt, snap, zsh
  - **RedHat/Fedora/CentOS**: dnf, zsh
  - **Ubuntu**: apt, snap, zsh
  - **Windows**: PowerShell 5.1+, winget (Windows Package Manager)

## CI/CD

This repository uses GitHub Actions for continuous integration:

- **CI Workflow** (`ci.yml`): Lints remaining shell scripts with ShellCheck and validates Python syntax
- **Validate Configs Workflow** (`validateConfigs.yml`): Validates all JSON configuration files, checks package existence, font availability, repository accessibility, and Git configuration

Both workflows run automatically on pushes and pull requests to the `main` branch.

## License

ISC License. See LICENSE.md for details.
