# Test Scripts

This directory contains both **validation scripts** for configuration files and **unit tests** for core functions. All scripts are written in Python3 and import from `common/common.py` for shared functionality.

## Overview

### Validation Scripts

These scripts validate JSON configuration files to ensure:

- Valid JSON syntax
- Package existence in package managers
- Font availability via Google Fonts API
- Repository accessibility
- Git configuration validity
- Work path syntax correctness

All validation scripts include timing information and provide actionable feedback.

## Validation Scripts

All validation scripts support `--help` and `--quiet` flags. Use `--quiet` to only show final success/failure message.

### `validatePackages.py` (Unified)

Unified package validation script that automatically detects package managers from JSON config files and validates packages accordingly.

**Supported Package Managers:**

- **Homebrew** (`brew`): Validates via `brew info`
- **Homebrew Cask** (`brewCask`): Validates via `brew info --cask`
- **APT** (`apt`): Validates via `apt-cache show`
- **Snap** (`snap`): Validates via `snap info`
- **Winget** (`winget`): Validates via `winstall.app` API (HTTP)
- **Windows Store** (`windowsStore`): Placeholder (validates at installation time)
- **Linux Common** (`linuxCommon`): For `linuxCommon.json`, validates against all available Linux package managers (apt, yum, dnf, rpm) on the system running the script

**Features:**

- Auto-detects package managers from JSON config structure
- Handles `linuxCommon` merging for Ubuntu/Raspberry Pi configs
- OOP design with abstract base class for extensibility
- Platform-specific validation logic
- For `linuxCommon.json`, dynamically detects available package managers and validates against all of them

**Usage:**

```bash
python3 test/validatePackages.py configs/macos.json [--quiet]
python3 test/validatePackages.py configs/ubuntu.json [--quiet]
python3 test/validatePackages.py configs/win11.json [--quiet]
python3 test/validatePackages.py configs/linuxCommon.json [--quiet]
```

For comprehensive `linuxCommon.json` validation with detailed recommendations, use `validateLinuxCommonPackages.py` instead.

### `validateFonts.py`

Validates Google Fonts configuration:

- Checks JSON syntax
- Validates font names exist via Google Fonts API
- Validates font variants are available for each font

**Usage:**

```bash
python3 test/validateFonts.py configs/fonts.json [--quiet]
```

### `validateRepositories.py`

Validates repository configuration (JSON syntax, work paths, URLs, accessibility).

**Usage:**

```bash
python3 test/validateRepositories.py configs/repositories.json [--quiet]
```

### `validateGitConfig.py`

Validates Git configuration (JSON syntax, aliases, defaults, user name, email, GitHub username).

**Usage:**

```bash
python3 test/validateGitConfig.py configs/gitConfig.json [--quiet]
```

### `validateLinuxCommonPackages.py`

Validates Linux common packages across all supported package managers with actionable recommendations.

**Usage:**

```bash
python3 test/validateLinuxCommonPackages.py configs/linuxCommon.json [--quiet]
```

## Unified Validation

Use the unified validation script for all configs:

```bash
# Validate all platform configs
python3 -m common.systems.validate

# Validate specific platform
python3 -m common.systems.validate ubuntu [--quiet]
```

This validates JSON syntax, schema compliance, packages, fonts, repositories, and Git config.

## CI Integration

All validation scripts are automatically run via GitHub Actions on every push and pull request. See `.github/workflows/validateConfigs.yml` for the CI configuration.

## Dependencies

All validation scripts require:

- **Python 3**: Python 3.6 or higher
- **common/common.py**: Shared utilities and logging functions
- **Platform-specific tools** (for package validation):
  - macOS: `brew` (for package validation)
  - Ubuntu/Raspberry Pi: `apt-cache`, `snap` (for package validation)
  - Windows: Internet connection (for `winstall.app` API)

## Unit Tests

All unit tests use Python's built-in `unittest` framework and follow repository naming conventions (camelCase for methods, PascalCase for classes).

### `testSetupValidation.py`

