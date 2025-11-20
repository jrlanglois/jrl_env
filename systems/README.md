# Systems

This directory historically contained platform-specific setup scripts. As of the refactoring, **all platform-specific logic has been unified** and moved to `common/systems/` using a data-driven approach with `GenericSystem`.

## Architecture

The jrl_env setup system uses a **data-driven architecture** to eliminate code duplication:

- **`common/systems/genericSystem.py`**: Unified system implementation that works for all platforms
- **`common/systems/systemsConfig.py`**: Platform configuration data (package managers, paths, dependencies)
- **`common/systems/systemBase.py`**: Base class with shared setup orchestration logic
- **`common/systems/setupOrchestrator.py`**: Orchestrates the setup process across all platforms
- **`common/install/setupDevEnv.py`**: Unified development environment setup (zsh, Oh My Zsh, essential tools)
- **`common/windows/configureSystem.py`**: Windows-specific system configuration (registry, dark mode, etc.)

All platforms now use the same codebase with configuration-driven behaviour, following SOLID principles and DRY best practices.

## Running Setup

**From project root (recommended):**

```bash
# Run unified setup (auto-detects OS)
python3 setup.py [options]
```

**Using shell wrappers (handles Python installation):**

Windows:
```powershell
.\setup.ps1 [options]
```

Unix/Linux/macOS:
```bash
./setup.sh [options]
```

## Setup Process

The unified setup orchestrates the entire environment configuration:

1. **Development Environment Setup**: Installs zsh, Oh My Zsh, and essential tools
2. **Font Installation**: Downloads and installs Google Fonts (parallel processing)
3. **Application Installation**: Installs/updates applications (parallel processing with progress indicators)
4. **Git Configuration**: Configures Git user info, defaults, and aliases
5. **GitHub SSH Configuration**: Generates SSH keys and helps configure them for GitHub
6. **Cursor Configuration**: Merges Cursor editor settings
7. **Repository Cloning**: Clones Git repositories (only on first run)
8. **Verification**: Runs post-setup verification checks

## Options

- `--help, -h`: Show help message
- `--version, -v`: Show version information
- `--quiet, -q`: Only show final success/failure message
- `--verbose`: Enable verbose output
- `--resume`: Automatically resume from last successful step
- `--noResume`: Do not resume from previous setup
- `--listSteps`: Preview what steps will be executed
- `--skipFonts`, `--skipApps`, `--skipGit`, `--skipCursor`, `--skipRepos`, `--skipSsh`: Skip specific steps
- `--appsOnly`: Only install/update applications
- `--dryRun`: Preview changes without making them
- `--noBackup`: Skip backing up existing configuration files

## Unified Operations

### Update

Pull latest changes and re-run setup:

```bash
python3 -m common.systems.update [--dryRun] [other setup args...]
```

### Status

Check current environment status:

```bash
python3 -m common.systems.status [--quiet] [--verbose]
```

Checks installed packages, Git config, fonts, repositories, and Cursor settings.

### Validation

Validate JSON configuration files:

```bash
# Validate all platform configs
python3 -m common.systems.validate [--quiet] [--verbose]

# Validate specific platform
python3 -m common.systems.validate <platform> [--quiet] [--verbose]
```

Valid platforms: `archlinux`, `macos`, `opensuse`, `raspberrypi`, `redhat`, `ubuntu`, `win11`.

### Individual Operations

Run specific operations using the unified CLI:

```bash
python3 -m common.systems.cli <platform> <operation> [options]
```

**Available operations:**
- `status`: Check environment status
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

## Platform-Specific Details

All platform-specific details are now configured in `common/systems/systemsConfig.py`:

### Windows 11

- Package manager: `winget`
- Fonts directory: `%LOCALAPPDATA%\Microsoft\Windows\Fonts`
- Cursor settings: `%APPDATA%\Cursor\User\settings.json`
- System configuration: Registry settings, dark mode, regional settings, WSL2

### macOS

- Package managers: `brew` (packages), `brew cask` (applications)
- Fonts directory: `~/Library/Fonts`
- Cursor settings: `~/Library/Application Support/Cursor/User/settings.json`
- Development environment: Homebrew, zsh, Oh My Zsh

