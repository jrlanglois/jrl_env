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

The easiest way to get started on a fresh machine is to download the latest release and run the unified setup script, which auto-detects your operating system and handles everything automatically.

#### Step 1: Download the Release

Download the latest release `.zip` file from the [GitHub releases page](https://github.com/jrlanglois/jrl_env/releases/latest).

No Git installation required at this stage!

#### Step 2: Extract and Navigate

Extract the downloaded `.zip` file to a location of your choice, then open a terminal or PowerShell window in the extracted directory.

**Windows 11:**

```powershell
cd path\to\extracted\jrl_env
```

**ArchLinux / macOS / OpenSUSE / Raspberry Pi / RedHat / Ubuntu:**

```bash
cd path/to/extracted/jrl_env
```

#### Step 3: Run Setup

Execute the unified setup script:

**Windows 11:**

```powershell
.\setup.ps1
```

**ArchLinux / macOS / OpenSUSE / Raspberry Pi / RedHat / Ubuntu:**

```bash
./setup.sh
```

The setup script will automatically:

- **Install Python3** (if not already present) via your system's package manager
- **Install Python dependencies** from `requirements.txt` (e.g., `jsonschema` for config validation)
- **Detect your operating system** and route to the appropriate platform-specific setup
- **Install Git** (if not already present) along with other essential tools
- **Configure Git** with your user info, aliases, and SSH keys for GitHub
- **Install applications** specified in your platform's config file
- **Install Google Fonts** for a consistent development environment
- **Configure Cursor editor** with your preferred settings
- **Clone repositories** to your workspace directory
- **Run verification checks** to ensure everything is set up correctly
- **Detect setup state** (first-time vs. update mode) and handle accordingly

#### Available Options

**Information & Help:**

- `--help, -h`: Show help message with all available options
- `--version, -v`: Show version information
- `--listSteps`: Preview what steps will be executed without running setup

**Output Control:**

- `--quiet, -q`: Only show final success/failure message
- `--verbose`: Enable verbose output (show debug messages)
- `--dryRun`: Preview changes without making them

**Execution Control:**

- `--resume`: Automatically resume from last successful step if setup was interrupted
- `--noResume`: Do not resume from previous setup (start fresh)
- `--noBackup`: Skip backing up existing configuration files

**Selective Operations:**

- `--appsOnly`: Only install/update applications
- `--skipFonts`: Skip font installation
- `--skipApps`: Skip application installation
- `--skipGit`: Skip Git configuration
- `--skipCursor`: Skip Cursor editor configuration
- `--skipRepos`: Skip repository cloning
- `--skipSsh`: Skip GitHub SSH configuration

**Custom Configuration:**

- `--configDir <path>`: Use a custom configuration directory instead of the default `configs/`

**Examples:**

**Windows 11:**

```powershell
# Run setup in dry-run mode to preview changes
.\setup.ps1 --dryRun

# Run setup with verbose output and skip font installation
.\setup.ps1 --verbose --skipFonts

# Resume interrupted setup
.\setup.ps1 --resume
```

**ArchLinux / macOS / OpenSUSE / Raspberry Pi / RedHat / Ubuntu:**

```bash
# Run setup in dry-run mode to preview changes
./setup.sh --dryRun

# Run setup with verbose output and skip font installation
./setup.sh --verbose --skipFonts

# Resume interrupted setup
./setup.sh --resume
```

#### After Setup Completes

Once setup finishes successfully:

- Git is installed and configured with your credentials
- Your preferred applications are installed and ready to use
- Fonts are installed system-wide
- Cursor editor is configured with your settings
- Repositories are cloned to your workspace directory
- Your machine is ready for development!

You can verify the setup by running:

```bash
python3 -m common.systems.cli <platform> status
```

### Alternative Setup: Clone with Git

If you already have Git and Python3 installed, you can clone the repository and run setup directly:

**Windows 11:**

```powershell
git clone https://github.com/jrlanglois/jrl_env.git
cd jrl_env
.\setup.ps1
```

**ArchLinux / macOS / OpenSUSE / Raspberry Pi / RedHat / Ubuntu:**

```bash
git clone https://github.com/jrlanglois/jrl_env.git
cd jrl_env
./setup.sh
```

**Note:** If you don't have Python3 installed yet, the setup scripts will detect this and offer to install it for you.


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
   ./setup.sh --configDir /path/to/your/configs
   # Or set environment variable:
   export JRL_ENV_CONFIG_DIR=/path/to/your/configs
   ./setup.sh
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

This repository follows DRY (Don't Repeat Yourself) and SOLID principles with a **data-driven architecture**:

- **Single Entry Point**:
  - `common/common.py` is the single entry point that all Python scripts import from. It exposes all common utilities and modules.
- **Data-Driven Platform Support**: All platform-specific behaviour is configured via data rather than code:
  - `common/systems/genericSystem.py`: Unified system implementation that works for all platforms
  - `common/systems/systemsConfig.py`: Platform configuration data (package managers, paths, dependencies)
  - `common/systems/systemBase.py`: Base class with shared setup orchestration logic
  - `common/systems/setupOrchestrator.py`: Orchestrates setup process across all platforms
- **Shared Logic**: Common Python functionality is centralised in `common/` (e.g., Git configuration, app installation, font installation)
- **OS Detection**: `common/core/utilities.py` provides OS detection functions (`findOperatingSystem()`, `getOperatingSystem()`, `isOperatingSystem()`) to identify the current platform
- **Shared Utilities**: Core utilities are in `common/core/`:
  - `common/core/utilities.py`: Generic Python utilities (e.g., `commandExists()`, JSON helpers, OS detection)
  - `common/core/logging.py`: Consistent logging functions with verbosity levels (`printInfo`, `printSuccess`, `printError`, `printWarning`, `printSection`, `printVerbose`, `safePrint`, `colourise`)
  - `common/core/logging.py`: Verbosity levels (`quiet`, `normal`, `verbose`) and ISO8601 timestamps
- **Platform-Agnostic Package Management**:
  - `common/install/packageManagers.py`: Unified package manager abstractions (Brew, Apt, Snap, Pacman, Zypper, DNF, Winget)
  - `common/linux/packageManager.py`: Legacy distro-agnostic OOP abstractions for Linux package managers
  - `common/windows/packageManager.py`: Windows-specific package management utilities
- **Unified Development Environment**: `common/install/setupDevEnv.py` provides unified dev environment setup (zsh, Oh My Zsh, essential tools) for all platforms
- **Windows Configuration**: `common/windows/configureSystem.py` handles Windows-specific system configuration (registry, dark mode, regional settings, WSL2)
- **Setup Utilities**: `common/install/setupUtils.py` provides shared setup functions (`initLogging`, `backupConfigs`, `checkDependencies`, `shouldCloneRepositories`)
- **Setup State**: `common/install/setupState.py` tracks setup progress to enable resuming from interrupted setups
- **Rollback**: `common/install/rollback.py` provides rollback capability for failed setups
- **Verification**: `common/systems/verify.py` performs post-setup verification checks
- **Schema Validation**: `common/systems/schemas.py` and `common/systems/validate.py` provide JSON schema validation
- **Helper Scripts**: Utility scripts are in `helpers/`:
  - All helper scripts import from `common/common.py` for consistent logging and utilities

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
