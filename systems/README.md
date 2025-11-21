# Systems

Platform-specific setup, update, status, and configuration scripts. All scripts are written in Python3 and import from `common/common.py` for shared functionality.

## Structure

```
systems/
├── archlinux/    # Arch Linux scripts
├── macos/        # macOS scripts
├── opensuse/     # OpenSUSE scripts
├── raspberrypi/  # Raspberry Pi scripts
├── redhat/       # RedHat/Fedora/CentOS scripts
├── ubuntu/       # Ubuntu scripts
└── win11/        # Windows 11 scripts
```

## Platform Scripts

Each platform directory contains the following scripts:

### `setup.py`

Main setup script that orchestrates the entire environment setup process:

1. **Development Environment Setup**: Installs essential tools
2. **Font Installation**: Downloads and installs Google Fonts (parallel processing)
3. **Application Installation**: Installs/updates applications (parallel processing with progress indicators)
4. **Git Configuration**: Configures Git user info, defaults, and aliases
5. **GitHub SSH Configuration**: Generates SSH keys and helps configure them for GitHub
6. **Cursor Configuration**: Merges Cursor editor settings
7. **Repository Cloning**: Clones Git repositories (only on first run)
8. **Verification**: Runs post-setup verification checks

**Usage:**

```bash
python3 setup.py [options]
```

**Options:**
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

### `update.py` (Unified)

Unified update script that pulls latest changes and re-runs setup:

**Usage:**

```bash
python3 -m common.systems.update [--dryRun] [other setup args...]
```

Automatically detects your platform and runs the appropriate setup. Supports all setup script options.

### `status.py` (Unified)

Unified status checking script for all platforms:

**Usage:**

```bash
python3 -m common.systems.status [--quiet] [--verbose]
```

Automatically detects your platform and checks installed packages, Git config, fonts, repositories, and Cursor settings.

### `validate.py` (Unified)

Unified validation script for JSON configuration files:

**Usage:**

```bash
# Validate all platform configs
python3 -m common.systems.validate [--quiet] [--verbose]

# Validate specific platform
python3 -m common.systems.validate <platform> [--quiet] [--verbose]
```

Validates JSON syntax, schema compliance, packages, fonts, repositories, and Git config. Valid platforms: `archlinux`, `macos`, `opensuse`, `raspberrypi`, `redhat`, `ubuntu`, `win11`.

### `setupDevEnv.py`

Development environment setup script:

- **macOS**: Installs zsh, Oh My Zsh, and Homebrew
- **Ubuntu/Raspberry Pi**: Updates package lists and installs essential packages (curl, wget, zsh, Oh My Zsh)
- **Windows 11**: Not applicable (Windows uses `configureWin11.py` for system configuration)

**Usage:**

```bash
python3 systems/<platform>/setupDevEnv.py [--dryRun]
```

Supports `--dryRun` flag to preview changes without actually installing.

### Individual Operations

Run specific operations using the unified CLI:

**Usage:**

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

**Options:**
- `--help, -h`: Show help message
- `--version, -v`: Show version information
- `--quiet, -q`: Only show final success/failure message
- `--verbose`: Enable verbose output
- `--dryRun`: Preview changes without making them

**Examples:**

```bash
# Check status
python3 -m common.systems.cli ubuntu status

# Install fonts
python3 -m common.systems.cli macos fonts

# Verify setup
python3 -m common.systems.cli win11 verify

# Rollback failed setup
python3 -m common.systems.cli ubuntu rollback
```

## Platform-Specific Notes

### Windows 11

- Uses `winget` for package management
- Includes `configureWin11.py` for Windows-specific system configuration (registry, regional settings, dark mode, etc.)
  - Supports `--dryRun` flag to preview registry and system changes
- Fonts are installed to `C:\Windows\Fonts\`
- Cursor settings are in `%APPDATA%\Cursor\User\settings.json`

### macOS

- Uses `brew` and `brew cask` for package management
- Installs zsh and Oh My Zsh during setup
- Fonts are installed to `~/Library/Fonts/`
- Cursor settings are in `~/Library/Application Support/Cursor/User/settings.json`

### Ubuntu

- Uses `apt` and `snap` for package management
- Merges packages from `configs/linuxCommon.json` with distro-specific packages
- Fonts are installed to `~/.local/share/fonts/`
- Cursor settings are in `~/.config/Cursor/User/settings.json`

### Raspberry Pi

- Uses `apt` and `snap` for package management (same as Ubuntu)
- Merges packages from `configs/linuxCommon.json` with distro-specific packages
- Fonts are installed to `~/.local/share/fonts/`
- Cursor settings are in `~/.config/Cursor/User/settings.json`

### RedHat/Fedora/CentOS

- Uses `dnf` for package management
- Merges packages from `configs/linuxCommon.json` with distro-specific packages
- Fonts are installed to `~/.local/share/fonts/`
- Cursor settings are in `~/.config/Cursor/User/settings.json`

### OpenSUSE

- Uses `zypper` for package management
- Merges packages from `configs/linuxCommon.json` with distro-specific packages
- Fonts are installed to `~/.local/share/fonts/`
- Cursor settings are in `~/.config/Cursor/User/settings.json`

### ArchLinux

- Uses `pacman` for package management
- Merges packages from `configs/linuxCommon.json` with distro-specific packages
- Fonts are installed to `~/.local/share/fonts/`
- Cursor settings are in `~/.config/Cursor/User/settings.json`

## Shared Functionality

All platform scripts import from `common/common.py` to access:

- Logging functions (`printInfo`, `printSuccess`, `printError`, `printWarning`, `printH2`)
- Utility functions (`commandExists`, `requireCommand`, `getJsonValue`, etc.)
- Configuration functions (`configureGit`, `configureCursor`, `configureGithubSsh`, `cloneRepositories`)
- Installation functions (`installApps`, `installGoogleFonts`)
- Setup utilities (`initLogging`, `backupConfigs`, `checkDependencies`, `shouldCloneRepositories`)

This ensures consistent behaviour across all platforms while allowing platform-specific customisation.

## Error Handling

All scripts include comprehensive error handling:

- Missing dependencies are detected and reported
- Configuration file errors are caught and logged
- Installation failures are tracked and reported
- Logs are written to platform-specific temp directories

## Logging

All scripts write logs to platform-specific temp directories with ISO8601 timestamps. Logs include detailed error context (command executed, exit code, stderr output) for troubleshooting.

## Features

- **Parallel Processing**: Package and font installation use parallel processing for faster execution
- **Progress Indicators**: Real-time progress indicators show "Installing package X/Y: ✓ package (installed/updated/failed)"
- **Resume Capability**: Setup can resume from the last successful step if interrupted
- **Rollback**: Failed setups can be rolled back to restore previous state
- **Verification**: Post-setup verification checks ensure everything is correctly configured
- **Schema Validation**: JSON schema validation catches configuration errors early
- **Verbosity Levels**: Control output detail with `--quiet` and `--verbose` flags
