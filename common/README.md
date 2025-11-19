# Common Modules

Shared logic and utilities used across all platform-specific scripts. This directory contains Python modules that provide common functionality.

## Structure

```text
common/
├── common.py          # Single entry point for Python - imports all common utilities
├── core/              # Core utilities (colours, logging, utilities)
├── configure/         # Configuration modules
├── install/           # Installation modules
├── linux/             # Linux-specific helpers
└── windows/           # Windows-specific helpers
```

## Entry Points

### `common.py` (Python)

The single entry point for all Python scripts. Import from this module to access all common utilities:

```python
from common.common import (
    # Logging
    printInfo, printSuccess, printError, printWarning, printSection,
    # Utilities
    commandExists, requireCommand, getJsonValue, getJsonArray, getJsonObject,
    # Package managers
    getPackageManager, createPackageManager,
    # Configuration
    configureGit, configureCursor, configureGithubSsh, cloneRepositories,
    # Installation
    installApps, installGoogleFonts,
    # Setup utilities
    initLogging, backupConfigs, checkDependencies, shouldCloneRepositories,
)
```

**Important**: Modules within `common/` should import directly from source modules (e.g., `from common.core.logging import printInfo`) to avoid circular dependencies. Only external scripts (in `systems/`, `test/`, `helpers/`) should import from `common.common`.

## Core Modules

### `core/logging.py`

Consistent logging functions with verbosity levels and ISO8601 timestamps:

- `printInfo(message)`: Print an info message in cyan (normal/verbose only)
- `printSuccess(message)`: Print a success message in green with ✓ emoji (normal/verbose only)
- `printError(message)`: Print an error message in red with ✗ emoji (always shown)
- `printWarning(message)`: Print a warning message in yellow with ⚠ emoji (normal/verbose only)
- `printVerbose(message)`: Print a verbose/debug message (verbose only)
- `printSection(message)`: Print a section header with `===` borders
- `printHelpText(...)`: Format and print consistent help messages
- `safePrint(*args, **kwargs)`: Thread-safe print function
- `colourise(text, code, enable)`: Apply ANSI colour codes to text if enabled
- `setVerbosity(level)`: Set verbosity level (`quiet`, `normal`, `verbose`)
- `setVerbosityFromArgs(quiet, verbose)`: Set verbosity from command-line arguments

All messages include ISO8601 timestamps by default (e.g., `[2024-01-15T14:30:45]`).

### `core/utilities.py`

Generic utility functions:

- `commandExists(cmd)`: Check if a command exists in PATH
- `requireCommand(cmd, installHint)`: Require a command to be available, show install hint if missing
- `getJsonValue(configPath, jsonPath, defaultValue)`: Get a JSON value from a file
- `getJsonArray(configPath, jsonPath)`: Get a JSON array from a file
- `getJsonObject(configPath, jsonPath)`: Get a JSON object from a file
- `findOperatingSystem()`: Detect the current operating system (returns "linux", "macos", "windows", or "unknown")
- `getOperatingSystem()`: Get the cached operating system
- `isOperatingSystem(targetOs)`: Check if the current OS matches the target

## Configuration Modules

### `configure/configureGit.py`

Git configuration functions (all support `dryRun` parameter):

- `configureGit(configPath, dryRun)`: Main function to configure Git from JSON config
- `configureGitUser(dryRun)`: Configure Git user name and email
- `configureGitDefaults(configPath, dryRun)`: Configure Git default settings
- `configureGitAliases(configPath, dryRun)`: Configure Git aliases
- `configureGitLfs(dryRun)`: Initialise Git LFS

### `configure/configureCursor.py`

Cursor editor configuration:

- `configureCursor(configPath, settingsPath, dryRun)`: Merge JSON settings from config file with existing Cursor settings
- `mergeJsonSettings(existing, config)`: Deep merge two JSON dictionaries

### `configure/configureGithubSsh.py`

GitHub SSH key configuration:

- `configureGithubSsh(configPath, dryRun)`: Generate SSH keys and help configure them for GitHub
- `copyToClipboard(text)`: Copy text to clipboard (platform-specific)
- `openUrl(url)`: Open URL in default browser (platform-specific)
- `startSshAgent()`: Start SSH agent
- `addKeyToSshAgent(keyPath)`: Add SSH key to agent

### `configure/cloneRepositories.py`

Repository cloning:

- `cloneRepositories(configPath, dryRun)`: Clone Git repositories from JSON config
- `cloneRepository(repoUrl, workPath)`: Clone a single repository
- `isRepositoryCloned(repoUrl, workPath)`: Check if repository is already cloned
- `expandPath(path)`: Expand path variables (e.g., `$HOME`, `~`)

## Installation Modules

### `install/installApps.py`

Application installation with parallel processing:

- `installApps(...)`: Main function to install apps from JSON config (primary and optional secondary package managers)
- `installPackages(...)`: Install a list of packages in parallel with progress indicators
- `installFromConfig(...)`: Install from JSON config
- `installFromConfigWithLinuxCommon(...)`: Install with Linux common packages merged
- `runConfigCommands(phase, configPath)`: Run preInstall/postInstall commands
- `InstallResult`: Dataclass with counts and lists of installed/updated packages for rollback tracking

Packages are installed in parallel (max 8 workers) with real-time progress indicators showing "Installing package X/Y: ✓ package (installed/updated/failed)".

