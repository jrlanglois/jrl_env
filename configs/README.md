# Configuration Files

JSON configuration files that define what gets installed and configured on each platform.

All configuration files use:
* 4-spaces (not tabs)
* CRLF line endings.
  * This is my preference. I don't really care about yours!
  * This shouldn't have an impact when providing your own hand-rolled configurations to the setup environment.

## Configuration Directory Specification

### Required Filenames

A valid `configs/` directory must contain the following files with exact names:

**Platform-Specific Configs (at least one required):**

- `alpine.json` - Alpine Linux configuration
- `archlinux.json` - Arch Linux configuration
- `debian.json` - Debian configuration
- `elementary.json` - Elementary OS configuration
- `endeavouros.json` - EndeavourOS configuration
- `fedora.json` - Fedora configuration
- `linuxmint.json` - Linux Mint configuration
- `macos.json` - macOS configuration
- `manjaro.json` - Manjaro configuration
- `mxlinux.json` - MX Linux configuration
- `opensuse.json` - OpenSUSE configuration
- `popos.json` - Pop!_OS configuration
- `raspberrypi.json` - Raspberry Pi OS configuration
- `redhat.json` - RedHat/CentOS configuration
- `ubuntu.json` - Ubuntu configuration
- `win11.json` - Windows 11 configuration
- `zorin.json` - Zorin OS configuration

**Shared Configs (all optional, but recommended):**

- `gitConfig.json` - Git user configuration, aliases, and defaults (skipped if missing)
- `fonts.json` - Google Fonts to install (skipped if missing)
- `repositories.json` - Git repositories to clone (skipped if missing)
- `cursorSettings.json` - Cursor/VSCode editor settings (skipped if missing)

**Optional Configs:**

- `linuxCommon.json` - Shared Linux packages (only used if `useLinuxCommon: true` in platform configs)
- `android.json` - Android SDK components configuration (used if Android Studio is installed or in platform config)

### File Naming Conventions

- All config files must use lowercase filenames
- Platform configs use the format: `<platform>.json` (e.g., `ubuntu.json`, `macos.json`)
- Shared configs use camelCase: `gitConfig.json`, `cursorSettings.json`
- File extensions must be `.json` (lowercase)
- No spaces or special characters in filenames (except hyphens in platform names like `raspberrypi`)

### Directory Structure

```text
configs/
├── <platform>.json          # One or more platform configs (required for detected platform)
├── gitConfig.json           # Optional (Git config step skipped if missing)
├── fonts.json               # Optional (font installation skipped if missing)
├── repositories.json        # Optional (repository cloning skipped if missing)
├── cursorSettings.json      # Optional (Cursor config skipped if missing)
├── linuxCommon.json         # Optional (only if using Linux common packages)
└── android.json             # Optional (Android SDK config, used if Android Studio detected)
```

### File Existence Behaviour

- **Missing platform config**: Setup will print an error and skip app installation, but continue with other steps (e.g., running on Ubuntu without `ubuntu.json` will skip app installation)
- **Missing shared configs**: Setup will skip the corresponding step gracefully:
  - No `gitConfig.json` → Git configuration step skipped
  - No `fonts.json` → Font installation step skipped
  - No `repositories.json` → Repository cloning step skipped
  - No `cursorSettings.json` → Cursor configuration step skipped
- **Missing optional configs**: Setup continues normally (e.g., `linuxCommon.json` is only needed if `useLinuxCommon: true` in platform config)
- **Android config**: `android.json` is used if Android Studio is detected or listed in platform config. If Android Studio is not found and not in config, user will be prompted to configure Android SDK

### Validation and Error Handling

**Validation Behaviour:**

The setup system performs strict validation and **fails early** with verbose error messages:

1. **Config directory validation**:
   - Checks that directory exists and is accessible
   - Verifies directory is not empty (must contain at least one JSON file)
   - Fails setup immediately if validation fails

2. **Platform config validation**:
   - Verifies platform config file exists (required for detected platform)
   - Validates JSON syntax before proceeding
   - Fails setup immediately if file is missing or invalid JSON

