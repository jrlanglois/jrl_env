# jrl_env

[![CI](https://github.com/jrlanglois/jrl_env/actions/workflows/ci.yml/badge.svg)](https://github.com/jrlanglois/jrl_env/actions/workflows/ci.yml)
[![Validate Configs](https://github.com/jrlanglois/jrl_env/actions/workflows/validateConfigs.yml/badge.svg)](https://github.com/jrlanglois/jrl_env/actions/workflows/validateConfigs.yml)

Cross-platform development environment setup and configuration.


## Overview

Automated setup and update scripts for many systems. Manages application installation, system configuration, Git setup, Cursor editor settings, font installation, and repository cloning.

### Purpose

This system is designed for configuring my own development machines. The scripts and configurations are tailored to my personal preferences and workflow, but you can write up your own and pass them as parameters.

Obviously this is a public repository to make things easier for myself. You can use it, but do so at your own risk! See the licence for details.

## Quick Start

### Unified Setup (Recommended)

The easiest way to get started is using the unified setup script at the root, which auto-detects your operating system:

#### Windows 11

```powershell
git clone https://github.com/jrlanglois/jrl_env.git
cd jrl_env
./setup.ps1
```

#### Everywhere Else

```bash
git clone https://github.com/jrlanglois/jrl_env.git
cd jrl_env
./setup.sh
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
- `--noTimestamps`: Hide timestamps in console output (log files always include timestamps)
- `--resume`: Automatically resume from last successful step if setup was interrupted
- `--noResume`: Do not resume from previous setup (start fresh)
- `--listSteps`: Preview what steps will be executed without running setup
- `--install[=TARGETS]`: Install components (default: all). Targets: `all`, `fonts`, `apps`, `git`, `cursor`, `repos`, `ssh`
- `--update[=TARGETS]`: Update components (default: all). Targets: `all`, `apps`, `system`
- `--passphrase=MODE`: SSH passphrase mode: `require` (default) or `no`
- `--dryRun`: Preview changes without making them
- `--noBackup`: Skip backing up existing configuration files

**Note:** The setup script will automatically install required Python packages. If you prefer to install them manually:

```bash
pip install -r requirements.txt
```

### Usage Examples

**Installation:**
```bash
# Install everything (default)
python3 setup.py
python3 setup.py --install
python3 setup.py --install=all

# Install specific components
python3 setup.py --install=apps
python3 setup.py --install=fonts,git,cursor

# Install with SSH passphrase control
python3 setup.py --install=ssh                    # Passphrase required (default)
python3 setup.py --install=ssh --passphrase=no    # No passphrase (not recommended)
```

**Updates:**
```bash
# Update everything (packages, Android SDK, OS, stores, OMZ)
python3 setup.py --update

# Update only applications (package managers + Android SDK)
python3 setup.py --update=apps

# Update only system components (OS, stores, OMZ)
python3 setup.py --update=system
```

**Dry Run (Preview Without Changes):**
```bash
python3 setup.py --install=apps --dryRun
python3 setup.py --update --dryRun
```

### Tab Completion

Tab completion is **automatically installed** on first run for Bash, Zsh, and PowerShell.

After running setup once, restart your shell and tab completion will work:

```bash
./setup.sh --inst<TAB>                 # Completes to --install
./setup.sh --install=<TAB>             # Shows: all, fonts, apps, git, cursor, repos, ssh
./setup.sh --install=fonts,<TAB>       # Shows remaining targets
./setup.sh --update=<TAB>              # Shows: all, apps, system
./setup.sh --passphrase=<TAB>          # Shows: require, no
```

See [`completions/README.md`](completions/README.md) for details.

### Individual Operations

Run specific operations without running the full setup:

```bash
python3 -m common.systems.cli <platform> <operation> [options]
```

**Available operations:**

- `apps`: Install/update applications
- `cursor`: Configure Cursor editor
- `fonts`: Install Google Fonts
- `git`: Configure Git
- `repos`: Clone repositories
- `ssh`: Configure GitHub SSH
- `status`: Check environment status (installed packages, Git config, fonts, repos)
- `verify`: Run post-setup verification checks
- `update`: Update system and all installed applications
- `rollback`: Rollback a failed setup session

**Examples:**

```bash
# Check status
python3 -m common.systems.cli ubuntu status

# Install fonts only
python3 -m common.systems.cli macos fonts

# Update everything (packages, system, OMZ, Android SDK)
python3 -m common.systems.cli macos update
python3 -m common.systems.cli ubuntu update --dryRun

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
- **Repositories**: Git repositories to clone (organised by owner, supports wildcards for auto-discovery)
- **Git**: User info, defaults, aliases, and GitHub username/email for SSH
- **Cursor**: Editor settings and preferences
- **Shell**: Per-OS shell preferences (e.g., `ohMyZshTheme`)
- **Cruft**: Packages to uninstall per package manager (supports wildcard patterns)
- **Commands**: Optional `preInstall`/`postInstall` command objects (name, shell, command, runOnce)
- **Linux Common**: Shared packages for all Linux distributions (merged with distro-specific packages)

See [`configs/README.md`](configs/README.md) for detailed configuration documentation.

### Wildcard Repository Support

Automatically discover and clone all repositories from a GitHub user or organization using wildcard patterns:

**Basic syntax:**
```json
{
  "repositories": [
    {
      "pattern": "git@github.com:jrlanglois/*",
      "visibility": "all"
    }
  ]
}
```

**Visibility options:**
- `"all"` (default) - All repositories
- `"public"` - Public repositories only
- `"private"` - Private repositories only

**Examples:**
```json
{
  "repositories": [
    {
      "pattern": "git@github.com:jrlanglois/*",
      "visibility": "all"
    },
    "git@github.com:specific/manual-repo",
    {
      "pattern": "git@github.com:SquarePine/*",
      "visibility": "public"
    }
  ]
}
```

**Features:**
- HTTP caching with ETags (RFC 7232) - minimal API calls
- Respects GitHub rate limits
- Falls back to cache on API failures
- Backward compatible (plain strings still work)

**Cache management:**
```bash
# Clear cache and refetch
python3 setup.py --clearRepoCache

# Cache location: ~/.cache/jrl_env/repo_cache.json
```

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

## Security

### SSH Key Configuration

#### Algorithm and Key Size

jrl_env supports configurable SSH key generation. Configure in `configs/gitConfig.json`:

```json
{
    "ssh": {
        "algorithm": "ed25519",
        "keySize": null,
        "keyFilename": "id_ed25519_github"
    }
}
```

**Supported Algorithms:**

| Algorithm | Key Size | Recommended | Notes |
|-----------|----------|-------------|-------|
| `ed25519` | N/A (fixed) | ✅ **Best choice** | Modern, secure, fast. Default. |
| `rsa` | 2048-4096 | ⚠️ 4096 bits | Legacy support. Use 4096+ for security. |
| `ecdsa` | 256, 384, 521 | ⚠️ 521 bits | Use 521 for maximum security. |
| `dsa` | N/A (fixed 1024) | ❌ **Not recommended** | Deprecated, weak security. |

**Configuration Examples:**

```json
// Default (ed25519 - recommended)
{
    "ssh": {
        "algorithm": "ed25519",
        "keySize": null,
        "keyFilename": "id_ed25519_github"
    }
}

// RSA 4096-bit (for legacy systems)
{
    "ssh": {
        "algorithm": "rsa",
        "keySize": 4096,
        "keyFilename": "id_rsa_github"
    }
}

// ECDSA 521-bit
{
    "ssh": {
        "algorithm": "ecdsa",
        "keySize": 521,
        "keyFilename": "id_ecdsa_github"
    }
}
```

**Validation:**
- Invalid algorithms fail immediately with clear error
- Invalid key sizes for algorithm fail immediately
- RSA keys < 2048 bits are rejected (insecure)
- ECDSA only accepts 256, 384, or 521 bits
- ed25519 and dsa don't support custom key sizes

#### SSH Key Passphrases

jrl_env supports secure SSH key generation with optional passphrases:

**Default Behaviour (Recommended):**
```bash
python3 setup.py
```
You'll be prompted to optionally add a passphrase. Press Enter to skip or enter a strong passphrase.

**Require Passphrase (Most Secure - Default):**
```bash
python3 setup.py --install=ssh --passphrase=require
# Or just:
python3 setup.py --install=ssh
```
Passphrase is required by default. Recommended for production environments.

**No Passphrase (Least Secure):**
```bash
python3 setup.py --install=ssh --passphrase=no
```
Skips passphrase prompt. Only use for testing/development. **Not recommended for production.**

#### Passphrase Storage

When you provide a passphrase, it's stored securely in your system keychain:
- **macOS:** Keychain
- **Linux:** Secret Service API (GNOME Keyring, KWallet)
- **Windows:** Credential Manager

Passphrases are encrypted by the OS and retrieved automatically when needed.

**Security Benefits:**
- No plaintext password storage
- OS-level encryption
- Per-user access control
- Automatic retrieval for ssh-agent

For comprehensive security information, see [`SECURITY.md`](SECURITY.md).

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
- **Data-Driven Platform Support**: All platform-specific behaviour is configured via data rather than code:
  - `common/systems/genericSystem.py`: Unified system implementation that works for all platforms
  - `common/systems/systemsConfig.py`: Platform configuration data (package managers, paths, dependencies)
  - `common/systems/systemBase.py`: Base class with shared setup orchestration logic
  - `common/systems/setupOrchestrator.py`: Orchestrates setup process across all platforms
- **Shared Logic**: Common Python functionality is centralised in `common/` (e.g., Git configuration, app installation, font installation)
- **OS Detection**: `common/core/utilities.py` provides OS detection functions (`findOperatingSystem()`, `getOperatingSystem()`, `isOperatingSystem()`) to identify the current platform
- **Shared Utilities**: Core utilities are in `common/core/`:
  - `common/core/utilities.py`: Generic Python utilities (e.g., `commandExists()`, JSON helpers, OS detection)
  - `common/core/logging.py`: Consistent logging functions with verbosity levels (`printInfo`, `printSuccess`, `printError`, `printWarning`, `printH2`, `printVerbose`, `safePrint`, `colourise`)
  - `common/core/logging.py`: Verbosity levels (`quiet`, `normal`, `verbose`) and ISO8601 timestamps
- **Package Managers**: `common/install/packageManagers.py` provides cross-platform OOP abstractions for all package managers with standardised install/update logic:
  - **macOS**: Homebrew, Homebrew Cask
  - **Linux**: APT, DNF, Pacman, Zypper, Snap
  - **Windows**: Winget, Chocolatey, Microsoft Store
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

### Documentation Generation

Generate comprehensive API documentation using Sphinx:

```bash
python3 docs/generateDocs.py
```

This creates HTML documentation with:
- Complete API reference from docstrings
- Module structure and relationships
- Function signatures and type hints
- Automatic cross-referencing

**Options:**
- `--clean`: Clean previous build before generating
- `--open`: Open documentation in browser after building
- `--quiet`: Only show final success/failure

Documentation will be generated in `docs/_build/html/index.html`.

## Style Guide

This repository follows a consistent and intentionally opinionated coding style. I'm particular about my environment and I like things the way I like them.

If you find something that causes a real technical issue, I'm happy to adjust it.

If it's a style debate, I have zero interest in entertaining it.

- **Naming**:
  - **Classes/Structs**: PascalCase (e.g., `PackageManager`, `TidyStats`, `Colours`)
  - **Functions/Variables/Macros**: camelCase (e.g., `printInfo`, `backupConfigs`, `isWingetInstalled`, `packageMappings`)
  - **Underscores**: Absolutely no underscores at any time.
- **Indentation**: 4 spaces, no tabs.
- **Braces**: Allman style (opening brace/bracket on its own line) where possible. Applies to code blocks, objects, and arrays.
- **Boolean functions**: Use `is/was/{verb}` prefixes for clarity (e.g., `isGitInstalled`, `isRepositoryCloned`).
- **Spelling**: Canadian English conventions:
  - Verbs: `-ise` (initialise, normalise, recognise, organise)
  - Nouns: `-our` (colour, behaviour, flavour, honour)
  - Other: `centre` (not center), `defence` (not defense), `licence` (not license)
- **Line endings**:
  - **JSON files**: CRLF (Windows-style) line endings
  - **PowerShell (`.ps1`)**: CRLF (Windows-style) line endings
  - **Everything Else**: LF (Unix-style) line endings
- **Timestamps**: ISO8601.

These conventions apply to all Python (`.py`) and PowerShell (`.ps1`) scripts in this repository.

Note: PowerShell has some syntax quirks that may prevent Allman braces in certain cases (e.g., pipeline operations), but I use them wherever possible.

## Requirements

- **Python 3**: Python 3.6 or higher
- **Dependencies**: Automatically installed from `requirements.txt` (includes `jsonschema` for validation)
- **Platform-specific**:
  - **macOS**: Homebrew, zsh
  - **Windows**: PowerShell 5.1+, winget (Windows Package Manager)
  - **APT-based Linux** (Debian, Ubuntu, Pop!_OS, Linux Mint, Elementary OS, Zorin OS, MX Linux, Raspberry Pi): apt, snap, flatpak (optional), zsh
  - **Pacman-based Linux** (Arch Linux, Manjaro, EndeavourOS): pacman, snap, flatpak (optional), zsh
  - **DNF-based Linux** (Fedora, RedHat/CentOS 8+): dnf, snap, flatpak (optional), zsh
  - **YUM-based Linux** (RedHat/CentOS 7): yum, zsh
  - **Zypper-based Linux** (OpenSUSE): zypper, zsh
  - **APK-based Linux** (Alpine): apk, zsh

## CI/CD

This repository uses GitHub Actions for continuous integration:

- **CI Workflow** (`ci.yml`): Lints remaining shell scripts with ShellCheck and validates Python syntax
- **Validate Configs Workflow** (`validateConfigs.yml`): Validates all JSON configuration files, checks package existence, font availability, repository accessibility, and Git configuration

Both workflows run automatically on pushes and pull requests to the `main` branch.

## Licence

ISC Licence. See LICENCE.md for details.