End-to-end tests for setup validation that simulate user journeys, testing success and failure scenarios.

**Framework:** Uses Python's built-in `unittest` framework (standard library, no external dependencies).

**Naming Conventions:** Follows repository conventions:
- **Test Classes**: PascalCase (e.g., `TestSetupValidation`, `TestSetupValidationIntegration`)
- **Test Methods**: camelCase with `test` prefix (e.g., `testValidConfigDirectory`, `testMissingPlatformConfig`)
- **Helper Methods**: camelCase (e.g., `createValidConfig`, `setUp`, `tearDown`)
- **Variables**: camelCase (e.g., `tempDir`, `configFile`, `platformConfig`)

**Test Coverage:**

- Valid config directory scenarios
- Missing config directory scenarios
- Empty config directory scenarios
- Invalid JSON scenarios
- Missing platform config scenarios
- Custom config directory (CLI arg and env var)
- Complete setup validation flow (success and failure paths)
- Permission error handling

**Usage:**

```bash
# Run all setup validation tests
python3 test/testSetupValidation.py

# Run with verbose output (default)
python3 test/testSetupValidation.py -v

# Run via unittest module
python3 -m unittest test.testSetupValidation

# Run specific test class
python3 -m unittest test.testSetupValidation.TestSetupValidation

# Run specific test method
python3 -m unittest test.testSetupValidation.TestSetupValidation.testValidConfigDirectory
```

**Test Structure:**

- `TestSetupValidation`: Unit tests for individual validation functions
- `TestSetupValidationIntegration`: Integration tests for setup flow

**Features:**

- **22+ test cases** covering all validation scenarios
- **Temporary directory handling** for isolated test environments
- **Mocking support** for testing CLI arguments and environment variables
- **Cross-platform compatibility** tests
- **User journey simulation** - tests flow as if a real user is running setup
- **Standard unittest patterns** - uses `setUp()`, `tearDown()`, `assertTrue()`, `assertFalse()`, etc.

**Example Output:**

```text
testValidConfigDirectory ... ok
testMissingConfigDirectory ... ok
testInvalidJsonPlatformConfig ... ok
...
----------------------------------------------------------------------
Ran 22 tests in 0.078s

OK
```

These tests verify that setup validation fails early and clearly when configuration files are missing or invalid.

### `testUtilities.py`

Comprehensive unit tests for core utility functions using Python's built-in `unittest` framework.

**Test Coverage:**

- **Command checking**: `commandExists()`, `requireCommand()`
- **JSON parsing**: `getJsonValue()`, `getJsonArray()`, `getJsonObject()`
- **Path expansion**: `expandPath()`
- **OS detection**: `findOperatingSystem()`, `getOperatingSystem()`, `isOperatingSystem()`

**Usage:**

```bash
# Run all unit tests
python3 test/testUtilities.py

# Run with verbose output
python3 test/testUtilities.py -v

# Run specific test class
python3 test/testUtilities.py TestJsonParsing

# Run specific test
python3 test/testUtilities.py TestJsonParsing.test_getJsonValue_simple_key
```

**Features:**

- **35+ test cases** covering all core utility functions
- **Mocking support** for testing error conditions and external dependencies
- **Temporary file handling** for JSON parsing tests
- **Cross-platform compatibility** tests for OS detection and path expansion

**Example Output:**

```text
test_commandExists_existing_command ... ok
test_getJsonValue_simple_key ... ok
test_expandPath_home_variable ... ok
...
----------------------------------------------------------------------
Ran 35 tests in 0.155s

OK
```

## Best Practices

1. **Run before committing**: Always run validation scripts and unit tests locally before committing changes
2. **Fix issues immediately**: Address validation errors and test failures before pushing to avoid CI failures
3. **Check timing**: Monitor validation times to catch performance regressions
4. **Review recommendations**: Pay attention to actionable recommendations from validation scripts
5. **Test edge cases**: Test with invalid configs to ensure error handling works correctly
6. **Maintain test coverage**: Add unit tests when adding new core utility functions