3. **Full configuration validation**:
   - Validates all config files (platform + shared configs)
   - Checks JSON syntax, schema compliance, and data validity
   - Fails setup immediately if any errors are found
   - Warnings are shown but don't stop setup (e.g., empty arrays)

4. **Invalid JSON**:
   - JSON syntax errors cause immediate failure with clear error messages
   - Setup does not proceed with invalid configurations

5. **Empty or useless configs**:
   - Empty arrays (e.g., `"apt": []`) generate warnings but don't stop setup
   - Empty config files may cause steps to be skipped

**Error Messages:**

When validation fails, you'll see:
- Clear error messages indicating what's wrong
- Specific file paths and line numbers (when available)
- Actionable guidance on how to fix the issues
- Setup stops immediately - no partial execution

**Manual Validation:**

You can also run validation manually before setup:
```bash
python3 -m common.systems.validate --configDir /path/to/configs
```

This is useful for:
- Pre-flight checks before running setup
- CI/CD pipelines
- Debugging configuration issues

## Platform-Specific Configs

### macOS (`macos.json`)

```javascript
{
    "brew": ["string"],              // Homebrew packages (formula names)
    "brewCask": ["string"],          // Homebrew Cask applications (cask names)
    "shell": {
        "ohMyZshTheme": "string"   // Oh My Zsh theme name
    },
    "commands": {
        "preInstall": [Command],     // Commands to run before installation
        "postInstall": [Command]     // Commands to run after installation
    }
}
```

**Package Managers:**

- `brew`: Homebrew formula packages (e.g., `"git"`, `"node"`, `"postgresql"`)
- `brewCask`: Homebrew Cask GUI applications (e.g., `"google-chrome"`, `"visual-studio-code"`)

### APT-based Linux (Debian, Ubuntu, Pop!_OS, Linux Mint, Elementary OS, Zorin OS, MX Linux)

Configuration files: `debian.json`, `ubuntu.json`, `popos.json`, `linuxmint.json`, `elementary.json`, `zorin.json`, `mxlinux.json`

```javascript
{
    "useLinuxCommon": boolean,       // Merge packages from linuxCommon.json (default: false)
    "apt": ["string"],                // APT packages (Debian/Ubuntu package names)
    "snap": ["string"],               // Snap packages (optional, cross-distro applications)
    "flatpak": ["string"],            // Flatpak packages (optional, cross-distro applications)
    "cruft": {                        // Packages to uninstall by package manager
        "apt": ["string"],            // APT packages (supports wildcards: `"package*"`)
        "snap": ["string"]            // Snap packages to remove
    }
    "shell": {
        "ohMyZshTheme": "string"    // Oh My Zsh theme name
    },
    "commands": {
        "preInstall": [Command],
        "postInstall": [Command]
    }
}
```

**Package Managers:**

- `apt`: APT packages to install (e.g., `"docker.io"`, `"postgresql"`, `"redis-server"`)
- `snap`: Snap packages to install (optional, e.g., `"code"`, `"slack"`, `"spotify"`)
- `flatpak`: Flatpak packages to install (optional, e.g., Flathub application IDs)
- `cruft.apt`: APT packages to remove (supports wildcards: `"libreoffice*"`, `"chromium*"`)
- `cruft.snap`: Snap packages to remove (optional)

### Raspberry Pi (`raspberrypi.json`)

Same structure as `ubuntu.json`:

```javascript
{
    "linuxCommon": boolean,
    "apt": ["string"],
    "snap": ["string"],
    "cruft": {
        "apt": ["string"]             // Packages to uninstall (wildcards supported)
    },
    "shell": {
        "ohMyZshTheme": "string"
    },
    "commands": {
        "preInstall": [Command],
        "postInstall": [Command]
    }
}
```

**Package Managers:**

Same as Ubuntu (apt, snap, cruft)

### DNF-based Linux (Fedora, RedHat/CentOS 8+)

Configuration files: `fedora.json`, `redhat.json`