### Ubuntu

- Package managers: `apt`, `snap`
- Fonts directory: `~/.local/share/fonts`
- Cursor settings: `~/.config/Cursor/User/settings.json`
- Uses Ubuntu-specific package list (no linuxCommon merge)

### Raspberry Pi

- Package managers: `apt`, `snap`
- Fonts directory: `~/.local/share/fonts`
- Cursor settings: `~/.config/Cursor/User/settings.json`
- Merges packages from `configs/linuxCommon.json`

### RedHat/Fedora/CentOS

- Package manager: `dnf`
- Fonts directory: `~/.local/share/fonts`
- Cursor settings: `~/.config/Cursor/User/settings.json`
- Merges packages from `configs/linuxCommon.json`

### OpenSUSE

- Package manager: `zypper`
- Fonts directory: `~/.local/share/fonts`
- Cursor settings: `~/.config/Cursor/User/settings.json`
- Merges packages from `configs/linuxCommon.json`

### ArchLinux

- Package manager: `pacman`
- Fonts directory: `~/.local/share/fonts`
- Cursor settings: `~/.config/Cursor/User/settings.json`
- Merges packages from `configs/linuxCommon.json`

## Shared Functionality

All setup operations use shared modules from `common/`:

- **Logging**: `common/core/logging.py` (`printInfo`, `printSuccess`, `printError`, `printWarning`, `printSection`)
- **Utilities**: `common/core/utilities.py` (`commandExists`, `requireCommand`, `getJsonValue`, etc.)
- **Configuration**: `common/configure/` (Git, Cursor, GitHub SSH, repositories)
- **Installation**: `common/install/` (apps, fonts, zsh, development environment)
- **Systems**: `common/systems/` (GenericSystem, SystemBase, SetupOrchestrator, config management)

This ensures consistent behaviour across all platforms while allowing platform-specific customisation through configuration data.

## Error Handling

All setup operations include comprehensive error handling:

- Missing dependencies are detected and reported
- Configuration file errors are caught and logged
- Installation failures are tracked and reported
- Logs are written to platform-specific temp directories with ISO8601 timestamps
- Rollback capability restores previous state on failure

## Features

- **Parallel Processing**: Package and font installation use parallel processing for faster execution
- **Progress Indicators**: Real-time progress shows "Installing package X/Y: ✓ package (installed/updated/failed)"
- **Resume Capability**: Setup can resume from the last successful step if interrupted
- **Rollback**: Failed setups can be rolled back to restore previous state
- **Verification**: Post-setup verification checks ensure everything is correctly configured
- **Schema Validation**: JSON schema validation catches configuration errors early
- **Verbosity Levels**: Control output detail with `--quiet` and `--verbose` flags
- **Data-Driven**: All platform-specific details configured in one place (`systemsConfig.py`)
- **DRY & SOLID**: Zero code duplication, single responsibility, open for extension

## Migration Notes

Previously, each platform had its own directory (`systems/ubuntu/`, `systems/macos/`, etc.) with `setup.py`, `system.py`, and `setupDevEnv.py` files. These were 98% identical with only minor platform-specific differences.

**Old structure (deprecated):**
```
systems/
├── ubuntu/
│   ├── setup.py         # Thin wrapper
│   ├── system.py        # Platform config class
│   └── setupDevEnv.py   # Dev environment setup
├── macos/
│   ├── setup.py         # Same code, different platform
│   ├── system.py        # Same code, different paths
│   └── setupDevEnv.py   # Same code, different package manager
└── ... (5 more identical copies)
```

**New structure (current):**
```
common/
├── systems/
│   ├── genericSystem.py      # Unified system (works for all platforms)
│   ├── systemsConfig.py      # Platform data (single source of truth)
│   ├── systemBase.py         # Base class (shared logic)
│   └── setupOrchestrator.py  # Setup orchestration
└── install/
    └── setupDevEnv.py        # Unified dev environment setup
```

The new architecture eliminates **~1,500 lines of duplicated code** while maintaining full backwards compatibility.
