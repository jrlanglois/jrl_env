# Configuration Files

JSON configuration files that define what gets installed and configured on each platform. All configuration files use 4-space indentation and CRLF line endings.

## Platform-Specific Configs

### `macos.json`

macOS-specific configuration:

- **`brew`**: Homebrew packages to install
- **`brewCask`**: Homebrew Cask applications to install
- **`ohMyZshTheme`**: Oh My Zsh theme to use
- **`commands`**: Optional `preInstall` and `postInstall` command objects

### `ubuntu.json`

Ubuntu-specific configuration:

- **`linuxCommon`**: Boolean flag to merge packages from `linuxCommon.json`
- **`apt`**: APT packages to install
- **`snap`**: Snap packages to install
- **`cruft`**: Packages to uninstall (wildcard patterns)
- **`ohMyZshTheme`**: Oh My Zsh theme to use
- **`commands`**: Optional `preInstall` and `postInstall` command objects

### `raspberrypi.json`

Raspberry Pi-specific configuration:

- **`linuxCommon`**: Boolean flag to merge packages from `linuxCommon.json`
- **`apt`**: APT packages to install
- **`snap`**: Snap packages to install
- **`cruft`**: Packages to uninstall (wildcard patterns)
- **`ohMyZshTheme`**: Oh My Zsh theme to use
- **`commands`**: Optional `preInstall` and `postInstall` command objects

### `win11.json`

Windows 11-specific configuration:

- **`winget`**: Winget packages to install (format: `Publisher.PackageName`)
- **`commands`**: Optional `preInstall` and `postInstall` command objects

## Shared Configs

### `linuxCommon.json`

Common Linux packages shared across all Linux distributions:

- **`linuxCommon`**: Array of package names that should exist in all supported Linux package managers (apt, yum, dnf, rpm)
- Packages are automatically merged with distro-specific packages when `linuxCommon: true` is set in the platform config
- Package names are automatically mapped to RPM equivalents for RPM-based systems (e.g., `libcurl4-openssl-dev` → `libcurl-devel`)

### `fonts.json`

Google Fonts to download and install:

- **`fonts`**: Array of font objects with:
  - **`name`**: Font family name (e.g., "Roboto")
  - **`variants`**: Array of font variants to install (e.g., `["400", "400italic", "700", "700italic"]`)

Fonts are downloaded from Google Fonts API and installed to platform-specific font directories.

### `repositories.json`

Git repositories to clone:

- **`workPathUnix`**: Unix-style work directory path (e.g., `"$HOME/Projects"`)
- **`workPathWindows`**: Windows-style work directory path (e.g., `"C:\\Projects"`)
- **`repositories`**: Array of repository URLs (SSH or HTTPS)

Repositories are cloned into a structured directory: `<workPath>/<owner>/<repo>/`

### `gitConfig.json`

Git configuration:

- **`user`**: Git user information
  - **`name`**: User name (must be valid UTF-8 and web-compatible)
  - **`email`**: User email (must be valid email format)
- **`defaults`**: Git default settings
  - **`init.defaultBranch`**: Default branch name
  - **`pull.rebase`**: Pull rebase setting
  - **`fetch.parallel`**: Fetch parallel setting (integer)
  - Any other Git config keys
- **`aliases`**: Git aliases
  - Key-value pairs where key is the alias name and value is the command
- **`lfs`**: Git LFS configuration
  - **`enabled`**: Boolean to enable/disable Git LFS
- **`usernameGitHub`**: GitHub username for SSH key generation

### `cursorSettings.json`

Cursor editor settings:

- Any valid Cursor/VSCode settings JSON
- Settings are merged with existing Cursor settings (config file takes precedence)
- Common settings include:
  - **`editor.fontFamily`**: Font family for editor
  - **`editor.fontSize`**: Font size
  - **`editor.tabSize`**: Tab size
  - **`editor.wordWrap`**: Word wrap setting
  - Any other Cursor/VSCode settings

## Command Objects

Command objects can be specified in `preInstall` and `postInstall` arrays:

```json
{
  "name": "Command Name",
  "shell": "bash",
  "command": "echo 'Hello World'",
  "runOnce": true
}
```

- **`name`**: Human-readable name for the command
- **`shell`**: Shell to use (`bash`, `powershell`, `cmd`, etc.)
- **`command`**: Command to execute
- **`runOnce`**: If `true`, command is only run once (tracked via flag files)

## Validation

All configuration files are validated via CI on every push and pull request. Validation includes JSON syntax, schema compliance, package existence, font availability, repository accessibility, and Git configuration.

### Local Validation

**Unified validation (recommended):**

```bash
# Validate all platform configs
python3 -m common.systems.validate

# Validate specific platform
python3 -m common.systems.validate ubuntu [--quiet]
```

**Individual validation scripts:**

```bash
# Package validation
python3 test/validatePackages.py configs/macos.json [--quiet]
python3 test/validateLinuxCommonPackages.py configs/linuxCommon.json [--quiet]

# Other configs
python3 test/validateFonts.py configs/fonts.json [--quiet]
python3 test/validateRepositories.py configs/repositories.json [--quiet]
python3 test/validateGitConfig.py configs/gitConfig.json [--quiet]
```

All validation scripts support `--help` and `--quiet` flags. See [`test/README.md`](../test/README.md) for details.

## JSON Formatting

All JSON files follow these conventions:

- **Indentation**: 4 spaces
- **Line Endings**: CRLF (`\r\n`)
- **Encoding**: UTF-8
- **Style**: Allman braces (opening brace on its own line)

Example:

```json
{
    "key": "value",
    "array": [
        "item1",
        "item2"
    ],
    "object": {
        "nested": "value"
    }
}
```

## Best Practices

1. **Keep packages up to date**: Regularly update package lists to ensure latest versions
2. **Use descriptive names**: Use clear, descriptive names for commands and aliases
3. **Validate before committing**: Run validation scripts locally before committing changes
4. **Document custom commands**: Add comments or documentation for non-standard commands
5. **Test on clean systems**: Test configuration changes on clean systems to catch issues early