```javascript
{
    "useLinuxCommon": boolean,        // Merge packages from linuxCommon.json
    "dnf": ["string"],                // DNF packages (RPM package names)
    "snap": ["string"],               // Snap packages (optional, cross-distro applications)
    "flatpak": ["string"],            // Flatpak packages (optional, cross-distro applications)
    "shell": {
        "ohMyZshTheme": "string"
    },
    "commands": {
        "preInstall": [Command],
        "postInstall": [Command]
    },
    "cruft": {
        "dnf": ["string"],            // Packages to uninstall (wildcards supported)
        "snap": ["string"]            // Snap packages to remove
    }
}
```

**Package Managers:**

- `dnf`: DNF packages to install (e.g., `"docker"`, `"postgresql"`, `"redis"`)
- `snap`: Snap packages to install (optional, e.g., `"code"`, `"slack"`, `"spotify"`)
- `flatpak`: Flatpak packages to install (optional, e.g., Flathub application IDs)
- `cruft.dnf`: DNF packages to remove (wildcards supported)
- `cruft.snap`: Snap packages to remove (optional)

### OpenSUSE (`opensuse.json`)

```javascript
{
    "linuxCommon": boolean,
    "zypper": ["string"],             // Zypper packages (RPM package names)
    "shell": {
        "ohMyZshTheme": "string"
    },
    "commands": {
        "preInstall": [Command],
        "postInstall": [Command]
    },
    "cruft": {
        "zypper": ["string"]          // Packages to uninstall
    }
}
```

**Package Managers:**

- `zypper`: Zypper packages to install (e.g., `"docker"`, `"postgresql"`, `"redis"`)
- `cruft.zypper`: Zypper packages to remove

**Note:** Package names from `linuxCommon.json` are automatically mapped to RPM equivalents.

### Pacman-based Linux (Arch Linux, Manjaro, EndeavourOS)

Configuration files: `archlinux.json`, `manjaro.json`, `endeavouros.json`

```javascript
{
    "useLinuxCommon": boolean,
    "pacman": ["string"],             // Pacman packages (Arch package names)
    "snap": ["string"],               // Snap packages (optional, cross-distro applications)
    "flatpak": ["string"],            // Flatpak packages (optional, cross-distro applications)
    "shell": {
        "ohMyZshTheme": "string"
    },
    "commands": {
        "preInstall": [Command],
        "postInstall": [Command]
    },
    "cruft": {
        "pacman": ["string"]          // Packages to uninstall
    }
}
```

**Package Managers:**

- `pacman`: Pacman packages to install (e.g., `"docker"`, `"postgresql"`, `"redis"`)
- `cruft.pacman`: Pacman packages to remove
- `snap`: Snap packages (optional, e.g., `"code"`, `"slack"`, `"spotify"`)
- `flatpak`: Flatpak packages (optional, e.g., Flathub application IDs)

**Note:** Package names from `linuxCommon.json` may need manual mapping for Arch-specific package names.

### Alpine Linux (`alpine.json`)

```javascript
{
    "apk": ["string"],                // APK packages (Alpine package names)
    "shell": {
        "ohMyZshTheme": "string"
    },
    "commands": {
        "preInstall": [Command],
        "postInstall": [Command]
    },
    "cruft": {
        "apk": ["string"]             // Packages to uninstall
    }
}
```

**Package Managers:**

- `apk`: APK packages to install (e.g., `"docker"`, `"postgresql"`, `"redis"`, `"build-base"`)
- `cruft.apk`: APK packages to remove

**Note:** Alpine uses musl libc instead of glibc. Package names often differ from other distributions (e.g., `build-essential` → `build-base`). Snap and Flatpak are typically not used on Alpine due to its minimal nature.

### Windows 11 (`win11.json`)

```javascript
{
    "winget": ["string"],             // Winget packages (format: "Publisher.PackageName")
    "windowsStore": ["string"],       // Microsoft Store app IDs
    "android": {
        "sdkComponents": ["string"]   // Optional: Override android.json config
    },
    "commands": {
        "preInstall": [Command],
        "postInstall": [Command]
    }
}
```

**Package Managers:**