### `install/installFonts.py`

Google Fonts installation with parallel processing:

- `installGoogleFonts(configPath, installDir, dryRun)`: Main function to install fonts from JSON config
- Downloads fonts in parallel with progress indicators
- Converts WOFF2 to TTF when needed
- Installs fonts in parallel with verification

Progress indicators show "Downloading font X/Y: ✓ font variant" and "Installing font X/Y: ✓ font variant".

### `install/setupArgs.py`

Setup script argument parsing:

- `parseSetupArgs(args)`: Parse command-line arguments for setup scripts
- `determineRunFlags(setupArgs)`: Determine which setup steps to run based on arguments
- `SetupArgs`: Dataclass for setup arguments (includes `quiet`, `verbose`, `resume`, `noResume`, `listSteps`)
- `RunFlags`: Dataclass for run flags

### `install/setupUtils.py`

Shared setup utilities:

- `initLogging(platformName)`: Initialise logging to a file (platform-specific temp directory)
- `backupConfigs(noBackup, dryRun, cursorSettingsPath)`: Backup configuration files before setup (returns backup directory path)
- `checkDependencies(requiredCommands, checkFunctions)`: Check if required dependencies are installed
- `shouldCloneRepositories(configPath, workPathKey)`: Check if repositories should be cloned (only on first run)

### `install/setupState.py`

Setup state tracking for resume functionality:

- `createState(platformName)`: Create a new setup state
- `loadState(platformName)`: Load existing setup state
- `clearState(platformName)`: Clear setup state after successful completion
- `isStepComplete(state, stepName)`: Check if a step is complete
- `markStepComplete(state, stepName)`: Mark a step as complete
- `markStepFailed(state, stepName)`: Mark a step as failed

### `install/rollback.py`

Rollback capability for failed setups:

- `createSession(platformName)`: Create a rollback session
- `saveSession(session)`: Save rollback session to disk
- `loadSession(sessionId)`: Load a rollback session
- `rollback(platformName, uninstallFunc)`: Rollback a failed setup session

## System Modules

### `systems/systemBase.py`

Base class for system-specific setup implementations:

- `SystemBase`: Abstract base class implementing the common setup flow
- `setupDevEnv()`: Set up development environment (optional step)
- `listSteps()`: Preview what steps will be executed
- Supports resume functionality via setup state tracking

### `systems/cli.py`

Unified CLI for individual operations:

- `status`: Check environment status
- `fonts`, `apps`, `git`, `ssh`, `cursor`, `repos`: Individual setup operations
- `verify`: Run post-setup verification checks
- `rollback`: Rollback a failed setup session

### `systems/status.py`

Status checking:

- `runStatusCheck(system)`: Check installed packages, Git config, fonts, repositories, Cursor settings
- Supports `--quiet` and `--verbose` flags

### `systems/verify.py`

Post-setup verification:

- `runVerification(system)`: Verify critical packages, Git config, fonts, SSH connectivity, repositories, Cursor settings

### `systems/validate.py`

Configuration validation:

- Validates JSON syntax and schema compliance
- Supports `--quiet` and `--verbose` flags

### `systems/schemas.py`

JSON schema definitions for configuration files.

## Platform-Specific Modules

### `linux/packageManager.py`

Linux package manager abstraction (legacy - prefer `install/packageManagers.py` for new code):

- `PackageManager`: Abstract base class for package managers
- `AptPackageManager`, `YumPackageManager`, `DnfPackageManager`, `RpmPackageManager`, `ZypperPackageManager`, `PacmanPackageManager`: Package manager implementations
- `getPackageManager(managerName)`: Factory function to create appropriate package manager
- `mapPackageName(package, manager)`: Map Debian/Ubuntu package names to RPM equivalents

### `install/packageManagers.py`

Platform-specific package manager helper classes (recommended for new code):

- `Apt`, `Snap`, `Brew`, `BrewCask`, `Winget`, `Store`, `Dnf`, `Zypper`, `Pacman`: Package manager classes
- All provide `install()` and `update()` methods with detailed error context (command, exit code, stderr)

### `windows/packageManager.py`

Windows package manager utilities:

- `isWingetInstalled()`: Check if Windows Package Manager (winget) is installed
- `installWinget()`: Install winget if not available
- `updateWinget()`: Update winget package index
- `updateMicrosoftStore()`: Update Microsoft Store apps
- `isAppInstalled(appId)`: Check if a winget app is installed

## Import Guidelines

### For Modules Within `common/`

Import directly from source modules to avoid circular dependencies:

```python
# ✅ Good
from common.core.logging import printInfo
from common.core.utilities import commandExists

# ❌ Bad (circular dependency)
from common.common import printInfo
```

### For External Scripts

Import from `common.common`:

```python
# ✅ Good (for scripts in systems/, test/, helpers/)
from common.common import printInfo, commandExists
```

## Dependency Structure

```text
common.core.logging (base - no dependencies)
    ↑
common.core.utilities
    ↑
common.configure.* (all import from core)
common.install.* (all import from core)
common.linux.* (all import from core)
common.windows.* (all import from core)
    ↑
common.common (aggregator - imports all above)
    ↑
systems/*, test/*, helpers/* (external - import from common.common)
```

This structure ensures no circular dependencies and clean separation of concerns.