- `chocolatey`: Chocolatey packages (e.g., `"graphviz"`, `"doxygen.install"`)
- `winget`: Windows Package Manager packages (format: `"Publisher.PackageName"`, e.g., `"Git.Git"`, `"Microsoft.VisualStudioCode"`)
- `windowsStore`: Microsoft Store app IDs (e.g., `"9MV0B5HZVK9Z"`)

## Shared Configs

### Linux Common (`linuxCommon.json`)

```javascript
{
    "linuxCommon": ["string"]         // Package names that should exist in all Linux package managers
}
```

**Purpose:** Shared packages across all Linux distributions. Packages are automatically merged when `useLinuxCommon: true` is set in platform configs.

**Package Name Mapping:**

- Debian/Ubuntu package names are automatically mapped to RPM equivalents for RPM-based systems
- Example mappings: `libcurl4-openssl-dev` → `libcurl-devel`, `zlib1g-dev` → `zlib-devel`

**Supported Package Managers:**

apt, yum, dnf, rpm, zypper, pacman, apk, snap, flatpak

### Fonts (`fonts.json`)

```javascript
{
    "googleFonts": ["string"]         // Font family names from Google Fonts
}
```

**Format:** Array of font family names (e.g., `"Roboto"`, `"Inter"`, `"Open Sans"`)

**Installation:** Fonts are downloaded from Google Fonts API and installed to platform-specific directories:

- **Linux/macOS**: `~/.local/share/fonts/`
- **Windows**: `%LOCALAPPDATA%\Microsoft\Windows\Fonts\`

### Repositories (`repositories.json`)

```javascript
{
    "workPathUnix": "$HOME/work",
    "workPathWindows": "D:\\work",
    "repositories": [
        "git@github.com:someOwner/repo.git",
        {
            "pattern": "git@github.com:otherOwner/*",
            "visibility": "all"
        }
    ]
}
```

**Format:** Array of repository entries (strings or objects)

**String format (backward compatible):**
- Direct repository URLs: `"git@github.com:owner/repo.git"`

**Object format (wildcard support):**
- `pattern`: Wildcard pattern (`"git@github.com:owner/*"`)
- `visibility`: `"all"` (default), `"public"`, or `"private"`

**Wildcard features:**
- Auto-discovers all repos from GitHub user/org
- HTTP caching with ETags (RFC 7232) for performance
- Clear cache: `python3 setup.py --clearRepoCache`

**Example:**

- `workPathUnix`: Path like `"$HOME/work"` or `"~/Projects"`
- `workPathWindows`: Path like `"D:\\work"` or `"C:\\Projects"`
- `repositories`: Array of Git URLs (e.g., `"git@github.com:user/repo.git"` or `"https://github.com/user/repo.git"`)

**Cloning Structure:** Repositories are cloned to `<workPath>/<owner>/<repo>/`

### Git Config (`gitConfig.json`)

```javascript
{
    "user": {
        "name": "string",             // Git user name (UTF-8, web-compatible)
        "email": "string",            // Git user email (valid email format)
        "usernameGitHub": "string"  // GitHub username (for SSH key generation)
    },
    "defaults": {
        "init.defaultBranch": "string",
        "pull.rebase": "string|boolean",
        "fetch.parallel": number,
        // ... any other Git config keys
    },
    "aliases": {
        "aliasName": "string"       // Key-value pairs: alias name → Git command
    },
    "lfs": {
        "enabled": boolean            // Enable/disable Git LFS
    }
}
```

**Format:**

- `user.name`: Must be valid UTF-8 and web-compatible
- `user.email`: Must be valid email format
- `defaults`: Any Git config keys (values can be strings, booleans, or numbers)
- `aliases`: Key-value pairs where key is alias name, value is Git command
- `lfs.enabled`: Boolean to enable/disable Git LFS

### Cursor Settings (`cursorSettings.json`)

```javascript
{
    // Any valid Cursor/VSCode settings JSON
    "editor.fontSize": number,
    "editor.fontFamily": "string",
    "editor.tabSize": number,
    // ... any other Cursor/VSCode settings
}
```

**Format:** Any valid Cursor/VSCode settings JSON. Settings are merged with existing Cursor settings (config file takes precedence).

**Common Settings:**

- `editor.*`: Editor settings (font, tab size, word wrap, etc.)
- `files.*`: File handling settings (auto-save, trim whitespace, etc.)
- `workbench.*`: Workbench appearance and behaviour
- `terminal.*`: Integrated terminal settings
- `git.*`: Git integration settings

### Android (`android.json`)

```javascript
{
    "android": {
        "sdkComponents": ["string"]    // Android SDK components to install via sdkmanager
    }
}
```

**Format:** Array of SDK component names (e.g., `"platform-tools"`, `"platforms;android-36"`, `"build-tools;36.1.0"`)

**Purpose:** Configure Android SDK components that should be installed via `sdkmanager`. This is a cross-platform configuration similar to Linux common.

**Usage:**

- **Common approach**: Create `android.json` in the `configs/` directory. This will be used automatically if Android Studio is detected or listed in your platform config.
- **Platform override**: You can override the common Android config by adding an `android` section directly to your platform config (e.g., `win11.json`, `macos.json`). Platform-specific configs take precedence over `android.json`.

**When Android Configuration Runs:**

1. If Android Studio is listed in your platform config packages (e.g., `"Google.AndroidStudio"` in `winget` array), Android configuration will run automatically after app installation.
2. If Android Studio is already installed on your system, Android configuration will run automatically.
3. If Android Studio is not found and not in your config, you will be prompted whether to configure Android SDK components.

**SDK Component Examples:**

- `"platform-tools"` - Android platform tools (adb, fastboot, etc.)
- `"platforms;android-36"` - Android platform API level 36
- `"build-tools;36.1.0"` - Build tools version 36.1.0
- `"ndk;29.0.14206865"` - Android NDK version
- `"cmake;4.1.2"` - CMake version
- `"emulator"` - Android emulator
- `"system-images;android-36;google_apis;x86_64"` - System image for emulator

**Note:** Android SDK must be installed (typically via Android Studio) before SDK components can be configured. The setup will detect Android SDK via `ANDROID_HOME`/`ANDROID_SDK_ROOT` environment variables or common installation paths.
- `[language]`: Language-specific settings (e.g., `[python]`, `[cpp]`)

## Command Objects

Command objects can be specified in `preInstall` and `postInstall` arrays:

```javascript
{
    "name": "string",                 // Human-readable command name
    "shell": "string",                // Shell to use: "bash", "powershell", "cmd", "zsh"
    "command": "string",               // Command to execute
    "runOnce": boolean                // If true, command only runs once (tracked via flag files)
}
```

**Fields:**

- `name`: Human-readable identifier for the command
- `shell`: Shell interpreter (`bash`, `powershell`, `cmd`, `zsh`, etc.)
- `command`: Command string to execute
- `runOnce`: If `true`, command execution is tracked via flag files and only runs once per system

**Execution Order:**

- `preInstall`: Executed before package installation
- `postInstall`: Executed after package installation

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
python3 test/validate/validatePackages.py configs/macos.json [--quiet]
python3 test/validate/validateLinuxCommonPackages.py configs/linuxCommon.json [--all | package-manager] [--quiet]

# Other configs
python3 test/validate/validateFonts.py configs/fonts.json [--quiet]
python3 test/validate/validateRepositories.py configs/repositories.json [--quiet]
python3 test/validate/validateGitConfig.py configs/gitConfig.json [--quiet]
```

All validation scripts support `--help` and `--quiet` flags. See the test suite documentation for details.

## JSON Formatting

All JSON files follow these conventions:

- **Indentation**: 4 spaces
- **Line Endings**: CRLF (`\r\n`)
- **Encoding**: UTF-8
- **Style**: Allman braces (opening brace on its own line)

Example:

```javascript
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
6. **Linux Common packages**: Only include packages in `linuxCommon.json` that exist in all supported Linux package managers (apt, yum, dnf, rpm, zypper, pacman)
